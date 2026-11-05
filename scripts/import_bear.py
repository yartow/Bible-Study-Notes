#!/usr/bin/env python3
"""Import the devotionals from Bear into the library.

Usage (run from the repository root):
  python3 scripts/import_bear.py [--dry-run] [--yes]
      Reads the notes straight from Bear's database (read-only); no export
      needed. See scripts/bear.py.
  python3 scripts/import_bear.py imports/2026-12-01 [--dry-run] [--yes]
      Fallback: imports a Markdown export made by hand from Bear, e.g.
      imports/2026-12-01/biblestudy:devotionals/

What it does:
  * Builds an export-shaped copy of the notes (or takes the given export),
    then deduplicates and sorts it in memory with organize_devotionals.py.
    An export folder itself is never changed.
  * Compares every devotional three ways:
      ours   = the note in biblestudy:devotionals/
      theirs = the note in the new export
      base   = the note in the previous export (kept on the git branch
               "bear-export")
    Bear-only changes are taken over, repo-only changes are kept, and when
    both sides changed, `git merge-file` merges them. If the same lines
    changed on both sides, the repo version stays and the Bear version is
    saved to biblestudy:devotionals/_conflicts/<date>/.
  * Notes that disappeared from Bear stay in the library and are reported.
  * After you confirm, it commits the library ("Import Bear export <date>")
    and moves the "bear-export" branch to the new export.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True  # keep scripts/__pycache__ out of the repo
sys.path.insert(0, str(Path(__file__).resolve().parent))
from organize_devotionals import DEFAULT_ROOT, FOLDER_NAMES, Planner  # noqa: E402
import bear  # noqa: E402

LIB = DEFAULT_ROOT  # "biblestudy:devotionals", relative to the repo root
SNAPSHOT_BRANCH = "bear-export"
CONFLICTS = "_conflicts"


# ---------- git helpers ----------
def git(*args: str, input: bytes | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], input=input, capture_output=True, check=check)


def git_out(*args: str) -> str:
    return git(*args).stdout.decode("utf-8", "surrogateescape").strip()


def blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n")


def snapshot_tree(rev: str) -> dict[str, str]:
    """Path -> blob id for every file in a snapshot commit."""
    out = git("ls-tree", "-r", "-z", rev).stdout.decode("utf-8", "surrogateescape")
    tree = {}
    for entry in filter(None, out.split("\0")):
        meta, path = entry.split("\t", 1)
        tree[path] = meta.split()[2]
    return tree


def write_blobs(contents: dict[str, bytes]) -> dict[str, str]:
    """Store contents as git blobs (no filters); return path -> blob id."""
    paths = list(contents)
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i, p in enumerate(paths):
            f = Path(tmp, str(i))
            f.write_bytes(contents[p])
            files.append(str(f))
        out = git("hash-object", "-w", "--no-filters", "--stdin-paths",
                  input="\n".join(files).encode()).stdout.decode().split()
    return dict(zip(paths, out))


def write_tree(blobs: dict[str, str]) -> str:
    """Build a git tree from path -> blob id, using a throwaway index."""
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(tmp, "index"))}
        info = "".join(f"100644 {b}\t{p}\n" for p, b in sorted(blobs.items()))
        subprocess.run(["git", "update-index", "--add", "--index-info"],
                       input=info.encode("utf-8", "surrogateescape"), env=env, check=True)
        return subprocess.run(["git", "write-tree"], env=env, capture_output=True,
                              check=True).stdout.decode().strip()


# ---------- export location ----------
def find_export(arg: str) -> tuple[Path, str]:
    folder = Path(arg)
    if not folder.is_dir():
        raise SystemExit(f"Not a folder: {folder}")
    m = re.search(r"\d{4}-\d{2}-\d{2}", folder.name)
    stamp = m.group(0) if m else date.today().isoformat()
    root = folder
    for _ in range(2):  # descend into a lone Bear folder such as biblestudy:devotionals/
        subs = [p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")]
        if not any(root.glob("*.md")) and len(subs) == 1:
            root = subs[0]
    return root, stamp


# ---------- planning ----------
@dataclass
class Result:
    new: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    merged: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    kept_repo: list[str] = field(default_factory=list)
    deleted_in_repo: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    unchanged: int = 0
    writes: dict[str, bytes] = field(default_factory=dict)  # library-relative path -> content


def merge3(ours: bytes, base: bytes, theirs: bytes) -> tuple[bytes, bool]:
    with tempfile.TemporaryDirectory() as tmp:
        o, b, t = (Path(tmp, n) for n in ("ours", "base", "theirs"))
        o.write_bytes(ours), b.write_bytes(base), t.write_bytes(theirs)
        p = git("merge-file", "-p", "-L", "repo", "-L", "previous Bear export",
                "-L", "new Bear export", str(o), str(b), str(t), check=False)
    if p.returncode < 0 or p.returncode > 127:
        raise SystemExit(f"git merge-file failed: {p.stderr.decode()}")
    return p.stdout, p.returncode == 0


def plan_import(lib: Path, export: dict[str, bytes], base: dict[str, str],
                stamp: str, text: dict[str, bool]) -> Result:
    r = Result()
    for path in sorted(export):
        theirs = export[path]
        file = lib / path
        ours = file.read_bytes() if file.exists() else None
        if ours is not None and text[path]:
            ours = lf(ours)
        base_id = base.get(path)
        if ours is None:
            if base_id is None:
                r.new.append(path)
                r.writes[path] = theirs
            else:
                r.deleted_in_repo.append(path)
            continue
        if theirs == ours:
            r.unchanged += 1
        elif base_id is not None and blob_id(theirs) == base_id:
            r.kept_repo.append(path)  # Bear unchanged, repo edited
        elif base_id is not None and blob_id(ours) == base_id:
            r.updated.append(path)  # repo unchanged, Bear edited
            r.writes[path] = theirs
        elif text[path]:
            base_data = git("cat-file", "blob", base_id).stdout if base_id else b""
            merged, clean = merge3(ours, base_data, theirs)
            if clean:
                r.merged.append(path)
                r.writes[path] = merged
            else:
                r.conflicts.append(path)
                r.writes[f"{CONFLICTS}/{stamp}/{path}"] = theirs
        else:  # an image changed on both sides
            r.conflicts.append(path)
            r.writes[f"{CONFLICTS}/{stamp}/{path}"] = theirs
    for path in sorted(base):
        if path not in export and path.endswith(".md") and (lib / path).exists():
            r.missing.append(path)
    return r


def report(r: Result, stamp: str, source: str, planner: Planner) -> str:
    def section(title: str, items: list[str], note: str = "") -> list[str]:
        out = [f"## {title} ({len(items)})", ""]
        if note:
            out += [note, ""]
        out += [f"- `{i}`" for i in items] or ["None."]
        return out + [""]

    dups = sum(n.action == "duplicate" for n in planner.notes)
    other = sum(n.action == "not-devotional" for n in planner.notes)
    lines = [f"# Bear Import {stamp}", "", f"Source: {source}", "",
             "## Summary", "",
             f"- Unchanged: {r.unchanged}",
             f"- New: {len(r.new)}",
             f"- Updated from Bear: {len(r.updated)}",
             f"- Merged (Bear and repo edits combined): {len(r.merged)}",
             f"- **Conflicts: {len(r.conflicts)}**",
             f"- Repo edits kept (Bear unchanged): {len(r.kept_repo)}",
             f"- Missing from this export (kept): {len(r.missing)}",
             f"- Deleted in the repo (not re-added): {len(r.deleted_in_repo)}",
             f"- Ignored in the export: {dups} exact duplicates, {other} non-devotionals", ""]
    lines += section("Conflicts", r.conflicts,
                     f"The repo version was kept. The Bear version is in "
                     f"`{CONFLICTS}/{stamp}/` under the same path. Merge it by hand, "
                     "then delete the copy.")
    lines += section("New", r.new)
    lines += section("Updated from Bear", r.updated)
    lines += section("Merged", r.merged, "Check these; both sides had changes.")
    lines += section("Repo Edits Kept", r.kept_repo)
    lines += section("Missing from This Export", r.missing,
                     "Deleted or renamed in Bear. The repo copy was kept.")
    lines += section("Deleted in the Repo", r.deleted_in_repo,
                     "These are in Bear but were deleted in the repo, so they were not re-added.")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export", nargs="?",
                    help="a Bear export folder (default: read straight from Bear)")
    ap.add_argument("--dry-run", action="store_true", help="report only; change nothing")
    ap.add_argument("--yes", action="store_true", help="apply without asking")
    args = ap.parse_args()

    repo = Path(git_out("rev-parse", "--show-toplevel"))
    lib = repo / LIB
    if git_out("status", "--porcelain", "--", str(lib)):
        raise SystemExit(f"{LIB}/ has uncommitted changes. Commit them first, then import.")

    with tempfile.TemporaryDirectory() as tmp:
        if args.export:
            export_root, stamp = find_export(args.export)
            print(f"Export: {export_root}  (date {stamp})")
        else:
            export_root, stamp = Path(tmp, "bear"), date.today().isoformat()
            count = len(bear.materialize(export_root))
            print(f"Read {count} notes from Bear ({bear.DB_PATH.name}, read-only)  (date {stamp})")
        run_import(args, repo, lib, export_root, stamp)


def run_import(args: argparse.Namespace, repo: Path, lib: Path, export_root: Path,
               stamp: str) -> None:

    # Base snapshot: the previous export. Bootstrap it from the current library.
    has_branch = git("rev-parse", "--verify", "--quiet", f"refs/heads/{SNAPSHOT_BRANCH}",
                     check=False).returncode == 0
    if has_branch:
        base_commit = SNAPSHOT_BRANCH
    else:
        print(f"First import: the current library (HEAD) becomes the baseline "
              f"on branch '{SNAPSHOT_BRANCH}'.")
        tree = git_out("rev-parse", f"HEAD:{LIB}")
        base_commit = git_out("commit-tree", tree, "-m", "Bear export baseline (library at first import)")
    base = {p: b for p, b in snapshot_tree(base_commit).items()
            if p.split("/", 1)[0] in FOLDER_NAMES}

    planner = Planner(export_root)
    planner.scan()
    planner.plan()
    export: dict[str, bytes] = {}
    is_text: dict[str, bool] = {}
    for note in planner.notes:
        if note.action == "keep":
            p = note.target.as_posix()
            export[p] = lf(planner.final_text(note).encode("utf-8", "surrogateescape"))
            is_text[p] = True
    for src, dest in planner.image_dest.items():
        if dest.parts[0] in FOLDER_NAMES:
            p = dest.as_posix()
            export[p] = (export_root / src).read_bytes()
            is_text[p] = False

    result = plan_import(lib, export, base, stamp, is_text)
    source = f"`{export_root}`" if args.export else "Bear database (read directly)"
    text = report(result, stamp, source, planner)
    summary = text.split("## Conflicts")[0].split("## Summary")[1].strip()
    print(summary)
    for c in result.conflicts:
        print(f"  conflict: {c}")

    changes = bool(result.writes)
    if args.dry_run:
        out = repo / "imports" / f"import-{stamp}-dry-run.md"
        out.parent.mkdir(exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"\nDry run. Report: {out}")
        return
    if not args.yes:
        if not sys.stdin.isatty():
            raise SystemExit("Not a terminal: re-run with --yes to apply.")
        if input("\nApply and commit? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Nothing changed.")
            return

    # Snapshot of this export: the merge base for the next import.
    old_snapshot = git_out("rev-parse", base_commit)
    new_tree = write_tree(write_blobs(export))
    if has_branch and new_tree == git_out("rev-parse", f"{old_snapshot}^{{tree}}"):
        new_snapshot = old_snapshot  # Bear content did not change
    else:
        new_snapshot = git_out("commit-tree", new_tree, "-p", old_snapshot,
                               "-m", f"Bear export {stamp}")
    undo_branch = (f"git branch -f {SNAPSHOT_BRANCH} {old_snapshot[:12]}" if has_branch
                   else f"git branch -D {SNAPSHOT_BRANCH}")

    committed = False
    if changes:
        for rel, data in result.writes.items():
            dest = lib / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        report_path = lib / "_removed" / f"import-report-{stamp}.md"
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(text, encoding="utf-8")
        git("add", "-A", "--", str(lib))
        message = (f"Import Bear export {stamp}\n\n"
                   f"Bear-Export: {new_snapshot}\nBear-Export-Previous: {old_snapshot}\n")
        git("commit", "-q", "-m", message, "--", str(lib))
        committed = True
    else:
        report_path = repo / "imports" / f"import-{stamp}-report.md"
        report_path.write_text(text, encoding="utf-8")
    git("update-ref", f"refs/heads/{SNAPSHOT_BRANCH}", new_snapshot)

    print(f"\nReport: {report_path}")
    if committed:
        print(f"Committed: Import Bear export {stamp}")
        print(f"Undo with:  git reset --hard HEAD~1 && {undo_branch}")
    elif new_snapshot != old_snapshot:
        print(f"No library changes. Bear snapshot updated (undo: {undo_branch}).")
    if result.conflicts:
        print(f"{len(result.conflicts)} conflict(s): see {LIB}/{CONFLICTS}/{stamp}/")


if __name__ == "__main__":
    main()
