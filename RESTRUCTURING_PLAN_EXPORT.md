# Crossword Project Restructuring — Chat Export

**Date:** 2026-03-19
**Context:** Review of the restructuring plan document and ordered implementation suggestions

---

## Executive Summary

This document captures the chat discussion about the Crossword Application restructuring plan. The plan aims to:

- Remove Flask and SQLAlchemy dependencies
- Move to a Hexagonal (Ports & Adapters) architecture
- Replace server-side sessions with a stateless HTTP server
- Build a plain-JavaScript SPA frontend

The restructuring is **not yet started** (plan only). This export includes the full plan context and detailed, ordered implementation suggestions.

---

## Suggested Implementation Order

### **Phase 1: Foundation (Ports & Adapters Core)**

#### 1.1 Define Port Interfaces First
Create `crossword/ports/` with the core contracts:

- **`persistence.py`** — CRUD for grids, puzzles, users (most critical; blocks adapters & use cases)
- **`word_list.py`** — word matching interface
- **`export.py`** — export format contract
- **`file_storage.py`** — if needed, defer unless you plan file import

**Why first:** Ports are dependency anchors. Once defined, adapters and use cases can develop in parallel.

#### 1.2 Implement Adapters (2 adapters minimum)
- **`SQLiteAdapter`** (from `sqlite3` directly, no ORM) — test against existing `samples.db` schema
- **`DictionaryAdapter`** — load word list into memory; verify current logic is preserved

**Checkpoint:** Write a small unit test that loads a grid from `samples.db` via the new adapter. This validates the schema hasn't drifted.

#### 1.3 Create Use-Case Classes
- **`grid_use_cases.py`** → GridUseCases
- **`puzzle_use_cases.py`** → PuzzleUseCases
- **`word_use_cases.py`** → WordUseCases
- **`export_use_cases.py`** → ExportUseCases (last; depends on export port)

Use **constructor injection** — each takes its ports as arguments. No globals, no singletons.

#### 1.4 Wire Dependencies (`config/wiring.py`)
One function, `make_app(config)`, that assembles adapters and injects them into use cases. Test this by calling `make_app()`, then verifying you can call a use-case method end-to-end.

**Checkpoint:** Run existing domain tests — should all pass (domain is untouched).

---

### **Phase 2: HTTP Delivery Layer**

#### 2.1 Build the HTTP Server (`http_server/server.py`)
- Minimal `BaseHTTPRequestHandler` subclass
- A regex-based router: `(method, path_pattern) → handler_function`
- Session token parsing (simple UUID in a cookie for now)

**Key point:** The handler receives parsed request data (params/JSON body) and routes to a handler function. Keep it thin.

#### 2.2 Implement Handlers by Feature Area
Start **smallest to largest**:

1. **`static_handlers.py`** — serve `index.html` + static assets (CSS, JS). Get the frontend shell loading first.
2. **`grid_handlers.py`** — CRUD grid operations via REST (GET/POST/PUT/DELETE). Re-raise errors with proper HTTP status codes.
3. **`puzzle_handlers.py`** — similar to grids
4. **`word_handlers.py`** — word-level operations + suggestions
5. **`export_handlers.py`** — export routes; wire to `ExportUseCases`

**Checkpoint:** For each handler, write a test that sends a raw HTTP request and validates the JSON response. Use `urllib.request` or write a minimal test client.

---

### **Phase 3: Frontend SPA**

#### 3.1 Create the Shell (`frontend/index.html`)
- Single entry point with placeholder divs: `#grid-editor`, `#puzzle-editor`, `#word-editor`, `#toolbar`, `#menu`
- Link CSS and JS files (in proper order)

#### 3.2 Build the API Wrapper (`frontend/js/api.js`)
- `fetch()` calls for each endpoint (GET grids, POST grid, PUT grid, etc.)
- Error handling: log server errors; promise-based

#### 3.3 Implement Client State (`frontend/js/state.js`)
- Simple observable: `get()`, `set(patch)`, `subscribe(fn)`
- Tracks: `{ mode, grid, puzzle, ... }`

#### 3.4 Build Editors Incrementally
**Order matters — build in dependency order:**

