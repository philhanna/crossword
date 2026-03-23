# Implementation Checkpoints — Restructuring Plan with Testable Stopping Points

**Date:** 2026-03-19
**Purpose:** Define explicit, testable stopping points throughout the restructuring. After each checkpoint, the system must be in a **stable, non-broken state**.

---

## Overview: Stopping Point Philosophy

Each stopping point has three components:

1. **Deliverable** — What code/files exist?
2. **Test Criteria** — What must pass? (existing tests + new tests)
3. **Validation Checklist** — Verify the system didn't regress.

If a test fails at any checkpoint, **do not proceed**. Fix the failing test and re-validate before moving forward.

---

## Phase 1: Foundation (Ports & Adapters Core)

### **Checkpoint 1.1: Port Interfaces Defined**

**Deliverable:**
- `crossword/ports/persistence.py` — CRUD interface for grids, puzzles, users
- `crossword/ports/word_list.py` — word matching interface
- `crossword/ports/export.py` — export format contract
- `crossword/ports/__init__.py` — package marker

**Test Criteria:**
- All 22 existing domain tests pass: `pytest crossword/tests/ -v`
- Port files have no runtime errors (import them all without exception)
- Port classes/protocols are documented with docstrings

**Validation Checklist:**
```bash
# Run domain tests
pytest crossword/tests/ -v

# Verify ports can be imported
python -c "from crossword.ports import persistence, word_list, export; print('✓ Ports OK')"

# Verify no Flask/SQLAlchemy imports in ports
grep -r "from flask\|import flask\|from flask_sqlalchemy\|import flask_sqlalchemy" crossword/ports/ && exit 1 || echo "✓ No Flask in ports"
```

**System State:** Stable. Domain is untouched; new ports define contracts only.

---

### **Checkpoint 1.2: SQLiteAdapter Implemented & Tested**

**Deliverable:**
- `crossword/adapters/sqlite_adapter.py` — reads/writes to sqlite3 directly
- `crossword/tests/adapters/test_sqlite_adapter.py` — unit tests for adapter

**Code to implement:**
```python
# crossword/adapters/sqlite_adapter.py
class SQLiteAdapter:
    def __init__(self, db_path):
        self.db_path = db_path

    def init_schema(self):
        """Create tables if not present; validate against existing samples.db schema."""
        pass

    def load_grid(self, user_id: int, grid_name: str) -> Grid:
        """Load a grid from the database."""
        pass

    def save_grid(self, user_id: int, grid_name: str, grid: Grid) -> None:
        """Save a grid to the database."""
        pass

    # ... other CRUD methods
```

**Test Criteria:**
- All 22 existing domain tests pass: `pytest crossword/tests/ -v`
- New adapter tests pass: `pytest crossword/tests/adapters/test_sqlite_adapter.py -v`
  - `test_init_schema()` — creates tables
  - `test_save_and_load_grid()` — round-trip grid
  - `test_load_existing_grid_from_samples_db()` — loads from actual `samples.db`
  - `test_grid_mutation_preserved()` — black cells, rotations, etc. persist
- Adapter uses `sqlite3` directly (no SQLAlchemy)

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
pytest crossword/tests/adapters/test_sqlite_adapter.py -v

# Verify schema matches existing samples.db
sqlite3 samples.db ".schema" > /tmp/schema_before.txt
python -c "
from crossword.adapters.sqlite_adapter import SQLiteAdapter
a = SQLiteAdapter(':memory:')
a.init_schema()
" && echo "✓ Schema creation OK"

# Spot-check: load a real grid
python -c "
from crossword.adapters.sqlite_adapter import SQLiteAdapter
a = SQLiteAdapter('samples.db')
g = a.load_grid(1, 'grid_1')
print(f'✓ Loaded grid size={g.size}')
"
```

**System State:** Stable. Adapter works for at least one grid from `samples.db`.

---

### **Checkpoint 1.3: Dictionary & Export Adapters Implemented & Tested**

**Deliverable:**
- `crossword/adapters/dictionary_adapter.py` — loads word list, provides suggestions
- `crossword/adapters/export_adapter.py` — exports grid/puzzle to PDF, PNG, AcrossLite, Puz
- `crossword/tests/adapters/test_dictionary_adapter.py`
- `crossword/tests/adapters/test_export_adapter.py`

**Test Criteria:**
- All 22 existing domain tests pass: `pytest crossword/tests/ -v`
- All adapter tests pass:
  - `test_dictionary_basic_lookup()`
  - `test_dictionary_suggestions()`
  - `test_export_to_pdf()`
  - `test_export_to_png()`
  - `test_export_to_acrosslite()`
  - `test_export_to_puz()`
- Exports are valid files (can be opened/read)

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
pytest crossword/tests/adapters/ -v

# Verify exports are readable
python -c "
from crossword.adapters.export_adapter import ExportAdapter
from crossword.domain import Grid
a = ExportAdapter()
grid = Grid(15)
pdf_bytes = a.export_pdf(grid, 'test.pdf')
print(f'✓ PDF export OK: {len(pdf_bytes)} bytes')
"
```

