# Frontend Architecture

The frontend is a **plain JavaScript SPA** (no build step, no framework). All
application logic lives in a single file (`app.js`, ~1,200 LOC).

## File Organization

```
frontend/
├── index.html
└── static/
    ├── css/
    │   └── style.css
    ├── images/
    │   └── mozart-crossword.png   # Header branding image
    └── js/
        └── app.js                 # Everything: state, rendering, API, dialogs
```

---

## Application State

A single plain object tracks all UI state:

```javascript
const AppState = {
    view: 'home',            // 'home' | 'grid-editor' | 'puzzle-editor'
    gridOriginalName: null,  // name of currently-open grid (saved copy)
    gridWorkingName:  null,  // working copy name (e.g. '__wc__a1b2c3d4')
    gridData:         null,  // { size, cells[] } from API
    puzzleName:       null,  // name of currently-open puzzle (saved copy)
    puzzleWorkingName:null,  // working copy name
    puzzleData:       null,  // response from GET /api/puzzles/{workingName}
    editingWord:      null,  // null | {seq, direction, cells, answer, clue}
    showingStats:     false, // true = RHS shows stats panel
};
```

---

## Working Copy Pattern

Every grid or puzzle is opened via a `POST .../open` call which creates a
`__wc__<uuid8>` working copy. All edits target the working copy. **Save** copies
`wc → original`; **Close** deletes the working copy. Working copies are filtered
out of chooser lists.

---

## View Management

`showView(view)` sets `AppState.view`, updates the menu, clears both panels,
then renders the new view into `#lhs` and `#rhs`:

| View | LHS | RHS |
|------|-----|-----|
| `home` | "Use the menu to get started" | (empty) |
| `grid-editor` | SVG grid + toolbar | (empty) |
| `puzzle-editor` | SVG puzzle + toolbar | Word editor OR stats OR clue lists |

---

## Menu Enable / Disable

Menu items are enabled/disabled on every `showView()` call:

| Item | home | grid-editor | puzzle-editor |
|------|------|-------------|---------------|
| Grid > New / New from Puzzle / Open | ✓ | ✗ | ✗ |
| Grid > Save / Save As / Close / Delete | ✗ | ✓ | ✗ |
| Puzzle > New / Open | ✓ | ✗ | ✗ |
| Puzzle > Save / Save As / Close / Delete | ✗ | ✗ | ✓ |
| Publish > all 3 | ✓ | ✓ | ✓ |

---

## Dialogs

Three modal dialogs are permanently rendered in `index.html` (hidden by
default). They are shown/hidden via `showElement(id)` / `hideElement(id)`.

### `#mb` — Message box
```javascript
messageBox(title, prompt, ok, okCallback)
// OK button either fires okCallback() or navigates to ok (href)
// Cancel button closes the dialog
```

### `#ib` — Input box
```javascript
inputBox(title, label, value, onSubmit)
// Shows a text input; form submit calls onSubmit(enteredValue)
```

### `#ch` — Chooser
```javascript
showChooser(title, items, onSelect)
// Simple list of clickable items

showPreviewChooser(title, names, apiPrefix, onSelect)
// Fetches GET {apiPrefix}/{name}/preview for each name in parallel
// Shows SVG thumbnails (150×150) beside the name
```

---

## API Helper

All HTTP calls go through one function:

```javascript
async function apiFetch(method, path, body)
// Returns parsed JSON. Does not throw on API errors — callers check data.error.
```

---

## SVG Rendering

Both grids and puzzles are rendered client-side as SVG strings injected into a
container `<div>`. Cell size is `BOXSIZE = 32` px.

### `buildGridSvg(cells, n)`
- `cells`: `bool[]`, true = black cell
- Computes cell numbers via `computeGridNumbers()`
- Renders black/white `<rect>` elements + number `<text>` elements
- Outer border drawn last

### `buildPuzzleSvg(puzzleData)`
- `puzzleData`: `{ grid: {size, cells[]}, puzzle: {cells: {"idx": {number?, letter?}}, words[]} }`
- Same layout as grid SVG; also renders letter `<text>` elements in white cells

---

## Grid Editor

**LHS** contains the grid SVG and a toolbar:

| Button | Action |
|--------|--------|
| Rotate | `POST /api/grids/{wn}/rotate` |
| Undo | `POST /api/grids/{wn}/undo` |
| Redo | `POST /api/grids/{wn}/redo` |
| Info | Shows size / white / black / numbered cell counts via `messageBox` |

**Click handling:** pixel coordinates → (row, col) → `PUT /api/grids/{wn}/cells/{r}/{c}` → re-render SVG in place.

