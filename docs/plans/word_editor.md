'# Word Editor Redesign — Implementation Plan

Design spec: `~/Desktop/newai.md`

---

## Phase 1 — Restructure the RHS panel (no tabs, flat layout)

**Goal:** Replace the three-tab layout with a flat panel. No behaviour changes yet — all existing
functionality stays wired up, just reorganised. Easiest to review visually.

**Changes — `app.js`:**

- `renderWordEditorPanel()` (lines 695–783): rewrite HTML
  - Remove tab bar (`w3-bar w3-blue-gray` with Suggest/Constraints/Reset buttons)
  - Remove `openWordEditTab()` function (line 786)
  - Remove `#we-tab-suggest`, `#we-tab-constraints`, `#we-tab-reset` divs
  - New layout (top to bottom):
    1. Header (unchanged)
    2. Clue input (unchanged, move to top)
    3. Suggestions section: `[🔍 Suggest]` button + `[Use constraints]` toggle checkbox +
       count label + scrollable `<ul>` list (replaces `<select>`) + pagination row
    4. `[↩ Undo]` `[↪ Redo]` `[↺ Reset]` row (Reset demoted from tab to button)
    5. `[OK]` `[Cancel]` row
  - Keep `#we-word` input hidden for now (still used by `doWordEditOK`)
  - Keep `weSelectChanged()` wired to list-item clicks

- `doWordSuggest()` (line 830): render into `<ul>` instead of `<select>`; each item is a
  clickable `<li>` that sets the hidden `#we-word` value
- `doConstrainedSuggest()` (line 870): same — render into `<ul>` with score display
- `doWordConstraints()` (line 908): move behind a `[Show crossing constraints ▸]` toggle
  link; collapsed by default; table rendered into a `<details>` element below suggestions

**Pagination state** (new module-level variables):
```js
let _weSuggestions = [];   // full list from last fetch
let _wePage = 0;           // current page (0-indexed)
const WE_PAGE_SIZE = 20;
```
Add `wePagePrev()` / `wePageNext()` that slice `_weSuggestions` and re-render the list.

**Review checkpoint:** Open a puzzle, click a word — panel looks right, all buttons work,
suggestions still populate, constraints still show (collapsed), Reset still works.

---

## Phase 2 — Word-editor local undo/redo stack

**Goal:** Add an independent undo/redo stack for word edits. Wire the panel Undo/Redo buttons
to it. Disable the puzzle-toolbar Undo/Redo while the word editor is open.

**Changes — `app.js`:**

New module-level state:
```js
let _weUndoStack = [];   // [{type, ...}]
let _weRedoStack = [];
```

New helpers:
- `wePush(entry)` — push to undo stack, clear redo stack, call `_updateWeUndoRedo()`
- `weUndo()` — pop from undo stack, apply inverse, push to redo stack
- `weRedo()` — pop from redo stack, apply, push to undo stack
- `_updateWeUndoRedo()` — toggle `w3-disabled` on `#we-undo-btn` / `#we-redo-btn`

**AppState additions:**
```js
weText: null,    // string[], one char per cell, length = word length (spaces for blanks)
```
Initialised in `openWordEditor()` from `data.answer`.

Undo entry types at this phase:
- `{type:'clue', old, new}` — pushed on blur of `#we-clue`
- `{type:'word', oldText, newText}` — pushed when suggestion clicked or Reset runs

**Wire into existing code:**
- `doWordReset()`: after updating `AppState.weText`, call `wePush({type:'reset', ...})`
- Suggestion list click: call `wePush({type:'word', ...})`
- `closeWordEditor()`: clear `_weUndoStack`, `_weRedoStack`, `AppState.weText = null`
- `_updatePuzzleUndoRedo()`: also disable both buttons when `AppState.editingWord !== null`

**Review checkpoint:** Word editor panel undo/redo buttons enable/disable correctly. Picking a
suggestion, then undoing, reverts the word text. Puzzle toolbar Undo/Redo are greyed out while
the editor is open and re-enable when it closes.

---

## Phase 3 — Grid keyboard editing

**Goal:** Type letters directly into the highlighted grid cells. The `#we-word` hidden input is
removed; `AppState.weText` is the single source of truth for the in-progress word.

**Changes — `app.js`:**

**`buildPuzzleSvg()`** gains an optional second argument `editState`:
```js
buildPuzzleSvg(puzzleData, editState = null)
// editState = { cells: [[r,c],...], cursorIdx: 0 }
```
When `editState` is set:
- Word cells get `fill="lightblue"` (or a CSS class)
- Cursor cell gets `fill="#aad4ff"` + a 2px blue stroke rect overlay
- Non-word white cells get `fill="#e8e8e8"` (dimmed)

New module-level cursor state:
```js
let _weCursorIdx = 0;   // index into editingWord.cells
```

