# Puzzle State & Dashboard — data model and workflow plan

## Goal

Give every puzzle an explicit **lifecycle state** and keep a **history** of how it
moved through that lifecycle. Some transitions happen automatically when the
puzzle is saved (the system inspects the puzzle and advances it); the rest are
driven by the user from new front-end controls (a "dashboard").

The lifecycle:

| State | Meaning | How it's set |
|---|---|---|
| `draft` | New puzzle, default | Auto (on create) |
| `filled` | All word cells are completed | Auto (on save) |
| `finished` | All clues are also completed | Auto (on save) |
| `submitted` | Submitted to a publisher | User |
| `published` | Published | User |
| `archived` | Saved old puzzle | User |

State is recorded in a **new `puzzle_state` table** with one row per state
change, so the full history is preserved.

> **Resolved decisions** (see §11 for the full list):
> `submitted`/`published`/`archived` are **read-only** (editing is
> blocked until the user reopens the puzzle → `draft`); **rename** is refactored
> to preserve the puzzle `id` and its history; **publisher** is a **free-form
> text field** and is **required** when moving to `submitted`, as are the
> relevant dates.

---

## Background — how puzzles are stored and saved today

### Storage

Puzzles live in a single SQLite table created/upgraded inline by
[sqlite_persistence_adapter.py:53-88](../../crossword/adapters/sqlite_persistence_adapter.py#L53-L88):

```sql
CREATE TABLE IF NOT EXISTS puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT NOT NULL,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle'
                        CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr         TEXT NOT NULL
);
CREATE UNIQUE INDEX idx_puzzles_userid_puzzlename ON puzzles(userid, puzzlename);
```

- The integer **`id`** is the natural foreign-key target for `puzzle_state`.
- A puzzle is addressed throughout the use cases by `(user_id, puzzlename)`; the
  adapter resolves that to `id` internally
  ([save_puzzle:110-143](../../crossword/adapters/sqlite_persistence_adapter.py#L110-L143)).
- There is **no migration framework** — schema evolution is done inline in
  `_ensure_schema_compatibility()`, using `CREATE TABLE IF NOT EXISTS` and
  `ALTER TABLE` guarded by `_column_exists()`. The new table follows the same
  pattern.

### Working-copy / save pattern

Editing uses a working copy. `open_puzzle_for_editing()` clones the puzzle to a
`__wc__<name>__<uuid8>` row
([puzzle_use_cases.py:168-193](../../crossword/use_cases/puzzle_use_cases.py#L168-L193));
every edit auto-persists to that working-copy row. **Save** and **Save As** both
collapse the working copy back onto a real name via `copy_puzzle()`:

- **Save** → `do_puzzle_save()` posts `…/<wc>/copy` with `new_name = <originalname>`
  ([puzzle-editor.js:1054-1067](../../frontend/static/js/puzzle-editor.js#L1054-L1067)).
- **Save As** → `do_puzzle_save_as()` → `_savePuzzleAsName()` posts the same with a
  new name ([puzzle-editor.js:1100-1130](../../frontend/static/js/puzzle-editor.js#L1100-L1130)).
- Backend: `handle_copy_puzzle` → `copy_puzzle()`
  ([puzzle_use_cases.py:124-149](../../crossword/use_cases/puzzle_use_cases.py#L124-L149)).
- **New** puzzles → `create_puzzle()`
  ([puzzle_use_cases.py:57-77](../../crossword/use_cases/puzzle_use_cases.py#L57-L77)).

So the **two hook points for auto-detection** are `create_puzzle()` (→ `draft`)
and `copy_puzzle()` (→ recompute on every Save / Save As).

> Working copies (`__wc__…`, `__new__…`) are transient and must **never** get
> state-history rows. State is only recorded against real, user-visible puzzle
> names — i.e. the *destination* of `copy_puzzle()` / `create_puzzle()`.

### Completeness signals available today

There is no puzzle-level "is it filled / finished" method yet, but the pieces
exist:

- `Word.is_complete()` — true when the word has no blank cells
  ([word.py:114-120](../../crossword/domain/word.py#L114-L120)).
- `Word.get_clue()` — the clue text (or `None`)
  ([word.py:85-87](../../crossword/domain/word.py#L85-L87)).
- `Puzzle.across_words` / `Puzzle.down_words` — the word dictionaries
  iterated by `validate_duplicate_words()`
  ([puzzle.py:444-477](../../crossword/domain/puzzle.py#L444-L477)).

---

## 1. Data model — the `puzzle_state` table

Add to `_ensure_schema_compatibility()`
([sqlite_persistence_adapter.py:53-88](../../crossword/adapters/sqlite_persistence_adapter.py#L53-L88))
so it is auto-created on first connect, exactly like `puzzles`:

```sql
CREATE TABLE IF NOT EXISTS puzzle_state (
    ts              TEXT    NOT NULL,         -- ISO timestamp of the change
    puzzle_id       INTEGER NOT NULL,         -- FK -> puzzles(id)
    state           TEXT    NOT NULL          -- draft|filled|finished|
                                              --   submitted|published|archived
                        CHECK (state IN (
                            'draft','filled','finished',
                            'submitted','published','archived')),
    -- state-specific columns, NULL when not applicable
    publisher       TEXT,                     -- NYT, LAT, WSJ, DTH, ...
    date_submitted  TEXT,                     -- ISO date, only for 'submitted'
    date_published  TEXT,                     -- ISO date, only for 'published'
    PRIMARY KEY (ts, puzzle_id),
    FOREIGN KEY (puzzle_id) REFERENCES puzzles(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_puzzle_state_puzzle
    ON puzzle_state(puzzle_id, ts DESC);
```

Notes:

- **PK = `(ts, puzzle_id)`** as specified. The supporting index
  `(puzzle_id, ts DESC)` makes "latest state for this puzzle" a single fast
  lookup.
- **`ON DELETE CASCADE`** keeps history from leaking when a puzzle is deleted.
  SQLite enforces FKs only when `PRAGMA foreign_keys = ON` — set this pragma in
  the adapter constructor (it is currently off by default). Even without the
  pragma, the delete path should clean up explicitly.
- The state-specific columns are deliberately nullable rather than a separate
  table — the set is small and fixed.

---

## 2. State semantics & transition policy

### State ladder for auto-detection

Auto-detection works on a three-rung *completion ladder*:

```
draft (0)  <  filled (1)  <  finished (2)
```

- `filled`   ⇔ the puzzle has ≥1 word and **every** across/down word is
  `is_complete()`.
- `finished` ⇔ `filled` **and** every word has a non-empty clue.
- otherwise → `draft`.

`submitted`, `published`, `archived` are **user-owned** states set only from the
dashboard.

### What happens on Save / Save As / create

Let `current` = the puzzle's latest recorded state (or `None`), and
`computed` = the ladder result above.

1. **Create** (`create_puzzle`): record `draft` (first-ever row).
2. **Save / Save As** (`copy_puzzle`):
   - `current is None` (Save As to a brand-new name) → record `computed`.
   - `current ∈ {submitted, published, archived}` → **no auto change**. In
     practice this can't be reached, because those states are read-only and a
     working copy can't have been opened (§ editing lock); the guard stays as a
     defensive no-op.
   - `current ∈ {draft, filled, finished}` → if `computed != current`, record
     `computed`. This allows forward moves (draft→filled→finished) **and**
     backward moves (e.g. finished→filled when a cell is later cleared), which
     reflects reality.
3. **Record only on change** — never write a `puzzle_state` row whose `state`
   (and state-specific columns) equal the latest row. This keeps the history
   meaningful and avoids a row on every keystroke-driven save.

### Editing lock for read-only states

`submitted`, `published`, and `archived` are **read-only**. Editing is blocked at
the single choke point where editing begins — `open_puzzle_for_editing()`:

- If the puzzle's current state ∈ {`submitted`, `published`, `archived`}, the use
  case **refuses to open a working copy** and signals the caller (e.g. raises a
  domain error / returns a `read_only` flag). The HTTP handler maps this to a
  `409`/`403` with a clear message.
- To edit such a puzzle the user must first **Reopen** it from the dashboard,
  which is just `set_puzzle_state(… , 'draft')`. After reopening, the normal
  open/edit/save flow applies and auto-detection takes over again.

Because every edit path requires `open_puzzle_for_editing()` first, locking at
open is sufficient — no per-edit guards are needed.

### User-driven transitions

Set explicitly via the dashboard (§8): `submitted` (requires `publisher` +
`date_submitted`), `published` (requires `date_published`), `archived`, and
**Reopen** (→ `draft`). `set_puzzle_state()` validates the target state, enforces
the required fields, and records the row. `publisher` is a free-form text field
(no value validation beyond being non-empty when required).

---

## 3. Domain changes (pure, no persistence)

### New module `crossword/domain/puzzle_state.py`

```python
# crossword.domain.puzzle_state

DRAFT      = "draft"
FILLED     = "filled"
FINISHED   = "finished"
SUBMITTED  = "submitted"
PUBLISHED  = "published"
ARCHIVED   = "archived"

ALL_STATES = [DRAFT, FILLED, FINISHED, SUBMITTED, PUBLISHED, ARCHIVED]

# states the auto-detector may assign, lowest → highest
COMPLETION_LADDER = [DRAFT, FILLED, FINISHED]

# read-only, user-owned states the auto-detector must not overwrite and that
# block editing until the user reopens the puzzle
READ_ONLY = {SUBMITTED, PUBLISHED, ARCHIVED}


def detect_completion_state(puzzle) -> str:
    """Pure ladder result: DRAFT | FILLED | FINISHED."""
    if not puzzle.is_filled():
        return DRAFT
    if puzzle.all_clues_complete():
        return FINISHED
    return FILLED
```

### New methods on `Puzzle` ([puzzle.py](../../crossword/domain/puzzle.py))

```python
def is_filled(self) -> bool:
    """True if the puzzle has at least one word and every word is complete."""
    words = list(self.across_words.values()) + list(self.down_words.values())
    return bool(words) and all(w.is_complete() for w in words)

def all_clues_complete(self) -> bool:
    """True if every word has a non-empty clue."""
    words = list(self.across_words.values()) + list(self.down_words.values())
    return bool(words) and all((w.get_clue() or "").strip() for w in words)
```

These belong on `Puzzle` next to `validate()`/`get_statistics()` and reuse the
existing `Word.is_complete()` / `Word.get_clue()` primitives.

---

## 4. Port changes — `PersistencePort`

Add state operations to
[persistence_port.py](../../crossword/ports/persistence_port.py), plus a real
**rename** that preserves `id` (replacing the copy+delete pattern). All stay
keyed by `(user_id, name)` so use cases never deal with raw row ids.

```python
def record_puzzle_state(self, user_id: int, name: str, state: str, *,
                        publisher: str | None = None,
                        date_submitted: str | None = None,
                        date_published: str | None = None,
                        when: str | None = None) -> None:
    """Append a state-history row for the puzzle, only if it differs from the
    current latest row. `when` defaults to now (ISO)."""

def get_current_puzzle_state(self, user_id: int, name: str) -> dict | None:
    """Latest state row as a dict, or None if no history."""

def get_puzzle_state_history(self, user_id: int, name: str) -> list[dict]:
    """All state rows, newest first."""

def rename_puzzle(self, user_id: int, old_name: str, new_name: str) -> None:
    """Rename in place: UPDATE puzzles SET puzzlename = ?. Preserves id, so the
    puzzle_state history follows automatically. Raises if new_name is taken."""
```

---

## 5. Adapter changes — `SQLitePersistenceAdapter`

- **Schema:** add the `puzzle_state` CREATE TABLE + index to
  `_ensure_schema_compatibility()`; enable `PRAGMA foreign_keys = ON` in
  `__init__`.
- **`record_puzzle_state`:** resolve `(userid, name) → id`; read the latest row;
  if `state` + state-specific columns are unchanged, return without inserting;
  otherwise `INSERT` with `ts = when or datetime.now().isoformat()`. Guard
  against `ts` collisions (same-millisecond saves) — if `INSERT` hits the PK,
  retry once with a nudged timestamp.
- **`get_current_puzzle_state`:** `SELECT … ORDER BY ts DESC LIMIT 1`.
- **`get_puzzle_state_history`:** `SELECT … ORDER BY ts DESC`.
- **`rename_puzzle`:** `UPDATE puzzles SET puzzlename = ?, modified = ? WHERE
  userid = ? AND puzzlename = ?`. The unique index on `(userid, puzzlename)`
  rejects a clashing name — translate that into a `PersistenceError`. Because
  `id` is unchanged, `puzzle_state` rows need no touching.
- **`delete_puzzle`:** also `DELETE FROM puzzle_state WHERE puzzle_id = ?`
  (belt-and-suspenders alongside the cascade)
  ([delete_puzzle:170-186](../../crossword/adapters/sqlite_persistence_adapter.py#L170-L186)).

---

## 6. Use-case changes — `PuzzleUseCases`

Add a private helper and call it from the two hook points:

```python
def _auto_record_state_on_save(self, user_id, name, puzzle):
    from crossword.domain import puzzle_state as ps
    current = self.persistence.get_current_puzzle_state(user_id, name)
    computed = ps.detect_completion_state(puzzle)
    if current is None:
        self.persistence.record_puzzle_state(user_id, name, computed)
        return
    if current["state"] in ps.READ_ONLY:
        return                       # defensive: read-only puzzles can't be open
    if computed != current["state"]:
        self.persistence.record_puzzle_state(user_id, name, computed)
```

- **`create_puzzle`** ([57-77](../../crossword/use_cases/puzzle_use_cases.py#L57-L77)):
  after `save_puzzle`, `record_puzzle_state(user_id, name, DRAFT)`.
- **`copy_puzzle`** ([124-149](../../crossword/use_cases/puzzle_use_cases.py#L124-L149)):
  after `save_puzzle`, call `_auto_record_state_on_save(user_id, new_name, puzzle)`.
  This covers both Save (dest = original name) and Save As (dest = new name).
- **`open_puzzle_for_editing`** ([168-193](../../crossword/use_cases/puzzle_use_cases.py#L168-L193)):
  before creating the working copy, read the current state; if it is in
  `READ_ONLY`, raise a `PuzzleReadOnlyError` (new, caught by the handler).
- **`rename_puzzle`** ([151-166](../../crossword/use_cases/puzzle_use_cases.py#L151-L166)):
  replace the copy+delete body with a single call to the new
  `persistence.rename_puzzle(...)`. History is preserved automatically (same
  `id`). Drop the `copy_puzzle` indirection here.

New public method for user-driven transitions:

```python
def set_puzzle_state(self, user_id, name, state, *,
                     publisher=None, date_submitted=None,
                     date_published=None) -> dict:
    """Validate `state` ∈ ALL_STATES; enforce required fields per target state
    (publisher + date_submitted for 'submitted'; date_published for 'published');
    record the row and return the new current-state dict.

    `publisher` is free-form text — required to be non-empty when moving to
    'submitted', but otherwise unvalidated."""
```

---

## 7. HTTP endpoints

Add to [puzzle_handlers.py](../../crossword/http_server/puzzle_handlers.py)
(register in the same router table as the existing `…/copy`, `…/rename` routes):

| Method | Route | Handler | Purpose |
|---|---|---|---|
| `GET` | `/api/puzzles/<name>/state` | `handle_get_puzzle_state` | Current state + fields |
| `GET` | `/api/puzzles/<name>/state/history` | `handle_get_puzzle_state_history` | Full history |
| `PUT` | `/api/puzzles/<name>/state` | `handle_set_puzzle_state` | User transition (incl. Reopen → draft) |

- `PUT` body: `{ "state": "submitted", "publisher": "NYT", "date_submitted": "2026-06-06" }`
  (only the fields relevant to the target state). `publisher` is free-form text.
  Missing required fields → `400`.
- `handle_open_puzzle_for_editing`
  ([puzzle_handlers.py:226-253](../../crossword/http_server/puzzle_handlers.py#L226-L253))
  must catch `PuzzleReadOnlyError` and return a `409`/`403` so the front-end can
  prompt the user to Reopen.
- All handlers extract `user_id = current_user["id"]` like the rest of the file.

Document the new endpoints in [docs/dev/endpoints.md](endpoints.md) and the
Swagger spec used by `tools/dev/swagger.py`.

---

## 8. Front-end — the dashboard *(to be defined; sketch)*

The prompt scopes manual transitions to "new front-end features, to be defined."
A **Puzzle Dashboard** view is the natural home:

- A table of the user's puzzles: **name · current state · last modified ·
  publisher · submitted · published**. Source: `list_puzzles` + per-puzzle
  `GET …/state` (or a future batched endpoint).
- Per-row actions to set user-owned states: **Submit** (prompt for publisher
  as free-form text + submitted date), **Mark published** (prompt for
  date), **Archive**, and **Reopen** (→ draft). Each calls `PUT …/state`.
- A **history** drawer per puzzle (`GET …/state/history`) showing the timeline.
- Filter/group by state (e.g. hide `archived` by default).
- Puzzles in a read-only state (`submitted`/`published`/`archived`) show **Open**
  as disabled; the user must **Reopen** first. If they try to open one anyway,
  the `409`/`403` from the open endpoint drives a "Reopen to edit?" prompt.

`filled`/`finished` are shown but **read-only** in the UI — they are driven by
Save. Publisher is entered as free-form text.

This section is intentionally a sketch — finalize the layout before building.

---

## 9. One-off migration tool

`tools/dev/migrate_puzzle_state.py` (sibling of
[import_grid.py](../../tools/dev/import_grid.py) and
[clear_work_files.py](../../tools/user/clear_work_files.py)):

1. Resolve the dbfile the same way the app does (config / `DATABASE_URL`), or
   take `--dbfile`.
2. Open the DB through `SQLitePersistenceAdapter` so the `puzzle_state` table is
   created by `_ensure_schema_compatibility()`.
3. For every row in `puzzles` **excluding working copies** (`puzzlename` starting
   with `__wc__` or `__new__`, and skipping legacy `NULL` names — see
   [list_puzzles:199](../../crossword/adapters/sqlite_persistence_adapter.py#L199))
   that has **no** `puzzle_state` row: insert one `draft` row, using the puzzle's
   `created` timestamp as `ts` so the history reads sensibly.
4. Support `--dry-run` (report counts, change nothing) like `clear_work_files.py`.
5. Idempotent: re-running adds nothing for puzzles that already have history.

> Per spec, the default backfill state is **`draft`** for every existing puzzle,
> regardless of how complete it actually is. (If desired later, a `--detect`
> flag could instead backfill via `detect_completion_state`, but the spec asks
> for `draft`.)

---

## 10. Tests (pytest, under `crossword/tests/`)

- **Domain:** `is_filled` / `all_clues_complete` / `detect_completion_state`
  across empty, partial, fully-filled-no-clues, fully-finished puzzles.
- **Adapter:** table created; `record_puzzle_state` dedups on unchanged state;
  history ordering newest-first; PK-collision retry; `rename_puzzle` preserves
  `id` + history and rejects a clashing name; delete removes history.
- **Use case:** `create_puzzle` → one `draft` row; `copy_puzzle` advances
  draft→filled→finished and backward finished→filled; `open_puzzle_for_editing`
  raises on read-only states; `set_puzzle_state` enforces required fields
  (incl. non-empty free-form publisher on submit), and Reopen (→ draft) clears
  the lock.
- **HTTP:** the three new routes happy-path; bad-state and missing-required-field
  rejection; open of a read-only puzzle returns `409`/`403`.
- **Migration:** backfills only real puzzles, skips working copies, idempotent,
  honors `--dry-run`.

---

## 11. Resolved decisions

1. **Read-only terminal states.** `submitted`/`published`/`archived` block
   editing; `open_puzzle_for_editing` refuses and the user must **Reopen**
   (→ draft) first.
2. **Rename preserves history.** Rename is refactored to a true
   `UPDATE puzzles SET puzzlename = ?`, keeping the puzzle `id` and its
   `puzzle_state` history.
3. **Publisher + required fields.** `publisher` is a free-form text field;
   moving to `submitted` requires a non-empty `publisher` + `date_submitted`, and
   moving to `published` requires `date_published`.

---

## 12. Suggested implementation order

1. Domain: `puzzle_state.py` + `Puzzle.is_filled` / `all_clues_complete` (+ tests).
2. Adapter: `puzzle_state` table, FK pragma, record/get/history, in-place
   `rename_puzzle`, delete cleanup (+ tests).
3. Port: declare the state methods and the new `rename_puzzle`.
4. Use cases: auto-record on `create_puzzle`/`copy_puzzle`, read-only lock in
   `open_puzzle_for_editing`, refactored `rename_puzzle`, `set_puzzle_state`
   with free-form publisher field (+ tests).
5. Migration tool + dry-run (+ tests); run it against the dev DB.
6. HTTP endpoints + read-only `409`/`403` on open + endpoints.md / Swagger
   (+ tests).
7. Front-end dashboard — design first, then build.
