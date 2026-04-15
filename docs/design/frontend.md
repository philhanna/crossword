# Frontend

The frontend is a plain-JavaScript single-page application (SPA). There is no framework — no React, Vue, or Angular.

## Files

- `frontend/index.html` — single HTML page; all markup is here
- `frontend/static/js/app.js` — all application logic (~1806 lines)
- `frontend/static/css/style.css` — styles
- `frontend/static/images/mozart-crossword.png` — header logo

The server serves these files directly. `app.js` is loaded at the bottom of `index.html` as a plain `<script>` tag.

## Layout

The page has three regions:

- **Header** — logo + title
- **Menu bar** — Puzzle / Import / Export dropdown menus + username display + Logout link + Help link (top right)
- **Main content** — two side-by-side cells:
  - `#lhs` (45%) — puzzle SVG + toolbar
  - `#rhs` (55%) — clue lists, word editor, or stats panel

Everything in `#lhs` and `#rhs` is replaced via `innerHTML` on every view transition.

In the `home` view, `#lhs` shows a brief prompt to use the Puzzle menu.

## Application State

A single global object `AppState` holds all runtime state:

```js
const AppState = {
    view: 'home',              // 'home' | 'editor'
    puzzleName: null,          // name of currently-open puzzle (original)
    puzzleWorkingName: null,   // working copy name (e.g. '__wc__a1b2c3d4')
    puzzleData: null,          // response from GET /api/puzzles/{workingName}
    puzzleSavedHash: null,     // checksum of puzzle at last open/save
    editingWord: null,         // null | {seq, direction, cells, answer, clue}
    selectedWord: null,        // null | {seq, direction, cells, initialText, currentText}
    showingStats: false,       // true = RHS shows stats panel
    _statsData: null,          // cached puzzle stats response
    gridStructureChanged: false, // true after Grid-mode edits until user returns to Puzzle mode
};
```

Dirty-checking uses a djb2 hash (`_hash()`) over `JSON.stringify` of the relevant data.

## Two-State View Machine

`showView(view)` drives the entire UI. It sets `AppState.view`, calls `updateMenu()`, clears both panels, then calls the appropriate render function:

| State | LHS | RHS |
|---|---|---|
| `home` | "Use the Puzzle menu…" prompt | empty |
| `editor` | Puzzle SVG + toolbar | clue lists / word editor / stats panel |

The editor is a single unified view for both Grid mode and Puzzle mode (there is no separate `grid-editor` state).

## Menu Enable/Disable

`updateMenu()` is called on every view transition. Rules:

| Menu item | Enabled when |
|---|---|
| Puzzle > New | `home` |
| Puzzle > Open | `home` |
| Puzzle > Save | `editor` |
| Puzzle > Save As | `editor` |
| Puzzle > Close | `editor` |
| Puzzle > Delete | always |
| Puzzle > Title | `editor` + Puzzle mode |
| Puzzle > Grid mode | `editor` + currently in Puzzle mode |
| Puzzle > Puzzle mode | `editor` + currently in Grid mode |
| Import > AcrossLite | `home` |
| Export > all three formats | always |

Items are toggled with `w3-disabled` CSS class.

## Notifications And Dialogs

A permanent message line and three permanent modals are declared in `index.html`.

- **`#ml` — Message line** (`showMessageLine(text, level, timeoutMs)` / `clearMessageLine()`) — fixed-position strip shown below the menu bar. `level` is `notice` (green) or `error` (red). Auto-dismisses after `MESSAGE_LINE_TIMEOUT_MS` (3 s). Has a manual close button. Used for passive status messages that do not require user action.

Three permanent modals are shown/hidden via `display:block/none`:

- **`#mb` — Message box** (`messageBox(title, prompt, ok, okCallback, okLabel)`) — shows a message with OK/Cancel. OK can be a URL link or a callback. Reserved for confirmations where the user must respond before the app proceeds.
- **`#ib` — Input box** (`inputBox(title, label, value, onSubmit)`) — prompts for a text string; submits via form `onsubmit`.
- **`#ch` — Chooser** (`showChooser` / `showPreviewChooser`) — scrollable list of items to pick from. `showPreviewChooser` fetches `GET /api/puzzles/{name}/preview` for each item, renders SVG thumbnails alongside each name.

## SVG Rendering

Both grid-only and puzzle SVGs are built client-side from API data.

**Grid SVG** (`buildGridSvg(cells, n)`) — used only in the preview chooser path indirectly (puzzles always use `buildPuzzleSvg`):
- `cells` is a flat bool array (`true` = black cell), row-major, 0-indexed
- Calls `computeGridNumbers(cells, n)` to assign sequence numbers (standard crossword numbering rules)
- Draws one `<rect>` per cell, small `<text>` for sequence numbers, bold outer border