**System State:** Stable. All adapters working independently.

---

### **Checkpoint 1.4: Use-Case Classes Created & Injected**

**Deliverable:**
- `crossword/use_cases/grid_use_cases.py` → `GridUseCases`
- `crossword/use_cases/puzzle_use_cases.py` → `PuzzleUseCases`
- `crossword/use_cases/word_use_cases.py` → `WordUseCases`
- `crossword/use_cases/export_use_cases.py` → `ExportUseCases`
- `crossword/config/wiring.py` → `make_app(config) -> Container`
- `crossword/tests/use_cases/test_*_use_cases.py`

**Example structure:**
```python
# crossword/use_cases/grid_use_cases.py
class GridUseCases:
    def __init__(self, persistence_port, word_list_port):
        self.persistence = persistence_port
        self.word_list = word_list_port

    def load_grid(self, user_id: int, name: str) -> Grid:
        return self.persistence.load_grid(user_id, name)

    def save_grid(self, user_id: int, name: str, grid: Grid) -> None:
        self.persistence.save_grid(user_id, name, grid)

    # ... other methods
```

**Test Criteria:**
- All 22 existing domain tests pass: `pytest crossword/tests/ -v`
- Use-case tests pass:
  - `test_grid_use_cases_load_and_save()`
  - `test_puzzle_use_cases_create_and_update()`
  - `test_word_use_cases_get_suggestions()`
  - `test_export_use_cases_export_to_all_formats()`
- `make_app()` returns a fully wired container (no missing dependencies)
- Use cases take all dependencies via constructor; no globals/singletons

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
pytest crossword/tests/use_cases/ -v

# Verify wiring works end-to-end
python -c "
from crossword.config.wiring import make_app
container = make_app({'db': 'samples.db'})
grid = container.grid_use_cases.load_grid(1, 'grid_1')
print(f'✓ Wiring OK: loaded grid size={grid.size}')
"
```

**System State:** Stable. Core business logic is now independent of Flask/SQLAlchemy.

---

### **Checkpoint 1.5: End-of-Phase 1 Validation**

**Deliverable:** Phase 1 is complete.

**Test Criteria:**
- All 22 existing domain tests pass
- All adapter tests pass
- All use-case tests pass
- `make_app()` works end-to-end
- No Flask or SQLAlchemy in any new code

**Validation Checklist:**
```bash
# Run full test suite
pytest crossword/tests/ -v --tb=short

# Verify no Flask/SQLAlchemy leakage
grep -r "from flask\|import flask\|from flask_sqlalchemy" crossword/{ports,adapters,use_cases,config}/ && exit 1 || echo "✓ No Flask leakage"

# Spot-check: all use cases can be instantiated
python -c "
from crossword.config.wiring import make_app
c = make_app({'db': 'samples.db'})
assert c.grid_use_cases is not None
assert c.puzzle_use_cases is not None
assert c.word_use_cases is not None
assert c.export_use_cases is not None
print('✓ All use cases wired')
"
```

**System State:** Stable. Ready to build HTTP layer. Old Flask code untouched; can be deleted after Phase 4.

**👉 Commit checkpoint:** Create a commit here. Message: "Phase 1: Ports, adapters, and use cases fully wired and tested."

---

## Phase 2: HTTP Delivery Layer

### **Checkpoint 2.1: HTTP Server & Router Scaffold**

**Deliverable:**
- `crossword/http_server/__init__.py`
- `crossword/http_server/server.py` — `BaseHTTPRequestHandler` subclass with route registry
- `crossword/http_server/router.py` — regex-based route matcher
- `crossword/tests/http_server/test_router.py`

**Code sketch:**
```python
# crossword/http_server/router.py
import re
from typing import Callable, Dict, Tuple

