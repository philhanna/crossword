# Change Log
All notable changes to this project will be documented in this file.
 
This project adheres to [Semantic Versioning],
and the format is based on [Keep a Changelog].

## [Unreleased]

## [3.4.0] - 2026-03-28

### Added

- AcrossLite export: populated AUTHOR and COPYRIGHT fields from config
- NYTimes XML (ccxml) export: `<creator>` from config author_name,
  `<copyright>` with current year, `.xml` file extension
- Export NYTimes submission as PDF via Chrome headless (`export_nytimes` tool)
- `export_ccxml` admin tool
- `export_acrosslite` admin tool
- `docs/file_formats.md` — reference document for supported export formats

### Changed

- `BasicExportAdapter` split into three focused adapters
- AcrossLite export simplified: returns plain text, no longer wraps in ZIP
- `XmlExportAdapter` renamed to `CcxmlExportAdapter`
- Swagger endpoint list updated
- `clear_work_files.py`: removed stale grid references

### Fixed

- Issue #199
- Publish menu: stale download filenames corrected
- Publish menu: success notification shown after download completes
- Test suite: `words.db` path corrected to `examples/words.db`

## [3.3.0] - 2026-03-28

### Changed

- Home view: removed the session activity log and its related frontend state,
  rendering, and styles
- Message line now appears as an overlay anchored below the top menu, so
  notifications no longer shift the editor layout during editing sessions
- Puzzle editor: non-selected cells in puzzle mode now use white background
  instead of light gray, matching grid mode
- Word editor: constrained Suggest now uses the word input box as the starting
  pattern; typed letters override per-position crossing-word constraints, dots
  defer to constraints

## [3.2.0] - 2026-03-27

### Added

