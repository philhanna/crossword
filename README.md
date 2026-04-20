# Crossword Composer

A web-based application for creating and editing crossword puzzles.

**Version: 4.6.1**

## Table of contents
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](https://github.com/philhanna/crossword/wiki/Configuration)
- [Running the server](#running-the-server)
- [Using the application](#using-the-application)
- [References](#references)

## Requirements

- Python 3.10 or greater
- git
- PyYAML and requests (`pip install pyyaml requests`)

## Setup

See installation and setup instructions at
[Installation](https://github.com/philhanna/crossword/wiki/Installation)

## Configuration

See [Configuration](https://github.com/philhanna/crossword/wiki/Configuration) in the wiki.

## Running the server

Linux/macOS:

```bash
source venv/bin/activate
python -m crossword.http_server
```

Windows Command Prompt:

```bat
venv\Scripts\activate.bat
python -m crossword.http_server
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
python -m crossword.http_server
```

On Linux/macOS you can also use the provided helper script:

```bash
./run_server
```

This starts the HTTP server on the host and port specified in `config.yaml`. Stop it at any time with `Ctrl-C`.

## Using the application

Open a browser and go to the host and port configured in config.yaml (e.g. **http://localhost:5000**).

The app runs in single-user mode. There is no login screen; puzzle actions use the built-in local user.

The application is a single-page app with a home screen plus one merged construction editor:

### Home
Starting state. Choose to create or open a puzzle.

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

### Export
Available from anywhere via the **Export** menu:

| Format | Description |
|--------|-------------|
| Across Lite (.txt) | Across Lite text export |
| Crossword Compiler (.xml) | XML export |
| New York Times (.pdf) | NYT submission PDF |
| Solver PDF (.pdf) | Empty grid plus compact clue list for solving/printing |

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
| Ports | `persistence`, `word_list`, `export` |
| Adapters | `SQLiteAdapter`, `DictionaryAdapter`, `ExportAdapter` |
| Use Cases | `PuzzleUseCases`, `WordUseCases`, `ExportUseCases` |
| HTTP Server | `BaseHTTPRequestHandler` with regex router (no Flask) |
| Frontend | Single `index.html` + `static/js/app.js` + `static/css/style.css` |

## Tools

### User

| Script | Description |
|--------|-------------|
| `tools/user/export_acrosslite.py` | Export a puzzle to Across Lite text format (`.txt`) |
| `tools/user/export_ccxml.py` | Export a puzzle to Crossword Compiler XML format (`.xml`) |
| `tools/user/export_json.py` | Export a puzzle to JSON format (`.json`) |
| `tools/user/export_nytimes.py` | Export a puzzle to NYTimes submission format (`.pdf`) |
| `tools/user/export_solver_pdf.py` | Export a puzzle to the compact solver PDF format (`.pdf`) |
| `tools/user/clear_work_files.py` | Remove orphaned working-copy rows from the database |
| `tools/user/grid_generator.py` | Generate candidate crossword grids |
| `tools/user/lookup.py` | Look up dictionary entries from the command line |

### Dev

| Script | Description |
|--------|-------------|
| `tools/dev/swagger.py` | Swagger UI for the REST API (`python3 tools/dev/swagger.py`) |
| `tools/dev/gen_endpoints_doc.py` | Regenerate `docs/design/endpoints.md` from live route registrations |
| `tools/dev/migrate196.py` | Migrate a pre-v3.2 database to the merged puzzle-only layout |

## References

- [GitHub repository](https://github.com/philhanna/crossword)
- [User guide (GitHub wiki)](https://github.com/philhanna/crossword/wiki)