1. **`grid-editor.js`** — render grid SVG; attach click handlers; call API to toggle black cells
2. **`puzzle-editor.js`** — render puzzle + word list; click to select a word; attach cell input listeners
3. **`word-editor.js`** — text input + clue input for a single word; word suggestions via API
4. **`dialogs.js`** — reusable modals (confirm delete, create new grid, etc.)

**Checkpoint:** After each editor, manually test in the browser. Create a grid → toggle a cell → refresh page (state is brief; this is OK for now).

---

### **Phase 4: Validation & Cut-Over**

#### 4.1 Existing Tests Must Pass
```bash
pytest crossword/tests/
```

All 22 tests should pass without modification. If they don't, the domain/adapter layer has a bug.

#### 4.2 Add Adapter Tests
Test `SQLiteAdapter` CRUD operations against an in-memory SQLite DB:

```python
# crossword/tests/adapters/test_sqlite_adapter.py
def test_save_and_load_grid():
    adapter = SQLiteAdapter(":memory:")
    adapter.init_schema()  # Create tables
    grid = Grid(15)
    adapter.save_grid(1, "test", grid)
    loaded = adapter.load_grid(1, "test")
    assert loaded.size == 15
```

#### 4.3 Smoke Test (manual checklist)
Work through the full workflow:

- Create grid → toggle black cells → rotate → undo/redo
- Create puzzle → fill words → enter clues → save
- Export to each format
- Re-import a puzzle

#### 4.4 Delete Old Flask Code
Once everything works:

- Delete `crossword/ui/templates/`
- Delete `crossword/ui/uimain.py`, `uigrid.py`, `uipuzzle.py`, `uiword.py`, `uistate.py`, `uipublish.py`
- Delete `crossword/flask_session/`
- Remove Flask, Flask-Session, Flask-SQLAlchemy from `requirements.txt`

---

## Priority Matrix

| Step | Priority | Reason |
|---|---|---|
| Define ports **first** | **P0** | Everything depends on them; changes ripple everywhere |
| Implement & test one adapter at a time | **P0** | Validates contract early; catches schema drift |
| Use-cases before handlers | **P1** | Ensures business logic is decoupled from HTTP |
| Static file serving (Phase 2.2.1) | **P1** | Gets the browser connected early; visual feedback |
| Feature order in Phase 3: grid → puzzle → word | **P1** | Grids are independent; puzzles depend on grids; words depend on puzzles |
| Integration tests during Phase 4 | **P1** | Validate the entire flow works (don't wait until the end) |

---

## Quick Start Checklist

### ✅ **Week 1 — Foundation (Days 1–2)**
- [ ] Create `crossword/ports/*.py` (4 files, ~150 lines total)
- [ ] Implement `SQLiteAdapter` & `DictionaryAdapter` (2 adapters, ~300 lines total)
- [ ] Create use-case classes (4 files, ~450 lines total)
- [ ] Wire dependencies; verify existing tests pass

### ✅ **Week 2 — HTTP (Days 3–4)**
- [ ] Write `http_server/server.py` with regex router (~150 lines)
- [ ] Implement handlers by feature (5 handler files, ~600 lines total)
- [ ] Add handler unit tests

### ✅ **Week 3 — Frontend (Days 5–6)**
- [ ] Create `index.html` shell + `api.js` + `state.js` (~200 lines total)
- [ ] Build editors incrementally; manual test after each

### ✅ **Week 4 — Test & Cut (Day 7)**
- [ ] Run full domain test suite
- [ ] Add adapter & integration tests
- [ ] Full end-to-end smoke test
- [ ] Delete old Flask code

---

## Reference: Detailed Plan Structure

For the complete restructuring plan, see `RESTRUCTURING_PLAN.md` in the project root. That document contains:

- Full motivation and architecture overview
- Complete directory structure and file listings
- REST API contract (all endpoints)
- Data models & DTOs
- Key design decisions with trade-off analysis
- Testing plan details
- Migration path strategy
- Risk assessment & mitigations
- Open questions for future phases

---

## Next Steps

1. **Start Phase 1 immediately** — Define ports first (P0 priority)
2. **Implement adapters in parallel** while fleshing out use cases
3. **Run domain tests early** to catch any integration issues
4. **Build HTTP handlers incrementally** — static serving first for early visual feedback
5. **Frontend development** should follow backend API stability

**Estimated timeline:** 4 weeks full-time, or 8 weeks part-time (~3–4 hours/week)

---

**Document exported:** 2026-03-19
