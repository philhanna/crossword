# Migration Plan For Issue 196 Databases

This document describes how to migrate a database from the pre-196 persistence layout to the merged puzzle-only layout introduced by issue 196.

The migration is copy-forward:

- the old database is opened read-only
- a new database file is created
- migrated rows are written into the new database only

It covers both:

- SQL schema changes
- `jsonstr` payload changes inside persisted puzzle rows

## Goal

After migration:

- `puzzles` is the only persisted construction table
- each puzzle row contains its own grid structure inside `jsonstr`
- each puzzle row has a persisted `last_mode` column
- the old standalone `grids` table is no longer required

## Old And New Formats

### Old database shape

The old design treated grids and puzzles as separate persisted objects.

Expected old tables:

```sql
CREATE TABLE grids (
    id          INTEGER PRIMARY KEY,
    userid      INTEGER NOT NULL,
    gridname    TEXT NOT NULL,
    created     TEXT NOT NULL,
    modified    TEXT NOT NULL,
    jsonstr     TEXT NOT NULL
);

CREATE TABLE puzzles (
    id          INTEGER PRIMARY KEY,
    userid      INTEGER NOT NULL,
    puzzlename  TEXT NOT NULL,
    created     TEXT NOT NULL,
    modified    TEXT NOT NULL,
    jsonstr     TEXT NOT NULL
);
```

Historical note:

- the exact old `puzzles.jsonstr` shape may vary by age of the database
- in the currently tested legacy case, puzzle JSON is already mostly modern and only lacks `last_mode`
- older databases may still contain puzzle JSON that assumes a separately persisted grid

### New database shape

The merged-editor design persists one unified puzzle row:

```sql
CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT NOT NULL,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle'
                        CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr         TEXT NOT NULL,
    UNIQUE (userid, puzzlename)
);
```

The `grids` table is removed in the target state.

## What Must Change In `jsonstr`

Each persisted puzzle JSON must be rewritten to the unified `Puzzle.to_json()` shape.

The target serialized puzzle currently includes:

- `n`
- `title`
- `last_mode`
- `cells`
- `black_cells`
- `across_words`
- `down_words`
- `undo_stack`
- `redo_stack`
- `puzzle_undo_stack`
- `puzzle_redo_stack`
- `grid_undo_stack`
- `grid_redo_stack`

### Required JSON migration rules

1. Ensure the puzzle JSON has its own embedded grid structure.
   Specifically, it must contain:
   - `n`
   - `black_cells`

2. Add `last_mode` if it is missing.
   Use:
   - `'puzzle'` for migrated existing rows unless a more trustworthy mode source exists

3. Normalize undo/redo keys.
   The final JSON should contain:
   - `puzzle_undo_stack`
   - `puzzle_redo_stack`
   - `grid_undo_stack`
   - `grid_redo_stack`

4. Preserve puzzle content already present in the row:
   - `title`
   - `across_words`
   - `down_words`
   - `cells`

5. If a legacy puzzle JSON refers to a saved grid indirectly rather than embedding `black_cells`, resolve that grid from the old `grids` table and embed the grid data directly into the migrated puzzle JSON.

### Fields that should not be guessed

Do not invent:

- clue text
- answer text
- black-cell locations
- grid size

If a row cannot be resolved deterministically, it should be reported and skipped for manual repair rather than silently migrated incorrectly.

## Migration Strategy

Use a one-off offline migration script, not lazy migration during normal app use.

Why:

- it preserves the old database unchanged
- it is easier to inspect and back up
- it allows row-by-row reporting
- it lets us rewrite both SQL schema and JSON payloads in one controlled pass
- it avoids running mixed old/new persistence rules in production longer than necessary

## Recommended Procedure

### Phase 1: Backup And Inspect

1. Stop the application.
2. Keep the old SQLite file as the read-only source of truth.
3. Choose a path for the new migrated SQLite file.
4. Record baseline counts from the old database:
   - number of rows in `puzzles`
   - number of rows in `grids`
