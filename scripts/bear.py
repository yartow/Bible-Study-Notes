"""Read devotionals straight from Bear, and write edits back through Bear's URL API.

Reading uses Bear's database, opened read-only. Writing never touches the
database, which would break iCloud sync. It goes through the official
x-callback-url API ("add-text" with mode=replace_all), and the database is
then read again to confirm the change.

Bear stores image links bare, e.g. ![](Timeline.png). Its Markdown export,
and therefore the repo, prefixes them with the note's folder:
![](Ezra%207%20%28LSB%29/Timeline.png). to_export_form() and
to_bear_form() convert between the two.
"""

from __future__ import annotations

import os
import re
import shutil
import sqlite3
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote, unquote

BEAR_DATA = Path.home() / "Library/Group Containers/9K33E3U3T4.net.shinyfrog.bear/Application Data"
DB_PATH = BEAR_DATA / "database.sqlite"
IMAGES_DIR = BEAR_DATA / "Local Files" / "Note Images"
ROOT_TAG = "biblestudy/devotionals"

IMAGE_LINK = re.compile(r"(!\[[^\]]*\]\()(<[^>]+>|[^)\s]+)(\))")
UNSAFE_NAME = re.compile(r'[:/\\?*<>|"]')


@dataclass
class BearNote:
    id: str
    title: str
    text: str
    created: float
    modified: float
    tags: list[str] = field(default_factory=list)  # below ROOT_TAG, e.g. "genesis/2024"
    images: dict[str, Path] = field(default_factory=dict)  # file name -> file on disk

    @property
    def file_stem(self) -> str:
        """The note's name in an export: the title without characters files can't hold."""
        return UNSAFE_NAME.sub("", self.title).strip() or "Untitled"


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise SystemExit(f"Bear database not found: {DB_PATH}")
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def devotional_notes(con: sqlite3.Connection | None = None) -> list[BearNote]:
    """Every live, unencrypted note tagged #biblestudy/devotionals (or a subtag)."""
    con = con or connect()
    rows = con.execute(
        """SELECT Z_PK, ZUNIQUEIDENTIFIER, ZTITLE, ZTEXT, ZCREATIONDATE, ZMODIFICATIONDATE
           FROM ZSFNOTE
           WHERE COALESCE(ZTRASHED, 0) = 0 AND COALESCE(ZPERMANENTLYDELETED, 0) = 0
             AND COALESCE(ZARCHIVED, 0) = 0 AND COALESCE(ZENCRYPTED, 0) = 0 AND ZTEXT LIKE ?""", (f"%#{ROOT_TAG}%",)).fetchall()
    notes = {r["Z_PK"]: BearNote(r["ZUNIQUEIDENTIFIER"], r["ZTITLE"] or "", r["ZTEXT"] or "",
                                 r["ZCREATIONDATE"] or 0, r["ZMODIFICATIONDATE"] or 0)
             for r in rows}
    tag_rows = con.execute(
        """SELECT nt.Z_5NOTES AS note, t.ZTITLE AS tag
           FROM Z_5TAGS nt JOIN ZSFNOTETAG t ON t.Z_PK = nt.Z_13TAGS
           WHERE t.ZTITLE = ? OR t.ZTITLE LIKE ?""", (ROOT_TAG, f"{ROOT_TAG}/%")).fetchall()
    for r in tag_rows:
        if r["note"] in notes:
            notes[r["note"]].tags.append(r["tag"][len(ROOT_TAG):].strip("/"))
    file_rows = con.execute(
        """SELECT ZNOTE, ZUNIQUEIDENTIFIER, ZFILENAME FROM ZSFNOTEFILE
           WHERE COALESCE(ZPERMANENTLYDELETED, 0) = 0 AND COALESCE(ZENCRYPTED, 0) = 0""").fetchall()
    for r in file_rows:
        if r["ZNOTE"] in notes and r["ZFILENAME"]:
            notes[r["ZNOTE"]].images[r["ZFILENAME"]] = IMAGES_DIR / r["ZUNIQUEIDENTIFIER"] / r["ZFILENAME"]
    return sorted(notes.values(), key=lambda n: (n.title, n.created, n.id))