**Puzzle SVG** (`buildPuzzleSvg(puzzleData, editState = null)`):
- `puzzleData.grid.cells` — flat bool array for black cells
- `puzzleData.puzzle.cells` — object keyed by flat index, each entry has optional `number` and `letter`
- Optional `editState` — `{cells, cursorIdx, text}` used to highlight the selected/editing word and draw a cursor indicator
  - Word cells are tinted `#c8e6fa` (light blue)
  - Cursor cell gets a bold blue inner border
  - Letters from `editState.text` override `puzzleData` letters for word cells

Both SVGs use `BOXSIZE = 32` pixels per cell.

## Puzzle Editor

Rendered by `renderPuzzleEditor()`, which calls `renderPuzzleEditorLhs()` + `renderPuzzleEditorRhs()`. The editor supports two sub-modes tracked via `puzzleData.mode`:

- **Puzzle mode** — editing answers and clues; keyboard entry active
- **Grid mode** — editing black cells; keyboard entry inactive

### Toolbar actions (LHS)

**Grid mode toolbar:** Save, Close, Undo, Redo, Rotate, Info

**Puzzle mode toolbar:** Save, Close, Undo, Redo, Edit word, Info

- **Save / Close** — same as Puzzle menu items
- **Undo / Redo** — `POST /api/puzzles/{wn}/grid/undo` / `/redo` in Grid mode; `POST /api/puzzles/{wn}/undo` / `/redo` in Puzzle mode. Buttons are disabled when the respective `can_undo` / `can_redo` flag is false in `puzzleData`.
- **Rotate** — Grid mode only; `POST /api/puzzles/{wn}/grid/rotate`
- **Edit word** — Puzzle mode only; opens word editor for the currently selected word. Disabled when no word is selected or the word editor is already open.
- **Info** — fetches `GET /api/puzzles/{wn}/stats` and toggles the stats panel on RHS

### Grid-mode click handling

- Converts click coordinates to `(row, col)` using `BOXSIZE`
- Calls `PUT /api/puzzles/{wn}/grid/cells/{r}/{c}` to toggle the cell
- Re-renders the shared puzzle SVG in place
- Refreshes stats if the stats panel is visible

### Puzzle-mode click handling

Single-click = select across word; double-click = select down word (280 ms timer via `CLICK_DELAY`). If the word editor is open, any click closes it without selecting a new word.

`puzzleClickAt(event, direction)` → `findWordAtCell(r, c, direction)` → `selectWord(seq, direction, clickR, clickC)`

`selectWord()` stores the selected word in `AppState.selectedWord`, positions the cursor (`_peCursorIdx`) at the clicked cell or first blank, and re-renders both panels.

### RHS content (mutually exclusive)

1. Stats panel — when `showingStats` is true
2. Word editor panel — when `editingWord` is set (Puzzle mode)
3. Clue lists — default in Puzzle mode (no word editor open)
4. Grid-mode guidance — empty `div` in Grid mode (stats panel replaces it when Info is active)

### Clue lists

Two columns (Across / Down), each a clickable `<ul>` (`w3-pale-yellow` / `w3-pale-green`). Clicking the clue text calls `selectWord(seq, direction)`. An `edit` link calls `do_puzzle_edit_word(seq, direction)` which opens the word editor. The currently selected word is highlighted (`w3-blue-gray`).

## Direct Keyboard Entry (Puzzle mode)

When no modal or word editor is open and Puzzle mode is active, `_peKeydown` handles keystrokes globally:

| Key | Action |
|---|---|
| Letter (A–Z) | Write letter at cursor, advance cursor |
| Space | Write blank at cursor, advance cursor |
| Backspace | Clear current cell (if filled) or move cursor back and clear |
| Delete | Clear current cell without moving cursor |
| Arrow (along word direction) | Move cursor within word |
| Arrow (perpendicular) | Switch to crossing word at current cell |
| Tab / Shift+Tab | Cycle to next / previous word |
| Escape | Commit pending text changes (`_peCommitWord`) and deselect word |

Text changes are buffered in `selectedWord.currentText` and committed to the server via `PUT /api/puzzles/{wn}/words/{seq}/{dir}` (with `{text}` only) when the user moves to another word, opens the word editor, saves, or closes.

## Word Editor Panel

Opened by `openWordEditor(seq, direction)`, which fetches `GET /api/puzzles/{wn}/words/{seq}/{dir}` to load current text/clue. While open, `_peKeydown` is suspended and `_weKeydown` is active instead.

The panel contains:

- **Word input** (`#we-text`) — monospace, uppercase, dots represent blanks; Enter triggers Suggest
- **Clue input** (`#we-clue`) — free text; blur writes to `AppState.editingWord.clue`
- **Suggest button** + **Use constraints checkbox** — triggers `doWordSuggestFetch()`
  - If "Use constraints" is checked: `GET /api/puzzles/{wn}/words/{seq}/{dir}/suggestions?pattern=…` — returns `{word, score}[]` ranked by crossword-fitness
  - If unchecked: `GET /api/words/suggestions?pattern=…` — returns plain string[]
  - Results shown in a paginated `<ul>` (20 items per page); clicking a word fills `#we-text`
  - Score bars visualize relative fitness when constrained suggestions are shown
- **OK button** — `doWordEditOK()`: pads/trims text to exact word length, calls `PUT /api/puzzles/{wn}/words/{seq}/{dir}` with `{text, clue}`, updates `puzzleData`, closes editor, syncs `selectedWord.currentText`
- **Cancel button / × button / Escape** — `closeWordEditor()`: discards pending word-input changes, restores `_peKeydown`
- **Show constraints button** (`doWordConstraints()`) — toggles a constraints table below. Calls `GET /api/puzzles/{wn}/words/{seq}/{dir}/constraints`. Shows columns: Pos, Letter, Location, Text, Index, Regexp, Choices; and the overall pattern.
- **Reset button** (`doWordReset()`) — calls `POST /api/puzzles/{wn}/words/{seq}/{dir}/reset`, updates `#we-text` to the new (partially cleared) text

## Export

`do_export(format)` — format is `'puz'` (Across Lite), `'xml'` (Crossword Compiler), or `'nyt'` (New York Times).

- If a puzzle is open in the editor, exports it directly
- Otherwise, shows a preview chooser to pick a puzzle

`_downloadExport(name, format)` fetches the export endpoint using raw `fetch()` (not `apiFetch`), checks `resp.ok`, creates a temporary `<a>` with `download` attribute to trigger a browser download.

Export filename conventions:
- `puz` → `acrosslite-{name}.txt`
- `xml` → `{name}.xml`
- `nyt` → `nytimes-{name}.pdf`

## Import AcrossLite

`do_puzzle_import()` — opens a hidden `<input type="file" accept=".txt">`, pre-populates the puzzle name from the filename, prompts the user to confirm the name, then calls `POST /api/import/acrosslite` with `{name, content}`. On success, opens the imported puzzle in the editor.

## HTTP Communication

All API calls go through `apiFetch(method, path, body)` — a thin wrapper around `fetch()` that:
- Sets `Content-Type: application/json`
- Parses JSON response
- Redirects to `/login` on HTTP 401

Errors are detected by checking `data.error` in the response body. HTTP status codes other than 401 are not checked (the exception is `_downloadExport`, which checks `resp.ok` directly).

## Bootstrap

```js
document.addEventListener('DOMContentLoaded', async () => {
    const resp = await fetch('/api/auth/me');
    if (resp.status === 401) { window.location.href = '/login'; return; }
    const user = await resp.json();
    // display username in menu bar
    positionMessageLine();
    window.addEventListener('scroll', positionMessageLine, { passive: true });
    window.addEventListener('resize', positionMessageLine);
    showView('home');
});
```

`positionMessageLine()` pins `#ml` just below the menu bar using `getBoundingClientRect`, and is re-called on scroll and resize.

## Example: End-to-End Interaction Flow

Tracing **clicking a clue in the clue list** — one of the most complete flows in the app.

### 1. User clicks a clue

`renderClues()` renders each item as:

```js
`<a onclick="selectWord(${w.seq}, '${direction}');return false;">`
```

### 2. `selectWord(seq, direction)`

Sets `AppState.selectedWord`, advances `_peCursorIdx` to the first blank cell, re-renders LHS (puzzle SVG with highlight) and RHS (clue lists with the selected item highlighted).

No network call is made on selection; the puzzle data already contains the word's cells.

### 3. User presses an arrow key or types a letter

`_peKeydown` handles the keystroke. Letters accumulate in `selectedWord.currentText` (client-side only).

### 4. User moves to a different word (Tab / click elsewhere)

`_peCommitWord()` is called: if `currentText !== initialText`, sends `PUT /api/puzzles/{wn}/words/{seq}/{dir}` with `{text}`, updates `AppState.puzzleData`, re-renders the SVG to show the new letters.

### Summary

```
click clue
  → selectWord(seq, dir)
    → AppState.selectedWord = { seq, dir, cells, initialText, currentText }
    → renderPuzzleEditorLhs()  [SVG re-drawn with highlight]
    → renderPuzzleEditorRhs()  [clue list re-rendered with selection]

type letters
  → _peKeydown → sw.currentText updated locally → renderPuzzleEditorLhs()

Tab / click new word
  → _peCommitWord()
    → apiFetch PUT /api/puzzles/{wn}/words/{seq}/{dir}  { text }
    ← updated puzzleData
  → selectWord(new seq, new dir)
```
