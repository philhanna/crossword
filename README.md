# Crossword Composer

A web-based application for creating and editing crossword puzzles.

**Version: 5.6.5**

## Table of contents
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](https://github.com/philhanna/crossword/wiki/Configuration)
- [Running the server](https://github.com/philhanna/crossword/wiki/Running-The-Server)
- [Using the application](#using-the-application)
- [Architecture](#architecture)
- [Tools](#tools)
- [References](#references)

## Requirements

- Python 3.10 or greater
- git
- PyYAML and requests (`pip install pyyaml requests`)

## Setup

See installation and setup instructions at
[Installation](https://github.com/philhanna/crossword/wiki/Installation)

For a quick local sample setup, copy [`samples/config.yaml`](samples/config.yaml)
to your user config location:

- Linux/macOS: `~/.config/crossword/config.yaml`
- Windows: `%APPDATA%\crossword\config.yaml`

The sample config is prewired to the bundled sample files:

- `dbfile: samples/crossword.db`
- `xdfile: samples/sample_grids.db`
- `word_file: samples/words.txt`

## Configuration

See [Configuration](https://github.com/philhanna/crossword/wiki/Configuration) in the wiki.

## Running the server

See [Running the Server](https://github.com/philhanna/crossword/wiki/Running-The-Server) in the wiki.

From the repository root you can also start the app directly with:

- Windows: `run_server.bat`
- Any platform with Python on `PATH`: `python -m crossword.http_server`

The API documents itself while the server is running: a browsable reference is
at `/docs` and the OpenAPI document at `/openapi.json`.

## Using the application

Open a browser and go to the host and port configured in config.yaml (e.g. **http://localhost:5000**).

The app runs in single-user mode. There is no login screen; puzzle actions use the built-in local user.

The application is a single-page app with a dashboard plus one merged construction editor:

### Dashboard
Starting view, and the place you return to with the **Dashboard** button in the top bar.
It shows four summary cards — in progress, completed, submitted and archived — over a
sortable table of every puzzle you own, with tabs to filter by lifecycle state.
Right-click a puzzle to show its save history, from which any earlier version can be
reopened.

### Merged editor
Create the grid and fill the puzzle in one editor, switching modes as needed.

- **Grid mode:** edit black cells, rotate the grid, inspect stats, and use mode-local undo/redo.
- **Puzzle mode:** fill answers and clues, set the title, inspect stats, and use mode-local undo/redo.
- New puzzles are created without a name; you are prompted for a name only when you first save.
- New puzzles begin in Grid mode.
- Existing puzzles reopen in the last mode used for that puzzle.
- Clicking a cell in Grid mode toggles it black/white. The grid is kept symmetric automatically.
- Click a cell or clue to select a word.
- The word editor panel offers **Suggest** (word suggestions), **Constraints** (pattern matching), and **Show definitions**.
- The statistics panel is shared across both modes.
- The top app bar shows the current puzzle and updates immediately after **Save as**.
- If `theme_color` is set in config, the app derives the app bar, primary accent, and sidebar colors from that base color.

### Import
Available from anywhere via the **Import** menu. Each entry prompts for a file and
creates a new puzzle from it:

| Format | Description |
|--------|-------------|
| AcrossLite binary (.puz) | Across Lite binary puzzle file |
| AcrossLite text (.txt) | Across Lite text format |
| ipuz (.ipuz, .json) | ipuz interchange format |
| xword xd (.xd) | xd plain-text format |
| Crossword Compiler (.xml) | Crossword Compiler XML |

### Export
Available from anywhere via the **Export** menu:

| Format | Description |
|--------|-------------|
| AcrossLite binary (.puz) | Across Lite binary puzzle file |
| AcrossLite text (.txt) | Across Lite text export |
| ipuz (.ipuz) | ipuz interchange format |
| xword xd (.xd) | xd plain-text format |
| Crossword Compiler (.xml) | XML export |
| New York Times (.pdf) | NYT submission PDF |
| Solver PDF (.pdf) | Empty grid plus compact clue list for solving/printing |
| Solution PDF (.pdf) | Filled-in grid plus clue list for answer-key printing |

### Working copy pattern
All edits target an invisible working copy (`__wc__<uuid>`). Choosing **Save** commits
the working copy back to the named puzzle. Choosing **Close** without saving
discards it. This means every keystroke is auto-persisted without overwriting the
last saved version until you explicitly save.

## Architecture

The backend follows a **Hexagonal (Ports & Adapters)** design:

| Layer | Modules |
|-------|---------|
| Domain | `grid`, `puzzle`, `word` — pure Python, no framework deps |
| Ports | `persistence`, `word_list`, `export`, `import`, `definition`, `grid_generator` |
| Adapters | `sqlite_persistence`, `flat_file_word_list`, `random_grid_generator`, `settings`, one export adapter per format (Across Lite text and binary, Crossword Compiler XML, ipuz, xd, NYTimes PDF, solver PDF, solved PDF), one import adapter per format (Across Lite text and binary, Crossword Compiler XML, ipuz, xd), and two definition providers (Dictionary API, Wiktionary) |
| Use Cases | `PuzzleUseCases`, `WordUseCases`, `ExportUseCases`, `ImportUseCases`, `DefinitionUseCases` |
| HTTP Server | FastAPI app served by uvicorn, wired in `crossword/wiring/` |
| Frontend | Single `index.html` + `static/css/style.css` + `static/js/{state,ui,svg,dashboard,puzzle-editor,word-editor,settings}.js` |

Routes are listed in [docs/dev/endpoints.md](docs/dev/endpoints.md) and the use-case
methods behind them in [docs/dev/usecases.md](docs/dev/usecases.md).

## Tools

### User

| Script | Description |
|--------|-------------|
| `tools/user/clear_work_files.py` | Remove leftover working-copy (`__wc__`) and new-puzzle (`__new__`) rows from the database |
| `tools/user/grid_generator.py` | Generate a random valid grid and print it to stdout |

The old command-line export and import scripts were removed; use the **Import** and
**Export** menus in the app instead.

### Dev

| Script | Description |
|--------|-------------|
| `tools/dev/gen_endpoints_doc.py` | Regenerate `docs/dev/endpoints.md`, and the wiki's copy `docs/dev/endpoints-wiki.md`, from live route registrations |
| `tools/dev/import_grid.py` | Bulk-import `.xd` puzzle files as blank grids (reads paths from stdin) |
| `tools/dev/impgrid.py` | Import a puzzle from an old `grids.db` into the main database |
| `tools/dev/migrate_puzzle_state.py` | One-off migration: rebuild the database with lifecycle state as columns on `puzzles` |
| `tools/dev/migrate_puzzle_state_history.py` | One-off migration: replace those columns with a `puzzle_state_history` table |
| `tools/dev/migrate_puzzle_save_comments.py` | One-off migration: add `comment` to `puzzle_state_history` |
| `tools/dev/migrate_puzzle_content_snapshots.py` | One-off migration: add `content` to `puzzle_state_history` |

Each migration reads the existing database read-only and writes a brand-new file.

## References

- [GitHub repository](https://github.com/philhanna/crossword)
- [User guide (GitHub wiki)](https://github.com/philhanna/crossword/wiki)