---

## Puzzle Editor

### LHS
SVG puzzle + toolbar:

| Button | Action |
|--------|--------|
| Save | `do_puzzle_save()` |
| Save As | `do_puzzle_save_as()` |
| Close | `do_puzzle_close()` |
| Title | Set puzzle title via `inputBox` |
| Info | Fetch and show stats panel |
| Undo | `POST /api/puzzles/{wn}/undo` |
| Redo | `POST /api/puzzles/{wn}/redo` |

**Click handling:** single click = across word, double click = down word
(280 ms timeout disambiguates). Finds the word at (r, c) from
`AppState.puzzleData.puzzle.words`, then calls `openWordEditor(seq, direction)`.

### RHS — three possible panels

Controlled by `renderPuzzleEditorRhs()`:

1. **Word editor panel** — when `AppState.editingWord` is set
2. **Stats panel** — when `AppState.showingStats` is true
3. **Clue lists** — default; Across and Down clue lists side by side

---

## Word Editor Panel

Shown in the RHS when a word is clicked. Three tabs:

### Suggest tab
- "Suggest" button reads the **Word** input (e.g. `G[^Q]....`) and calls
  `GET /api/words/suggestions?pattern={pattern}`
- Shows match count and a `<select>` of suggestions (uppercase)
- Selecting a suggestion copies it into the Word input

### Constraints tab
- "Find constraints" button calls
  `GET /api/puzzles/{wn}/words/{seq}/{dir}/constraints`
- Shows a table of per-position crossing-word constraints
- **Overall pattern** field (editable) + "Suggest ›" button jumps to Suggest
  tab with that pattern pre-filled (`doFastpath`)

### Reset tab
- "Clear letters" button calls
  `POST /api/puzzles/{wn}/words/{seq}/{dir}/reset`
- Clears letters not shared with fully-filled crossing words

### Inputs and buttons
- **Word:** text input (monospace); dots represent blank cells
- **Clue:** text input
- **OK:** sends `PUT /api/puzzles/{wn}/words/{seq}/{dir}` with `{text, clue}`;
  text is undo-tracked server-side
- **Cancel:** closes editor without saving

---

## Stats Panel

Shown when Info toolbar button is clicked. Displays:
- Valid / Invalid status
- Errors list
- Grid size, word count, black cell count
- Word-lengths table (Across / Down breakdowns)

---

## Menu Actions

### Grid menu
| Action | Flow |
|--------|------|
| New grid | `inputBox` size → `inputBox` name → `POST /api/grids` → open in editor |
| New grid from puzzle | preview chooser (puzzles) → `inputBox` name → `POST /api/grids/from-puzzle` → open |
| Open grid | preview chooser (grids) → `POST .../open` → load wc → editor |
| Save grid | `POST .../copy {new_name}` → confirmation |
| Save grid as | `inputBox` name → `POST .../copy` |
| Close grid | delete wc → `showView('home')` |
| Delete grid | `messageBox` confirm → `DELETE` original → close |

### Puzzle menu
| Action | Flow |
|--------|------|
| New puzzle | preview chooser (grids) → `inputBox` name → `POST /api/puzzles` → open in editor |
| Open puzzle | preview chooser (puzzles) → `POST .../open` → load wc → editor |
| Save puzzle | `POST .../copy {new_name}` → confirmation |
| Save puzzle as | `inputBox` name → `POST .../copy` |
| Close puzzle | delete wc → `showView('home')` |
| Delete puzzle | confirm → `DELETE` original → close |

### Publish menu
Stub — shows an alert. Three formats: Across Lite (`.puz`), Crossword Compiler
(`.xml`), New York Times (`.nyt`).

---

## Bootstrap

```javascript
document.addEventListener('DOMContentLoaded', () => {
    showView('home');
});
```

No data is pre-fetched. Everything is loaded on demand via menu actions.

---

## Key Design Decisions

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Framework | None (vanilla JS) | No build step; lightweight; matches server simplicity |
| Single file | `app.js` only | No module bundler needed; straightforward to serve |
| SVG | Client-side rendered | Vector scales cleanly; no server round-trip for re-renders |
| Working copies | `__wc__<uuid8>` | Auto-persistence with explicit save; no accidental overwrites |
| Menu state machine | 3-state enable/disable | Clear UX — unavailable actions are visually disabled |
| Dialogs | 3 permanent modals | Reused for all prompts; no dynamic dialog creation |
| Preview chooser | Parallel fetch | Fast UX — all SVG previews load simultaneously |
