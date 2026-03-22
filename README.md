# Crossword Composer

A web-based application for creating and editing crossword puzzles.

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

The application is configured via `~/.crossword.ini` in your home directory:

```ini
[DEFAULT]
#
# dbfile - Fully qualified path to the SQLite 3 database.
#
dbfile=/path/to/crossword.db
#
# log_level - One of: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
#
log_level=INFO
```

If the file does not exist, the application uses `samples.db` in the project directory
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

The application is a single-page app with three modes:

### Home
Starting state. Choose to create or open a grid or puzzle.

### Grid editor
Create and edit the black-cell pattern of a crossword grid.

- **Toolbar:** Rotate, Undo, Redo, Info, Save, Close
- **Menu (Grid):** New, New from puzzle, Open, Save, Save As, Close, Delete
- Click a cell to toggle it black/white. The grid is kept symmetric automatically.
- Undo/redo history is maintained per session.

### Puzzle editor
Fill in answers and clues for a grid.

- **Toolbar:** Save, Save As, Close, Title, Info, Undo, Redo
- **Menu (Puzzle):** New, Open, Save, Save As, Close, Delete
- Click a cell or clue to select a word.
- The word editor panel offers three tabs: **Suggest** (word suggestions), **Constraints** (pattern matching), and **Reset**.
- A statistics panel shows fill progress.

### Publish
Available from any mode via the **Publish** menu:

| Format | Description |
|--------|-------------|
| Across Lite (.puz) | Standard binary format for most crossword apps |
| Crossword Compiler (.xml) | XML export |
| New York Times (.nyt) | NYT submission format |

### Working copy pattern
All edits target an invisible working copy (`__wc__<uuid>`). Choosing **Save** commits
the working copy back to the named puzzle/grid. Choosing **Close** without saving
discards it. This means every keystroke is auto-persisted without overwriting the
last saved version until you explicitly save.

## Architecture

The backend follows a **Hexagonal (Ports & Adapters)** design:

| Layer | Modules |
|-------|---------|
| Domain | `grid`, `puzzle`, `word` — pure Python, no framework deps |
| Ports | `persistence`, `word_list`, `export` |
| Adapters | `SQLiteAdapter`, `DictionaryAdapter`, `ExportAdapter` |
| Use Cases | `GridUseCases`, `PuzzleUseCases`, `WordUseCases`, `ExportUseCases` |
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
