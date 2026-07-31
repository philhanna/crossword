# Require a comment on every save — design doc

## The problem this solves

Since [puzzle content snapshots](puzzle_content_snapshots.md) shipped, every
Save or Save As writes a full copy of the puzzle into
`puzzle_state_history`, and the "Show history" popup on the dashboard lists
every one of those saves. But the list is just a bare timeline right now —
a date and a state, nothing that says *why* the puzzle was saved at that
point. Looking at a puzzle worked on over dozens of sessions, there's no
way to tell "this was the version I fixed the theme in" from "this was a
random mid-edit save" without opening each one.

This doc adds a short, required comment to every Save and Save As — like a
commit message — and shows it in the history popup, so the timeline
becomes something a person can actually read back later.

## Where "save" happens today

As established when content snapshots were added, both **Save** and **Save
As** funnel through the same two functions, so there's one place to add
the requirement:

- Frontend: `do_puzzle_save()`
  ([puzzle-editor.js:1114](../../frontend/static/js/puzzle-editor.js#L1114))
  and `do_puzzle_save_as()` → `_savePuzzleAsName()`
  ([puzzle-editor.js:1160](../../frontend/static/js/puzzle-editor.js#L1160),
  [puzzle-editor.js:1137](../../frontend/static/js/puzzle-editor.js#L1137))
  both call `POST /api/puzzles/<name>/copy` with `{ new_name }`.
- Backend: `handle_copy_puzzle`
  ([puzzle_handlers.py:848](../../crossword/http_server/puzzle_handlers.py#L848))
  calls `PuzzleUseCases.copy_puzzle()`
  ([puzzle_use_cases.py:139](../../crossword/use_cases/puzzle_use_cases.py#L139)),
  which saves the new content and then calls `_auto_set_state_on_save()`
  ([puzzle_use_cases.py:167](../../crossword/use_cases/puzzle_use_cases.py#L167)),
  the method that writes the `puzzle_state_history` row.

A brand-new puzzle's very first Save also goes through this same path:
`do_puzzle_save()` falls back to `do_puzzle_save_as()` whenever
`AppState.puzzleName` is still empty
([puzzle-editor.js:1117](../../frontend/static/js/puzzle-editor.js#L1117)).
So there's exactly one gate to add the comment requirement to, and every
kind of save — first save, Save, Save As — already passes through it.

**What's deliberately out of scope**, because it isn't "a save" in this
sense: `create_puzzle()`
([puzzle_use_cases.py:65](../../crossword/use_cases/puzzle_use_cases.py#L65))
writes the very first history row when a puzzle is created (before the
user has typed anything), and the state-transition dialog ("Mark as
submitted", etc.) calls `PuzzleUseCases.set_puzzle_state()`
([puzzle_use_cases.py:236](../../crossword/use_cases/puzzle_use_cases.py#L236))
directly. Both of those call `persistence.set_puzzle_state()` too, so both
also produce a `puzzle_state_history` row — but neither is triggered by the
Save/Save As buttons, and requiring a comment there would mean prompting
for one on puzzle creation and on every state change, which the request
doesn't ask for. Their rows simply get `comment = NULL`, the same way rows
written before this feature existed have `content = NULL` today.

## Schema change

Add one nullable column, the same way `content` was added:

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
    comment         TEXT,
    changed_at      TEXT NOT NULL
)
```

It's nullable for the same reason `content` is: existing rows, and rows
written by `create_puzzle`/`set_puzzle_state`, have nothing to put there.
Only rows written through `copy_puzzle` will always have one, because that
path will refuse to write a row without it.

## Adapter and port change

`set_puzzle_state()`
([sqlite_persistence_adapter.py:210](../../crossword/adapters/sqlite_persistence_adapter.py#L210))
gains an optional `comment` keyword, stored exactly like `publisher` is
today — passed straight through, `NULL` if not given:

```python
def set_puzzle_state(self, user_id: int, name: str, state: str, *,
                     publisher: str | None = None,
                     date_submitted: str | None = None,
                     date_published: str | None = None,
                     comment: str | None = None) -> None:
    ...
    cursor.execute(
        """INSERT INTO puzzle_state_history
                (puzzle_id, state, publisher, date_submitted, date_published,
                 content, comment, changed_at)
            SELECT id, ?, ?, ?, ?, jsonstr, ?, ? FROM puzzles WHERE userid = ? AND puzzlename = ?""",
        (state, publisher, date_submitted, date_published, comment, now, user_id, name),
    )
```

`get_puzzle_state_history()`
([sqlite_persistence_adapter.py:263](../../crossword/adapters/sqlite_persistence_adapter.py#L263))
adds `h.comment` to the `SELECT` and to each returned dict, alongside the
existing `state`/`publisher`/`changed_at` fields. `get_puzzle_state()`
(the "just the latest row" reader used to check current state) doesn't
need it — nothing reads a comment off the *current* state, only off the
history list.

`PersistencePort.set_puzzle_state()`
([persistence_port.py:82](../../crossword/ports/persistence_port.py#L82))
and `get_puzzle_state_history()`
([persistence_port.py:121](../../crossword/ports/persistence_port.py#L121))
get the matching optional parameter and returned key in their abstract
signatures and docstrings.

## Use-case change: `copy_puzzle` requires a non-empty comment

```python
def copy_puzzle(self, user_id: int, source_name: str, new_name: str, comment: str) -> Puzzle:
    if not new_name or not new_name.strip():
        raise ValueError("new_name must not be empty")
    if not comment or not comment.strip():
        raise ValueError("comment must not be empty")
    validate_public_name("puzzle", new_name)
    puzzle = self.persistence.load_puzzle(user_id, source_name)
    ...
    self.persistence.save_puzzle(user_id, new_name, puzzle)
    self._auto_set_state_on_save(user_id, new_name, puzzle, comment=comment)
    return puzzle
```

`_auto_set_state_on_save()`
([puzzle_use_cases.py:167](../../crossword/use_cases/puzzle_use_cases.py#L167))
takes the same `comment` and forwards it to
`persistence.set_puzzle_state(..., comment=comment)` on both branches (the
still-on-the-ladder branch and the past-the-ladder carry-forward branch) —
it's new content for the row being written either way, not something
carried forward from the previous row the way `publisher`/dates are once a
puzzle is past the ladder. Each save gets its own comment; it doesn't
inherit the last one.

This mirrors the existing `new_name` check right above it — same shape,
same "reject before touching anything" placement, same `ValueError`
pattern used everywhere else in this file.

## HTTP layer

`POST /api/puzzles/<name>/copy`'s body gains a required `comment` field,
validated the same way `new_name` already is in the handler, before the
use case is even called:

```python
def handle_copy_puzzle(...):
    ...
    new_name = body_params.get("new_name")
    if not new_name or not isinstance(new_name, str):
        return {"error": "Missing or invalid 'new_name'"}

    comment = body_params.get("comment")
    if not comment or not isinstance(comment, str) or not comment.strip():
        return {"error": "Missing or invalid 'comment'"}

    user_id = current_user["id"]
    puzzle = app.puzzle_uc.copy_puzzle(user_id, name, new_name, comment)
    ...
```

(`handle_copy_puzzle` is at
[puzzle_handlers.py:848](../../crossword/http_server/puzzle_handlers.py#L848).)
The use case's own check stays too — same double-checked pattern the
handler already uses for `new_name`, so the use case is safe to call
directly (from tests, from any future caller) without relying on the HTTP
layer to have validated first.

`GET /api/puzzles/<name>/state/history`'s response is unchanged in shape
except each entry gains a `comment` field (string or `null`) — it already
passes the use case's dicts straight through, so no handler change is
needed there.

## Frontend

**Save** (`do_puzzle_save()`,
[puzzle-editor.js:1114](../../frontend/static/js/puzzle-editor.js#L1114)):
prompt for a comment with the existing `inputBox()` helper
([ui.js:104](../../frontend/static/js/ui.js#L104)), which already supports
a `required` option that blocks submission client-side while empty —
exactly what's needed here, no new modal:

```javascript
async function do_puzzle_save() {
    const wn   = AppState.puzzleWorkingName;
    const name = AppState.puzzleName;
    if (!name) { do_puzzle_save_as(); return; }
    inputBox('Save puzzle', 'What changed?', '', async (comment) => {
        try {
            await _settlePuzzleEditingBeforeSave();
            const data = await apiFetch('POST',
                `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: name, comment });
            if (data.error) { showMessageLine(`Save failed: ${data.error}`, 'error', 0); return; }
            AppState.puzzleSavedHash = _hash(AppState.puzzleData.puzzle);
            renderPuzzleEditor();
            showMessageLine(`Puzzle ${name} saved.`, 'notice');
        } catch (e) { showMessageLine('Error saving puzzle', 'error', 0); }
    });
}
```

Cancelling the prompt (the dialog's Cancel/close button) just closes it
without calling the callback — the same as cancelling any other
`inputBox()` today — so nothing is saved and no comment is required for a
save the user backs out of.

**Save As** (`do_puzzle_save_as()`,
[puzzle-editor.js:1160](../../frontend/static/js/puzzle-editor.js#L1160)):
already prompts for a name with `inputBox()`. Since it needs two fields
now, switch it to `multiInputBox()`
([ui.js:129](../../frontend/static/js/ui.js#L129)), which works the same
way but takes a list of fields and gives back a `{name: value}` object —
each field defaults to `required: true`, so both name and comment are
enforced the same way:

```javascript
async function do_puzzle_save_as() {
    multiInputBox('Save puzzle as', [
        { name: 'newName', label: 'Puzzle name:', value: AppState.puzzleName || '' },
        { name: 'comment',  label: 'What changed?', value: '' },
    ], async ({ newName, comment }) => {
        if (!validateUserFacingName('puzzle', newName)) return;
        try {
            await _settlePuzzleEditingBeforeSave();
            await confirmOverwriteIfExists(
                'puzzle',
                newName,
                _listSavedPuzzleNames,
                () => _savePuzzleAsName(newName, comment)
            );
        } catch (e) { showMessageLine('Error saving puzzle', 'error', 0); }
    });
}
```

`_savePuzzleAsName()`
([puzzle-editor.js:1137](../../frontend/static/js/puzzle-editor.js#L1137))
gains a `comment` parameter and passes it through in the `/copy` body,
same as the `do_puzzle_save()` change above. It has exactly one caller
(itself, from `do_puzzle_save_as()`), so this is a contained change.

**History popup** (`_historyTableHtml()`,
[dashboard.js:462](../../frontend/static/js/dashboard.js#L462)): add a
"Comment" column, rendered plainly (escaped, no truncation — comments are
expected to be short, and there's no existing precedent in this table for
truncating a text field):

```javascript
function _historyTableHtml(history) {
    ...
    return `<tr>
        <td>${fmtDateTime(h.changed_at)}</td>
        <td>${escapeHtml(h.state)}</td>
        <td>${detail}</td>
        <td>${escapeHtml(h.comment || '')}</td>
        <td>${restoreCell}</td>
      </tr>`;
    ...
    return `
      <table class="dash-table">
        <thead><tr><th>Changed</th><th>State</th><th>Details</th><th>Comment</th><th></th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
}
```

Rows written before this feature (or by `create_puzzle`/state transitions)
show an empty Comment cell — same treatment as the `detail` column already
gets when there's nothing to show.

## Restoring an old version doesn't need special handling

`restore_puzzle_from_history()`
([puzzle_use_cases.py:329](../../crossword/use_cases/puzzle_use_cases.py#L329))
opens an old snapshot as a new working copy — it doesn't call
`copy_puzzle`, so it doesn't need a comment itself (restoring isn't a
save; nothing is written to history until the user acts on the restored
copy). If they then hit Save or Save As from that working copy, that goes
through the same `copy_puzzle` path as any other save and prompts for a
comment like normal — describing what changed *this* time, not repeating
whatever the restored row's original comment was.

## Migration

Same shape as
[migrate_puzzle_content_snapshots.py](../../tools/dev/migrate_puzzle_content_snapshots.py),
which already established the pattern for adding a nullable column to
`puzzle_state_history`: read the old DB read-only, write a new DB with the
updated schema, copy every row across unchanged. The one difference from
that migration is that this time `content` already exists in the source
and must be carried over too — the earlier migration left it `NULL`
because the source didn't have it yet; this one isn't dropping it.

New tool: `tools/dev/migrate_puzzle_save_comments.py`

- `SCHEMA_DDL` matches `_ensure_schema_compatibility()`
  ([sqlite_persistence_adapter.py:62](../../crossword/adapters/sqlite_persistence_adapter.py#L62))
  with `comment TEXT` added to `puzzle_state_history`.
- `fetch_history()` selects `content` in addition to the existing columns
  (`id, puzzle_id, state, publisher, date_submitted, date_published,
  content, changed_at`).
- `copy_data()` inserts all of those plus `comment`, which is always
  `NULL` — there's nothing to backfill, since no comment was ever
  collected before this feature shipped.
- Same CLI and safety rules as the existing tool: `--new-dbfile` required
  and must not already exist, `--old-dbfile` optional (defaults to the
  configured `dbfile`), `--dry-run` reports row counts without writing.
- After running, point `~/.config/crossword/config.yaml`'s `dbfile` at the
  new file, same as documented for the earlier migration.

## Tests to update

- `crossword/tests/adapters/test_sqlite_adapter.py` — `comment` column
  exists on `puzzle_state_history`; `set_puzzle_state` stores a given
  comment and defaults to `NULL` when omitted; `get_puzzle_state_history`
  returns `comment` for each row.
- `crossword/tests/test_puzzle_use_cases.py`:
  - `copy_puzzle` raises `ValueError` for an empty or whitespace-only
    comment, and never reaches `save_puzzle`/`set_puzzle_state` when it
    does.
  - `copy_puzzle` with a valid comment writes a history row whose
    `comment` matches (via `get_puzzle_state_history`).
  - `create_puzzle` and `set_puzzle_state` (state transition) still write
    rows with `comment = None` — unaffected by this change.
  - `_auto_set_state_on_save` passes `comment` through unchanged on both
    the on-the-ladder and past-the-ladder branches.
- `crossword/tests/test_http_server.py` — `handle_copy_puzzle` returns
  `{"error": ...}` (not a 500) when `comment` is missing or blank; a
  successful call passes `comment` through to
  `puzzle_uc.copy_puzzle(user_id, name, new_name, comment)`.
- New sibling test file for the migration tool, mirroring
  `test_migrate_puzzle_content_snapshots.py`: schema has `comment`;
  existing `content` values are preserved (not dropped); `comment` is
  `NULL` for every copied row; dry-run writes nothing.

## Decisions

1. **Is there a length limit on the comment? No.** No existing free-text
   field in this app (title, clues, publisher) has one, and this doesn't
   introduce one either — no client-side or server-side cap. Ship as-is;
   revisit only if long comments turn out to make the history table
   unreadable in practice.
2. **Should the comment be editable after the fact? No.** History rows
   stay append-only, consistent with everything else in
   `puzzle_state_history` (state, publisher, dates are all set once, at
   save time, and never edited post-write). No edit endpoint, no edit UI.
   If a typo needs fixing, that's a follow-up feature, not part of this
   one.
