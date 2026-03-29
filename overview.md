# Crossword Composer — Codebase Overview

## Overview

**Crossword Composer** (v3.4.0) is a web-based application for creating and editing crossword puzzles. It runs a local Python HTTP server on port 5000 and is accessed through a browser. It supports NYT-style rules for grid construction, filling, cluing, and exporting puzzles to multiple industry-standard formats.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.10+ |
| **Web framework** | None — uses Python's built-in `http.server.BaseHTTPRequestHandler` |
| **Database** | SQLite (via standard `sqlite3` module) |
| **Configuration** | YAML (via `PyYAML`) |
| **Frontend** | Vanilla HTML/CSS/JavaScript — no frameworks |
| **Testing** | `pytest` |
| **Build/Package** | `setuptools` (`pyproject.toml`) |
| **Dependencies** | Only `PyYAML` (+ `pytest` for dev) |

This is deliberately **dependency-minimal** — no Flask, no Django, no ORM, no frontend framework.

---

## Architectural Pattern: Hexagonal (Ports & Adapters)

The backend is organized in clean, concentric layers:

```
crossword/
├── domain/          ← Pure business logic, no I/O
├── ports/           ← Abstract interfaces (ABCs)
├── adapters/        ← Concrete implementations of ports
├── use_cases/       ← Orchestrates domain + ports
├── http_server/     ← HTTP layer (routes, handlers)
└── wiring/          ← Dependency injection / app assembly
```

---

## Layer-by-Layer Breakdown

### 1. `domain/` — Core Business Logic

Pure Python, no external dependencies. The fundamental model objects:

| File | Role |
|------|------|
| `grid.py` | An **n×n grid** of black/white cells. Handles symmetry (black cells are always placed in 180°-symmetric pairs), numbered cell computation, undo/redo, rotation, validation (NYT rules: interlock, unchecked squares, min word length), and JSON serialization. |
| `puzzle.py` | A **grid + words + clues** combined. Contains across/down word maps, cell letters, title, two separate undo/redo stacks (one for grid mode, one for puzzle mode), and a "last mode" flag. Also does JSON serialization/deserialization. |
| `word.py` | `AcrossWord` and `DownWord` classes. Know which cells they span and provide `get_text()`/`set_text()`/`get_clue()`/`set_clue()`. |
| `numbered_cell.py` | A cell that starts an across or down word, storing its sequence number, position, and word lengths. |
| `letter_list.py` | Utility for constraint/pattern matching. |
| `to_svg.py` | Renders the grid as an SVG image. |

**Key design decisions:**
- Grids enforce 180° rotational symmetry automatically on every black-cell toggle.
- Grid mode and puzzle mode each have their own independent undo/redo stacks.
- All domain objects serialize to/from JSON for persistence.

---

### 2. `ports/` — Abstract Interfaces

Python `ABC`s defining contracts without implementation:

| Port | Contract |
|------|----------|
| `PersistencePort` | `save_puzzle`, `load_puzzle`, `delete_puzzle`, `list_puzzles` |
| `WordListPort` | `get_matches(pattern)`, `get_all_words()` |
| `ExportPort` | `export_puzzle_to_acrosslite`, `export_puzzle_to_xml`, `export_puzzle_to_json`, `export_puzzle_to_nytimes`, `export_grid_to_pdf`, `export_grid_to_png` |

---

### 3. `adapters/` — Concrete Implementations

| Adapter | Implements | Details |
|---------|-----------|---------|
| `SQLitePersistenceAdapter` | `PersistencePort` | Stores puzzles as JSON blobs in SQLite. |
| `SQLiteDictionaryAdapter` | `WordListPort` | Loads word list from SQLite database or flat file; pattern matching via regex. |
| `AcrossLiteExportAdapter` | `ExportPort` | Exports to `.puz`-compatible text format (AcrossLite). |
| `CcxmlExportAdapter` | `ExportPort` | Exports to Crossword Compiler XML. |
| `NYTimesExportAdapter` | `ExportPort` | Exports a PDF in NYT submission format (answer grid + clue sheet). |
| `JsonExportAdapter` | `ExportPort` | Clean JSON export. |

---

### 4. `use_cases/` — Application Logic

