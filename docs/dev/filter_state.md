# Puzzle Open Dialog — filter by puzzle state

## Goal

In the **Open puzzle** dialog, add a dropdown labeled **Puzzle state** with
these entries:

- `all`
- `draft`
- `filled`
- `finished`
- `submitted`
- `published`
- `archived`

Default it to `all`. When the user picks any non-`all` value, the dialog should
show only puzzles whose `puzzles.state` column matches that value.

## Background — how Open puzzle works today

Frontend:

- `do_puzzle_open()` in
  [frontend/static/js/puzzle-editor.js](../../frontend/static/js/puzzle-editor.js)
  fetches `GET /api/puzzles`, removes `__wc__...` names, and passes the result
  to `showPreviewChooser(...)`.
- The chooser UI itself lives in
  [frontend/index.html](../../frontend/index.html) (`#ch`) and
  [frontend/static/js/ui.js](../../frontend/static/js/ui.js)
  (`showPreviewChooser`, `_chRender`, sort/paging helpers).

Backend:

- `handle_list_puzzles()` in
  [crossword/http_server/puzzle_handlers.py](../../crossword/http_server/puzzle_handlers.py)
  calls `app.puzzle_uc.list_puzzles(user_id)` and filters out `__new__...`
  rows before returning `{"puzzles": [...]}`.
- `PuzzleUseCases.list_puzzles()` in
  [crossword/use_cases/puzzle_use_cases.py](../../crossword/use_cases/puzzle_use_cases.py)
  is currently a thin pass-through.
- `SQLitePersistenceAdapter.list_puzzles()` in
  [crossword/adapters/sqlite_persistence_adapter.py](../../crossword/adapters/sqlite_persistence_adapter.py)
  selects puzzle names ordered by `modified DESC` with no state filter.

State vocabulary already exists in
[crossword/domain/puzzle_state.py](../../crossword/domain/puzzle_state.py), and
the `puzzles` table already stores the `state` column described in
[puzzle_state.md](./puzzle_state.md).

## Design choice

Filter on the backend rather than fetching all puzzles and filtering in the
browser.

Why:

- The requested behavior is defined in terms of the database `state` column.
- The open dialog should not need extra per-puzzle state fetches.
- The server can validate the filter once and keep the API reusable for future
  state-filtered views.

## API shape

Extend `GET /api/puzzles` with an optional query parameter:

- no `state` query param, or `state=all` -> existing behavior
- `state=<one of the six real states>` -> return only puzzles in that state

So the open dialog requests:

- initial load: `GET /api/puzzles?state=all` (or plain `GET /api/puzzles`)
- filtered load: `GET /api/puzzles?state=draft`, etc.

Invalid state values should return an error in the existing handler style, e.g.
`{"error": "Invalid state: 'bogus'"}`.

## Implementation plan

### 1. Persistence port + adapter

Update `PersistencePort.list_puzzles(...)` to accept an optional state filter,
for example:

```python
def list_puzzles(self, user_id: int, state: str | None = None) -> list[str]:
```

Then update `SQLitePersistenceAdapter.list_puzzles(...)`:

- keep `ORDER BY modified DESC`
- when `state is None`, use the current query
- when `state` is provided, add `AND state = ?`

This keeps the filtering anchored directly to the `puzzles.state` column.

### 2. Use case validation

Update `PuzzleUseCases.list_puzzles(...)` to accept the same optional filter.

Behavior:

- `None` or `"all"` -> pass `None` to persistence
- one of the six valid states -> pass that state through
- anything else -> raise `ValueError`

This is the right place to centralize the user-facing vocabulary instead of
teaching the adapter what `"all"` means.

### 3. HTTP handler

Update `handle_list_puzzles()` to read `query_params.get("state")` and pass it
to `app.puzzle_uc.list_puzzles(user_id, state=...)`.

Keep the existing `__new__...` filtering in the handler, since that rule is
about hiding internal rows from the API response, not about lifecycle state.

No route change is needed; `register_routes()` already matches query strings on
`/api/puzzles`.

### 4. Open-dialog UI

Add the dropdown to the chooser dialog header area (`#ch-sort`) in
[frontend/index.html](../../frontend/index.html), labeled **Puzzle state** with
the seven requested entries and default `all`.

Then extend the chooser JS in
[frontend/static/js/ui.js](../../frontend/static/js/ui.js):

- add chooser-level state for the current puzzle-state filter
- add a small handler such as `chSetPuzzleStateFilter(value)`
- reset paging to page 0 when the filter changes
- keep the existing sort controls working unchanged

Because the chooser currently receives a fixed list of names and immediately
loads previews, the cleanest update is to let `showPreviewChooser(...)` accept
an optional reload callback for dynamic data. For the Open puzzle flow, that
callback can:

1. request `GET /api/puzzles?state=<current-filter>`
2. remove `__wc__...` rows as today
3. fetch previews for the returned names
4. re-render the chooser

Other chooser uses that do not need state filtering can continue to work with
the existing static-list behavior.

### 5. Open-puzzle flow

Update `do_puzzle_open()` in
[frontend/static/js/puzzle-editor.js](../../frontend/static/js/puzzle-editor.js)
to open the chooser in "dynamic list" mode rather than doing a one-time
`GET /api/puzzles` before the modal appears.

Desired UX:

- opening the dialog shows `Puzzle state = all`
- changing the dropdown reloads the puzzle list in-place
- if the filtered result is empty, show an empty-state message in the chooser
  instead of the current top-level "No saved puzzles found." message
- selecting a puzzle still opens it through `_openPuzzleInEditor(name)`

## Edge cases

- `all` should include puzzles whose state is any valid lifecycle state.
- Internal working copies (`__wc__...`) should remain hidden in the Open dialog,
  regardless of state.
- Internal `__new__...` rows should remain hidden by the API, regardless of
  state.
- If a filter yields zero puzzles, the dialog should stay open and say so.
- If the API returns an error for an invalid state, surface it through the
  existing message-line/error path.

## Testing

Backend:

- `crossword/tests/test_puzzle_use_cases.py`
  - `list_puzzles(..., state="all")` delegates with no adapter filter
  - `list_puzzles(..., state="draft")` delegates with `"draft"`
  - invalid state raises `ValueError`
- `crossword/tests/adapters/test_sqlite_adapter.py`
  - mixed-state rows return all puzzles with no filter
  - state filter returns only matching rows
  - ordering remains `modified DESC` within the filtered set
- `crossword/tests/test_http_server.py`
  - `handle_list_puzzles` forwards the `state` query param
  - `state=all` still works
  - invalid `state` returns an error payload
  - `__new__...` rows are still removed after filtering

Frontend/manual:

- Open dialog initially shows the new dropdown with default `all`.
- Switching from `all` to each concrete state reloads the cards and shows only
  matching puzzles.
- Empty filtered result shows a friendly empty state inside the dialog.
- Sort order and pagination still work after changing the state filter.
- Selecting a filtered puzzle still opens the editor correctly.
