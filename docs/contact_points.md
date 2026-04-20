# Frontend–Server Contact Points

All HTTP interactions go through `apiFetch(method, path, body?)` at [app.js:61](frontend/static/js/app.js#L61),
which JSON-encodes the body and JSON-parses the response.
Export downloads use a raw `fetch()` to stream a blob.
No authentication — single-user mode; user id is hard-coded to 1 on the server.

---

## Bootstrap

On `DOMContentLoaded`, the app calls `GET /api/config` (raw `fetch()`) to read server-configured UI
settings (currently `message_line_timeout_ms`). `showView('home')` runs unconditionally after.

---

## Puzzles — lifecycle

### Opening a puzzle

**Puzzle > Open** → `do_puzzle_open()`:
1. `GET /api/puzzles` — lists all puzzle names; filters out `__wc__` entries before showing chooser
2. `showPreviewChooser()` fires `GET /api/puzzles/{name}/preview` for each name **in parallel**
3. User picks a name → `_openPuzzleInEditor(name)`:
   - `POST /api/puzzles/{name}/open` → returns `{working_name}`
   - `GET /api/puzzles/{working_name}` → full puzzle data, stored in `AppState.puzzleData`

### Creating a new puzzle

**Puzzle > New** → `do_puzzle_new()`:
1. Prompts for grid size (must be an odd positive integer)
2. Generates an internal name `__new__<random8>`
3. `POST /api/puzzles` body `{name: "__new__…", size: n}` — creates the puzzle record
4. Calls `_openPuzzleInEditor("__new__…")` (same 2-step open flow above)
5. `AppState.puzzleName` is left `null` — the puzzle has no user-facing name yet

### Saving

**Puzzle > Save** → `do_puzzle_save()`:
- Settles any in-flight word edit first
- `POST /api/puzzles/{wn}/copy` body `{new_name: name}` — copies working copy to saved name
- If no `AppState.puzzleName` yet, delegates to Save As

**Puzzle > Save As** → `do_puzzle_save_as()`:
- Prompts for name; rejects `__wc__` prefix; checks for duplicate names
- `POST /api/puzzles/{wn}/copy` body `{new_name}` — same copy call
- If this is the first save of a `__new__` puzzle: `AppState.puzzleName` is assigned and
  `DELETE /api/puzzles/{__new__name}` cleans up the internal entry

### Setting the title

**Puzzle > Set Title** → `do_puzzle_title()`:
1. `PUT /api/puzzles/{wn}/title` body `{title}`
2. `GET /api/puzzles/{wn}` — refreshes `AppState.puzzleData` to pick up the new title

### Renaming

**Puzzle > Rename** → `do_puzzle_rename()`:
1. Prompts for new name; rejects `__wc__` prefix; lists saved names to check for conflict
2. `POST /api/puzzles/{name}/rename` body `{new_name}` — renames in place; updates `AppState`

### Closing

**Puzzle > Close** → `do_puzzle_close()`:
- Detects unsaved changes via `_hash(puzzleData.puzzle) !== puzzleSavedHash`; if dirty, shows confirm dialog
- `_doPuzzleCloseConfirmed()`:
  - `DELETE /api/puzzles/{wn}` — deletes the working copy
  - If puzzle was never saved (`AppState.puzzleName` is `null`): also `DELETE /api/puzzles/{__new__name}`
  - Returns to home view

### Deleting

**Puzzle > Delete** → `do_puzzle_delete()`:
1. `GET /api/puzzles` (filters `__` prefixes)
2. `showPreviewChooser()` — fetches previews in parallel; user picks a name
3. Confirm dialog → `DELETE /api/puzzles/{name}`
4. If the deleted puzzle is currently open, also runs `_doPuzzleCloseConfirmed()`

### Importing AcrossLite

**Import > AcrossLite** → `do_puzzle_import()`:
1. Triggers a hidden `<input type="file">` — user picks a `.txt` file
2. Prompts for a puzzle name (pre-filled from the filename)
3. Reads file content with `file.text()`
4. `POST /api/import/acrosslite` body `{name, content}`
5. On success, calls `_openPuzzleInEditor(name)`

---

## Puzzle — words

### Selecting a word (live typing)

Clicking a white cell in puzzle mode calls `selectWord(seq, dir)`, which stores
`{seq, direction, cells, initialText, currentText}` in `AppState.selectedWord`.
Keystrokes update `currentText` locally — **no API call on each keystroke**.

When the user navigates away (clicks another word, presses Escape, triggers undo/save/mode-switch, etc.),
`_peCommitWord()` fires if `currentText !== initialText`:
- `PUT /api/puzzles/{wn}/words/{seq}/{dir}` body `{text}` — saves answer; returns full puzzle data
  which replaces `AppState.puzzleData`

### Word editor

Clicking an already-selected word (or the Edit toolbar button) opens the word editor panel.

`openWordEditor(seq, dir)`:
- `GET /api/puzzles/{wn}/words/{seq}/{dir}` → `{seq, direction, cells, answer, clue}`;
  stored in `AppState.editingWord`

**OK button** / Enter key → `doWordEditOK()`:
- `PUT /api/puzzles/{wn}/words/{seq}/{dir}` body `{text, clue}` — saves answer and clue together;
  returns full puzzle data

### Word suggestions

The pattern is taken live from the answer text field (spaces → `.`).

- **Constrained** (default checkbox): `_fetchConstrainedSuggestions()` →
  `GET /api/puzzles/{wn}/words/{seq}/{dir}/suggestions?pattern=`
  Returns `[{word, score}]` ranked by crossing-letter compatibility; scores render as bar-chart sparklines.
- **Unconstrained** (checkbox off): `_fetchPatternSuggestions()` →
  `GET /api/words/suggestions?pattern=`
  Returns a plain string list. No score bars.

Results are paginated in the UI; clicking a suggestion copies it into the answer field.

### Constraints popup

Constraints tab button → `doWordConstraints()`:
- `GET /api/puzzles/{wn}/words/{seq}/{dir}/constraints`
- Returns `{pattern, crossers[]}` — rendered as a table of per-position crosser data in a popup

### Definitions popup

Definitions tab button → `doWordDefinitions()`:
- `GET /api/words/{word}/definitions` — uses the current text-field value as the word
- Returns `{entries[]}` — rendered as POS groups in a popup

---

## Puzzle — grid mode

**Puzzle > Modify Grid** shows a confirmation dialog. `_switchToGridModeConfirmed()`:
- Settles any pending word edit first
- `POST /api/puzzles/{wn}/mode/grid` — switches working copy to grid-edit mode; returns updated data

While in grid mode:

| User action | Call | Notes |
|---|---|---|
| Click a cell | `PUT /api/puzzles/{wn}/grid/cells/{r}/{c}` | Toggles black/white; returns full data |
| Rotate toolbar button | `POST /api/puzzles/{wn}/grid/rotate` | |
| Generate toolbar button | `POST /api/puzzles/{wn}/grid/generate` | Button disabled while in flight |
| Undo toolbar button | `POST /api/puzzles/{wn}/grid/undo` | |
| Redo toolbar button | `POST /api/puzzles/{wn}/grid/redo` | |

After any grid-mode mutation `AppState.gridStructureChanged = true`; stats and fill-order panels
auto-refresh if visible.

**Puzzle > Return to Puzzle Mode** → `do_switch_to_puzzle_mode()`:
- `POST /api/puzzles/{wn}/mode/puzzle` — recomputes entries; returns updated data
- If `gridStructureChanged` was `true`, shows a notice about recomputed entries and cleared clues

Undo/Redo in puzzle mode (toolbar buttons):
- Commits the selected word first via `_peCommitWord()`
- `POST /api/puzzles/{wn}/undo` or `POST /api/puzzles/{wn}/redo`

---

## Puzzle — stats and fill order

**Stats panel** → `do_puzzle_stats()`:
- Settles any pending word edit, then `GET /api/puzzles/{wn}/stats`
- Result cached in `AppState._statsData`; auto-refreshed (`_refreshPuzzleStatsIfVisible()`) after
  every grid-mode mutation

**Fill Order panel** → `do_puzzle_fill_order()`:
- `GET /api/puzzles/{wn}/fill-order`
- Result cached in `AppState._fillOrderData`; auto-refreshed after every grid-mode mutation
- Clicking a row in the fill-order table opens the word editor for that slot

---

## Export

**Publish > …** → `do_export(format)`:
- If a puzzle is open **and** saved (`AppState.puzzleName` set): uses that name directly
- Otherwise: `GET /api/puzzles` + preview chooser to let the user pick a puzzle

`_downloadExport(name, format)` uses raw `fetch()` (bypasses `apiFetch`) to receive a binary blob:

| Menu item | format arg | API path | Downloaded as |
|---|---|---|---|
| Publish > AcrossLite | `puz` | `GET /api/export/puzzles/{name}/acrosslite` | `acrosslite-{name}.txt` |
| Publish > CW Compiler | `xml` | `GET /api/export/puzzles/{name}/xml` | `{name}.xml` |
| Publish > NYT | `nyt` | `GET /api/export/puzzles/{name}/nytimes` | `nytimes-{name}.pdf` |
| Publish > Solver PDF | `solver` | `GET /api/export/puzzles/{name}/solver-pdf` | `{name}-solver.pdf` |

The blob is downloaded via a temporary `<a download>` element injected into and removed from the DOM.
`GET /api/export/puzzles/{name}/json` exists on the server but is not wired to a menu item.