| Use Case | Role |
|----------|------|
| `PuzzleUseCases` | Create, open, save, copy, delete puzzles; toggle black cells; rotate; toggle modes; set cells/clues/title; undo/redo; stats; working-copy management. |
| `WordUseCases` | Word suggestions, constraint matching, validation, ranked suggestions. |
| `ExportUseCases` | Delegates to export adapters. |
| `_name_validation.py` | Validates puzzle names (private utility). |

---

### 5. `wiring/` — Dependency Injection

`make_app(config)` is the **single assembly point**:
1. Reads config (from `~/.config/crossword/config.yaml` or passed-in dict)
2. Creates all adapter instances with their config (DB paths, author name, etc.)
3. Injects them into use case constructors
4. Returns an `AppContainer` with `puzzle_uc`, `word_uc`, `export_uc`

---

### 6. `http_server/` — HTTP Layer

**No Flask** — uses Python's built-in `BaseHTTPRequestHandler` with a custom regex-based router:

- `server.py`: `Router` + `RequestHandler` — parses URL, extracts path params, reads body/cookies, dispatches to handler
- `main.py`: Registers all routes and starts the server
- `puzzle_handlers.py`: ~20 REST endpoints for puzzle CRUD and editing
- `word_handlers.py`: Word suggestion/constraint endpoints
- `export_handlers.py`: Export endpoints (returns binary/text files)
- `static_handlers.py`: Serves `index.html` and static assets

**Sample routes:**

```
GET  /api/puzzles                         → list all puzzles
POST /api/puzzles                         → create new puzzle
POST /api/puzzles/{name}/open             → open for editing (creates working copy)
PUT  /api/puzzles/{name}/grid/cells/r/c   → toggle black cell
GET  /api/puzzles/{name}/words/3/across   → get word info
GET  /api/export/puzzles/{name}/nytimes   → download NYT PDF
```

---

### 7. `frontend/` — Single-Page App

| File | Role |
|------|------|
| `index.html` | Single HTML page — home screen + merged editor |
| `static/js/app.js` | ~1,730 lines of vanilla JS — all UI logic, API calls, state management, grid rendering |
| `static/css/style.css` | Styling |

**Frontend state machine (`AppState`):**
- `view`: `'home'` or `'editor'`
- `puzzleName` / `puzzleWorkingName`: tracks original vs. working copy
- `editingWord` / `selectedWord`: current word being edited
- `gridStructureChanged`: flags that the grid shape changed during grid mode

**Working copy pattern:** Every time you open a puzzle for editing, the server creates an invisible copy named `__wc__<uuid>`. All edits go to this copy. "Save" commits it back; "Close" discards it. This prevents accidental overwrites.

---

### 8. `tests/` — Test Suite

Located at `crossword/tests/`, run via `pytest`. Covers:
- Domain: grid operations, word operations, puzzle behaviors (undo/redo, validation, SVG, XML, etc.)
- Adapters: SQLite persistence, dictionary, export
- Use cases: puzzle and word use cases
- HTTP server: route-level integration tests
- Utilities: wiring, ports, migration tool

---

## Configuration & Data Files

```
~/.config/crossword/config.yaml
  dbfile:      /path/to/crossword.db    ← Puzzle storage (SQLite)
  word_dbfile: /path/to/words.db        ← Word list (SQLite, separate)
  log_level:   INFO
  author_name: ...                      ← Used in NYT export PDF
```

---

## Tools

| Directory | Scripts |
|-----------|---------|
| `tools/admin/` | Export puzzles from CLI, clean up orphaned working copies |
| `tools/dev/` | Swagger UI for API exploration, endpoint doc generator, v3.2 DB migration script |

---

## Summary Diagram

```
Browser (index.html + app.js)
        ↕ HTTP/REST
http_server/ (BaseHTTPRequestHandler + Router)
        ↕
wiring/AppContainer
    ├── PuzzleUseCases ──→ SQLitePersistenceAdapter ──→ crossword.db (SQLite)
    ├── WordUseCases   ──→ SQLiteDictionaryAdapter   ──→ words.db (SQLite)
    └── ExportUseCases ──→ AcrossLite / CCXML / NYTimes / JSON adapters
            ↕ (all use)
        domain/ (Grid, Puzzle, Word — pure Python)
```

The architecture is clean, testable, and framework-free — making it easy to understand, extend, or swap out any individual layer (e.g., replace SQLite with a different store by implementing a new `PersistencePort`).
