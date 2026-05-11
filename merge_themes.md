# Plan: Merge theme_editor into crossword

Source project: `/home/saspeh/dev/python/theme_editor`  
Target project: `/home/saspeh/dev/python/crossword`

---

## What's being merged

The `theme_editor` project is a standalone REST API that manages crossword **themes** — named sets of palindromic word lengths paired with selected words — and searches a library of grid patterns to find grids whose across-slot structure matches a theme.

After the merge, the crossword app will be able to:

1. Create, read, update, and delete themes (with palindrome validation).
2. Add and remove words from a theme's selected list.
3. Search existing puzzle grids for ones whose across-slot structure matches a theme.
4. Edit themes and browse grid matches from the existing SPA frontend.

---

## Key architecture decisions

| Question | Decision | Rationale |
|---|---|---|
| Theme storage | SQLite table in the existing `dbfile`, not a separate JSON file | Single DB, same backup/migration path as puzzles |
| Theme scoping | Add `user_id` to the `themes` table (consistent with puzzles) | Multi-user support from day one |
| Grid library | Add `grids` + `slot_counts` tables to the existing `dbfile`; index them when puzzles are saved | No external DB; reuses data already in the app |
| Grid indexing trigger | `ThemeUseCases.index_puzzle_grid()` called by puzzle save handlers | Keeps slot-count computation in the use-case layer, not the adapter |
| Use-case style | Class `ThemeUseCases` (matching `PuzzleUseCases`) instead of module-level functions | Consistent with existing codebase pattern |
| Palindrome validation | Kept at use-case layer (not HTTP layer) | Matches theme_editor design; raises `ValueError` |
| No `python-dotenv` | Not added as a dependency | crossword uses PyYAML config; env-var loading not needed |

---

## Database schema additions

Add to `SQLitePersistenceAdapter._ensure_schema_compatibility()`:

```sql
-- Theme storage
CREATE TABLE IF NOT EXISTS themes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    word_lengths TEXT   NOT NULL,  -- JSON array, e.g. "[5,7,7,5]"
    selected_words TEXT NOT NULL   -- JSON array, e.g. '["CRANE","PELICAN"]'
);

-- Grid pattern library (indexed from saved puzzles)
CREATE TABLE IF NOT EXISTS grids (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     TEXT    NOT NULL,
    puzzle_name TEXT    NOT NULL,
    size        INTEGER NOT NULL,
    UNIQUE(user_id, puzzle_name)
);

CREATE TABLE IF NOT EXISTS slot_counts (
    grid_id     INTEGER NOT NULL REFERENCES grids(id) ON DELETE CASCADE,
    direction   TEXT    NOT NULL CHECK (direction IN ('A', 'D')),
    length      INTEGER NOT NULL,
    count       INTEGER NOT NULL,
    PRIMARY KEY (grid_id, direction, length)
);
```

---

## Files to create

### 1. `crossword/domain/theme.py`

Copy `Theme` and `GridPattern` dataclasses verbatim from
`theme_editor/src/theme_editor/domain/theme.py`. No changes needed.

### 2. `crossword/ports/theme_persistence_port.py`

Abstract base class `ThemePersistencePort` mirroring the shape of
`theme_editor/src/theme_editor/ports/theme_repo.py`, but adapted for
crossword conventions (`user_id` parameter on every method):

```python
class ThemePersistencePort(ABC):
    def create(self, user_id, title, word_lengths) -> Theme: ...
    def get(self, user_id, theme_id) -> Theme | None: ...
    def list_all(self, user_id) -> list[Theme]: ...
    def update(self, user_id, theme_id, *, title=None, word_lengths=None) -> Theme | None: ...
    def delete(self, user_id, theme_id) -> bool: ...
    def add_word(self, user_id, theme_id, words) -> Theme | None: ...
    def remove_word(self, user_id, theme_id, word) -> Theme | None: ...
```

### 3. `crossword/adapters/sqlite_theme_adapter.py`

`SQLiteThemeAdapter(ThemePersistencePort)` — stores themes in the `themes`
table created above. Replaces the JSON-file `JsonThemeRepo`.

- Constructor takes the same `sqlite3.Connection` (or `db_path` string) used
  by `SQLitePersistenceAdapter`.
- `word_lengths` and `selected_words` serialized as JSON strings.
- ID is `AUTOINCREMENT`; `user_id` filters all queries.