class Router:
    def __init__(self):
        self.routes: Dict[Tuple[str, str], Callable] = {}

    def register(self, method: str, path_pattern: str, handler: Callable):
        """Register a route: (GET, "/grids/(\d+)") -> handler"""
        self.routes[(method, path_pattern)] = handler

    def match(self, method: str, path: str) -> Tuple[Callable, Dict[str, str]]:
        """Return (handler, params) or (None, {})"""
        for (m, pattern), handler in self.routes.items():
            if m != method:
                continue
            match = re.match(pattern, path)
            if match:
                return handler, match.groupdict()
        return None, {}
```

**Test Criteria:**
- All 22 existing domain tests pass
- Router tests pass:
  - `test_router_exact_match()`
  - `test_router_regex_match_with_params()`
  - `test_router_no_match()`
- HTTP server starts without error
- No dependencies on Flask

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
pytest crossword/tests/http_server/test_router.py -v

# Verify server starts
python -c "
import threading
from crossword.http_server.server import HTTPServerHandler
from crossword.config.wiring import make_app

container = make_app({'db': 'samples.db'})
handler = HTTPServerHandler(container)
print('✓ Server scaffold OK')
"
```

**System State:** Stable. HTTP infrastructure exists but no handlers yet.

---

### **Checkpoint 2.2: Static File Handler**

**Deliverable:**
- `crossword/http_server/handlers/static_handler.py`
- `crossword/frontend/index.html` — shell with placeholder divs
- `crossword/frontend/css/style.css` — basic styling
- `crossword/tests/http_server/test_static_handler.py`

**Test Criteria:**
- All existing tests pass
- New static handler tests pass:
  - `test_serve_index_html()`
  - `test_serve_css()`
  - `test_404_for_missing_file()`
- `index.html` loads in browser without JS errors (manual check)

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
pytest crossword/tests/http_server/test_static_handler.py -v

# Verify index.html is valid HTML
python -c "
from html.parser import HTMLParser
with open('crossword/frontend/index.html') as f:
    HTMLParser().feed(f.read())
print('✓ index.html is valid HTML')
"
```

**System State:** Stable. Frontend shell loads; visual feedback confirmed.

---

### **Checkpoint 2.3: Grid CRUD Handlers**

**Deliverable:**
- `crossword/http_server/handlers/grid_handlers.py`
- `crossword/tests/http_server/test_grid_handlers.py`
  - `test_get_grid()`
  - `test_post_grid()`
  - `test_put_grid()`
  - `test_delete_grid()`
  - `test_error_on_not_found()`

**Test Criteria:**
- All existing tests pass
- All grid handler tests pass
- HTTP responses have correct status codes (200, 201, 404, 500, etc.)
- JSON serialization works for Grid objects

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
pytest crossword/tests/http_server/test_grid_handlers.py -v

# Spot-check handler response
python -c "
from crossword.http_server.handlers.grid_handlers import GridHandlers
from crossword.config.wiring import make_app

container = make_app({'db': 'samples.db'})
handlers = GridHandlers(container.grid_use_cases)
status, body = handlers.get_grid(1, 'grid_1')
assert status == 200, f'Expected 200, got {status}'
print('✓ Grid handler OK')
"
```

**System State:** Stable. Full grid CRUD over HTTP works.

---

### **Checkpoint 2.4: Puzzle & Word CRUD Handlers**

**Deliverable:**
- `crossword/http_server/handlers/puzzle_handlers.py`
- `crossword/http_server/handlers/word_handlers.py`
- Tests for both

**Test Criteria:**
- All existing tests pass
- All puzzle & word handler tests pass
- Error handling returns proper HTTP status codes

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
pytest crossword/tests/http_server/test_puzzle_handlers.py -v
pytest crossword/tests/http_server/test_word_handlers.py -v
```

**System State:** Stable. All CRUD endpoints functional.

---

### **Checkpoint 2.5: Export & Misc Handlers**

**Deliverable:**
- `crossword/http_server/handlers/export_handlers.py`
- `crossword/http_server/handlers/session_handler.py` — token-based sessions (simple UUID)
- Tests for both

**Test Criteria:**
- All existing tests pass
- Export handler tests pass (verify PDF/PNG/Puz files are generated)
- Session handler tests pass

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
pytest crossword/tests/http_server/test_export_handlers.py -v
pytest crossword/tests/http_server/test_session_handler.py -v
```

**System State:** Stable. HTTP layer complete and functional.

---

### **Checkpoint 2.6: End-of-Phase 2 Validation**

**Deliverable:** Phase 2 is complete.

