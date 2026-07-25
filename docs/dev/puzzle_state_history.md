# Puzzle State History — design doc

## Goal

Replace the four lifecycle columns currently living on `puzzles` — `state`,
`publisher`, `date_submitted`, `date_published` — with a separate
`puzzle_state_history` table that records **every** state transition, not just
the current one. "Current state" stops being a stored fact and becomes a
derived read: the most recent row in that table for a given puzzle.

This is a storage-layer refactor only. The HTTP API contract, the domain
ladder logic in `crossword/domain/puzzle_state.py`, and the frontend are
unchanged — see "Frontend" below for why.

## Background: this repeats an earlier, abandoned design

This isn't a new idea for this project. The original plan for puzzle
lifecycle states (`821c1ad`, `docs/dev/dashboard.md`, since deleted as
obsolete) specified exactly this: a `puzzle_state` history table with one row
per transition, keyed by `puzzle_id` with `ON DELETE CASCADE`. Before that
table was ever wired up to the use-case layer, it was collapsed to plain
columns (`ba33ef3`, "Store puzzle state as columns on puzzles, drop history
table") and the column design is what actually got implemented
(`b67e678`) and is running today. This doc is effectively reverting that
collapse, now that the column design has been live long enough to know it
doesn't capture history.

One thing from that original plan is **not** being resurrected: a `READ_ONLY`
set of states that blocked editing until the user explicitly reopened a
puzzle. That was implemented and then deliberately removed (`58a204f`,
"Remove read-only puzzle state concept") because it made editing
submitted/published/archived puzzles impossible without an extra step, and
the team decided re-detection on save was preferable. Nothing in this doc
reintroduces that lock.

## Current state of the code (for grounding)

- Schema:
  [sqlite_persistence_adapter.py:61-84](../../crossword/adapters/sqlite_persistence_adapter.py#L61-L84)
  — `state`/`publisher`/`date_submitted`/`date_published` are columns on
  `puzzles`, with a `CHECK` constraint on `state`.
- Domain ladder (unaffected by this change):
  [puzzle_state.py](../../crossword/domain/puzzle_state.py) — `ALL_STATES`,
  `COMPLETION_LADDER`, `detect_completion_state()`.
- Port:
  [persistence_port.py:82-172](../../crossword/ports/persistence_port.py#L82-L172)
  — `set_puzzle_state` (overwrite), `get_puzzle_state` (read columns),
  `list_puzzles(state=...)`, `list_puzzle_summaries`.
- Adapter implementations:
  [sqlite_persistence_adapter.py:188-307](../../crossword/adapters/sqlite_persistence_adapter.py#L188-L307).
- Use cases:
  [puzzle_use_cases.py](../../crossword/use_cases/puzzle_use_cases.py) —
  `create_puzzle` (63-83, does **not** set state explicitly — relies on the
  column `DEFAULT 'draft'`), `copy_puzzle` (136-162, calls
  `_auto_set_state_on_save`), `_auto_set_state_on_save` (164-167),
  `open_puzzle_for_editing` (253-278, writes the working copy via
  `persistence.save_puzzle` directly — bypasses state entirely),
  `get_puzzle_state`/`set_puzzle_state` (188-251), `get_dashboard`/
  `_dashboard_row` (611-650).
- HTTP: `GET`/`PUT /api/puzzles/<name>/state` in
  [puzzle_handlers.py](../../crossword/http_server/puzzle_handlers.py)
  (routes at 12-13, handlers at 281+ and 311+).
- Frontend consumer:
  [dashboard.js](../../frontend/static/js/dashboard.js) — reads `row.state` /
  `row.publisher` etc. from `GET /api/dashboard` rows, and drives
  `PUT /api/puzzles/<name>/state` from the state-change dialog.
- Existing one-off migration tool:
  [tools/dev/migrate_puzzle_state.py](../../tools/dev/migrate_puzzle_state.py)
  — rebuilds a fresh DB with the column schema, auto-detecting each puzzle's
  ladder state. This tool migrated pre-state DBs *into* the column design;
  it's the mirror image of what this doc now needs.

## New table

```sql
CREATE TABLE IF NOT EXISTS puzzle_state_history (
    id              INTEGER PRIMARY KEY,
    puzzle_id       INTEGER NOT NULL REFERENCES puzzles(id) ON DELETE CASCADE,
    state           TEXT NOT NULL CHECK (state IN (
                        'draft','filled','finished',
                        'submitted','published','archived')),
    publisher       TEXT,
    date_submitted  TEXT,
    date_published  TEXT,
    changed_at      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_puzzle_state_history_puzzle
    ON puzzle_state_history(puzzle_id, id DESC);
```

Design choices, and why they differ slightly from the 2026-06 plan:

- **Surrogate `id INTEGER PRIMARY KEY`** for ordering, instead of the
  original plan's composite `PRIMARY KEY (ts, puzzle_id)`. `changed_at` is
  `datetime.now().isoformat()` — the same clock used for `puzzles.modified`
  today — and its resolution isn't guaranteed fine enough to break ties
  between two rows written in the same request. Autoincrementing rowid gives
  unambiguous insert order for "what's the latest row" regardless of clock
  resolution; `changed_at` remains a plain column for display.
- **FK on `puzzle_id` → `puzzles.id`**, not `puzzlename`. `id` is stable
  across renames (`rename_puzzle` preserves it —
  [sqlite_persistence_adapter.py:234-254](../../crossword/adapters/sqlite_persistence_adapter.py#L234-L254));
  `puzzlename` is not.
- **`ON DELETE CASCADE`** — deleting a puzzle deletes its history with it.
  This requires `PRAGMA foreign_keys = ON`, which SQLite does not enable by
  default per-connection; the adapter's `__init__`
  ([sqlite_persistence_adapter.py:21-37](../../crossword/adapters/sqlite_persistence_adapter.py#L21-L37))
  currently does not set this pragma and needs to.
- Everything except `id`/`puzzle_id`/`state`/`changed_at` stays nullable,
  same as today — only `submitted` rows populate `publisher` +
  `date_submitted`, only `published` rows populate `date_published`.

## `puzzles` table changes

Drop the four columns from the `CREATE TABLE` in `_ensure_schema_compatibility()`,
back to its pre-`b67e678` shape:

```sql
CREATE TABLE puzzles (
    id          INTEGER PRIMARY KEY,
    userid      INTEGER NOT NULL,
    puzzlename  TEXT NOT NULL,
    created     TEXT NOT NULL,
    modified    TEXT NOT NULL,
    last_mode   TEXT NOT NULL DEFAULT 'puzzle'
                    CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr     TEXT NOT NULL
);
```

The project's stated convention is no live `ALTER TABLE` — schema evolution
happens once, via a rebuild tool (see Migration below), and the running
adapter only ever does `CREATE TABLE IF NOT EXISTS` against the target shape.

## Persistence port (`persistence_port.py`)

No method signatures change. Docstrings do:

- `set_puzzle_state(...)`: currently documented as "Overwrite the puzzle's
  state columns in place"; becomes "Append a new state-history row." Callers
  are unaffected — they already treat this as "set the current state."
- `get_puzzle_state(...)`: becomes "Return the most recent state-history row
  for this puzzle" instead of "read the columns." Same return dict shape
  (`state`, `publisher`, `date_submitted`, `date_published`), so `None` still
  means "puzzle not found."
- `list_puzzles(state=...)` / `list_puzzle_summaries`: docstrings note the
  filter/columns now come from each puzzle's latest history row rather than
  from columns on the same row.

Optional addition (see Open Questions): `get_puzzle_state_history(user_id,
name) -> list[dict]`, returning every row oldest-to-newest, for a future
"view history" affordance. Not required by anything in scope today.

## SQLite adapter (`sqlite_persistence_adapter.py`)

- `__init__`: add `self.conn.execute("PRAGMA foreign_keys = ON")` right after
  connecting, so the new FK's `ON DELETE CASCADE` actually fires.
- `_ensure_schema_compatibility`: drop the 4 columns from the `puzzles` DDL;
  add the `puzzle_state_history` table + its index (both `CREATE ... IF NOT
  EXISTS`, matching the existing pattern for `puzzles`).
- A shared SQL fragment for "the latest history row per puzzle" is needed in
  three places below, so it's worth defining once as a module-level constant
  or a small private helper, e.g.:

  ```sql
  SELECT puzzle_id, state, publisher, date_submitted, date_published
  FROM puzzle_state_history
  WHERE id IN (SELECT MAX(id) FROM puzzle_state_history GROUP BY puzzle_id)
  ```

  (A `ROW_NUMBER() OVER (PARTITION BY puzzle_id ORDER BY id DESC)` window
  function would also work — the project's bundled SQLite is 3.45.1, well
  past the 3.25 minimum — but the `MAX(id)` grouped subquery reads more
  plainly for a three-line fragment and doesn't need explaining to future
  readers unfamiliar with window functions.)

- `set_puzzle_state`: becomes an insert instead of an update:
  ```sql
  INSERT INTO puzzle_state_history
      (puzzle_id, state, publisher, date_submitted, date_published, changed_at)
  SELECT id, ?, ?, ?, ?, ? FROM puzzles WHERE userid = ? AND puzzlename = ?
  ```
  then check `cursor.rowcount == 0` for the "puzzle not found" error, same as
  today. Still also `UPDATE puzzles SET modified = ? WHERE ...` in the same
  call, so state changes keep bumping `modified` — the dashboard's
  most-recently-modified sort depends on that today and should keep working
  unchanged.
- `get_puzzle_state`: rewritten as a single join, ordered by `id DESC`,
  `LIMIT 1`:
  ```sql
  SELECT h.state, h.publisher, h.date_submitted, h.date_published
  FROM puzzles p
  JOIN puzzle_state_history h ON h.puzzle_id = p.id
  WHERE p.userid = ? AND p.puzzlename = ?
  ORDER BY h.id DESC LIMIT 1
  ```
  Returns `None` both when the puzzle doesn't exist and when it exists but
  has no history row yet — the latter should no longer be reachable once
  `create_puzzle` is fixed (see below), but the code shouldn't crash if it
  happens.
- `list_puzzles(state=filter)` and `list_puzzle_summaries`: both join
  `puzzles` against the shared "latest per puzzle" fragment above instead of
  reading columns directly. `list_puzzle_summaries` should `LEFT JOIN` (not
  `JOIN`) so a puzzle without a history row still appears in the dashboard
  (with `state: None`) rather than silently vanishing — defensive, since this
  case shouldn't occur in practice after the fix below.

## Use cases (`puzzle_use_cases.py`)

- **`create_puzzle` needs a real fix, not just a passthrough.** Today it
  relies on the `state` column's `DEFAULT 'draft'` and never calls any state
  method — [puzzle_use_cases.py:63-83](../../crossword/use_cases/puzzle_use_cases.py#L63-L83).
  Once the column (and its default) is gone, a freshly created puzzle has
  *no* history row until its first Save/Save As (which goes through
  `copy_puzzle` → `_auto_set_state_on_save`). Add an explicit
  `self.persistence.set_puzzle_state(user_id, name, ps.DRAFT)` call at the
  end of `create_puzzle`. This is a latent gap the migration surfaces, not
  scope creep — call it out as a required part of this change.
- `_auto_set_state_on_save` / `copy_puzzle`: no logic change — still
  "compute the ladder state, call `set_puzzle_state`." Only the storage
  underneath moves from update to insert.
- `open_puzzle_for_editing`: no change — it saves the working copy via
  `persistence.save_puzzle` directly
  ([puzzle_use_cases.py:253-278](../../crossword/use_cases/puzzle_use_cases.py#L253-L278)),
  never through `copy_puzzle`, so working copies (`__wc__…`, `__new__…`)
  still never get a history row. Worth a new test asserting this explicitly:
  under the column design a wc row silently got the column default and was
  just filtered out of listings; under the table design there's no implicit
  row for it at all, so `get_puzzle_state` on a wc name must resolve to
  `None` cleanly rather than error.
- **De-duplication (decided):** `set_puzzle_state` should not insert a new
  row when the incoming state+publisher+dates are identical to the latest
  row, matching the abandoned 2026-06 plan ("record only on change...
  avoids a row on every keystroke-driven save"). `_auto_set_state_on_save`
  compares the computed ladder state against the current latest state
  before calling `persistence.set_puzzle_state`, and skips the call if
  unchanged. Without this, saving a `finished` puzzle repeatedly (which
  happens constantly via autosave in the editor) would write a history row
  every time, defeating the point of a history table.

## Migration

Same rebuild-a-fresh-file approach as
[tools/dev/migrate_puzzle_state.py](../../tools/dev/migrate_puzzle_state.py)
today, run in reverse:

- New tool (`tools/dev/migrate_puzzle_state_history.py`, mirroring the
  existing tool's name/shape) opens the *current* production DB read-only,
  reads every real puzzle's `id`, `state`, `publisher`, `date_submitted`,
  `date_published`, `modified` (same `__wc__`/`__new__`/NULL-name exclusion
  filter as today).
- Writes a new DB with: the `puzzles` table *without* the four columns, the
  new `puzzle_state_history` table, and — for each real puzzle — exactly one
  history row seeded from its current column values, with `changed_at` set
  to that puzzle's `modified` timestamp. There's nothing to backfill beyond
  "current state as of now"; the column design never recorded transition
  history, so there's no way to reconstruct earlier states.
- Same safety properties as the existing tool: `--new-dbfile` required and
  must not already exist, `--old-dbfile` optional (defaults to the
  configured dbfile), `--dry-run` reports counts without writing, source
  connection is opened read-only.
- After running, the user points `~/.config/crossword/config.yaml`'s
  `dbfile` at the new file, same as documented today.

The existing `tools/dev/migrate_puzzle_state.py` and its test
(`test_migrate_puzzle_state.py`) should stay — they're still the correct
path for anyone migrating a database from *before* puzzle state existed at
all (pre-`b67e678`). The two tools serve different source schemas.

## HTTP layer

No changes. `handle_get_puzzle_state`, `handle_set_puzzle_state`, and
`handle_get_dashboard` in
[puzzle_handlers.py](../../crossword/http_server/puzzle_handlers.py) keep
their exact request/response JSON shapes — this whole doc is scoped to sit
entirely underneath them.

## Frontend

The request that prompted this doc says state should be "constructed from
the latest value in the puzzle state table" on the front end. Worth being
explicit about what that means given this app's architecture: `dashboard.js`
and `state.js` have no database access — the SPA only ever talks to the HTTP
API (hexagonal architecture, driving side). So "construct current state from
the latest history row" necessarily happens server-side, in the adapter
queries described above, not in JavaScript. Because the API responses are
unchanged, **no frontend code changes at all** are needed for this migration
— `dashboard.js` already just reads whatever `state`/`publisher`/etc. come
back from `GET /api/dashboard` and `GET /api/puzzles/<name>/state`.

If what's actually wanted is a client-*visible* history — e.g. an audit
trail in the state-change dialog showing every past transition, not just the
current one — that's a separate, additive feature on top of this: a new
`GET /api/puzzles/<name>/state/history` endpoint plus a "History" section in
`dashboard.js`'s state dialog. Flagging as a natural follow-up, not included
here unless wanted.

## Tests to update

- `crossword/tests/adapters/test_sqlite_adapter.py` — schema assertions
  (columns removed from `puzzles`; `puzzle_state_history` table + index
  exist); `set_puzzle_state` now appends (assert row count grows) instead of
  overwriting; `get_puzzle_state` returns the latest row when several exist;
  cascade delete removes history rows when a puzzle is deleted.
- `crossword/tests/test_puzzle_use_cases.py` — `create_puzzle` now expected
  to produce a `draft` history row (new assertion, paired with the fix
  above); de-dup behavior on repeated saves at the same ladder state, if
  that's confirmed.
- `crossword/tests/test_puzzle_state.py` — unaffected; pure domain ladder
  logic, no persistence involved.
- `crossword/tests/test_http_server.py` — unaffected; these mock the
  use-case layer and never touch SQL.
- `crossword/tests/test_migrate_puzzle_state.py` — unaffected, stays testing
  the existing (pre-state → columns) tool; a new sibling test file covers
  the new (columns → history table) tool.

## Open questions

1. ~~De-dup identical consecutive rows on autosave~~ — **decided: yes**,
   matching the abandoned 2026-06 plan (see `_auto_set_state_on_save` above).
2. **Expose history reads at all right now** (`get_puzzle_state_history` /
   a history endpoint), or add the table purely for future use and wire up
   reads only when a UI need exists? Recommended: defer — nothing in scope
   consumes it yet.
3. ~~Naming~~ — **decided: `puzzle_state_history`**, to avoid colliding with
   the existing `crossword/domain/puzzle_state.py` module name.
