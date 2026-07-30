# Puzzle content snapshots — design doc

## The problem this solves

A user submitted a puzzle to a publisher. The publisher asked for changes.
The user made the changes and saved. Only then did they realize they had no
way to get back the exact version they'd originally submitted — the save had
overwritten it.

Today's `puzzle_state_history` table (added in `7b1f46d`, see
[puzzle_state_history.md](puzzle_state_history.md)) already keeps a row for
every state change — draft, filled, finished, submitted, published,
archived. But it only records the *fact* that a puzzle reached that state,
plus who it was submitted to and when. It does not keep a copy of the puzzle
itself — the grid, the fill, the clues — as they were at that moment. So even
with that table in place, there was never anything to go back to.

This doc adds that missing piece: each row in `puzzle_state_history` gets a
copy of the full puzzle content as it stood at that moment. Later, the user
can look at the history, see what the puzzle looked like at each past state,
and — if they want — bring an old version back into the editor to work from.

## Why this is a small change

The puzzle's full content is already stored as one JSON blob:
`puzzles.jsonstr` ([sqlite_persistence_adapter.py:71-79](../../crossword/adapters/sqlite_persistence_adapter.py#L71-L79)).
Every code path that changes a puzzle's state also happens to run right
after that JSON blob is already up to date:

- `create_puzzle` saves the new puzzle, then sets state to `draft`
  ([puzzle_use_cases.py:84-85](../../crossword/use_cases/puzzle_use_cases.py#L84-L85)).
- `copy_puzzle` (used for both "Save" and "Save As") saves the new content,
  then recomputes and sets state
  ([puzzle_use_cases.py:162-163](../../crossword/use_cases/puzzle_use_cases.py#L162-L163)).
- The state-change dialog ("Mark as submitted", "Mark as published", etc.)
  calls `set_puzzle_state` directly. It doesn't touch content, so whatever is
  already saved is the current content.

That means the adapter can grab a copy of `puzzles.jsonstr` at the exact
moment it writes a `puzzle_state_history` row, in the same SQL statement,
with no new plumbing through the use-case layer. No caller needs to pass
puzzle content around — it's already sitting right there in the `puzzles`
row being joined against.

## A bug that has to be fixed first

While tracing this, a related problem turned up in
`_auto_set_state_on_save` ([puzzle_use_cases.py:166-177](../../crossword/use_cases/puzzle_use_cases.py#L166-L177)),
which runs on every "Save":

```python
def _auto_set_state_on_save(self, user_id, name, puzzle):
    computed = ps.detect_completion_state(puzzle)   # only ever draft/filled/finished
    current = self.persistence.get_puzzle_state(user_id, name)
    if current is not None and current["state"] == computed:
        return
    self.persistence.set_puzzle_state(user_id, name, computed)
```

`detect_completion_state` can only return `draft`, `filled`, or `finished`
— it has no idea about `submitted`, `published`, or `archived`
([puzzle_state.py:19-27](../../crossword/domain/puzzle_state.py#L19-L27)).
So once a puzzle has been marked `submitted`, every later "Save" compares
`"submitted"` against something like `"finished"`, sees they don't match,
and silently writes a new history row that knocks the puzzle's displayed
state back down to `finished`. This already happens today, independent of
this doc — it's the reason the user's puzzle history doesn't cleanly show
"submitted" as the last thing that happened.

For this doc, it also matters directly: without a fix, every ordinary save
after submission would keep minting new history rows (and, once this doc
ships, a fresh content snapshot with each one) for a state change nobody
asked for. That defeats the point — the submitted snapshot would immediately
get buried under snapshots from routine post-submission edits.

**Fix:** `_auto_set_state_on_save` should only touch state while a puzzle is
still on the completion ladder. Once the current state is `submitted`,
`published`, or `archived`, plain saves should leave state alone entirely —
those states are user-owned (set only through the state dialog), not
something autosave should ever move.

```python
def _auto_set_state_on_save(self, user_id, name, puzzle):
    current = self.persistence.get_puzzle_state(user_id, name)
    if current is not None and current["state"] not in ps.COMPLETION_LADDER:
        return
    computed = ps.detect_completion_state(puzzle)
    if current is not None and current["state"] == computed:
        return
    self.persistence.set_puzzle_state(user_id, name, computed)
```

With this fix, saving a submitted puzzle after making the publisher's
requested changes no longer touches history at all — which is correct. The
snapshot from the original `submitted` row stays exactly as it was, untouched,
ready to be looked at or restored. If the user submits again later, that's a
deliberate action through the state dialog, and it gets its own fresh
snapshot (see below).

## Schema change

Add one nullable column to the existing table:

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
    content         TEXT,
    changed_at      TEXT NOT NULL
);
```

`content` holds the same JSON text format as `puzzles.jsonstr`
(`puzzle.to_json()` / `Puzzle.from_json()`). It's nullable because rows
written before this change won't have it, and there's nothing to
retroactively fill it with — the old design never captured content, so
there's no way to reconstruct what a puzzle looked like before this ships.

Every snapshot is stored in full, not as a diff against the previous one.
Puzzle JSON is small (a grid plus a handful of clue strings — a few
kilobytes at most), and history rows are already rare, thanks to the
de-duplication in `_auto_set_state_on_save` and the fix above. Diffing would
save a little disk space at the cost of real complexity (reconstructing any
given version means replaying every diff before it). Not worth it here.

## Adapter change

`set_puzzle_state` in `sqlite_persistence_adapter.py`
([sqlite_persistence_adapter.py:188-209](../../crossword/adapters/sqlite_persistence_adapter.py#L188-L209))
already inserts by selecting from `puzzles`:

```sql
INSERT INTO puzzle_state_history
        (puzzle_id, state, publisher, date_submitted, date_published, changed_at)
SELECT id, ?, ?, ?, ?, ? FROM puzzles WHERE userid = ? AND puzzlename = ?
```

Add `content` to both the column list and the `SELECT`:

```sql
INSERT INTO puzzle_state_history
        (puzzle_id, state, publisher, date_submitted, date_published, content, changed_at)
SELECT id, ?, ?, ?, ?, jsonstr, ? FROM puzzles WHERE userid = ? AND puzzlename = ?
```

That's the entire write-side change. No other method needs to change to
capture content — it happens automatically, every time.

## Reading history without the extra weight

`get_puzzle_state_history` ([sqlite_persistence_adapter.py:239-264](../../crossword/adapters/sqlite_persistence_adapter.py#L239-L264))
is used to render the whole history list in one go (the "Show history"
popup in the dashboard). If it also pulled back full puzzle content for
every row, that list would get noticeably heavier for no benefit — the user
just wants to see *when* things happened, not read the puzzle content
inline.

So: leave `get_puzzle_state_history` as it is today, except add one cheap
boolean, `has_content` (`content IS NOT NULL`), so the frontend knows which
rows can be restored. Add a separate, new method for fetching one snapshot's
content on demand:

```python
def get_puzzle_state_history_content(self, user_id: int, name: str, history_id: int) -> str | None:
    """Return the saved puzzle-content JSON for one history row, or None if
    that row doesn't exist, doesn't belong to this puzzle/user, or predates
    this feature (no content saved)."""
```

Implementation joins `puzzle_state_history` to `puzzles` on `puzzle_id`,
filtered by `puzzles.userid`, `puzzles.puzzlename`, and `puzzle_state_history.id`
— the same ownership check pattern used everywhere else in this file.

## Restoring an old snapshot

The safest way to bring back an old version is to treat it exactly like
opening a puzzle for editing — not to silently overwrite the live puzzle.
The app already has a working-copy pattern for exactly this kind of "let the
user review before committing" flow: `open_puzzle_for_editing`
([puzzle_use_cases.py:283-308](../../crossword/use_cases/puzzle_use_cases.py#L283-L308))
loads a puzzle, clears its undo/redo stacks, and saves it under a fresh
`__wc__<name>__<uuid>` name that the editor then opens.

Add a new use case that does the same thing, but loads content from a
history row instead of from the puzzle's current saved copy:

```python
def restore_puzzle_from_history(self, user_id: int, name: str, history_id: int) -> str:
    """
    Open an old snapshot of a puzzle for editing, as a new working copy.

    Does not touch the live puzzle or its state. The user reviews the old
    version in the editor and decides whether to keep it (Save / Save As)
    or discard it (Close), exactly as with any other working copy.

    Returns: working_name, the name of the new working copy.
    Raises: PersistenceError if the puzzle or history row isn't found, or
        that row has no saved content (predates this feature).
    """
```

This means "Restore" needs no new state-machine concept, no new undo
behavior, and no special-cased save path — it's just "open a puzzle for
editing," pointed at a different source. Once it's open, all the existing
Save / Save As / Close logic applies unchanged. If the user hits Save, that
goes through `copy_puzzle` as usual, which (per the fix above) will only
touch state — and thus only take a new snapshot — if the puzzle is still on
the completion ladder or if the user explicitly changes state via the
dialog afterward.

## HTTP layer

One new route, following the existing pattern in `puzzle_handlers.py`:

```
POST /api/puzzles/<name>/state/history/<id>/restore
  -> { "working_name": "__wc__..." }
```

`handle_restore_puzzle_from_history` mirrors
`handle_open_puzzle_for_editing` ([puzzle_handlers.py:252-281](../../crossword/http_server/puzzle_handlers.py#L252-L281))
almost exactly — same auth check, same shape of response — just calling
`restore_puzzle_from_history` instead of `open_puzzle_for_editing`, with the
history id taken from the URL.

`GET /api/puzzles/<name>/state/history` is unchanged in shape except each
entry gains `has_content: true/false`.

## Frontend

In the "Show history" popup (`_dashShowHistory` /
`_historyTableHtml` in [dashboard.js:441-476](../../frontend/static/js/dashboard.js#L441-L476)),
add a "Restore" link/button on each row where `has_content` is true. Clicking
it should:

1. Ask for confirmation, since it leaves the dashboard and opens the editor.
2. Call the new restore endpoint.
3. Open the puzzle editor on the returned `working_name`, exactly the way
   opening a puzzle from the dashboard already does.

No changes needed anywhere else in the frontend — the editor, Save, Save As,
and Close flows are all reused as-is.

## Migration

The project's convention is: no live `ALTER TABLE` on a production
database; schema changes ship as a one-off rebuild tool, and the running
adapter's `CREATE TABLE IF NOT EXISTS` only ever describes the *new* shape.
This follows the same shape as
[tools/dev/migrate_puzzle_state_history.py](../../tools/dev/migrate_puzzle_state_history.py),
which did the equivalent job for the original `puzzle_state_history` table.

New tool, `tools/dev/migrate_puzzle_content_snapshots.py`:

- Opens the current database read-only.
- Writes a new database with the updated `puzzle_state_history` table
  (the `content` column included) and copies every existing row across
  unchanged, with `content` left `NULL` — there is nothing to backfill,
  since old rows never captured content.
- Same safety rules as the existing tool: `--new-dbfile` required and must
  not already exist, `--old-dbfile` optional (defaults to the configured
  `dbfile`), `--dry-run` reports row counts without writing anything.
- After running, point `~/.config/crossword/config.yaml`'s `dbfile` at the
  new file, same as documented for the earlier migration.

## Tests to update

- `crossword/tests/adapters/test_sqlite_adapter.py` — `content` column
  exists on `puzzle_state_history`; `set_puzzle_state` stores the current
  `jsonstr` into `content`; `get_puzzle_state_history_content` returns the
  right snapshot for a given history id, and `None` for a row that isn't
  found, doesn't belong to the user, or has no content.
- `crossword/tests/test_puzzle_use_cases.py` —
  - `_auto_set_state_on_save` no longer touches state once a puzzle is
    `submitted`/`published`/`archived` (the bug fix above).
  - `restore_puzzle_from_history` creates a working copy whose content
    matches the historical snapshot, and raises when the history row has no
    content or doesn't belong to the puzzle/user.
- `crossword/tests/test_http_server.py` — new restore route: success case,
  and 404-style error when the history id is missing or has no content.
- New sibling test file for the migration tool, mirroring
  `test_migrate_puzzle_state_history.py`.

## Open questions

1. **Should restoring also log something in history?** Right now,
   restoring is just "open old content in a working copy" — nothing is
   written to `puzzle_state_history` until the user actually saves, and at
   that point the normal save/state-change rules apply. Recommended:
   leave it this way. A "restored" audit entry could be added later if
   there's a real need to track who restored what and when, but nothing
   today needs it.
2. **How far back should snapshots be kept?** No pruning is proposed here.
   Puzzle JSON is small and history rows are already infrequent, so unbounded
   retention seems fine unless it turns out to matter in practice.
