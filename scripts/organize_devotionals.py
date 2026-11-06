#!/usr/bin/env python3
"""Organize devotional commentaries into numbered Bible-book folders.

What the script does:
  1. Classifies every Markdown note by its file name. A devotional commentary
     starts with an English Bible-book name and a chapter, e.g.
     "Genesis 3 (LSB).md", "Psalm 23.md" or "Luke 2436-53 (ESV).md"
     (Luke 24:36-53).
  2. Quarantines byte-identical duplicates and everything that is not a
     devotional in "_removed/". Nothing is deleted except .DS_Store files.
  3. Moves each devotional to "<NN>. <Book>/" ("01. Genesis/" through
     "66. Revelation/") and flattens year, translation and other subfolders.
     Images linked from a note move with it, and links are rewritten only
     when an image's path changes.
  4. Writes a manifest (for --undo) and a review report.

Usage (run from the repository root):
  python3 scripts/organize_devotionals.py            # dry run, moves nothing
  python3 scripts/organize_devotionals.py --apply    # carry out the plan
  python3 scripts/organize_devotionals.py --undo "biblestudy:devotionals/_removed/manifest-<stamp>.csv"
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, unquote

DEFAULT_ROOT = "biblestudy:devotionals"
REMOVED = "_removed"

# Canonical order, chapter count, and extra spellings seen in the notes.
BOOKS: list[tuple[str, int, tuple[str, ...]]] = [
    ("Genesis", 50, ()), ("Exodus", 40, ()), ("Leviticus", 27, ()),
    ("Numbers", 36, ()), ("Deuteronomy", 34, ()), ("Joshua", 24, ()),
    ("Judges", 21, ()), ("Ruth", 4, ()), ("1 Samuel", 31, ()),
    ("2 Samuel", 24, ()), ("1 Kings", 22, ()), ("2 Kings", 25, ()),
    ("1 Chronicles", 29, ()), ("2 Chronicles", 36, ()), ("Ezra", 10, ()),
    ("Nehemiah", 13, ()), ("Esther", 10, ()), ("Job", 42, ()),
    ("Psalms", 150, ("Psalm",)), ("Proverbs", 31, ()),
    ("Ecclesiastes", 12, ()),
    ("Song of Songs", 8, ("Song of Song", "Song of Solomon")),
    ("Isaiah", 66, ()), ("Jeremiah", 52, ()), ("Lamentations", 5, ()),
    ("Ezekiel", 48, ()), ("Daniel", 12, ()), ("Hosea", 14, ()),
    ("Joel", 3, ()), ("Amos", 9, ()), ("Obadiah", 1, ()), ("Jonah", 4, ()),
    ("Micah", 7, ()), ("Nahum", 3, ()), ("Habakkuk", 3, ("Habbakuk",)),
    ("Zephaniah", 3, ()), ("Haggai", 2, ()),
    ("Zechariah", 14, ("Zecheriah",)), ("Malachi", 4, ()),
    ("Matthew", 28, ()), ("Mark", 16, ()), ("Luke", 24, ()),
    ("John", 21, ()), ("Acts", 28, ()), ("Romans", 16, ()),
    ("1 Corinthians", 16, ()), ("2 Corinthians", 13, ()),
    ("Galatians", 6, ()), ("Ephesians", 6, ()), ("Philippians", 4, ()),
    ("Colossians", 4, ()), ("1 Thessalonians", 5, ()),
    ("2 Thessalonians", 3, ()), ("1 Timothy", 6, ()), ("2 Timothy", 4, ()),
    ("Titus", 3, ()), ("Philemon", 1, ()), ("Hebrews", 13, ()),
    ("James", 5, ()), ("1 Peter", 5, ()), ("2 Peter", 3, ()),
    ("1 John", 5, ()), ("2 John", 1, ()), ("3 John", 1, ()),
    ("Jude", 1, ()), ("Revelation", 22, ()),
]

# Only used to explain why a note was quarantined.
DUTCH_BOOK_WORDS = {
    "richteren", "numeri", "jozua", "judas", "ezechiël", "filippenzen",
    "timotheüs", "marcus", "matteüs", "mattheüs", "lukas", "johannes",
    "handelingen", "romeinen", "hebreeën", "openbaring", "openbaringen",
    "jesaja", "jeremia", "psalmen", "spreuken", "prediker", "hooglied",
    "daniël", "kronieken", "koningen", "samuël", "thessalonicenzen",
    "korintiërs", "efeziërs", "kolossenzen", "galaten", "jakobus", "petrus",
}

IMPORT_FOLDERS = re.compile(r"^(toaddfrom.*|essay|questions)$", re.I)
# An image link ![](x.png), or a plain link [x.pdf](x.pdf) to an attached file.
FILE_LINK = re.compile(r"(!?\[[^\]]*\]\()(<[^>]+>|[^)\s]+)(\))")
URL_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)  # http:, bear:, data:
TAG = re.compile(r"#biblestudy/devotionals/([0-9a-z]+)", re.I)
TRANSLATION = re.compile(r"\(([A-Z]{2,5})\)")


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def squash(text: str) -> str:
    """Lowercase, no spaces: '1 Kings' -> '1kings'."""
    return re.sub(r"\s+", "", nfc(text).casefold())


@dataclass(frozen=True)
class Book:
    index: int
    name: str
    chapters: int
    spellings: tuple[str, ...]

    @property
    def folder(self) -> str:
        return f"{self.index:02d}. {self.name}"

    @property
    def keys(self) -> set[str]:
        return {squash(s) for s in self.spellings}


BOOK_LIST = [Book(i, n, c, (n, *alts)) for i, (n, c, alts) in enumerate(BOOKS, 1)]
SPELLING_TO_BOOK = {nfc(s).casefold(): b for b in BOOK_LIST for s in b.spellings}
FOLDER_NAMES = {b.folder for b in BOOK_LIST}
_alternation = "|".join(
    re.escape(s) for s in sorted(SPELLING_TO_BOOK, key=len, reverse=True)
)
TITLE = re.compile(
    rf"^(?P<book>{_alternation})(?=[\s(.]|$)\s*(?P<num>\d+(?:-\d+)?)?(?P<rest>.*)$",
    re.I,
)


@dataclass
class Parsed:
    book: Book
    chapter: int | None
    verses: str | None
    translation: str | None
    range_note: str | None  # set when a collapsed verse range was split


def parse_title(stem: str) -> Parsed | None:
    """Return book/chapter info if the note title is a devotional title."""
    title = re.sub(r"^#+\s*", "", nfc(stem)).strip()
    m = TITLE.match(title)
    if not m:
        return None
    book = SPELLING_TO_BOOK[m.group("book").casefold()]
    num, rest = m.group("num"), m.group("rest")
    tr = TRANSLATION.search(rest)
    translation = tr.group(1) if tr else None
    if num is None:
        # Single-chapter books may leave out the chapter: "2 John (ESV)".
        if book.chapters == 1:
            return Parsed(book, 1, None, translation, None)
        return None
    first, _, last = num.partition("-")
    if int(first) <= book.chapters and int(first) > 0:
        verses = None
        if last:  # a chapter range such as "15-16"
            verses = f"chapters {first}–{last}"
        return Parsed(book, int(first), verses, translation, None)
    # Collapsed reference: "2436-53" -> 24:36-53, "830" -> 8:30.
    for k in range(len(first) - 1, 0, -1):
        chap, verse = int(first[:k]), first[k:]
        if 1 <= chap <= book.chapters and not verse.startswith("0"):
            verses = verse + (f"–{last}" if last else "")
            return Parsed(book, chap, verses, translation,
                          f"{book.name} {chap}:{verses}")
    return None


def quarantine_reason(stem: str) -> str:
    title = re.sub(r"^#+\s*", "", nfc(stem)).strip()
    if re.match(r"^\d{8}|^\d{4}-\d{2}-\d{2}", title):
        return "dated note (sermon, meeting, or journal entry)"
    words = re.findall(r"[^\W\d_]+", title.casefold())
    if any(w in DUTCH_BOOK_WORDS for w in words[:2]):
        return "Dutch book name"
    if TITLE.match(title):
        return "book name without a chapter"
    return "title is not '<Book> <chapter>'"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class Note:
    rel: Path  # relative to root
    digest: str
    parsed: Parsed | None
    action: str = ""  # keep | duplicate | not-devotional
    target: Path | None = None  # relative to root
    reason: str = ""
    renamed_from_conflict: bool = False
    links: dict[str, Path] = field(default_factory=dict)  # link text -> image rel path

    @property
    def top_folder(self) -> str:
        return self.rel.parts[0] if len(self.rel.parts) > 1 else ""


def in_matching_folder(note: Note) -> bool:
    if not note.parsed or not note.top_folder:
        return False
    if note.top_folder == note.parsed.book.folder:  # e.g. "01. Genesis"
        return True
    top = squash(note.top_folder)
    return any(k == top or k.startswith(top) for k in note.parsed.book.keys)


def keeper_rank(note: Note) -> tuple:
    return (
        note.parsed is None,
        not in_matching_folder(note),
        bool(IMPORT_FOLDERS.match(note.top_folder)),
        len(note.rel.parts),
        str(note.rel),
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="surrogateescape")


def image_links(root: Path, note_rel: Path) -> tuple[dict[str, Path], list[str]]:
    """Map each local image or attachment link in a note to the file it points to.

    Returns the resolved links and the image links whose file does not exist.
    A plain link counts only if it points to an existing file that is not a note.
    """
    out: dict[str, Path] = {}
    broken: list[str] = []
    text = read_text(root / note_rel)
    for m in FILE_LINK.finditer(text):
        raw = m.group(2).strip("<>")
        is_image = m.group(1).startswith("!")
        if URL_SCHEME.match(raw) or raw.startswith("#"):
            continue
        if not is_image and unquote(raw).lower().endswith(".md"):
            continue
        candidate = (root / note_rel.parent / unquote(raw)).resolve()
        try:
            rel = candidate.relative_to(root.resolve())
        except ValueError:
            if is_image:
                broken.append(raw)
            continue
        if candidate.is_file():
            out[m.group(2)] = rel
        elif is_image:
            broken.append(raw)
    return out, broken


class Planner:
    def __init__(self, root: Path):
        self.root = root
        self.notes: list[Note] = []
        self.images: dict[Path, str] = {}  # rel -> sha256
        self.moves: list[tuple[Path, str, Path, str]] = []  # src, action, dst, sha
        self.rewrites: dict[Path, dict[str, str]] = {}  # final note rel -> {old: new}
        self.broken: list[tuple[Path, str]] = []
        self.ds_store: list[Path] = []
        self.image_dest: dict[Path, Path] = {}  # image src rel -> destination rel

    # ---------- scanning ----------
    def scan(self) -> None:
        for dirpath, dirnames, filenames in os.walk(self.root):
            d = Path(dirpath)
            rel_dir = d.relative_to(self.root)
            if rel_dir.parts and rel_dir.parts[0] == REMOVED:
                dirnames[:] = []
                continue
            dirnames.sort()
            for name in sorted(filenames):
                rel = rel_dir / name
                if name == ".DS_Store":
                    self.ds_store.append(rel)
                elif name.lower().endswith(".md"):
                    self.notes.append(Note(rel, sha256(self.root / rel),
                                           parse_title(Path(name).stem)))
                else:
                    self.images[rel] = sha256(self.root / rel)
        for note in self.notes:
            note.links, broken = image_links(self.root, note.rel)
            self.broken += [(note.rel, link) for link in broken]

    # ---------- planning ----------
    def plan(self) -> None:
        by_hash: dict[str, list[Note]] = defaultdict(list)
        for note in self.notes:
            by_hash[note.digest].append(note)
        for group in by_hash.values():
            group.sort(key=keeper_rank)
            for dup in group[1:]:
                dup.action = "duplicate"
                dup.reason = f"identical to {group[0].rel}"
                dup.target = Path(REMOVED, "duplicates", dup.rel)

        for note in self.notes:
            if note.action:
                continue
            if note.parsed is None:
                note.action = "not-devotional"
                note.reason = quarantine_reason(note.rel.stem)
                note.target = Path(REMOVED, "not-devotional", note.rel)
            else:
                note.action = "keep"

        taken: dict[str, set[str]] = defaultdict(set)  # folder -> casefolded names
        keepers = sorted((n for n in self.notes if n.action == "keep"), key=keeper_rank)
        # Notes already in place claim their names first (makes reruns safe).
        for note in keepers:
            folder = note.parsed.book.folder
            if note.rel.parent == Path(folder):
                note.target = note.rel
                taken[folder].add(nfc(note.rel.name).casefold())
        for note in keepers:
            if note.target is not None:
                continue
            folder = note.parsed.book.folder
            name = nfc(note.rel.name)
            if name.casefold() in taken[folder] or (self.root / folder / name).exists():
                source = note.rel.parent.name or "top level"
                base = f"{Path(name).stem} — from {source}"
                name, n = f"{base}.md", 2
                while name.casefold() in taken[folder] or (self.root / folder / name).exists():
                    name, n = f"{base} {n}.md", n + 1
                note.renamed_from_conflict = True
            taken[folder].add(name.casefold())
            note.target = Path(folder, name)

        for note in self.notes:
            if note.target != note.rel:
                self.moves.append((note.rel, f"note:{note.action}", note.target, note.digest))

        self.plan_images()

    def plan_images(self) -> None:
        claimed: dict[Path, Path] = {}  # image src -> destination
        used_dest: set[Path] = set()
        for note in sorted((n for n in self.notes if n.action == "keep"), key=keeper_rank):
            note_dir = note.target.parent
            for link, src in note.links.items():
                if src in claimed:
                    dest = claimed[src]
                else:
                    if note.target == note.rel and src.parent.parent == note_dir:
                        dest = src  # note and image already in place
                    else:
                        dest = note_dir / note.target.stem / src.name
                        n = 2
                        while dest in used_dest or ((self.root / dest).exists() and dest != src):
                            dest = dest.with_name(f"{src.stem}-{n}{src.suffix}")
                            n += 1
                    claimed[src] = dest
                    used_dest.add(dest)
                new_link = quote(os.path.relpath(dest, note_dir), safe="/")
                if unquote(link.strip("<>")) != unquote(new_link):
                    self.rewrites.setdefault(note.target, {})[link] = new_link

        for note in self.notes:  # images of quarantined notes travel with them
            if note.action == "keep":
                continue
            category = note.target.parts[1]
            for src in note.links.values():
                if src not in claimed:
                    claimed[src] = Path(REMOVED, category, src)
        self.image_dest = claimed
        for src, dest in claimed.items():
            if dest != src:
                self.moves.append((src, "image", dest, self.images[src]))
        for src in self.images:
            if src not in claimed:
                self.moves.append((src, "image:orphan", Path(REMOVED, "orphans", src),
                                   self.images[src]))

    def final_text(self, note: Note) -> str:
        """The note's text with its planned image-link rewrites applied."""
        text = read_text(self.root / note.rel)
        changes = self.rewrites.get(note.target, {})
        if not changes:
            return text

        def swap(m: re.Match) -> str:
            new = changes.get(m.group(2))
            return m.group(1) + new + m.group(3) if new else m.group(0)

        return FILE_LINK.sub(swap, text)

    # ---------- execution ----------
    def apply(self, out_dir: Path, stamp: str) -> Path:
        manifest = out_dir / f"manifest-{stamp}.csv"
        backups = Path(REMOVED, f"link-backups-{stamp}")
        with manifest.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["original", "action", "new", "sha256"])
            for src, action, dst, digest in self.moves:
                s, d = self.root / src, self.root / dst
                if d.exists():
                    raise SystemExit(f"Refusing to overwrite {d}")
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(s, d)
                w.writerow([src, action, dst, digest])
                fh.flush()
            for note_rel, changes in self.rewrites.items():
                path = self.root / note_rel
                backup = backups / note_rel
                (self.root / backup).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, self.root / backup)
                text = read_text(path)

                def swap(m: re.Match, changes=changes) -> str:
                    new = changes.get(m.group(2))
                    return m.group(1) + new + m.group(3) if new else m.group(0)

                path.write_text(FILE_LINK.sub(swap, text), encoding="utf-8",
                                errors="surrogateescape")
                w.writerow([note_rel, "rewrite-links", backup, ""])
            for rel in self.ds_store:
                (self.root / rel).unlink(missing_ok=True)
        remove_empty_dirs(self.root)
        return manifest

    # ---------- reporting ----------
    def report(self) -> str:
        keep = [n for n in self.notes if n.action == "keep"]
        dups = [n for n in self.notes if n.action == "duplicate"]
        rest = [n for n in self.notes if n.action == "not-devotional"]
        lines = ["# Devotionals Organizer Report", "",
                 f"Generated {datetime.now():%Y-%m-%d %H:%M}.", "",
                 "## Summary", "",
                 f"- Notes scanned: {len(self.notes)}",
                 f"- Devotionals kept: {len(keep)}",
                 f"- Exact duplicates quarantined: {len(dups)}",
                 f"- Non-devotionals quarantined: {len(rest)}",
                 f"- Images: {len(self.images)} "
                 f"({sum(1 for m in self.moves if m[1] == 'image:orphan')} unused)",
                 f"- Notes with rewritten image links: {len(self.rewrites)}",
                 f"- Notes renamed to avoid a name conflict: "
                 f"{sum(n.renamed_from_conflict for n in keep)}", ""]

        lines += ["## Devotionals per Book", "", "| Folder | Notes |", "| --- | ---: |"]
        per_book = defaultdict(int)
        for n in keep:
            per_book[n.parsed.book.folder] += 1
        for b in BOOK_LIST:
            if per_book[b.folder]:
                lines.append(f"| {b.folder} | {per_book[b.folder]} |")
        lines.append("")

        lines += ["## Near-Duplicates to Review", "",
                  "Same book, chapter, and translation, but different text.", ""]
        groups = defaultdict(list)
        for n in keep:
            p = n.parsed
            groups[(p.book.index, p.chapter, p.verses, p.translation)].append(n)
        for key in sorted(groups, key=lambda k: (k[0], k[1] or 0, str(k[2]), str(k[3]))):
            members = groups[key]
            if len(members) > 1:
                p = members[0].parsed
                label = f"{p.book.name} {p.chapter}"
                label += f":{p.verses}" if p.verses and not p.verses.startswith("ch") else ""
                label += f" ({p.translation})" if p.translation else ""
                lines.append(f"- **{label}** in `{p.book.folder}/`")
                for n in sorted(members, key=lambda n: str(n.target)):
                    size = (self.root / n.rel).stat().st_size if (self.root / n.rel).exists() \
                        else (self.root / n.target).stat().st_size
                    lines.append(f"  - `{n.target.name}` ({size:,} bytes; from `{n.rel}`)")
        lines.append("")

        lines += ["## Renamed Because of a Name Conflict", ""]
        lines += [f"- `{n.rel}` → `{n.target}`" for n in keep if n.renamed_from_conflict] or ["None."]
        lines.append("")

        lines += ["## Moved to a Different Book Folder", "",
                  "These notes were filed under another book.", ""]
        misfiled = [n for n in keep if n.top_folder and not in_matching_folder(n)
                    and not IMPORT_FOLDERS.match(n.top_folder) and n.target != n.rel]
        lines += [f"- `{n.rel}` → `{n.target}`" for n in misfiled] or ["None."]
        lines.append("")

        lines += ["## Collapsed Verse References", "",
                  "Colons are missing from these file names; check the reading.", ""]
        ranged = [n for n in keep if n.parsed.range_note]
        lines += [f"- `{n.rel.name}` read as {n.parsed.range_note}" for n in ranged] or ["None."]
        lines.append("")

        lines += ["## Tag Does Not Match the File Name", ""]
        mism = []
        for n in keep:
            path = self.root / n.rel
            text_lines = read_text(path).splitlines()
            edge = "\n".join(text_lines[:5] + text_lines[-5:])
            tags = {t.casefold() for t in TAG.findall(edge)}
            if tags and not any(t in n.parsed.book.keys or any(k.startswith(t) for k in n.parsed.book.keys)
                                for t in tags):
                mism.append(f"- `{n.target}` has `#biblestudy/devotionals/{'`, `'.join(sorted(tags))}`")
        lines += mism or ["None."]
        lines.append("")

        if self.broken:
            lines += ["## Broken Image Links", ""]
            lines += [f"- `{r}`: `{l}`" for r, l in self.broken]
            lines.append("")

        lines += ["## Quarantined Notes", "", "### Exact duplicates", ""]
        lines += [f"- `{n.rel}`: {n.reason}" for n in sorted(dups, key=lambda n: str(n.rel))] or ["None."]
        lines += ["", "### Not devotionals", ""]
        by_reason = defaultdict(list)
        for n in rest:
            by_reason[n.reason].append(n)
        for reason in sorted(by_reason):
            lines.append(f"**{reason[0].upper() + reason[1:]}**")
            lines.append("")
            lines += [f"- `{n.rel}`" for n in sorted(by_reason[reason], key=lambda n: str(n.rel))]
            lines.append("")
        return "\n".join(lines)


