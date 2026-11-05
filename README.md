# Bible Study Notes

Devotional commentaries and study notes on the Bible, written chapter by chapter. They will be the content for a planned study-Bible app, working title “Bayble.” In the app, readers will see each chapter with its commentary, essays, and notes beside it. The notes will later be converted to LaTeX for print; `Devotionals App.md` has the original plan.

## Contents

```
Bibles/                       Bible translations (XML)
biblestudy:devotionals/
    01. Genesis/
        Genesis 1 (ESV).md
        Genesis 3 (LSB).md
        …
    15. Ezra/
        Ezra 7 (LSB).md
        Ezra 7 (LSB)/         images for that note
    …
    66. Revelation/
    _removed/                 quarantined files, reports, undo manifests
scripts/
    organize_devotionals.py   sort and deduplicate the notes
    import_bear.py            import the notes from Bear
    push_to_bear.py           send repo edits back to Bear
    bear.py                   reads Bear (read-only) and writes through its URL API
```

Each book has its own folder, numbered in canonical order from `01. Genesis` to `66. Revelation`. Books without notes yet have no folder.

## Naming Notes

Name each note after the passage and the translation used:

| File name | Meaning |
| --- | --- |
| `Genesis 3 (LSB).md` | Genesis 3, Legacy Standard Bible |
| `Psalm 23.md` | Psalm 23, translation not stated |
| `Luke 2436-53 (ESV).md` | Luke 24:36–53, English Standard Version (file names can’t contain a colon) |
| `2 John (ESV).md` | a single-chapter book; the chapter number may be omitted |

Each note also has the tag `#biblestudy/devotionals/<book>`, e.g. `#biblestudy/devotionals/genesis`, in its first or last five lines.

## Organizing the Notes

`scripts/organize_devotionals.py` cleans up `biblestudy:devotionals/` in three steps:

1. **Deduplicate.** If two notes are byte-for-byte identical, it keeps one copy and quarantines the rest. It prefers the copy that is already in the right book folder.
2. **Filter.** Only devotional commentaries stay: notes whose file name starts with an English book name and a chapter. Everything else is quarantined. That includes notes with Dutch book names, dated sermon notes, overviews, reading logs, and unrelated notes.
3. **Sort.** Each devotional moves to its book folder, regardless of where it was filed before. The script flattens year and translation subfolders, and images move with their notes.

Nothing is deleted. Removed files go to `_removed/duplicates/`, `_removed/not-devotional/`, or `_removed/orphans/`, and keep their original paths there. If two different notes would end up with the same name, the second gets a suffix such as `Genesis 15 (LSB) — from 2024.md`.

Run it from the repository root (Python 3.9 or later; no extra packages):

```sh
# 1. Dry run: shows what would happen and writes a report; moves nothing
python3 scripts/organize_devotionals.py

# 2. Carry out the plan
python3 scripts/organize_devotionals.py --apply

# 3. If needed, reverse an applied run
python3 scripts/organize_devotionals.py --undo "biblestudy:devotionals/_removed/manifest-<timestamp>.csv"
```

Each run writes a report to `_removed/`. The report lists:

- the number of notes per book;
- **near-duplicates to review**: notes on the same passage and translation but with different text, such as `Genesis 3 (LSB).md` and `Genesis 3 (LSB) 2.md`;
- notes renamed to avoid a name conflict;
- collapsed verse references and how they were read;
- notes whose tag doesn’t match the file name;
- every quarantined file, with the reason.

It is safe to run the script again. Notes that are already in place stay where they are.

## Importing from Bear

Bear is where the notes are written, so the library is refreshed from Bear from time to time. `scripts/import_bear.py` reads the notes straight from Bear’s database, opened read-only, so no export is needed. It cleans up the notes and merges them in one step.

1. **Run the import** from the repository root:

   ```sh
   python3 scripts/import_bear.py --dry-run   # report only
   python3 scripts/import_bear.py             # asks before applying
   ```

   The script collects every note tagged `#biblestudy/devotionals` (or a subtag) and lays the notes out as Bear’s Markdown export would. It then sorts and deduplicates them the same way as the organizer. It prints a summary and asks **Apply and commit? [y/N]**.

   If two notes in the same tag have the same title, the older one keeps the plain name and the newer one gets ` 2`. That order never changes, even after a note is edited. (Bear’s own export orders them by last edit instead.)

   A Markdown export made by hand still works as a fallback. Put it in `imports/YYYY-MM-DD/` and pass the folder: `python3 scripts/import_bear.py imports/2026-12-01`. `imports/` is ignored by git.

2. **Read the summary.** Each note falls into one of these groups:

   | Result | Meaning |
   | --- | --- |
   | Unchanged | The same in Bear and in the repo |
   | New | A new note in Bear; it is added to its book folder |
   | Updated from Bear | Changed in Bear only; the Bear version is taken |
   | Merged | Changed in both places, on different lines; both changes are kept |
   | **Conflict** | The same lines changed in both places. The repo version stays, and the Bear version is saved to `_conflicts/<date>/` for you to merge by hand |
   | Repo edits kept | Changed in the repo only (e.g. a style fix); see the next section |
   | Missing from this export | Deleted or renamed in Bear. The repo copy is kept and listed |

   The full report is saved as `biblestudy:devotionals/_removed/import-report-<date>.md` and committed with the import.

3. **Resolve any conflicts.** Merge the Bear copy in `_conflicts/<date>/` into the note, delete the copy, and commit. Then send the merged note back to Bear (next section).

The import only runs if `biblestudy:devotionals/` has no uncommitted changes. To decide what changed, it compares each note with the version from the previous import. That version is kept as a snapshot on the git branch `bear-export`, which you never need to check out. To undo an import, run the command the script prints at the end:

```sh
git reset --hard HEAD~1 && git branch -f bear-export <previous snapshot>
```

The previous snapshot's ID is also recorded in the import commit message, under `Bear-Export-Previous:`.

## Sending Edits Back to Bear

Edits made in the repo, such as style fixes, go back into Bear with `scripts/push_to_bear.py`:

```sh
python3 scripts/push_to_bear.py --dry-run                       # report only
python3 scripts/push_to_bear.py --only "15. Ezra/Ezra 7 (LSB).md" # one note
python3 scripts/push_to_bear.py                                 # asks before pushing
```

The script writes through Bear’s official URL API, never into Bear’s database, so iCloud sync keeps working. It pushes only committed edits, and only to notes that Bear hasn’t changed since the last import. A note that was edited in Bear too is listed as **changed in Bear**: run the import first, then push again. Bear keeps its own image links, because the repo edit is merged into Bear’s text line by line. The script skips any note whose title line changed, since that would rename the note in Bear.

Before each change, Bear’s current text is saved in `imports/_bear-backups/<timestamp>/`, and afterward the script reads Bear again to confirm it. Bear opens in the background while the script runs.

## Style

All English writing in this repository follows *The Chicago Manual of Style*, 18th edition. `CLAUDE.md` summarizes the rules that matter most here: Bible references, dashes, numbers, and quotation marks. A full style review of the existing notes is planned.
