#!/usr/bin/env python3
"""Send edits made in the repo (e.g. style fixes) back into Bear.

Usage (run from the repository root):
  python3 scripts/push_to_bear.py --dry-run          # report only
  python3 scripts/push_to_bear.py                    # asks before pushing
  python3 scripts/push_to_bear.py --only "15. Ezra/Ezra 7 (LSB).md"
  python3 scripts/push_to_bear.py --yes              # push without asking

What it does:
  * Reads the notes from Bear's database (read-only) and works out which Bear
    note each library note came from, the same way the import does.
  * A note is pushed only if the repo text differs from Bear and Bear still
    holds the last synced version. That is the "bear-export" snapshot, or,
    before the first import, any committed version of the note. That way an
    edit made in Bear is never overwritten; such notes are listed as
    "changed in Bear" and need an import first.
  * A note with an unmerged Bear version in _conflicts/ is skipped too: that
    copy holds Bear edits the repo doesn't have yet.
  * Image links keep Bear's own form: the repo edit is merged into Bear's
    text with `git merge-file`.
  * Each note is written through Bear's URL API (add-text, replace_all). Bear's
    text is first backed up to imports/_bear-backups/<timestamp>/, and the
    database is read again to confirm the change.
  * Nothing is committed to the current branch. Each push is recorded as a
    new commit on "bear-export" (never a rewrite), so the next push and
    import know that Bear now holds the pushed text.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bear  # noqa: E402
from import_bear import (CONFLICTS, LIB, SNAPSHOT_BRANCH, git, git_out, lf, merge3,  # noqa: E402
                         snapshot_tree, write_blobs, write_tree)
from organize_devotionals import FOLDER_NAMES, Planner  # noqa: E402


@dataclass
class Push:
    path: str  # library-relative
    note: bear.BearNote
    new_text: str  # in Bear's form


@dataclass
class Plan:
    in_sync: int = 0
    pushes: list[Push] = field(default_factory=list)
    changed_in_bear: list[str] = field(default_factory=list)
    open_conflict: list[str] = field(default_factory=list)
    title_changed: list[str] = field(default_factory=list)
    no_merge: list[str] = field(default_factory=list)
    not_in_bear: list[str] = field(default_factory=list)


def title_line(text: str) -> str:
    return text.split("\n", 1)[0].strip()


def history(path: str) -> set[bytes]:
    """Every committed version of a library note, following renames."""
    out = git_out("-c", "core.quotePath=false", "log", "--follow", "--name-only", "--format=%x00%H", "--", f"{LIB}/{path}")
    versions = set()
    for chunk in filter(None, out.split("\0")):
        lines = [l for l in chunk.splitlines() if l.strip()]
        if len(lines) >= 2:
            blob = git("cat-file", "blob", f"{lines[0]}:{lines[1]}", check=False)
            if blob.returncode == 0:
                versions.add(lf(blob.stdout))
    return versions


def has_snapshot() -> bool:
    return git("rev-parse", "--verify", "--quiet", f"refs/heads/{SNAPSHOT_BRANCH}",
               check=False).returncode == 0


def bear_versions() -> dict[str, tuple[bear.BearNote, str]]:
    """Library path -> (Bear note, its text in repo form), mapped as the import does."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        written = bear.materialize(root, link_images=True)
        planner = Planner(root)
        planner.scan()
        planner.plan()
        out: dict[str, tuple[bear.BearNote, str]] = {}
        for n in planner.notes:
            if n.action == "keep" and n.target.parts[0] in FOLDER_NAMES:
                text = lf(planner.final_text(n).encode("utf-8", "surrogateescape"))
                out[n.target.as_posix()] = (written[n.rel], text.decode("utf-8", "surrogateescape"))
    return out


def open_conflicts(lib: Path) -> set[str]:
    """Library paths that still have an unmerged Bear copy in _conflicts/<date>/."""
    out = set()
    for day in (lib / CONFLICTS).glob("*"):
        if day.is_dir():
            out |= {f.relative_to(day).as_posix() for f in day.rglob("*.md")}
    return out


def plan_push(lib: Path, only: str | None) -> Plan:
    has_branch = has_snapshot()
    snapshot = snapshot_tree(SNAPSHOT_BRANCH) if has_branch else {}
    p = Plan()
    from_bear = bear_versions()
    conflicted = open_conflicts(lib)

    paths = sorted(f.relative_to(lib).as_posix() for f in lib.rglob("*.md")
                   if f.relative_to(lib).parts[0] in FOLDER_NAMES)
    if only:
        only = only.removeprefix(f"{LIB}/")
        if only not in paths:
            raise SystemExit(f"Not a note in the library: {only}")
        paths = [only]

    for path in paths:
        repo_text = lf((lib / path).read_bytes()).decode("utf-8", "surrogateescape")
        if path not in from_bear:
            p.not_in_bear.append(path)
            continue
        note, bear_text = from_bear[path]  # bear_text: Bear's note in repo form
        if bear_text == repo_text:
            p.in_sync += 1
            continue
        if path in conflicted:
            p.open_conflict.append(path)
            continue
        synced = bear_text.encode("utf-8", "surrogateescape")
        if has_branch:
            base_id = snapshot.get(path)
            ok = base_id is not None and lf(git("cat-file", "blob", base_id).stdout) == synced
        else:
            ok = synced in history(path)
        if not ok:
            p.changed_in_bear.append(path)
            continue
        if title_line(repo_text) != title_line(bear_text):
            p.title_changed.append(path)
            continue
        merged, clean = merge3(repo_text.encode("utf-8", "surrogateescape"), synced,
                               note.text.encode("utf-8", "surrogateescape"))
        if not clean:
            p.no_merge.append(path)
            continue
        p.pushes.append(Push(path, note, merged.decode("utf-8", "surrogateescape")))
    return p