**`openWordEditor()`**: after loading word data, set `AppState.weText`, `_weCursorIdx = 0`
(or first blank cell index), call `renderPuzzleEditorLhs()` to re-render grid in edit mode,
attach keyboard listener.

**`renderPuzzleEditorLhs()`**: if `AppState.editingWord`, pass `editState` to `buildPuzzleSvg`.

**SVG click handler** (`puzzleClickAt`): if word editor is open and clicked cell is in the
current word, move cursor there (undo step: `{type:'cursor'}` — no, cursor moves don't need
undo). Do not open a different word while editing.

**Keyboard handler** (`_weKeydown(e)`), attached to `document` on `openWordEditor`,
removed on `closeWordEditor`:
- Letter (`/^[a-zA-Z]$/`): `wePush({type:'letter', idx:_weCursorIdx, old, new})`; write to
  `AppState.weText`; advance cursor to next cell (wrap at end); re-render LHS
- `Backspace`: if current cell not blank, clear it (push undo); else move back and clear
- `Delete`: clear current cell (push undo); don't move cursor
- `ArrowLeft`/`ArrowRight` (Across) or `ArrowUp`/`ArrowDown` (Down): move cursor ±1, clamp
- `Home`/`End`: jump to 0 / last cell
- `Enter`: same as clicking OK
- `Escape`: same as Cancel

**Remove `#we-word` input** from the panel HTML (no longer needed).

**`doWordEditOK()`**: read text from `AppState.weText.join('')` instead of `#we-word`.

**Review checkpoint:** Open a word — grid highlights correctly. Type letters, they appear in
the grid cells. Backspace clears and moves back. Arrows move the cursor. Undo/redo within the
word editor reverts letter-by-letter. Clicking OK saves the word and clue.

---

## Phase 4 — OK squash into puzzle undo stack

**Goal:** After OK, the puzzle-level undo stack gets exactly one entry representing the entire
word edit session (old text+clue → new text+clue).

**Context:** The backend `PUT /api/puzzles/{wn}/words/{seq}/{dir}` already records one undo
entry for the text change. The puzzle `can_undo` flag reflects this. But if the user had been
interacting with the grid *before* opening the word editor (typing letters one by one via the
old cell API), there could be many stacked entries. Under the new model, **all letter changes
stay local** until OK — so by construction the backend only ever sees one PUT per word-editor
session. No backend changes needed.

**Frontend changes:**
- `doWordEditOK()`: after the PUT succeeds, clear `_weUndoStack`, `_weRedoStack`,
  `AppState.weText = null`, `_weCursorIdx = 0`
- `_updatePuzzleUndoRedo()`: now reads `puzzleData.can_undo` as before — correct, since the
  single PUT wrote one entry
- Re-enable puzzle toolbar Undo/Redo (they were disabled; now editor is closed)

**`cancelWordEditor()`** (rename from `closeWordEditor` or add as separate path):
- Revert `AppState.weText` to the original answer (saved at open time as
  `AppState._weOriginalText`)
- Re-render LHS (removes highlights, restores original letters visually)
- Clear stacks, close editor — **no PUT is sent**
- Puzzle undo stack is unchanged

**Review checkpoint:** Full workflow: open word, type several letters, undo some, pick a
suggestion, edit clue, click OK → puzzle undo stack has exactly one new entry → puzzle-level
Undo reverses the whole word change → Redo re-applies it.

---

## Summary of `app.js` symbols affected

| Symbol | Phase | Change |
|---|---|---|
| `renderWordEditorPanel()` | 1 | Full rewrite |
| `openWordEditTab()` | 1 | Delete |
| `weSelectChanged()` | 1 | Replace with `weListItemClick()` |
| `doWordSuggest()` | 1 | Render to `<ul>` |
| `doConstrainedSuggest()` | 1 | Render to `<ul>`, add score bar |
| `doWordConstraints()` | 1 | Move into collapsible `<details>` |
| `_weSuggestions`, `_wePage` | 1 | New |
| `wePagePrev()`, `wePageNext()` | 1 | New |
| `_weUndoStack`, `_weRedoStack` | 2 | New |
| `wePush()`, `weUndo()`, `weRedo()` | 2 | New |
| `_updateWeUndoRedo()` | 2 | New |
| `AppState.weText` | 2 | New field |
| `_updatePuzzleUndoRedo()` | 2 | Extend to disable when editing |
| `openWordEditor()` | 2, 3 | Extend |
| `closeWordEditor()` | 2, 4 | Extend / split into close vs cancel |
| `buildPuzzleSvg()` | 3 | Add `editState` param |
| `renderPuzzleEditorLhs()` | 3 | Pass `editState` when editing |
| `_weKeydown()` | 3 | New |
| `puzzleClickAt()` | 3 | Guard: don't open new word while editing |
| `_weCursorIdx` | 3 | New |
| `doWordEditOK()` | 3, 4 | Read from `AppState.weText`; clear stacks |
| `AppState._weOriginalText` | 4 | New field (saved at open) |
