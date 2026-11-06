# CLAUDE.md

Guidance for Claude when working in this repository.

## Project

This repository holds Bible-study notes, chiefly devotional commentaries written chapter by chapter. The notes are the content for a planned app, working title “Bayble” (also “Study Bible”). In the app, readers will see the Bible text with the matching commentary, essays, and notes beside it.

`Devotionals App.md` is the original app spec. It is partly outdated, but it still describes the planned Markdown-to-LaTeX conversion: headings, footnotes, `==highlights==`, wikilinks, images, and Mermaid diagrams. Read it before working on any export or conversion.

## Repository Layout

- `Bibles/`: Bible translations as XML (ESV, KJV, LSB, NASB, NIV, RSV, HSV, HTB, and a Dutch Bible).
- `biblestudy:devotionals/`: the devotional commentaries. (Finder shows the colon in this folder name as a slash.)
  - `01. Genesis/` through `66. Revelation/`: one folder per book, in canonical order. A note’s images sit in a subfolder named after the note, e.g. `15. Ezra/Ezra 7 (LSB)/`.
  - `_removed/`: quarantined files (exact duplicates, non-devotionals, unused images), plus the organizer’s reports and undo manifests. Nothing in it has been deleted.
  - `_conflicts/<date>/`: Bear versions of notes that could not be merged automatically during an import.
- `scripts/organize_devotionals.py`: deduplicates the notes and sorts them into the book folders. See `README.md`.
- `scripts/import_bear.py`: imports the notes from Bear, read straight from Bear’s database (read-only), with a three-way merge. The base is the previous import, kept on the `bear-export` branch. A manual export in `imports/YYYY-MM-DD/` still works as a fallback.
- `scripts/push_to_bear.py`: sends committed repo edits back into Bear through Bear’s URL API, and records each push as a new commit on `bear-export`.
- `scripts/bear.py`: shared code for reading Bear’s database and writing through its URL API. Never write into Bear’s database; it would break iCloud sync.
- `imports/`: raw Bear exports, dry-run reports, and `_bear-backups/`. Ignored by git.
- `01. Bear/`: an older copy that git still tracks but that no longer exists on disk. Don’t restore or commit it without asking.

## Note Conventions

- The notes are Markdown exported from Bear (Bear-flavored Markdown).
- File name: `<Book> <chapter> (<TRANSLATION>).md`, e.g. `Genesis 3 (LSB).md`. Some file names have no translation (`Psalm 23.md`). Some have a verse range with the colon left out, because file names can’t contain one: `Luke 2436-53 (ESV).md` means Luke 24:36–53.
- Translation codes in use: LSB, ESV, NIV, NASB, KJV, RSV, HSV.
- Each note carries a tag `#biblestudy/devotionals/<book>` (e.g. `#biblestudy/devotionals/1kings`) in its first or last five lines.
- Images use relative, URL-encoded links: `![](Ezra%207%20%28LSB%29/Ezra%20Nehemiah%20Timeline.png)`.
- Bible text is quoted in blockquotes. Verse numbers are bold, e.g. `> **Gen. 3:1** Now the serpent…`.

## Style: *The Chicago Manual of Style*

All English prose follows *The Chicago Manual of Style*, 18th edition (CMOS). This applies to new writing, documentation, and commit messages. The main rules:

- Use the serial (Oxford) comma: “faith, hope, and love.”
- Use closed em dashes—like this—and en dashes for ranges: Luke 24:36–53, pages 12–15, 2020–24.
- Use curly quotation marks and apostrophes (“ ” ‘ ’) in prose. Put periods and commas inside the closing quotation mark.
- In prose, spell out whole numbers from zero to one hundred, and round multiples of those (“two hundred”). Chapter and verse numbers are always numerals.
- Bible references:
  - Use a colon between chapter and verse (John 3:16) and an en dash between verses (Rom. 8:28–30).
  - In running text, write book names out (“In Romans 8 Paul argues…”).
  - Use the traditional CMOS abbreviations (Gen., Exod., Ps./Pss., Isa., Matt., Rom., 1 Cor., Heb., Rev.) only in parenthetical references, notes, and tables.
  - Name the translation in parentheses after a quotation, e.g. (LSB), unless the note’s title already states it.
- Quoted Scripture keeps the wording, spelling, and capitalization of its translation, e.g. the LSB’s capitalized “He” for God. CMOS lowercases pronouns for God in an author’s own prose. The notes currently follow the LSB habit, so ask before changing that.
- Headings use headline-style capitalization (“The Lives of the Army Commanders”).
- Use *italics* for titles of books and for words used as words. Don’t italicize for emphasis when bold or rephrasing works better.

The CMOS review of the existing notes is a separate, planned task. Don’t start it until the user asks.

## Working Rules

- Don’t change the wording of a devotional without asking. Mechanical fixes such as moving files or repairing links are fine when the task calls for them.
- Always run `scripts/organize_devotionals.py` as a dry run first and show the user the summary before running it with `--apply`.
- Notes are imported from Bear with `scripts/import_bear.py` (see `README.md`), not with the organizer. When the user asks for an import:
  1. Run the import with `--dry-run` and show the summary.
  2. Run it with `--yes` only after the user agrees.
- Edits are sent back to Bear with `scripts/push_to_bear.py`. It writes into the user’s Bear library, so:
  1. Run it with `--dry-run` and show the summary.
  2. Push (`--only <path>` or `--yes`) only after the user agrees.
- Merge a note in `_conflicts/<date>/` only with the user’s agreement, because those are their words on both sides. Delete a conflict copy only after its note is merged.
- Never rewrite, rebase, or delete the `bear-export` branch. It is the merge base for the next import. Only the import and push scripts add commits to it.
- Never delete anything from `_removed/` without asking.
- Some notes are in Dutch (e.g. the children’s series for Nathan). CMOS applies only to English text.