Reference: `theme_editor/src/theme_editor/adapters/json_theme_repo.py` for
the logic; replace file I/O with SQL.

### 4. `crossword/adapters/sqlite_grid_adapter.py`

`SQLiteGridAdapter` — queries the `grids`/`slot_counts` tables using the
same SQL algorithm as `theme_editor/src/theme_editor/adapters/sqlite_grid_repo.py`.

Key differences from source:
- `search(user_id, spec, size)` (adds `user_id` filter on `grids`)
- Returns puzzle names instead of filenames
- Add `index_grid(user_id, puzzle_name, size, slot_counts_by_direction)` to
  upsert a grid's slot data after puzzle save

Reference for the complex SQL algorithm:
`theme_editor/src/theme_editor/adapters/sqlite_grid_repo.py`

### 5. `crossword/use_cases/theme_use_cases.py`

`ThemeUseCases` class (constructor: `theme_repo`, `grid_adapter`):

```python
class ThemeUseCases:
    def __init__(self, theme_repo: ThemePersistencePort,
                 grid_adapter: SQLiteGridAdapter): ...
    def create_theme(self, user_id, title, word_lengths, selected_words=None) -> Theme
    def get_theme(self, user_id, theme_id) -> Theme | None
    def list_themes(self, user_id) -> list[Theme]
    def update_theme(self, user_id, theme_id, *, title=None, word_lengths=None) -> Theme | None
    def delete_theme(self, user_id, theme_id) -> bool
    def add_words(self, user_id, theme_id, words) -> Theme | None
    def remove_word(self, user_id, theme_id, word) -> Theme | None
    def search_grids(self, user_id, theme_id, size) -> list[str]
    def index_puzzle_grid(self, user_id, puzzle_name, puzzle) -> None
```

`index_puzzle_grid` computes slot counts from the `Puzzle` domain object's
`across_words` and `down_words` dicts (word lengths already available) and
calls `grid_adapter.index_grid()`. Call this from puzzle save handlers.

Palindrome validation lives here (raises `ValueError`), matching the
theme_editor design.

### 6. `crossword/http_server/theme_handlers.py`

Eight handler functions matching the existing handler signature
`(path_params, query_params, body_params, session_token, request_handler, app, current_user, **kwargs)`:

| Handler | Method | Route |
|---|---|---|
| `handle_list_themes` | GET | `/api/themes` |
| `handle_create_theme` | POST | `/api/themes` |
| `handle_get_theme` | GET | `/api/themes/{id}` |
| `handle_update_theme` | PUT | `/api/themes/{id}` |
| `handle_delete_theme` | DELETE | `/api/themes/{id}` |
| `handle_add_words` | POST | `/api/themes/{id}/words` |
| `handle_remove_word` | DELETE | `/api/themes/{id}/words/{word}` |
| `handle_search_grids` | GET | `/api/themes/{id}/grids` |

`handle_search_grids` reads `size` from query params (required integer).
All handlers use `app.theme_uc`. `ValueError` (palindrome) → 400. Missing
theme → 404.

### 7. `frontend/static/js/theme-editor.js`

New JS module providing theme management UI. Key functions:

- `openThemeEditor()` — fetch theme list, render as a chooser or dedicated panel
- `renderThemeList()` — list of themes with title + word_lengths + completion badge
- `renderThemeDetail(themeId)` — form for title/word_lengths, word slot editor,
  grid search results
- `doThemeNew()` — input box for title + word_lengths → POST `/api/themes`
- `doThemeAddWord(themeId)` — input box → POST `/api/themes/{id}/words`
- `doThemeRemoveWord(themeId, word)` — DELETE `/api/themes/{id}/words/{word}`
- `doThemeSearchGrids(themeId)` — prompt for size → GET `/api/themes/{id}/grids`,
  show results (puzzle names) in a list with "Open" links

---

## Files to modify

### `crossword/adapters/sqlite_persistence_adapter.py`

Add the three `CREATE TABLE IF NOT EXISTS` statements for `themes`,
`grids`, and `slot_counts` to `_ensure_schema_compatibility()`.

### `crossword/http_server/main.py`

Import `theme_handlers` and register the eight new routes.

### `crossword/wiring/__init__.py`

