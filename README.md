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
    organize_devotionals.py
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

## Style

All English writing in this repository follows *The Chicago Manual of Style*, 18th edition. `CLAUDE.md` summarizes the rules that matter most here: Bible references, dashes, numbers, and quotation marks. A full style review of the existing notes is planned.
