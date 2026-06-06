# Puzzle State & Dashboard — data model and workflow plan

## Goal

Give every puzzle an explicit **lifecycle state**. Some transitions happen
automatically when the puzzle is saved (the system inspects the puzzle and
advances it); the rest are driven by the user from new front-end controls (a
"dashboard"). Only the **current** state is kept — there is no separate history.

The lifecycle:

| State | Meaning | How it's set |
|---|---|---|
| `draft` | New puzzle, default | Auto (on create) |
| `filled` | All word cells are completed | Auto (on save) |
| `finished` | All clues are also completed | Auto (on save) |
| `submitted` | Submitted to a publisher | User |
| `published` | Published | User |
| `archived` | Saved old puzzle | User |

State is stored **directly on the `puzzles` table** as extra columns — the
current `state` plus its state-specific fields (`publisher`, `date_submitted`,
`date_published`). Each save overwrites the columns in place; no history rows are
kept.

> **Resolved decisions** (see §11 for the full list):
> any puzzle may be opened for editing regardless of state (there is no
> read-only lock); **rename** is refactored to preserve the puzzle `id`;
> **publisher** is a **free-form text field** and is **required** when moving to
> `submitted`, as are the relevant dates.

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

- The state columns are added to this same table (§1).
- A puzzle is addressed throughout the use cases by `(user_id, puzzlename)`; the
  adapter resolves that to `id` internally
  ([save_puzzle:110-143](../../crossword/adapters/sqlite_persistence_adapter.py#L110-L143)).
- There is **no migration framework** — schema evolution is done inline in
  `_ensure_schema_compatibility()`, using `CREATE TABLE IF NOT EXISTS` and
  `ALTER TABLE` guarded by `_column_exists()`. The state columns, however, are
  **not** added inline — they are part of the `CREATE TABLE` (§1), and existing
  databases are upgraded once by the migration tool (§9) rather than altered in
  place.

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

> Working copies (`__wc__…`, `__new__…`) are transient and carry whatever state
> they were cloned with. The meaningful state lives on real, user-visible puzzle
> names — i.e. the *destination* of `copy_puzzle()` / `create_puzzle()`, which is
> where the auto-detector writes.

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

## 1. Data model — state columns on `puzzles`

State lives directly on the `puzzles` table as four extra columns. The
`CREATE TABLE IF NOT EXISTS puzzles` in `_ensure_schema_compatibility()`
([sqlite_persistence_adapter.py:53-88](../../crossword/adapters/sqlite_persistence_adapter.py#L53-L88))
simply **carries the columns** — no `ALTER TABLE`, no `_column_exists()` probing.
The running app never mutates an existing schema; databases that predate these
columns are upgraded **once** by the migration tool (§9), which rebuilds into a
fresh file with this exact table:

```sql
CREATE TABLE IF NOT EXISTS puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT NOT NULL,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle'
                        CHECK (last_mode IN ('grid', 'puzzle')),
    state           TEXT NOT NULL DEFAULT 'draft'
                        CHECK (state IN (
                            'draft','filled','finished',
                            'submitted','published','archived')),
    jsonstr         TEXT NOT NULL,
    publisher       TEXT,                     -- NYT, LAT, WSJ, DTH, ...
    date_submitted  TEXT,                     -- ISO date, only for 'submitted'
    date_published  TEXT                      -- ISO date, only for 'published'
);
```

Notes:

- **`state` defaults to `draft`** and is constrained by the `CHECK` to the six
  valid states — both come from the `CREATE TABLE`, so they apply to every
  database the app creates or is pointed at after migration.
- The state-specific columns are deliberately nullable — they apply only to the
  user-owned states.
- Because state is a column on the puzzle row, it is read in the same `SELECT`
  that loads the puzzle and deleted with it — no extra table, no foreign keys,
  no cascade.

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

Let `current` = the puzzle's current `state` column (or `None` for a name that
doesn't exist yet), and `computed` = the ladder result above.

1. **Create** (`create_puzzle`): set `state = draft`.
2. **Save / Save As** (`copy_puzzle`): always set `computed`, regardless of the
   current state. This allows forward moves (draft→filled→finished) **and**
   backward moves (e.g. finished→filled when a cell is later cleared, or a saved
   `submitted` puzzle dropping back onto the completion ladder), which reflects
   reality.

Each save simply overwrites the `state` column with the computed value; there is
no history to keep meaningful, so no on-change guard is needed.

### No editing lock

Any puzzle may be opened for editing regardless of its state —
`open_puzzle_for_editing()` always creates a working copy. A subsequent Save
recomputes the state from the puzzle's contents (§ "What happens on Save"), so a
`submitted`/`published`/`archived` puzzle that is edited and saved is reclassified
by the completion ladder.

### User-driven transitions

Set explicitly via the dashboard (§8): `submitted` (requires `publisher` +
`date_submitted`), `published` (requires `date_published`), `archived`, and
**Reopen** (→ `draft`). `set_puzzle_state()` validates the target state, enforces
the required fields, and writes the columns. `publisher` is a free-form text
field (no value validation beyond being non-empty when required).

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
def set_puzzle_state(self, user_id: int, name: str, state: str, *,
                     publisher: str | None = None,
                     date_submitted: str | None = None,
                     date_published: str | None = None) -> None:
    """Overwrite the puzzle's state columns in place
    (UPDATE puzzles SET state = ?, publisher = ?, ...)."""

def get_puzzle_state(self, user_id: int, name: str) -> dict | None:
    """The puzzle's current state columns as a dict, or None if the puzzle
    doesn't exist."""

def rename_puzzle(self, user_id: int, old_name: str, new_name: str) -> None:
    """Rename in place: UPDATE puzzles SET puzzlename = ?. Preserves id and all
    its columns (state included). Raises if new_name is taken."""
```

---

## 5. Adapter changes — `SQLitePersistenceAdapter`

- **Schema:** the four state columns are part of the `CREATE TABLE IF NOT
  EXISTS puzzles` in `_ensure_schema_compatibility()` (§1) — no `ALTER TABLE`.
- **`set_puzzle_state`:** `UPDATE puzzles SET state = ?, publisher = ?,
  date_submitted = ?, date_published = ?, modified = ? WHERE userid = ? AND
  puzzlename = ?`.
- **`get_puzzle_state`:** `SELECT state, publisher, date_submitted,
  date_published FROM puzzles WHERE userid = ? AND puzzlename = ?` → dict, or
  `None` if the row is absent. (Loading the full puzzle already returns these
  columns too.)
- **`rename_puzzle`:** `UPDATE puzzles SET puzzlename = ?, modified = ? WHERE
  userid = ? AND puzzlename = ?`. The unique index on `(userid, puzzlename)`
  rejects a clashing name — translate that into a `PersistenceError`. Because
  the row (and its state columns) is unchanged otherwise, nothing else is
  touched.
- **`delete_puzzle`:** unchanged — the state columns live on the row that
  `delete_puzzle` already removes
  ([delete_puzzle:170-186](../../crossword/adapters/sqlite_persistence_adapter.py#L170-L186)).

---

## 6. Use-case changes — `PuzzleUseCases`

Add a private helper and call it from the two hook points:

```python
def _auto_set_state_on_save(self, user_id, name, puzzle):
    from crossword.domain import puzzle_state as ps
    computed = ps.detect_completion_state(puzzle)
    self.persistence.set_puzzle_state(user_id, name, computed)
```

- **`create_puzzle`** ([57-77](../../crossword/use_cases/puzzle_use_cases.py#L57-L77)):
  the row is created with `state = draft` (the column default), so no extra call
  is needed.
- **`copy_puzzle`** ([124-149](../../crossword/use_cases/puzzle_use_cases.py#L124-L149)):
  after `save_puzzle`, call `_auto_set_state_on_save(user_id, new_name, puzzle)`.
  This covers both Save (dest = original name) and Save As (dest = new name).
- **`open_puzzle_for_editing`** ([168-193](../../crossword/use_cases/puzzle_use_cases.py#L168-L193)):
  always creates the working copy — no state check.
- **`rename_puzzle`** ([151-166](../../crossword/use_cases/puzzle_use_cases.py#L151-L166)):
  replace the copy+delete body with a single call to the new
  `persistence.rename_puzzle(...)`. State is preserved automatically (same row).
  Drop the `copy_puzzle` indirection here.

New public method for user-driven transitions:

```python
def set_puzzle_state(self, user_id, name, state, *,
                     publisher=None, date_submitted=None,
                     date_published=None) -> dict:
    """Validate `state` ∈ ALL_STATES; enforce required fields per target state
    (publisher + date_submitted for 'submitted'; date_published for 'published');
    write the columns and return the new state dict.

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
| `PUT` | `/api/puzzles/<name>/state` | `handle_set_puzzle_state` | User transition (incl. Reopen → draft) |

- `PUT` body: `{ "state": "submitted", "publisher": "NYT", "date_submitted": "2026-06-06" }`
  (only the fields relevant to the target state). `publisher` is free-form text.
  Missing required fields → `400`.
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
- Filter/group by state (e.g. hide `archived` by default).
- Any puzzle can be opened for editing regardless of state. Editing a
  `submitted`/`published`/`archived` puzzle and saving it reclassifies it via the
  completion ladder, so the dashboard may warn before opening such a puzzle.

`filled`/`finished` are shown but not directly editable in the UI — they are
driven by Save. Publisher is entered as free-form text.

This section is intentionally a sketch — finalize the layout before building.

---

## 9. One-off migration tool

`tools/dev/migrate_puzzle_state.py` (sibling of
[import_grid.py](../../tools/dev/import_grid.py) and
[clear_work_files.py](../../tools/user/clear_work_files.py)).

This is a **rebuild, not an in-place upgrade**: it reads the existing database
and writes a **brand-new** SQLite file with the full target schema (the `puzzles`
table carrying the state columns directly). The old file is opened read-only and
never modified. Because the destination is fresh, the schema is defined **once,
unconditionally** — no `CREATE TABLE IF NOT EXISTS`, no `ALTER TABLE`, no
`_column_exists()` guards. The single user runs it once, verifies the result,
then points the app at the new file.

This is the **only** way an existing database gains the state columns — the
running app never runs `ALTER TABLE`. The rebuild also lets the tool **backfill**
each puzzle's `state` with its real, auto-detected value rather than a flat
`draft`.

It uses **plain `sqlite3`** for the schema and the row copy, and **reuses the
domain code** to classify each puzzle — `Puzzle.from_json()` plus
`crossword.domain.puzzle_state.detect_completion_state()` (§3). It does **not**
import `SQLitePersistenceAdapter`.

**Arguments**

- `--old-dbfile` — source DB. Default: resolved the same way the app does
  (config / `DATABASE_URL`).
- `--new-dbfile` — destination DB. **Required.** Must **not already exist** — the
  tool refuses to overlay or overwrite (no `--force`); the old DB is never the
  destination.
- `--dry-run` — report counts (puzzles to copy, working copies skipped, the
  auto-detected state breakdown) and write nothing, like `clear_work_files.py`.

**Procedure**

1. Open `--old-dbfile` read-only (`file:...?mode=ro` URI). Refuse if
   `--new-dbfile` already exists.
2. Create the new DB and define the **complete** schema in one unconditional
   pass — the `puzzles` table (including the state columns) + its unique index
   (DDL exactly as in §1's `CREATE TABLE` form). Copy the DDL from
   `_ensure_schema_compatibility()`
   ([sqlite_persistence_adapter.py:53-88](../../crossword/adapters/sqlite_persistence_adapter.py#L53-L88))
   so it stays faithful; that method remains the schema source of truth for the
   running app.
3. Copy puzzle rows, **preserving `id`** (explicit `INSERT … (id, userid, …,
   state)`), **excluding working copies** — `puzzlename` starting with `__wc__`
   or `__new__`, and skipping legacy `NULL` names (see
   [list_puzzles:199](../../crossword/adapters/sqlite_persistence_adapter.py#L199)).
   The `state` column is **auto-detected** from the puzzle's contents via the
   completion ladder (§2–§3): `Puzzle.from_json(jsonstr)` →
   `detect_completion_state(puzzle)`, yielding `draft` / `filled` / `finished`. A
   fully filled-and-clued puzzle therefore migrates as `finished`, not `draft`.
   The `publisher` / date columns are left NULL.
4. After it finishes, swap the app over: update `dbfile` in
   `~/.config/crossword/config.yaml` (or rename the new file into place).

> Each puzzle's migrated `state` reflects its real completeness via the same
> `detect_completion_state` the running app uses — never a flat `draft`. The
> user-owned states (`submitted`/`published`/`archived`) are out of scope for the
> backfill; they are only ever set later from the dashboard.

> Idempotency is not a concern here: the destination is always a fresh file, so
> there is nothing to re-apply onto. Re-running means deleting the new file and
> rebuilding from the old one again.

---

## 10. Tests (pytest, under `crossword/tests/`)

- **Domain:** `is_filled` / `all_clues_complete` / `detect_completion_state`
  across empty, partial, fully-filled-no-clues, fully-finished puzzles.
- **Adapter:** state columns added/created; `set_puzzle_state` overwrites the
  columns in place; `get_puzzle_state` returns the current values (or `None`);
  `rename_puzzle` preserves `id` + state and rejects a clashing name; delete
  removes the row (and its state).
- **Use case:** `create_puzzle` → `draft`; `copy_puzzle` advances
  draft→filled→finished and backward finished→filled, and recomputes the state
  regardless of the source state; `open_puzzle_for_editing` creates a working
  copy for any state; `set_puzzle_state` enforces required fields (incl.
  non-empty free-form publisher on submit), and Reopen (→ draft).
- **HTTP:** the two new routes happy-path; bad-state and missing-required-field
  rejection.
- **Migration:** writes a fresh DB without touching the source; refuses when the
  destination already exists; copies only real puzzles (preserving `id`), skips
  working copies and `NULL` names; sets each copied puzzle's `state` to its
  auto-detected value (`draft`/`filled`/`finished` via `detect_completion_state`);
  honors `--dry-run`.

---

## 11. Resolved decisions

1. **No editing lock.** Any puzzle may be opened for editing regardless of
   state; `open_puzzle_for_editing` always creates a working copy, and Save
   reclassifies the puzzle via the completion ladder.
2. **Rename preserves state.** Rename is refactored to a true
   `UPDATE puzzles SET puzzlename = ?`, keeping the puzzle `id` and its state
   columns.
3. **Publisher + required fields.** `publisher` is a free-form text field;
   moving to `submitted` requires a non-empty `publisher` + `date_submitted`, and
   moving to `published` requires `date_published`.

---

## 12. Suggested implementation order

1. Domain: `puzzle_state.py` + `Puzzle.is_filled` / `all_clues_complete` (+ tests).
2. Adapter: state columns in the `puzzles` `CREATE TABLE` (no `ALTER TABLE`),
   `set_puzzle_state` / `get_puzzle_state`, in-place `rename_puzzle` (+ tests).
3. Port: declare the state methods and the new `rename_puzzle`.
4. Use cases: auto-set state on `copy_puzzle`, refactored `rename_puzzle`,
   `set_puzzle_state` with free-form publisher field (+ tests).
5. Migration tool + dry-run (+ tests); run it against the dev DB.
6. HTTP endpoints + endpoints.md / Swagger (+ tests).
7. Front-end dashboard — design first, then build.