def note_text(note_id: str, con: sqlite3.Connection | None = None) -> str | None:
    con = con or connect()
    row = con.execute("SELECT ZTEXT FROM ZSFNOTE WHERE ZUNIQUEIDENTIFIER = ?", (note_id,)).fetchone()
    return None if row is None else (row[0] or "")


# ---------- text forms ----------
def _is_local(link: str) -> bool:
    return not re.match(r"^[a-z][a-z0-9+.-]*:", link, re.I)


def to_export_form(text: str, stem: str, images: set[str] | None = None) -> str:
    """Bear text -> the text of the exported file (and of the repo note)."""
    prefix = quote(stem)

    def swap(m: re.Match) -> str:
        raw = m.group(2)
        bare = raw.strip("<>")
        if not _is_local(bare) or "/" in bare:
            return m.group(0)
        if images is not None and unquote(bare) not in images:
            return m.group(0)
        return f"{m.group(1)}{prefix}/{bare}{m.group(3)}"

    return IMAGE_LINK.sub(swap, text)


def to_bear_form(text: str) -> str:
    """Repo text -> Bear text: image links lose their folder prefix."""

    def swap(m: re.Match) -> str:
        bare = m.group(2).strip("<>")
        if not _is_local(bare) or "/" not in bare:
            return m.group(0)
        return f"{m.group(1)}{bare.rsplit('/', 1)[1]}{m.group(3)}"

    return IMAGE_LINK.sub(swap, text)


# ---------- export ----------
def export_layout(notes: list[BearNote]) -> list[tuple[BearNote, Path]]:
    """Where Bear's export puts each note: one copy per deepest tag folder.

    A note tagged #biblestudy/devotionals/genesis/2024 lands in genesis/2024/.
    Repeated names in a folder get " 2", " 3", … in order of creation.
    """
    placed: list[tuple[BearNote, Path]] = []
    by_folder: dict[str, list[BearNote]] = defaultdict(list)
    for note in notes:
        tags = set(note.tags) or {""}
        leaves = {t for t in tags if not any(o != t and o.startswith(t + "/" if t else "") for o in tags)}
        for folder in sorted(leaves):
            by_folder[folder].append(note)
    for folder, group in by_folder.items():
        seen: dict[str, int] = defaultdict(int)
        for note in sorted(group, key=lambda n: (n.created, n.id)):
            key = note.file_stem.casefold()
            seen[key] += 1
            stem = note.file_stem if seen[key] == 1 else f"{note.file_stem} {seen[key]}"
            placed.append((note, Path(folder, f"{stem}.md")))
    return placed


def materialize(dest: Path, notes: list[BearNote] | None = None) -> dict[Path, BearNote]:
    """Write a folder laid out like a Bear Markdown export.

    Returns each written note file (relative to dest) with its Bear note.
    """
    notes = notes if notes is not None else devotional_notes()
    written: dict[Path, BearNote] = {}
    for note, rel in export_layout(notes):
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        stem = rel.stem
        path.write_text(to_export_form(note.text, stem, set(note.images)), encoding="utf-8")
        for name, src in note.images.items():
            if src.is_file():
                img = path.parent / stem / name
                img.parent.mkdir(exist_ok=True)
                shutil.copy2(src, img)
        written[rel] = note
    return written


# ---------- writing ----------
def replace_text(note_id: str, text: str) -> None:
    """Replace a note's whole text (title included) through Bear's URL API."""
    url = ("bear://x-callback-url/add-text?"
           f"id={quote(note_id, safe='')}&mode=replace_all&open_note=no&show_window=no"
           f"&text={quote(text, safe='')}")
    subprocess.run(["open", "-g", url], check=True)


def wait_for_text(note_id: str, expected: str, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = note_text(note_id)
        if current == expected:
            return True
        time.sleep(0.5)
    return False


if __name__ == "__main__":  # quick self-check: python3 scripts/bear.py
    ns = devotional_notes()
    print(f"{len(ns)} devotional notes, {sum(len(n.images) for n in ns)} images; "
          f"database {os.path.getsize(DB_PATH) // 1024} KB")
