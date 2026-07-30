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

This doc adds that missing piece: **every time the puzzle is saved** — not
just when its state changes — the current row in `puzzle_state_history`
gets a copy of the full puzzle content as it stood at that moment. Later,
the user can look at the history, see what the puzzle looked like at any
past save, and — if they want — bring an old version back into the editor
to work from. Because every save is captured, there's no gap where an
in-between version can quietly vanish: whatever you last saved, before you
went and restored something older, is already sitting safely in history.

## Why this is a small change

The puzzle's full content is already stored as one JSON blob:
`puzzles.jsonstr` ([sqlite_persistence_adapter.py:71-79](../../crossword/adapters/sqlite_persistence_adapter.py#L71-L79)).
Every code path that writes a `puzzle_state_history` row also happens to
run right after that JSON blob is already up to date:

- `create_puzzle` saves the new puzzle, then sets state to `draft`
  ([puzzle_use_cases.py:84-85](../../crossword/use_cases/puzzle_use_cases.py#L84-L85)).
- `copy_puzzle` (used for both "Save" and "Save As") saves the new content,
  then records a fresh history row
  ([puzzle_use_cases.py:162-163](../../crossword/use_cases/puzzle_use_cases.py#L162-L163)).
- The state-change dialog ("Mark as submitted", "Mark as published", etc.)
  calls `set_puzzle_state` directly. It doesn't touch content, so whatever is
  already saved is the current content.

That means the adapter can grab a copy of `puzzles.jsonstr` at the exact
moment it writes a `puzzle_state_history` row, in the same SQL statement,
with no new plumbing through the use-case layer. No caller needs to pass
puzzle content around — it's already sitting right there in the `puzzles`
row being joined against.

## Prerequisite (already done)

An earlier draft of this doc flagged a bug where saving a puzzle after it
had been submitted would silently reset its state. That's now fixed
(`df49739`): a plain "Save" no longer touches *state* once a puzzle is
`submitted`, `published`, or `archived` — those fields stay exactly as the
state dialog last set them. That guarantee still matters here: it's what
keeps "who it was submitted to, and when" correct on the dashboard no
matter how many more times the puzzle is saved afterward.

## One more change needed: snapshot on every save, not just state changes

The version originally in this doc only wrote a `puzzle_state_history` row
when the puzzle's state actually changed — same as the shipped fix above,
which (correctly, for *state*) skips the write entirely once a puzzle is
past the ladder. But that means content snapshots would inherit the same
gap the fix above was created to avoid: any save that doesn't change state
— which, once a puzzle is `finished` or `submitted`, is *every* ordinary
save from then on — would leave nothing behind. That's exactly the
scenario that prompted this doc: a puzzle gets edited after submission, and
whatever it looked like a moment ago is gone the instant the new content is
saved.

So `_auto_set_state_on_save`
([puzzle_use_cases.py:166-184](../../crossword/use_cases/puzzle_use_cases.py#L166-L184))
needs to always write a row on every save, whether or not state itself is
changing:

- **Still on the ladder** (`draft`/`filled`/`finished`, or a brand-new
  puzzle with no history yet): behave as today — recompute state with
  `detect_completion_state` and write it, along with the fresh content.
  `publisher`/`date_submitted`/`date_published` stay `None`, as they always
  have for ladder states.
- **Past the ladder** (`submitted`/`published`/`archived`): still write a
  row every save, but *carry forward* the current `state`, `publisher`,
  `date_submitted`, and `date_published` unchanged from the latest row,
  rather than recomputing or clearing them. Only the `content` and
  `changed_at` are new. This is what keeps the dashboard's "submitted to
  NYT on 2026-06-06" display correct after the puzzle is saved again — if
  this row instead left those fields blank, that information would
  disappear the moment the user made one more edit.

```python
def _auto_set_state_on_save(self, user_id: int, name: str, puzzle: Puzzle) -> None:
    """Record a fresh content snapshot on every save.

    While the puzzle is still on the completion ladder, state is
    recomputed as usual. Once it's past the ladder, state/publisher/dates
    are user-owned (set only via the state dialog) and are carried
    forward unchanged — only the content snapshot is new.
    """
    current = self.persistence.get_puzzle_state(user_id, name)
    if current is None or current["state"] in ps.COMPLETION_LADDER:
        state = ps.detect_completion_state(puzzle)
        publisher = date_submitted = date_published = None
    else:
        state = current["state"]
        publisher = current["publisher"]
        date_submitted = current["date_submitted"]
        date_published = current["date_published"]
    self.persistence.set_puzzle_state(
        user_id, name, state,
        publisher=publisher, date_submitted=date_submitted, date_published=date_published,
    )
```

**This removes the de-duplication that shipped with the original
`puzzle_state_history` design** — the rule that skipped writing a row when
the computed state matched the latest one, specifically to avoid a row on
every save at an unchanged ladder state
([puzzle_state_history.md](puzzle_state_history.md), "De-duplication
(decided)"). That rule was the right call when a row only meant "state
changed." Now that a row also means "here's a recoverable copy of the
puzzle," always writing is the point, not a regression — see storage
tradeoff below.

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
kilobytes at most), so even with a row per save, a puzzle worked on over
dozens of sessions is still at most a few hundred kilobytes of history.
Diffing would save some of that at the cost of real complexity
(reconstructing any given version means replaying every diff before it) —
not worth it at this size. Since every save now writes a row instead of
only state changes, the table will grow noticeably faster than the original
`puzzle_state_history` design intended; see "How far back should snapshots
be kept?" below.

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
goes through `copy_puzzle` as usual, which — per the every-save change
above — always records a fresh snapshot of the restored-and-edited content.

Restoring doesn't need to snapshot the puzzle's *current* content before
swapping the old version in, either. That content was already captured the
moment it was last saved, since every save writes a row now. Restore just
reads an existing row; it never deletes or modifies one, so nothing is at
risk of being overwritten without a copy of it already sitting safely in
history.

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

No other changes are needed for Restore to work — the editor, Save, Save
As, and Close flows are all reused as-is.

One thing worth calling out, though not required for a first version: since
every save now adds a row, `_historyTableHtml` will render a much longer
list than it does today — a puzzle worked on across many sessions could
easily have dozens of rows, most with an unchanged `state`. The table as
written handles that fine (it's just more rows), but it may be worth
grouping consecutive same-state rows in the display (e.g. "6 saves while
`finished`, latest 2026-07-28" with the individual saves reachable by
expanding), so the popup still reads as a short, meaningful timeline rather
than a long list of near-duplicates. Leaving this as a follow-up rather
than speccing it here — the current one-row-per-entry layout is a correct
starting point either way.

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
- `crossword/tests/test_puzzle_use_cases.py`:
  - **`test_copy_skips_write_when_state_unchanged`
    ([test_puzzle_use_cases.py:835-840](../../crossword/tests/test_puzzle_use_cases.py#L835-L840))
    needs to be replaced, not just tweaked.** It currently asserts that
    saving a `finished` puzzle again does *not* call `set_puzzle_state` —
    that was the de-duplication behavior this doc removes. The new test
    should assert the opposite: a repeat save at the same ladder state
    still calls `set_puzzle_state` (so a fresh content snapshot is taken),
    with the same `state` value as before.
  - New test: after a puzzle is `submitted`, saving it again calls
    `set_puzzle_state` with `state`, `publisher`, `date_submitted`, and
    `date_published` all carried forward unchanged from the current row —
    i.e. the three `test_copy_does_not_touch_state_once_*` tests added in
    `df49739` need updating too, since "does not touch state" no longer
    means "does not call `set_puzzle_state` at all" — it now means "calls
    it with the same state/publisher/dates as before."
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
2. **How far back should snapshots be kept?** Unlike the original
   state-only design, this one writes a row on every save, so the table
   will grow roughly in step with how often a puzzle is worked on and
   saved — not just how many times it changed lifecycle state. No pruning
   is proposed in this doc: puzzle JSON is small enough that even a puzzle
   saved a few hundred times is a modest amount of data, and deleting old
   snapshots is the one thing that can't be undone. Recommended: ship
   without pruning, watch actual database growth in practice, and revisit
   with a real retention policy (e.g. "keep every row for 90 days, then
   only one per day") only if it turns out to matter.
3. **Should the history popup show every save, or just state changes?**
   Flagged above under Frontend — a first version can simply list every
   row and let it be long; collapsing consecutive same-state rows is a
   presentation improvement that can follow once this is in use and it's
   clear whether the length is actually a problem.