def summary(p: Plan) -> str:
    def section(title: str, items: list[str], note: str) -> list[str]:
        if not items:
            return []
        return ["", f"{title} ({len(items)}): {note}"] + [f"  {i}" for i in items]

    lines = [f"In sync with Bear: {p.in_sync}",
             f"To push: {len(p.pushes)}",
             f"Changed in Bear (import first): {len(p.changed_in_bear)}",
             f"Unmerged conflict (skipped): {len(p.open_conflict)}",
             f"Title changed (skipped): {len(p.title_changed)}",
             f"Could not merge (skipped): {len(p.no_merge)}",
             f"Not found in Bear: {len(p.not_in_bear)}"]
    lines += section("To push", [x.path for x in p.pushes], "repo edits that go to Bear")
    lines += section("Changed in Bear", p.changed_in_bear,
                     "Bear has edits the repo doesn't have yet; run import_bear.py first")
    lines += section("Unmerged conflict", p.open_conflict,
                     f"merge the Bear copy in {CONFLICTS}/<date>/ into the note first")
    lines += section("Title changed", p.title_changed,
                     "changing the first line would rename the note in Bear; do it in Bear")
    lines += section("Could not merge", p.no_merge,
                     "the edit touches an image line; copy it into Bear by hand")
    lines += section("Not found in Bear", p.not_in_bear,
                     "no Bear note maps to this file (renamed, deleted, or archived in Bear)")
    return "\n".join(lines)


def record_pushes(lib: Path, pushed: list[str], stamp: str) -> list[str]:
    """Record the pushed notes on bear-export as Bear's last synced version.

    Bear is read again, and a note is recorded only if Bear, in repo form, now
    matches the repo exactly. Adds a commit on top of the snapshot; never
    rewrites it. Returns the notes that could not be recorded.
    """
    if not has_snapshot():
        print(f"No '{SNAPSHOT_BRANCH}' snapshot yet; run import_bear.py once to create it.")
        return []
    now = bear_versions()
    recorded, problems = {}, []
    for path in pushed:
        repo_bytes = lf((lib / path).read_bytes())
        if path in now and now[path][1].encode("utf-8", "surrogateescape") == repo_bytes:
            recorded[path] = repo_bytes
        else:
            problems.append(f"{path}: pushed, but Bear doesn't match the repo exactly; "
                            "not recorded (the next import will sort it out)")
    if recorded:
        old = git_out("rev-parse", SNAPSHOT_BRANCH)
        tree = {**snapshot_tree(old), **write_blobs(recorded)}
        new = git_out("commit-tree", write_tree(tree), "-p", old, "-m",
                      f"Bear push {stamp}\n\n" + "\n".join(sorted(recorded)) + "\n")
        git("update-ref", f"refs/heads/{SNAPSHOT_BRANCH}", new, old)
        print(f"Recorded {len(recorded)} push(es) on '{SNAPSHOT_BRANCH}' "
              f"(undo: git branch -f {SNAPSHOT_BRANCH} {old[:12]})")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="report only; change nothing")
    ap.add_argument("--yes", action="store_true", help="push without asking")
    ap.add_argument("--only", metavar="PATH", help="push only this note (library-relative path)")
    args = ap.parse_args()

    repo = Path(git_out("rev-parse", "--show-toplevel"))
    lib = repo / LIB
    if git_out("status", "--porcelain", "--", str(lib)):
        raise SystemExit(f"{LIB}/ has uncommitted changes. Commit them first, then push.")

    p = plan_push(lib, args.only)
    print(summary(p))
    if not p.pushes or args.dry_run:
        print("\nDry run; nothing pushed." if args.dry_run else "\nNothing to push.")
        return
    if not args.yes:
        if not sys.stdin.isatty():
            raise SystemExit("Not a terminal: re-run with --yes to push.")
        if input(f"\nPush {len(p.pushes)} note(s) to Bear? [y/N] ").strip().lower() not in ("y", "yes"):
            print("Nothing pushed.")
            return

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backups = repo / "imports" / "_bear-backups" / stamp
    failed, pushed = [], []
    for push in p.pushes:
        current = bear.note_text(push.note.id)
        if current != push.note.text:  # edited in Bear while we were planning
            failed.append(f"{push.path}: changed in Bear just now; skipped")
            continue
        backup = backups / push.path
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_text(current, encoding="utf-8", errors="surrogateescape")
        bear.replace_text(push.note.id, push.new_text)
        if bear.wait_for_text(push.note.id, push.new_text):
            print(f"pushed  {push.path}")
            pushed.append(push.path)
        else:
            failed.append(f"{push.path}: Bear did not confirm the change")
    print(f"\nBear's previous text is backed up in {backups.relative_to(repo)}/")
    if pushed:
        failed += record_pushes(lib, pushed, stamp)
    if failed:
        print(f"{len(failed)} failed:")
        for f in failed:
            print(f"  {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
