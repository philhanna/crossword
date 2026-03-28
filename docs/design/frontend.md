# Frontend

The frontend is a plain-JavaScript single-page application (SPA). There is no framework — no React, Vue, or Angular.

## Files

- `frontend/index.html` — single HTML page; all markup is here
- `frontend/static/js/app.js` — all application logic (~1400 lines)
- `frontend/static/css/style.css` — styles
- `frontend/static/images/mozart-crossword.png` — header logo

The server serves these files directly. `app.js` is loaded at the bottom of `index.html` as a plain `<script>` tag.

## Layout

The page has three regions:

- **Header** — logo + title
- **Menu bar** — Grid / Puzzle / Publish dropdown menus + Help link (top right)
- **Main content** — two side-by-side cells:
  - `#lhs` (45%) — grid or puzzle SVG
  - `#rhs` (55%) — clue lists, word editor, or stats panel

Everything in `#lhs` and `#rhs` is replaced via `innerHTML` on every view transition.

## Application State

A single global object `AppState` holds all runtime state:

```js
const AppState = {
    view: 'home',            // 'home' | 'grid-editor' | 'puzzle-editor'
    gridOriginalName: null,  // name of the saved grid
    gridWorkingName: null,   // working copy name, e.g. '__wc__a1b2c3d4'
    gridData: null,          // { size, cells[], can_undo, can_redo }
    gridSavedHash: null,     // hash of cells[] at last open/save (dirty check)
    puzzleName: null,
    puzzleWorkingName: null,
    puzzleData: null,        // full GET /api/puzzles/{wn} response
    puzzleSavedHash: null,
    editingWord: null,       // { seq, direction, cells, answer, clue } | null
    showingStats: false,
    showingGridStats: false,
    _gridStatsData: null,
    _statsData: null,
};
```

Dirty-checking uses a djb2 hash (`_hash()`) over `JSON.stringify` of the relevant data.

## Three-State View Machine

`showView(view)` drives the entire UI. It sets `AppState.view`, calls `updateMenu()`, clears both panels, then calls the appropriate render function:

| State | LHS | RHS |
|---|---|---|
| `home` | "Use the Grid or Puzzle menu…" | empty |
| `grid-editor` | SVG grid + toolbar | stats panel (optional) |
| `puzzle-editor` | SVG puzzle + toolbar | clue lists / word editor / stats panel |

## Menu Enable/Disable

`updateMenu()` is called on every view transition. Rules:

| Menu item | Enabled in |
|---|---|
| Grid > New / New from puzzle / Open | `home` |
| Grid > Save / Save As / Close / Delete | `grid-editor` |
| Puzzle > New / Open | `home` |
| Puzzle > Save / Save As / Close / Delete | `puzzle-editor` |
| Publish > all three formats | always |

Items are toggled with `w3-disabled` CSS class.

## Notifications And Dialogs

A permanent message line and three permanent modals are declared in `index.html`.

- **`#ml` — Message line** (`showMessageLine(text, level, timeoutMs)` / `clearMessageLine()`) — single-line notification strip shown below the menu bar. `level` is `notice` or `error`; notice renders green and error renders red. This is used for passive status messages that do not require any user action.

Three permanent modals are shown/hidden via `display:block/none`:

- **`#mb` — Message box** (`messageBox(title, prompt, ok, okCallback)`) — shows a message with OK/Cancel. OK can be a URL link or a callback.
- **`#ib` — Input box** (`inputBox(title, label, value, onSubmit)`) — prompts for a text string; submits via form `onsubmit`.
- **`#ch` — Chooser** (`showChooser` / `showPreviewChooser`) — scrollable list of items to pick from. `showPreviewChooser` fetches `GET /api/puzzles/{name}/preview` for puzzle choosers and renders SVG thumbnails alongside each name.

The modal message box is now reserved for confirmations and flows where the user must explicitly respond before the app proceeds.

## SVG Rendering

Both grid and puzzle SVGs are built client-side from API data (no server-rendered SVG in the editor).

**Grid SVG** (`buildGridSvg(cells, n)`):
- `cells` is a flat bool array (`true` = black cell), row-major, 0-indexed
- Calls `computeGridNumbers(cells, n)` to assign sequence numbers (standard crossword numbering rules)
- Draws one `<rect>` per cell (black or white), then small `<text>` for sequence numbers, then a bold outer border

**Puzzle SVG** (`buildPuzzleSvg(puzzleData)`):
- `puzzleData.grid.cells` — same bool array for black cells
- `puzzleData.puzzle.cells` — object keyed by flat index, each entry has optional `number` and `letter`
- Draws rects + sequence number texts + centered letter texts

Both SVGs use `BOXSIZE = 32` pixels per cell.

## Merged Editor

Rendered by `renderPuzzleEditor()`, which calls `renderPuzzleEditorLhs()` + `renderPuzzleEditorRhs()`.

The editor has two modes:

- **Grid mode** — edits black cells through puzzle endpoints
- **Puzzle mode** — edits answers and clues against the same working puzzle