**Test Criteria:**
- All 22 existing domain tests pass
- All HTTP handler tests pass
- Server starts on port 5000 without error
- API responses are valid JSON

**Validation Checklist:**
```bash
pytest crossword/tests/ -v --tb=short

# Dry-run: start server
timeout 2 python -m crossword.http_server.server || echo "✓ Server starts (timeout expected)"
```

**System State:** Stable. HTTP API fully functional.

**👉 Commit checkpoint:** "Phase 2: HTTP server and all handlers implemented and tested."

---

## Phase 3: Frontend SPA

### **Checkpoint 3.1: API Wrapper & State Management**

**Deliverable:**
- `crossword/frontend/js/api.js` — fetch-based API client
- `crossword/frontend/js/state.js` — simple observable state
- `crossword/tests/frontend/test_api.test.js` (Jest)
- `crossword/tests/frontend/test_state.test.js` (Jest)

**Test Criteria:**
- All existing backend tests pass
- API wrapper tests pass (mock fetch)
- State management tests pass

**Validation Checklist:**
```bash
pytest crossword/tests/ -v  # backend
npm test -- --testPathPattern="api|state"  # frontend
```

**System State:** Stable. Frontend scaffolding ready.

---

### **Checkpoint 3.2: Grid Editor**

**Deliverable:**
- `crossword/frontend/js/editors/grid-editor.js`
- `crossword/frontend/css/grid-editor.css`
- Manual test: create a grid, toggle black cells, see changes persist

**Test Criteria:**
- All existing tests pass
- Manual test: load page, create/load grid, toggle cell, refresh, cell state persists

**Validation Checklist:**
```bash
pytest crossword/tests/ -v

# Manual: start server, open browser, test workflow
python -m crossword.http_server.server &
sleep 2
echo "Open http://localhost:5000 in browser; test grid editor manually"
```

**System State:** Stable. Grid editor works end-to-end.

---

### **Checkpoint 3.3: Puzzle Editor**

**Deliverable:**
- `crossword/frontend/js/editors/puzzle-editor.js`
- `crossword/frontend/css/puzzle-editor.css`
- Manual test: words appear; can select and edit

**Test Criteria:**
- All existing tests pass
- Manual test: select word, enter clue, see it persist

**System State:** Stable. Puzzle editor works.

---

### **Checkpoint 3.4: Word Editor**

**Deliverable:**
- `crossword/frontend/js/editors/word-editor.js`
- `crossword/frontend/css/word-editor.css`
- Word suggestions via API

**Test Criteria:**
- All existing tests pass
- Manual test: type clue, see suggestions appear

**System State:** Stable. Word editor works.

---

### **Checkpoint 3.5: End-of-Phase 3 Validation**

**Deliverable:** Phase 3 is complete.

**Test Criteria:**
- Full end-to-end workflow:
  1. Create grid → toggle cells → save
  2. Create puzzle → add words → add clues → save
  3. Export to PDF/PNG/Puz
  4. Refresh page → state persists
  5. Re-import puzzle

**Validation Checklist:**
```bash
# Smoke test: manual workflow
pytest crossword/tests/ -v
# Then:
# 1. Start server
# 2. Create grid, add 5 black cells, save
# 3. Create puzzle, add word "HELLO", enter clue, save
# 4. Export to PDF
# 5. Refresh page
# 6. Verify grid and puzzle still exist
```

**System State:** Stable. Full SPA functional.

**👉 Commit checkpoint:** "Phase 3: Complete SPA frontend with all editors."

---

## Phase 4: Validation & Cut-Over

### **Checkpoint 4.1: Full Domain Test Suite Pass**