- Message line: single-line notification bar below the menu for success/error
  feedback (issue #195); styled with distinct notice and error variants
- Merged editor: puzzle working copies now support a Grid mode alongside Puzzle
  mode, with separate undo/redo history for each (issue #196)
- New puzzle routes: `POST /mode/grid`, `POST /mode/puzzle`,
  `PUT /grid/cells/{r}/{c}`, `POST /grid/rotate`, `POST /grid/undo`,
  `POST /grid/redo` — puzzle grid can be edited in-place without opening the
  standalone grid editor

### Changed

- Standalone grid editor and all grid-only routes removed; grids are now edited
  exclusively through the puzzle editor's Grid mode
- `GridUseCases`, `grid_use_cases.py`, and `grid_handlers.py` removed; grid
  operations on puzzles delegated to `PuzzleUseCases`
- `samples.db` migrated to remove legacy standalone grid rows (issue #196)
- Message line moved to the bottom of the page (fixed to viewport)
- Puzzle editor: selected cursor cell is now light blue (same as word highlight)
  with only a bounding border to mark the active cell; dark blue fill removed

### Fixed

- `tools/dev/gen_endpoints_doc.py`: `ROOT` path calculation used one too few
  `dirname()` calls, producing a doubled `tools/tools/dev/` path when loading
  `swagger.py`

## [3.1.1] - 2026-03-27

### Changed

- Word editor: "Show constraints" and "Reset" buttons now appear on the same
  row; the collapsible dropdown is removed
- Word editor: "Show constraints" toggles to "Hide constraints" while the
  table is visible; clicking again closes it
- Word editor: "Suggest ›" button removed from the constraints display

## [3.1.0] - 2026-03-27

### Changed

- Puzzle editor: clicking a cell now selects the word and places the cursor at
  the clicked cell, without automatically opening the word editor
- Letters can be typed directly into the puzzle grid; the cursor advances with
  each keystroke; Space clears the current cell
- Undo/redo in the puzzle editor now operates at word granularity: a single
  undo entry is created when the user moves away from a word whose text changed
- Word editor is now opened explicitly via a new **Edit word** toolbar button,
  or by clicking a clue in the clue list
- Word editor now shows a text input for the word (blank cells displayed as
  `.`); nothing is written to the puzzle until OK is clicked
- Word editor: dots in the word input are converted back to spaces on OK, so
  the input doubles as a regex pattern for suggestions
- Word editor: local undo/redo stack removed; Cancel discards all changes
  including any Reset performed during the session

### Fixed

- Word editor: allow typing in the clue input while the word editor is open
- Word editor: Enter in the clue input now triggers OK
- Word editor: reset_word correctly stores `Word.ACROSS`/`Word.DOWN` in the
  undo stack

## [3.0.1] - 2026-03-26

### Changed

- Renamed port modules to include `_port` suffix for clarity:
  `persistence.py` → `persistence_port.py`,
  `word_list.py` → `word_list_port.py`,
  `export.py` → `export_port.py`
- Renamed adapter modules and classes to reflect the technology and port they implement:
  `sqlite_adapter.py` / `SQLiteAdapter` → `sqlite_persistence_adapter.py` / `SQLitePersistenceAdapter`,
  `dictionary_adapter.py` / `DictionaryAdapter` → `sqlite_dictionary_adapter.py` / `SQLiteDictionaryAdapter`,
  `export_adapter.py` / `ExportAdapter` → `basic_export_adapter.py` / `BasicExportAdapter`
- Replaced `LetterList` static class with module-level functions in `letter_list.py`

### Fixed

- Test suite updated to use `words.db` instead of the removed `words` table in `samples.db`

## [3.0.0] - 2026-03-24

First stable release. Cleanup: removed dead code.

### Changed

- Removed unused methods: `get_numbered_cell_across()` and `get_numbered_cell_down()` from Puzzle class
- Removed unused methods: `__id__()` and `__hash__()` from Grid class

### Fixed

- Issue #185: Corrected toolbar button ordering in grid and puzzle editors

## [2.5.0] - 2026-03-23

Complete rewrite of the application backend and frontend.

### Added

- Hexagonal (Ports & Adapters) architecture replacing the Flask/SQLAlchemy stack
  - Domain models (`Grid`, `Puzzle`, `Word`) with no framework dependencies
  - Port interfaces: `PersistencePort`, `WordListPort`, `ExportPort`
  - Adapters: `SQLitePersistenceAdapter`, `SQLiteDictionaryAdapter`, `BasicExportAdapter`
  - Use cases: `GridUseCases`, `PuzzleUseCases`, `WordUseCases`, `ExportUseCases`
  - Wiring module assembles the app via constructor injection
- Built-in HTTP server (Python `BaseHTTPRequestHandler`) replacing Flask
- Single-page frontend in plain JavaScript (`frontend/index.html`, `static/`)
  - Grid editor: clickable SVG, rotate, undo/redo, info toolbar
  - Puzzle editor: clickable SVG, word editor panel, clue lists, stats panel
  - Preview chooser for all grid and puzzle open/new actions
  - 3-state menu machine: `home` / `grid-editor` / `puzzle-editor`
  - Auto-persistence: every edit saves to the DB immediately
  - Working-copy pattern (`__wc__<uuid>`) for in-progress edits
- Word editor panel: suggest, constraints, and reset tabs
- Word constraints endpoint (`GET /api/words/constraints`)
- Puzzle statistics panel
- Grid statistics panel
- Grid preview and puzzle preview endpoints
- `create_grid_from_puzzle` use case and endpoint
- Delete grid option
- Save and Close buttons on grid toolbar
- Warn on unsaved changes when closing grid or puzzle
- Confirmation dialog after Grid > Save and Puzzle > Save succeed
- Publish feature (Phases 1–4): AcrossLite `.puz` export, PDF, and print
- Rebranded header with Mozart image and "Crossword Composer" title
- Puzzle undo/redo button enable/disable driven by `can_undo`/`can_redo` API fields
- Swagger UI tool (`tools/swagger.py`) with live route diff checking
- `tools/md_to_pdf.py` — Markdown to PDF via Chrome headless
- `tools/gen_endpoints_doc.py` — generates `docs/endpoints.md` from live routes
- `docs/endpoints.md` — auto-generated API endpoint reference
- `design.md` — architecture overview (ports & adapters)
- `pyproject.toml` replacing `setup.py` and `requirements.txt`

### Changed

- Config file format switched to YAML in local config directory
- Reorganized `docs/` directory structure
- Undo/redo stacks persisted in working copy only, not in canonical saves
- `can_undo` / `can_redo` exposed in grid and puzzle API responses

### Fixed

- Issue #184: Grid undo/redo delegated to domain model `Grid.undo()` / `Grid.redo()`; stacks cleared when creating working copy
- Grid undo/redo: persist stacks in working copy, update toolbar buttons correctly
- Puzzle undo/redo: persist stacks in working copy, clear on open and save
- Grid LHS vertical shift when info panel opens/closes
- Missing cell numbers for down-only words in puzzle SVG
- Regexp suggest ignoring character classes in word editor
- `New Grid from Puzzle` sending wrong field name to API
- Treat dot as single-char wildcard in word suggestion patterns

### Removed

- Flask, Flask-Session, Flask-SQLAlchemy, SQLAlchemy, Jinja2 dependencies
- All Jinja2 templates and Flask blueprint code

## [2.4.0] - 2020-08-01

Major overhaul of HTML files.  Now using templates with inheritance.
Made two common modal dialogs to replace all the individual ones.

## [2.3.0] - 2020-07-12

Starting with this release, grids, puzzles, configuration,
and words are stored in a database, rather than files in
the filesystem.  The database is an SQLite database
`crossword.db`.

The sample grids and puzzles are now distributed in
the `samples.db` database, which is used by default
for new installations.

Added a `users` database table, but only with a
single hard-coded user.  Will be expanded when I
add authentication and login.

The configuration file is simpler (just two options)
and renamed `.crossword.ini`.

### Added

- Issue #103: Added toolbar to word edit screen
- Issue #104: Scroll to the last used row in clues
- Issue #108: Switched to tabbed view in word edit screen
- Issue #111: Switch from files to sqlite3 database
- Issue #115: Switch database usage to SQLAlchemy
- Issue #116: Moved Flask secret key into environment variable
- Issue #117: Refactored app routing into blueprint classes
- Enabled logging in the UI classes
- SHA-1 encoding for JSON strings and passwords
- Bumped the version number to 2.3.0

### Changed

- Raised test coverage to 93%
- Refactored imports
- Moved `<style>` bits into common file
- Moved classes to more logical packages (issue #114)
- Removed unused classes
    - Configuration
    - crossword/util programs
- Updated README with better install instructions

### Fixed

- Issue #97: Added preview icon to PuzzleNew dialog
- Issue #98: Do not clear clue if word is blank

## [2.2.0] - 2020-06-30

The main feature of this release is the UI upgrade to the `puzzle.html`
screen, which now shows the clues on the same screen when the puzzle
editing is done (see Issue #99).

### Added

- Issue #90: JSON representation of puzzles and grids is no longer indented
- Added this **CHANGELOG.md**
- Added ability to scale the SVG (for preview)
- Added ability to have multiple actions in grid and puzzle choosers
- Issue #94: Added preview to grid chooser
- Issue #95: Added preview to puzzle chooser
- Issue #99: Show clues on puzzle screen
- Bumped the version number to 2.2.0

### Changed

- Refactored attribute names in `NumberedCell` (Issue #91)
- Use list comprehension in wordlist.lookup
- Added word count to preview screens (Issue #96)
- Moved clue import and export visitors to `util` subdirectory

### Fixed

- Issue #97: Added preview icon to PuzzleNew dialog
- Issue #98: Do not clear clue if word is blank

## [2.1.4] - 2020-06-23

### Added

- Added setup instructions to README.md
- Added LICENSE
- Bumped the version number to 2.1.4

### Changed

- Switched the NYTimes and AcrossLite menu option order
- Moved unit tests into crossword.tests package
- Fix for issue #89
- Fix for issue #88
- Fix for issue #87

## [2.0.0] - 2020-06-21

### Added

- Issue #88: Remove WordLookup menu item
- Issue #62: Make utilities directory
- Issue #63: Utility to create a word list and split it by length
- Issue #64: Add grid cells to grid.json
- Issue #66: Toolbar for puzzle screen
- Issue #67: Add undo/redo
- Issue #69: Show existing puzzle title in set title dialog
- Issue #71: Change save / save as workflow in Puzzle
- Issue #72: Change save / save as workflow in Grid
- Issue #74: Add toolbar to grid editor screen
- Issue #76: Add "rotate" to the grid editor toolbar
- Issue #80: Remove save and replace puzzle grid
- Issue #84: Refactor names of functions, HTML files, webapp methods for consistency

### Changed

- Added normalize_wordlist.py
- Added normalize_wordlist utility
- Added unit test for word.is_complete()
- Added Word.ACROSS and Word.DOWN enumeration
- Allow simple package name to be used in imports
- Made statistics dialog not as wide
- Refactored directory structure
- Refactored directory structure to use packages
- Removed instructions under the toolbar
- Removed puzzle stats and title from menu
- Removed unclosed quotes from puzzle.html
- Replace special characters with blanks
- Undo/redo text only, not clues or titles
- Use my class name for toolbar icons

### Fixed

- Issue #61: Add duplicate word check to puzzle statistics
- Issue #65: Edit word does not accept blanks
- Issue #68: After edit word, delete puzzle is not enabled
- Issue #70: Delete puzzle should not be enabled until the puzzle has been named
- Issue #75: "Save puzzle" is not enabled on new puzzles
- Issue #77: Delete grid fails if the object is named but unsaved
- Issue #78: Delete puzzle fails if the object is named but unsaved
- Issue #79: Check for existing file when doing "Save As" or "Rename"
- Issue #81: Puzzle title sometimes lost
- Issue #82: Limit undo/redo to word text, not clues and titles
 

## [1.4.0] - 2020-06-14

### Added

- Issue #46: Show grid and puzzle statistics and error checks
- Issue #51: Separate sections for the three grid validation checks
- Issue #53: Made grid and puzzle chooser dialogs scrollable
- Issue #54: Refactored display of suggested words
- Issue #55: Publish in AcrossLite format
- Issue #56: Added JSON source to publish .zip file
- Issue #58: Sort puzzle and grid lists by date of last save
- Issue #59: Added puzzle title

### Fixed

- Issue #47: Doubled display of statistics
- Issue #50: Double-click vs single-click broken

[Semantic Versioning]: https://semver.org/
[Keep a Changelog]: https://keepachangelog.com/
[Unreleased]: https://github.com/philhanna/crossword/compare/3.4.0..HEAD
[3.4.0]: https://github.com/philhanna/crossword/compare/3.3.0..3.4.0
[3.3.0]: https://github.com/philhanna/crossword/compare/3.2.0..3.3.0
[3.2.0]: https://github.com/philhanna/crossword/compare/3.1.1..3.2.0
[3.1.1]: https://github.com/philhanna/crossword/compare/3.1.0..3.1.1
[3.1.0]: https://github.com/philhanna/crossword/compare/3.0.1..3.1.0
[3.0.1]: https://github.com/philhanna/crossword/compare/3.0.0..3.0.1
[3.0.0]: https://github.com/philhanna/crossword/compare/2.5.0..3.0.0
[2.5.0]: https://github.com/philhanna/crossword/compare/2.4.0..2.5.0
[2.4.0]: https://github.com/philhanna/crossword/compare/2.3.0..2.4.0
[2.3.0]: https://github.com/philhanna/crossword/compare/2.2.0..2.3.0
[2.2.0]: https://github.com/philhanna/crossword/compare/2.1.4..2.2.0
[2.1.4]: https://github.com/philhanna/crossword/compare/2.0.0..2.1.4
[2.0.0]: https://github.com/philhanna/crossword/compare/1.4.0..2.0.0
[1.4.0]: https://github.com/philhanna/crossword/compare/3508c1..1.4.0