**Toolbar actions** (LHS):
- **Mode switch** — toggles between Grid mode and Puzzle mode
- **Save / Save As / Close** — same working copy pattern for the working puzzle
- **Title** — `PUT /api/puzzles/{wn}/title`
- **Info** — fetches stats and toggles the stats panel on RHS
- **Undo / Redo** — `POST /api/puzzles/{wn}/undo` and `/redo` in Puzzle mode, `POST /api/puzzles/{wn}/grid/undo` and `/redo` in Grid mode
- **Rotate** — in Grid mode only, `POST /api/puzzles/{wn}/grid/rotate`

**Grid-mode click handling**
- Converts click coordinates to `(row, col)` using `BOXSIZE`
- Calls `PUT /api/puzzles/{wn}/grid/cells/{r}/{c}` to toggle the cell
- Re-renders the shared puzzle SVG in place
- If stats are visible, refreshes them after the edit

**Click handling** — single-click = across word, double-click = down word (280 ms timer). `puzzleClickAt()` calls `findWordAtCell()` to locate the word from `puzzleData.puzzle.words`, then calls `openWordEditor(seq, direction)`.

**RHS content** is mutually exclusive:
1. Grid-mode guidance / stats panel (Grid mode)
2. Word editor panel (Puzzle mode when `editingWord` is set)
3. Stats panel (Puzzle mode when `showingStats` is true)
4. Clue lists (Puzzle mode default)

**Clue lists** — two columns (Across / Down), each a clickable `<ul>`. Clicking the clue text selects the word; clicking `edit` opens the word editor.

## Word Editor Panel

Opened by `openWordEditor(seq, direction)`, which fetches `GET /api/puzzles/{wn}/words/{seq}/{dir}` to load current text/clue.

Three tabs:

**Suggest tab** — `doWordSuggest()`
- Takes the current value of the Word input as the pattern (`.` or `?` = wildcard)
- Calls `GET /api/words/suggestions?pattern=...`
- Populates a `<select>` with results; selecting a word fills the Word input

**Constraints tab** — `doWordConstraints()`
- Calls `GET /api/puzzles/{wn}/words/{seq}/{dir}/constraints`
- Renders a table: one row per letter position showing the crossing word, which letter index it intersects, valid-letter regexp, and number of dictionary matches
- Shows an "Overall pattern" input with a "Suggest ›" button that passes the combined pattern directly to the Suggest tab (`doFastpath()`)

**Reset tab** — `doWordReset()`
- Calls `POST /api/puzzles/{wn}/words/{seq}/{dir}/reset`
- Clears letters not shared with fully-completed crossing words

**OK button** — `doWordEditOK()`
- Validates characters (A–Z, space, dot)
- Pads/trims text to exact word length; dots are treated as blanks
- Calls `PUT /api/puzzles/{wn}/words/{seq}/{dir}` with `{ text, clue }`
- On success: updates `puzzleData`, closes the word editor, re-renders the full puzzle editor

## Publish

`do_publish(format)` — format is `'puz'` (Across Lite), `'xml'` (Crossword Compiler), or `'nyt'` (New York Times).

- If a puzzle is currently open in the editor, publishes that puzzle directly
- Otherwise, shows a preview chooser to pick a puzzle

`_downloadExport(name, format)` fetches the export endpoint and triggers a browser download by creating a temporary `<a>` element with `download` attribute.

## Example: End-to-End Interaction Flow

Tracing **clicking a clue in the clue list** — one of the most complete flows in the app.

### 1. User clicks a clue

`renderClues()` renders each item as:

```js
`<li><a onclick="openWordEditor(${w.seq}, '${direction}')">`
```

### 2. `openWordEditor(seq, direction)`

```js
const data = await apiFetch('GET',
    `/api/puzzles/${encodeURIComponent(wn)}/words/${seq}/${direction}`);
AppState.editingWord = { seq, direction, cells, answer, clue };
renderPuzzleEditorRhs();
```

`apiFetch` calls `fetch()` with `Content-Type: application/json`.

### 3. Server handles `GET /api/puzzles/{wn}/words/{seq}/{dir}`

Routes to `handle_get_word` in `puzzle_handlers.py`, which calls `puzzle_uc.get_word(user_id, name, seq, direction)`. Returns:

```json
{ "seq": 5, "direction": "across", "cells": [[1,1],[1,2],...], "answer": "HELLO", "clue": "A greeting" }
```

### 4. Response rendered

`openWordEditor` stores the response in `AppState.editingWord`, then `renderPuzzleEditorRhs()` picks the word editor branch:

```js
if (AppState.editingWord)
    html = renderWordEditorPanel();
```

`renderWordEditorPanel()` builds the word editor HTML from `AppState.editingWord` and assigns it to `rhs.innerHTML`.

### Summary

```
click clue
  → openWordEditor(seq, dir)
    → apiFetch GET /api/puzzles/{wn}/words/{seq}/{dir}
      → puzzle_handlers.handle_get_word
        → puzzle_uc.get_word(...)
      ← JSON { seq, direction, cells, answer, clue }
    ← AppState.editingWord = data
  → renderPuzzleEditorRhs()
    → renderWordEditorPanel()
      → rhs.innerHTML = <word editor HTML>
```

## HTTP Communication

All API calls go through `apiFetch(method, path, body)` — a thin wrapper around `fetch()` that sets `Content-Type: application/json` and parses the JSON response. Errors are detected by checking `data.error` in the response body (HTTP status is not checked).

## Bootstrap

```js
document.addEventListener('DOMContentLoaded', () => {
    showView('home');
});
```
