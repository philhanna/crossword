# Change Log
All notable changes to this project will be documented in this file.
 
This project adheres to [Semantic Versioning],
and the format is based on [Keep a Changelog].

## [5.5.1] - 2026-08-01

### Fixed

- PDF export filenames now correctly use the puzzle name instead of a generic name

## [5.5.0] - 2026-07-31

### Added

- Required save comment: Save and Save As now prompt for a non-empty
  comment describing what changed; it's stored on the puzzle's history row
  and shown as a new column in the dashboard's "Show history" popup (see
  `docs/dev/puzzle_save_comments.md`)

## [5.4.0] - 2026-07-31

### Added

- Duplicate-word check: the word editor and direct grid typing now reject
  a word that duplicates, or is a plain plural of, another complete word
  already in the puzzle; the same check filters both suggestion-list
  endpoints so a conflicting word is never offered in the first place
  (see `docs/dev/no_duplicate_words.md`)
- Puzzle content snapshots: a full copy of the puzzle (grid, fill, clues)
  is now saved on every save, not just state changes, so an earlier
  version — e.g. what was actually submitted to a publisher — can always
  be recovered even after later edits; "Restore" button added to the
  puzzle history popup (see `docs/dev/puzzle_content_snapshots.md`)

## [5.3.2] - 2026-07-30

### Fixed

- `_auto_set_state_on_save` no longer silently demotes a puzzle's state
  after it has been submitted/published/archived; those states are
  user-owned and only autosave's ladder detection (draft/filled/finished)
  should stay hands-off once past them

## [5.3.0] - 2026-07-26

### Added

- `puzzle_state_history` table replacing the old state/publisher/
  date_submitted/date_published columns on the puzzles table; current
  state is derived from the latest history row
- Migration tool to rebuild an existing column-schema database into
  the new puzzle_state_history shape
- Context menu to show puzzle history in the puzzle editor

### Fixed

- Fix for issue #246

## [5.2.0] - 2026-07-15

### Added

- WiktionaryAPIDefinition adapter for word definitions, using Wikimedia's
  Wiktionary REST API
- `definition_provider` setting to choose between the Wiktionary and
  dictionaryapi.dev definition providers

### Changed

- Puzzle export downloads now use the server-provided filename
- "Clear" action includes the currently selected word

## [5.1.0] - 2026-06-26

### Added

- Word locking in the puzzle editor: locked words' letters survive direct
  edits, crossing-word edits, and undo/redo; locking/unlocking is itself
  undoable
- Bulk "Clear" action that blanks every unlocked word's text and clue as a
  single undo entry

### Changed

- Grid Mode is unreachable while any word is locked
- Reordered puzzle editor toolbar buttons and adjusted locked-word cell color
- Moved the "all" button to the beginning of the button row

## [5.0.0] - 2026-06-09

### Added

- Dashboard view for browsing puzzles by state
- `% Complete` column on the dashboard draft/all tabs
- Puzzle state label in the puzzle editor app bar
- Delete button on the puzzle editor action bar

### Changed

- Clear clues for incomplete words
- CSS adjustments

[Semantic Versioning]: https://semver.org/
[Keep a Changelog]: https://keepachangelog.com/