1. Import `SQLiteThemeAdapter`, `SQLiteGridAdapter`, `ThemeUseCases`.
2. Instantiate both adapters (they share `dbfile` / connection).
3. Instantiate `ThemeUseCases(theme_repo, grid_adapter)`.
4. Add `theme_uc` to `AppContainer`.

### `crossword/wiring/__init__.py` — `AppContainer`

Add `theme_uc` parameter:
```python
class AppContainer:
    def __init__(self, ..., theme_uc=None, ...):
        ...
        self.theme_uc = theme_uc
```

### `crossword/http_server/puzzle_handlers.py`

After every successful `puzzle_uc.save_puzzle()` call (create, copy, import,
word edit), call `app.theme_uc.index_puzzle_grid(user_id, name, puzzle)` so
the grid search index stays current.

### `frontend/index.html`

Add a **Themes** top-level menu item (alongside Puzzle, Import, Export,
Settings). Add a `<div id="theme-panel">` workspace section.

### `frontend/static/css/style.css`

Add styles for the theme panel: theme list cards, slot-length badge row,
word slot inputs, and grid search results list. Keep the same design tokens
(`--c-*` variables).

---

## Wiring call graph (after merge)

```
HTTP handler
  → app.theme_uc.{create,get,...}(user_id, ...)
      → self.theme_repo.{create,get,...}(user_id, ...)   [SQLiteThemeAdapter]
      → self.grid_adapter.search(user_id, spec, size)     [SQLiteGridAdapter]

HTTP puzzle save handler
  → app.puzzle_uc.save_puzzle(...)
  → app.theme_uc.index_puzzle_grid(user_id, name, puzzle)
      → self.grid_adapter.index_grid(...)
```

---

## Tests to port

The theme_editor has 56 tests across 5 files. Each maps to a new test file
in `crossword/tests/`:

| Source | Target | Notes |
|---|---|---|
| `tests/domain/test_theme.py` (4 tests) | `crossword/tests/test_theme_domain.py` | Copy verbatim; adjust import path |
| `tests/application/test_theme_service.py` (14 tests) | `crossword/tests/test_theme_use_cases.py` | Convert module-function calls to `ThemeUseCases` method calls; add `user_id` arg |
| `tests/application/test_grid_service.py` (1 test) | Merge into `test_theme_use_cases.py` | `search_grids()` test |
| `tests/adapters/test_json_theme_repo.py` (15 tests) | `crossword/tests/test_sqlite_theme_adapter.py` | Replace JSON file setup with `:memory:` SQLite; same CRUD + word logic |
| `tests/adapters/test_sqlite_grid_repo.py` (9 tests) | `crossword/tests/test_sqlite_grid_adapter.py` | Port test grid fixtures; add `user_id`; test `index_grid()` + `search()` |
| `tests/http/test_handlers.py` (18 tests) | `crossword/tests/http/test_theme_handlers.py` | Adapt to crossword handler signature and test harness pattern |

New test needed: `test_theme_use_cases.py::test_index_puzzle_grid` — verifies
that saving a puzzle populates `slot_counts` correctly.

---

## Implementation order

1. **Schema** — add tables in `sqlite_persistence_adapter.py`; run existing test
   suite to confirm no breakage.
2. **Domain** — add `crossword/domain/theme.py`; port domain tests.
3. **Port** — add `crossword/ports/theme_persistence_port.py`.
4. **Adapters** — `sqlite_theme_adapter.py` + `sqlite_grid_adapter.py`; port
   adapter tests.
5. **Use cases** — `theme_use_cases.py`; port use-case tests.
6. **HTTP handlers** — `theme_handlers.py` + route registration; port HTTP
   tests.
7. **Wiring** — update `AppContainer` and `make_app()`.
8. **Grid indexing** — hook `index_puzzle_grid()` into puzzle save paths.
9. **Frontend** — `theme-editor.js` + `index.html` menu + CSS additions.
10. **Full regression** — run `pytest crossword/tests/` and manual browser test.

---

## Out of scope

- The bash scripts in `theme_editor/scripts/` — they wrap the old HTTP API
  and are not needed once the crossword frontend provides the UI.
- The `python-dotenv` dependency — not added; crossword uses `config.yaml`.
- The `GridPattern.grid_text` field in search results — crossword returns
  puzzle names; callers can open the puzzle to see the grid.
- Import of an external grid library — the `grids` table is populated only
  from puzzles the current user has saved. A bulk-import tool can be added
  later if needed.
