# Crossword Composer — Ports & Adapters Design

## The big idea

The app is structured so that the core business logic (domain) never knows about
databases, file formats, or HTTP. Instead, it talks through abstract interfaces
called **ports**. Concrete **adapters** plug in behind those ports and do the
actual work. A thin **wiring** layer assembles everything at startup.

```
HTTP request
     │
     ▼
┌──────────────┐
│  HTTP Server │  — routes request to a handler function
└──────┬───────┘
       │ calls
       ▼
┌──────────────┐
│  Use Cases   │  — pure business logic, no HTTP/DB knowledge
└──────┬───────┘
       │ calls (through ports)
       ▼
┌──────────────┐       ┌──────────────┐
│ SQLiteAdapter│       │DictionaryAdpt│
│ (persistence)│       │ (word list)  │
└──────────────┘       └──────────────┘
```

---

## Layers

### Domain models (`crossword/domain/`)

Pure Python classes. No database, no HTTP, no third-party libraries.

- **Grid** — an n×n grid of black and white cells, with undo/redo history
- **Puzzle** — a Grid plus letter cells, across/down words, and clues
- **Word** — a single word slot in a puzzle; constants `Word.ACROSS = "A"`,
  `Word.DOWN = "D"`

These classes serialize themselves to/from JSON (`to_json()` / `from_json()`),
but they don't know where that JSON goes.

---

### Ports (`crossword/ports/`)

Abstract base classes that define *what* the app needs from the outside world.
The domain and use cases depend only on these interfaces.

| Port | What it represents |
|------|--------------------|
| `PersistencePort` | Save/load/delete/list grids and puzzles |
| `WordListPort` | Look up words by pattern |
| `ExportPort` | Export grids/puzzles to PDF, PNG, AcrossLite, etc. |

Each port is just method signatures + a matching exception class. No
implementation lives here.

---

### Adapters (`crossword/adapters/`)

Concrete classes that implement the ports using real technology.

**SQLiteAdapter** implements `PersistencePort`:
- Connects to an SQLite file (`samples.db` by default)
- Stores grids in a `grids` table, puzzles in a `puzzles` table
- Serializes domain objects to JSON strings before writing; deserializes on read

**DictionaryAdapter** implements `WordListPort`:
- Loads a word list from the same SQLite database (`words` table)
- Keeps words in memory as a Python set
- Matches patterns using `re.fullmatch()` (full-word match, case-insensitive)

---

### Use cases (`crossword/use_cases/`)

One class per domain concept. They receive port objects via their constructor
(dependency injection) and coordinate the work:

```
GridUseCases(persistence)      — load, save, rotate, undo/redo, open-for-editing
PuzzleUseCases(persistence)    — load, save, set cell, set clue, undo/redo
WordUseCases(word_list)        — suggest words, validate, compute constraints
ExportUseCases(persistence)    — load then delegate to ExportPort
```

A typical use-case method:
1. Load a domain object from the persistence port
2. Call a method on it (pure logic, no side effects)
3. Save the updated domain object back through the port
4. Return the result to the caller

Use cases never import SQLite, HTTP, or any framework.

---

### Wiring (`crossword/wiring/__init__.py`)

The single place that knows about every concrete adapter. Called once at
startup:

```python
def make_app(config) -> AppContainer:
    persistence = SQLiteAdapter(config['dbfile'])
    words = DictionaryAdapter()
    words.load_from_database(config['dbfile'])

    return AppContainer(
        grid_uc   = GridUseCases(persistence),
        puzzle_uc = PuzzleUseCases(persistence),
        word_uc   = WordUseCases(words),
        export_uc = ExportUseCases(persistence, export_adapter=None),
    )
```

`AppContainer` is a plain data object that carries the four use-case instances.

---

### HTTP server (`crossword/http_server/`)

Built on Python's built-in `BaseHTTPRequestHandler`. No web framework.

**Startup sequence** (`main.py`):
1. Read config from `~/.crossword.ini`
2. Call `make_app(config)` to build the wired container
3. Register ~40 URL routes (method + regex → handler function)
4. Start the server, attaching the container as `handler.app`

**Per-request flow:**
1. `do_GET` / `do_POST` / `do_PUT` / `do_DELETE` → `_handle_request(method)`
2. Router matches path, extracts path params
3. Handler function is called with `path_params`, `query_params`, `body_params`,
   and `app` (the container)
4. Handler calls `app.grid_uc.some_method(...)` or similar
5. Returns a dict (serialized to JSON) or raw bytes

---

## End-to-end example

**Request:** `GET /api/words/suggestions?pattern=?HALE`

```
HTTP server
  → router matches → handle_get_suggestions(app=..., query_params={"pattern":"?HALE"})

handle_get_suggestions
  → app.word_uc.get_suggestions("?HALE")

WordUseCases.get_suggestions
  → _pattern_to_regex("?HALE") → "^.HALE$"
    (regex-syntax patterns like "[A-Z]..." also get ^...$ anchors added)
  → self.word_list.get_matches("^.HALE$")   ← calls the port

DictionaryAdapter.get_matches
  → filter in-memory word set with re.fullmatch("^.HALE$", word, re.IGNORECASE)
  → returns ["SHALE", "WHALE", ...]

Response: {"pattern": "?HALE", "suggestions": ["SHALE", "WHALE", ...], "count": 2}
```

---

## Dependency rules (what knows about what)

| Layer | May import |
|-------|-----------|
| Domain | stdlib only |
| Ports | Domain |
| Adapters | Ports + Domain + technology libs (sqlite3, re) |
| Use Cases | Ports + Domain |
| HTTP handlers | Use Cases + Ports (for exceptions) |
| Wiring | Adapters + Use Cases |
| HTTP server | Wiring + HTTP handlers |

The arrows always point inward toward the domain. The domain knows nothing about
any other layer.

---

## Swapping an adapter

Because use cases only depend on the port interface, swapping an adapter is
straightforward: write a new class that implements the same ABC, then change the
single `make_app()` call in `wiring/__init__.py`. Everything else stays the same.

For example, switching from SQLite to PostgreSQL would only require a new
`PostgresAdapter` that implements `PersistencePort`. No use-case code changes.
