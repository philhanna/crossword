# Crossword Composer

A web-based application for creating and editing crossword puzzles.

**Version: 4.6.1**

## Table of contents
- [Requirements](#requirements)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running the server](#running-the-server)
- [Using the application](#using-the-application)
- [References](#references)

## Requirements

- Python 3.10 or greater
- git
- PyYAML and requests (`pip install pyyaml requests`)

## Setup

### Clone the repository

```bash
git clone https://github.com/philhanna/crossword
cd crossword
```

### Install in a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate.bat
pip install -e .
```

### Upgrading

```bash
cd crossword
git pull
pip install -e .
```

## Configuration

The application is configured via `~/.config/crossword/config.yaml`.
A sample configuration file is provided at `examples/sample.yaml` — copy it to get started:

```bash
mkdir -p ~/.config/crossword
cp examples/sample.yaml ~/.config/crossword/config.yaml
```

Then edit `~/.config/crossword/config.yaml`:

```yaml
# host: IP address the server will bind to (required)
host: 127.0.0.1

# port: TCP port the server will listen on (required)
port: 5000

# dbfile: fully qualified path to the SQLite 3 database (required)
dbfile: /path/to/crossword.db

# word_dbfile: fully qualified path to the word list SQLite database
word_dbfile: /path/to/words.db

# log_level: one of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
log_level: INFO

# How many milliseconds notification messages remain visible (default: 3000)
message_line_timeout_ms: 3000

# Optional base color for the frontend theme; the app derives related colors automatically
#theme_color: "#004953"

# NYTimes submission: author info printed on the grid page
#author_name: Your Name
#author_address: "123 Main St, City, ST 12345"
#author_email: you@example.com
```

`host`, `port`, and `dbfile` are required — the server will not start without them.

## Running the server

```bash
source venv/bin/activate   # if not already active
python -m crossword.http_server
```

Or use the provided script:

```bash
./run_server
```

This starts the HTTP server on the host and port specified in config.yaml. Stop it at any time with `Ctrl-C`.

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
