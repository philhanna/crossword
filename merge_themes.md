# Plan: Merge theme_editor into crossword

Source project: `/home/saspeh/dev/python/theme_editor`  
Target project: `/home/saspeh/dev/python/crossword`

---

## What's being merged

The `theme_editor` project is a standalone REST API that manages crossword **themes** — named sets of palindromic word lengths paired with selected words — and searches a library of grid patterns to find grids whose across-slot structure matches a theme.

After the merge, the crossword app will be able to:

1. Create, read, update, and delete themes (with palindrome validation).
2. Add and remove words from a theme's selected list.
3. Search an external grid library for grids whose across-slot structure matches a theme.
4. Edit themes and browse grid matches from the existing SPA frontend.

---

## Key architecture decisions

| Question | Decision | Rationale |
|---|---|---|
| Theme storage | SQLite table in the existing `dbfile`, not a separate JSON file | Single DB, same backup/migration path as puzzles |
| Theme scoping | Add `user_id` to the `themes` table (consistent with puzzles) | Multi-user support from day one |
| Grid library | Separate, read-only SQLite file; path configured via `grids_db` in `config.yaml` | Mirrors theme_editor design exactly; DB is managed independently |
| Grid DB access | `SQLiteGridAdapter` opens the `grids_db` file read-only; no writes ever | Preserve the separation between the grid library and application data |
| Use-case style | Class `ThemeUseCases` (matching `PuzzleUseCases`) instead of module-level functions | Consistent with existing codebase pattern |
| Palindrome validation | Kept at use-case layer (not HTTP layer) | Matches theme_editor design; raises `ValueError` |
| No `python-dotenv` | Not added as a dependency | crossword uses PyYAML config; env-var loading not needed |

---

## Database schema additions

Add to `SQLitePersistenceAdapter._ensure_schema_compatibility()` (main `dbfile` only):

```sql
-- Theme storage
CREATE TABLE IF NOT EXISTS themes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        TEXT    NOT NULL,
    title          TEXT    NOT NULL,
    word_lengths   TEXT    NOT NULL,   -- JSON array, e.g. "[5,7,7,5]"
    selected_words TEXT    NOT NULL    -- JSON array, e.g. '["CRANE","PELICAN"]'
);
```

The `grids` and `slot_counts` tables live in the separate grids DB and are
never created or modified by crossword.

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

`SQLiteGridAdapter` — read-only queries against the external grids DB.
Nearly identical to `theme_editor/src/theme_editor/adapters/sqlite_grid_repo.py`.

Key differences from source:
- Constructor takes `grids_db_path: str` (read from config, may be `None`
  if the user has not configured a grids DB — in that case `search()` returns `[]`)
- Opens the connection in read-only URI mode (`?mode=ro`)
- No `user_id` parameter — the grids DB is global/shared
- Returns filenames from the `grids` table (same as theme_editor)
- No `index_grid()` method — the DB is read-only

Reference for the SQL algorithm:
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
```

`search_grids` fetches the theme (for `word_lengths`), then delegates to
`grid_adapter.search(spec, size)`. No `user_id` is passed to the grid adapter
since the grids DB is global.

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
  show results (grid filenames from the external library) in a list

---

## Files to modify

### `crossword/adapters/sqlite_persistence_adapter.py`

Add the `CREATE TABLE IF NOT EXISTS themes` statement to
`_ensure_schema_compatibility()`.

### `crossword/http_server/main.py`

Import `theme_handlers` and register the eight new routes.

### `crossword/wiring/__init__.py`

1. Import `SQLiteThemeAdapter`, `SQLiteGridAdapter`, `ThemeUseCases`.
2. Instantiate `SQLiteThemeAdapter` with the main `dbfile` connection.
3. Instantiate `SQLiteGridAdapter` with `config.get("grids_db")` (may be
   `None`; adapter returns `[]` from `search()` in that case).
4. Instantiate `ThemeUseCases(theme_repo, grid_adapter)`.
5. Add `theme_uc` to `AppContainer`.

### `crossword/wiring/__init__.py` — `AppContainer`

Add `theme_uc` parameter:
```python
class AppContainer:
    def __init__(self, ..., theme_uc=None, ...):
        ...
        self.theme_uc = theme_uc
```

### `crossword/adapters/settings_adapter.py` (and settings UI)

Add `grids_db` as a recognised config key — the path to the external read-only
grids SQLite file. Expose it in the settings panel so users can configure it
from the UI (similar to `word_file`). The field is optional; leave blank to
disable grid search.

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
HTTP theme handler
  → app.theme_uc.{create,get,...}(user_id, ...)
      → self.theme_repo.{create,get,...}(user_id, ...)   [SQLiteThemeAdapter → main dbfile]

HTTP theme grid-search handler
  → app.theme_uc.search_grids(user_id, theme_id, size)
      → self.theme_repo.get(user_id, theme_id)           [get word_lengths]
      → self.grid_adapter.search(spec, size)             [SQLiteGridAdapter → separate grids_db]
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
| `tests/adapters/test_sqlite_grid_repo.py` (9 tests) | `crossword/tests/test_sqlite_grid_adapter.py` | Port verbatim; no `user_id`; no `index_grid()` (read-only adapter) |
| `tests/http/test_handlers.py` (18 tests) | `crossword/tests/http/test_theme_handlers.py` | Adapt to crossword handler signature and test harness pattern |

New test needed: `test_theme_use_cases.py::test_search_grids_no_grids_db` — verifies
that `search_grids()` returns `[]` gracefully when no `grids_db` is configured.

---

## Implementation order

1. **Schema** — add `themes` table in `sqlite_persistence_adapter.py`; run
   existing test suite to confirm no breakage.
2. **Domain** — add `crossword/domain/theme.py`; port domain tests.
3. **Port** — add `crossword/ports/theme_persistence_port.py`.
4. **Adapters** — `sqlite_theme_adapter.py` + `sqlite_grid_adapter.py`; port
   adapter tests.
5. **Use cases** — `theme_use_cases.py`; port use-case tests.
6. **HTTP handlers** — `theme_handlers.py` + route registration; port HTTP
   tests.
7. **Wiring** — update `AppContainer` and `make_app()`; add `grids_db` to
   settings adapter.
8. **Frontend** — `theme-editor.js` + `index.html` menu + CSS additions,
   including `grids_db` field in settings panel.
9. **Full regression** — run `pytest crossword/tests/` and manual browser test.

---

## Out of scope

- The bash scripts in `theme_editor/scripts/` — they wrap the old HTTP API
  and are not needed once the crossword frontend provides the UI.
- The `python-dotenv` dependency — not added; crossword uses `config.yaml`.
- Management of the external grids DB — crossword never writes to it; how
  it is populated and updated is outside this project's scope.
- The `GridPattern.grid_text` field — search results are filenames only;
  grid text is not surfaced in the crossword UI.