def remove_empty_dirs(root: Path) -> None:
    for dirpath, _, _ in sorted(os.walk(root), key=lambda t: -len(t[0])):
        d = Path(dirpath)
        if d == root:
            continue
        leftovers = [p for p in d.iterdir() if p.name != ".DS_Store"]
        if not leftovers:
            for p in d.iterdir():
                p.unlink()
            d.rmdir()


def undo(root: Path, manifest: Path) -> None:
    with manifest.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for row in reversed(rows):
        orig, new = root / row["original"], root / row["new"]
        if row["action"] == "rewrite-links":
            if new.exists():
                shutil.copy2(new, orig)
                new.unlink()
            continue
        if not new.exists():
            print(f"skip (missing): {row['new']}", file=sys.stderr)
            continue
        if orig.exists():
            print(f"skip (occupied): {row['original']}", file=sys.stderr)
            continue
        orig.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(new, orig)
    remove_empty_dirs(root)
    print(f"Undid {len(rows)} actions from {manifest}.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=DEFAULT_ROOT, help="folder with the notes")
    ap.add_argument("--apply", action="store_true", help="carry out the moves")
    ap.add_argument("--undo", metavar="MANIFEST", help="reverse an applied run")
    ap.add_argument("--report-dir", help="where to write the report (default: <root>/_removed)")
    args = ap.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        raise SystemExit(f"Not a folder: {root}")
    if args.undo:
        undo(root, Path(args.undo))
        return

    planner = Planner(root)
    planner.scan()
    planner.plan()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path(args.report_dir) if args.report_dir else root / REMOVED
    out_dir.mkdir(parents=True, exist_ok=True)
    report_text = planner.report()  # before moving, while sources still exist
    kind = "report" if args.apply else "dry-run-report"
    report_path = out_dir / f"{kind}-{stamp}.md"
    report_path.write_text(report_text, encoding="utf-8")

    summary = report_text.split("## Devotionals per Book")[0]
    print(summary.strip())
    print(f"\nPlanned moves: {len(planner.moves)}; link rewrites: {len(planner.rewrites)}")
    print(f"Report: {report_path}")
    if args.apply:
        manifest = planner.apply(out_dir, stamp)
        print(f"Applied. Manifest for --undo: {manifest}")
    else:
        print("Dry run: nothing was moved. Re-run with --apply to carry out the plan.")


if __name__ == "__main__":
    main()