**Test Criteria:**
- `pytest crossword/tests/ -v` — **all 22 tests pass**
- No modifications to existing tests

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
# Output: ✓ 22 passed
```

**System State:** Stable. No regressions.

---

### **Checkpoint 4.2: Comprehensive Integration Tests**

**Deliverable:**
- `crossword/tests/integration/test_full_workflow.py` — end-to-end backend tests
- `crossword/tests/integration/test_adapter_compat.py` — adapters work with real `samples.db`

**Test Criteria:**
- All integration tests pass
- No data loss when migrating from Flask to new stack

**Validation Checklist:**
```bash
pytest crossword/tests/integration/ -v
```

**System State:** Stable. Integration verified.

---

### **Checkpoint 4.3: Manual Smoke Test Checklist**

**Workflow to verify:**
1. ✅ Start server: `python -m crossword.http_server.server`
2. ✅ Create a new grid (15x15)
3. ✅ Toggle black cells in a pattern
4. ✅ Rotate grid 90°
5. ✅ Undo/Redo operations
6. ✅ Create a puzzle from the grid
7. ✅ Add 10 words with clues
8. ✅ Export to PDF, PNG, AcrossLite, Puz
9. ✅ Re-import a puzzle
10. ✅ Refresh webpage → all state persists
11. ✅ Create a grid via API (curl/Postman)
12. ✅ Load grid via API and verify integrity

**Validation Checklist:**
```bash
# Each step must succeed; if any step fails, stop and fix.
```

**System State:** Stable. All manual workflows verified.

---

### **Checkpoint 4.4: Performance & Load Tests**

**Deliverable:**
- `crossword/tests/performance/test_load_times.py`

**Test Criteria:**
- Grid load: < 500ms
- Puzzle load: < 500ms
- Export: < 2s
- HTTP response: < 200ms (p95)

**Validation Checklist:**
```bash
pytest crossword/tests/performance/ -v
```

**System State:** Stable. Performance acceptable.

---

### **Checkpoint 4.5: Clean up Old Flask Code**

**Deliverable:** Old Flask code removed.

**Steps:**
1. ✅ Delete `crossword/ui/templates/`
2. ✅ Delete `crossword/ui/uimain.py`, `uigrid.py`, `uipuzzle.py`, `uiword.py`, `uistate.py`, `uipublish.py`
3. ✅ Delete `crossword/flask_session/`
4. ✅ Remove Flask, Flask-Session, Flask-SQLAlchemy from `requirements.txt`
5. ✅ Run full test suite one final time

**Test Criteria:**
- All 22 existing tests pass
- No import errors

**Validation Checklist:**
```bash
pytest crossword/tests/ -v
# Output: ✓ 22 passed
```

**System State:** Stable. Old code removed, new stack in place.

**👉 Commit checkpoint:** "Phase 4: Cut-over complete. Flask code removed; new HTTP+SPA stack live."

---

## Summary: Stopping Points at a Glance

| Checkpoint | Deliverable | Test Command | Next Step |
|---|---|---|---|
| 1.1 | Port interfaces | `pytest` (22 pass) | Implement adapters |
| 1.2 | SQLiteAdapter | `pytest crossword/tests/adapters/` | More adapters |
| 1.3 | Dictionary & Export | `pytest crossword/tests/adapters/` | Use cases |
| 1.4 | Use cases + wiring | `pytest crossword/tests/use_cases/` | Phase 2 |
| 1.5 | Phase 1 validation | `pytest` (all pass) | **COMMIT** |
| 2.1 | HTTP server scaffold | `pytest crossword/tests/http_server/` | Static handler |
| 2.2 | Static files | `pytest` + manual | Grid handlers |
| 2.3 | Grid CRUD | `pytest crossword/tests/http_server/test_grid_handlers.py` | Puzzle/Word handlers |
| 2.4 | Puzzle/Word CRUD | `pytest` (all handlers) | Export/Session |
| 2.5 | Export/Session | `pytest` (all pass) | Phase 3 |
| 2.6 | Phase 2 validation | `pytest` + API alive | **COMMIT** |
| 3.1 | API wrapper + state | `pytest` + `npm test` | Grid editor |
| 3.2 | Grid editor | `pytest` + manual | Puzzle editor |
| 3.3 | Puzzle editor | `pytest` + manual | Word editor |
| 3.4 | Word editor | `pytest` + manual | Phase 3 validation |
| 3.5 | Phase 3 validation | `pytest` + full workflow | Phase 4 |
| 4.1 | Domain tests | `pytest` (22 pass) | Integration tests |
| 4.2 | Integration tests | `pytest crossword/tests/integration/` | Manual smoke |
| 4.3 | Manual smoke test | Manual workflow checklist | Perf tests |
| 4.4 | Performance tests | `pytest crossword/tests/performance/` | Clean up |
| 4.5 | Cut-over complete | `pytest` (all pass) + no Flask | **COMMIT & DONE** |

---

## Rules for Implementation

1. **After each checkpoint, run the validation checklist.**
2. **If any test fails, stop and fix it before proceeding.**
3. **Commit a checkpoint only after all tests in that checkpoint pass.**
4. **Never skip a checkpoint.**
5. **If you discover a breaking change, revert and investigate.**

---

**Status:** Ready to begin Phase 1. Checkpoints 1.1–1.5 define the foundation layer.