5. Sample a few `jsonstr` values from both tables to confirm which legacy shapes are present.

Suggested inspection queries:

```sql
SELECT COUNT(*) FROM puzzles;
SELECT COUNT(*) FROM grids;
SELECT puzzlename, substr(jsonstr, 1, 200) FROM puzzles LIMIT 5;
SELECT gridname, substr(jsonstr, 1, 200) FROM grids LIMIT 5;
```

### Phase 2: Create The New Schema

Create a brand-new destination database with the final puzzle-only schema.

```sql
CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT NOT NULL,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle'
                        CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr         TEXT NOT NULL,
    UNIQUE (userid, puzzlename)
);
```

The `'puzzle'` default is only a migration placeholder for rows whose old data has no trustworthy mode value.

### Phase 3: Rewrite Puzzle JSON

For each puzzle row:

1. Parse `puzzles.jsonstr`.
2. Detect whether the row is:
   - already in unified form
   - missing only `last_mode` / new undo keys
   - still dependent on a separately persisted grid
3. Produce a new canonical puzzle JSON object.
4. Insert a new row into the destination database with:
   - migrated `jsonstr`
   - migrated `last_mode`
   - copied identity and timestamps

### Phase 4: Validate Migrated Rows

For each migrated row in the new database:

1. Deserialize with the current `Puzzle.from_json()`.
2. Verify:
   - `n` is present
   - `black_cells` is present
   - `last_mode` is either `grid` or `puzzle`
   - across/down word collections rebuild successfully
3. Record any rows that fail validation and stop before promoting the new database.

### Phase 5: Finalize And Promote The New Database

Only after all puzzle rows validate:

1. Close both databases.
2. Keep the old database untouched for rollback.
3. Rename or deploy the new database as the active application database.

### Phase 6: Add Final Constraint/Index Cleanup

Ensure the final uniqueness rule exists:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_puzzles_userid_puzzlename
ON puzzles(userid, puzzlename);
```

## Canonical Row-Rewrite Algorithm

For each `(userid, puzzlename, jsonstr)` in `puzzles`:

1. Parse the puzzle JSON.
2. Start a new `image` object.
3. Copy over puzzle-owned fields when present:
   - `title`
   - `cells`
   - `across_words`
   - `down_words`
   - `undo_stack`
   - `redo_stack`
4. Set `image["last_mode"]`:
   - old value if present and valid
   - otherwise `'puzzle'`
5. Determine the grid:
   - if the old puzzle JSON already has `n` and `black_cells`, use them
   - otherwise resolve the referenced grid row from `grids`
6. Normalize undo stacks:
   - `puzzle_undo_stack = old.puzzle_undo_stack or old.undo_stack or []`
   - `puzzle_redo_stack = old.puzzle_redo_stack or old.redo_stack or []`
   - `grid_undo_stack = old.grid_undo_stack or []`
   - `grid_redo_stack = old.grid_redo_stack or []`
7. Ensure required collections exist even if empty:
   - `across_words`
   - `down_words`
8. Serialize back to JSON and insert the migrated row into the destination `puzzles` table.

## Two Practical Legacy Cases

### Case A: Puzzle JSON is already almost current

This is the legacy shape currently covered by automated tests.

Characteristics:

- puzzle JSON already includes `n`
- puzzle JSON already includes `black_cells`
- puzzle JSON is missing `last_mode`
- puzzle JSON may be missing `grid_undo_stack` and `grid_redo_stack`

Migration action:

- copy the row into the new database
- add `last_mode = 'puzzle'`
- add missing grid undo arrays
- optionally normalize `puzzle_undo_stack` / `puzzle_redo_stack`

### Case B: Puzzle JSON still depends on a separate saved grid

This is the older shape implied by the original architecture.

Characteristics:

- puzzle JSON does not contain enough grid structure to reconstruct the puzzle by itself
- another field or naming convention must identify the source grid row

Migration action:

1. load the referenced old grid row
2. parse `grids.jsonstr`
3. copy `n` and `black_cells` into the new puzzle JSON
4. keep the puzzle’s clue/answer/title content
5. set `last_mode = 'puzzle'`
6. insert the rewritten row into the new database

If the puzzle row cannot be matched to a grid row with certainty, report it as a migration failure.

## Suggested SQL Skeleton

The JSON rewrite itself should be done in application code, but the SQL shell around the destination database can be:

```sql
BEGIN TRANSACTION;

CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT NOT NULL,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle'
                        CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr         TEXT NOT NULL,
    UNIQUE (userid, puzzlename)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_puzzles_userid_puzzlename
ON puzzles(userid, puzzlename);

-- Row-by-row INSERT INTO puzzles
--        (userid, puzzlename, created, modified, last_mode, jsonstr)
-- VALUES (:userid, :puzzlename, :created, :modified, :last_mode, :new_json);

COMMIT;
```

## Suggested Python Migration Flow

At a high level, the migration script should:

1. open the old database read-only
2. create the new database
3. inspect source schema and row counts
4. create the destination schema
5. iterate through every source puzzle row
6. build canonical unified puzzle JSON
7. insert the migrated row into the new database
8. validate every migrated row with current deserialization
9. close both databases
10. promote the new database only if validation succeeded

Pseudo-code:

```python
for row in old_puzzle_rows:
    image = json.loads(row["jsonstr"])

    if has_embedded_grid(image):
        n = image["n"]
        black_cells = image["black_cells"]
    else:
        grid_ref = find_grid_reference(image, row)
        grid_row = load_old_grid(grid_ref)
        grid_image = json.loads(grid_row["jsonstr"])
        n = grid_image["n"]
        black_cells = grid_image["black_cells"]

    new_image = {
        "n": n,
        "title": image.get("title"),
        "last_mode": normalize_last_mode(image.get("last_mode")),
        "cells": image.get("cells"),
        "black_cells": black_cells,
        "across_words": image.get("across_words", []),
        "down_words": image.get("down_words", []),
        "undo_stack": image.get("undo_stack", []),
        "redo_stack": image.get("redo_stack", []),
        "puzzle_undo_stack": image.get("puzzle_undo_stack", image.get("undo_stack", [])),
        "puzzle_redo_stack": image.get("puzzle_redo_stack", image.get("redo_stack", [])),
        "grid_undo_stack": image.get("grid_undo_stack", []),
        "grid_redo_stack": image.get("grid_redo_stack", []),
    }

    insert_rewritten_row(row, new_image, new_image["last_mode"])
    validate_with_current_code(row["userid"], row["puzzlename"], new_db)
```

## Verification Checklist

After migration, verify all of the following:

- the application can list puzzles without referencing `grids`
- every puzzle row can be loaded by `SQLitePersistenceAdapter.load_puzzle()`
- every loaded puzzle has:
  - `last_mode in {"grid", "puzzle"}`
  - a valid `grid.n`
  - embedded `black_cells`
- new puzzles save into the new schema without any extra migration step
- the database has no remaining `grids` table

Suggested checks:

```sql
SELECT COUNT(*) FROM puzzles;
SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'grids';
PRAGMA table_info(puzzles);
```

## Rollback Plan

If any row rewrite or validation fails:

1. discard the new database
2. keep the original database unchanged
3. inspect the reported failing rows
4. patch the migration script for that legacy shape
5. rerun against the same old database

Do not partially migrate and continue normal use against a half-written destination database.

## Recommended Deliverable

The safest deliverable is a dedicated migration script under `tools/` that:

- prints a pre-migration summary
- rewrites rows deterministically
- validates with current domain code
- prints a post-migration summary
- exits nonzero on any unresolved legacy row

That gives us a repeatable operator workflow instead of relying on ad hoc SQL edits.
