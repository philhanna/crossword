# Crossword Composer

A web-based application for creating and editing crossword puzzles.

**Version: 3.0.0** — First stable release

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

The application has **no external Python dependencies** — it uses only the standard library.

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
pip install .
```

### Upgrading

```bash
cd crossword
git pull
pip install .
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
# dbfile: fully qualified path to the SQLite 3 database
dbfile: /path/to/crossword.db

# log_level: one of CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
log_level: INFO
```

If the file does not exist, the application uses `examples/sample.crossword.db`
and a log level of `INFO`.

## Running the server

```bash
source venv/bin/activate   # if not already active
python -m crossword.http_server
```

Or use the provided script:

```bash
./run_server
```

This starts an HTTP server on port 5000. Stop it at any time with `Ctrl-C`.

## Using the application

Open a browser and go to **http://localhost:5000**.

The application is a single-page app with a home screen plus one merged construction editor:

### Home
Starting state. Choose to create or open a puzzle.

### Merged editor
Create the grid and fill the puzzle in one editor, switching modes as needed.

- **Grid mode:** edit black cells, rotate the grid, inspect stats, and use mode-local undo/redo.
- **Puzzle mode:** fill answers and clues, set the title, inspect stats, and use mode-local undo/redo.
- New puzzles begin in Grid mode.
- Existing puzzles reopen in the last mode used for that puzzle.
- Clicking a cell in Grid mode toggles it black/white. The grid is kept symmetric automatically.
- Click a cell or clue to select a word.
- The word editor panel offers three tabs: **Suggest** (word suggestions), **Constraints** (pattern matching), and **Reset**.
- The statistics panel is shared across both modes.

### Publish
Available from anywhere via the **Publish** menu:

| Format | Description |
|--------|-------------|
| Across Lite (.puz) | Standard binary format for most crossword apps |
| Crossword Compiler (.xml) | XML export |
| New York Times (.nyt) | NYT submission format |

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

| Script | Description |
|--------|-------------|
| `tools/swagger.py` | Swagger UI for the REST API (`python3 tools/swagger.py`) |
| `tools/md_to_pdf.py` | Convert Markdown to PDF via Chrome headless |

## References

- [GitHub repository](https://github.com/philhanna/crossword)
- [User guide (GitHub wiki)](https://github.com/philhanna/crossword/wiki)
