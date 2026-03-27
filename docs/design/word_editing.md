# Word Editing — Revised Interaction Model

## Overview

This document describes the planned changes to how words are edited in the puzzle editor.

**Before:** clicking a cell automatically opens the word editor, which takes over keyboard input and has its own local undo/redo stack. Pressing OK fires a single `PUT` to the backend.

**After:** keyboard entry works directly in the puzzle grid at all times. The word editor is opened explicitly via a new toolbar button, contains a plain text input for the word, and does not write anything to the puzzle until OK is clicked. Undo/redo operates at word granularity in both paths.

---

## 1. Direct keyboard entry in the puzzle grid

### 1.1 Word selection

`puzzleClickAt` (app.js:687) currently calls `openWordEditor` on every click. This is split into two functions:

- **`selectWord(seq, direction)`** — highlights the word, sets `AppState.selectedWord` and `_peCursorIdx`, re-renders the LHS with the cursor visible. Does not open the word editor panel.
- **`openWordEditor(seq, direction)`** — now only invoked explicitly from the new toolbar button (see §3).

Before selecting a new word, `puzzleClickAt` calls `_peCommitWord()` (see §1.3) to flush any pending edit from the previously selected word.

The clue lists rendered in the RHS panel (app.js:783) currently have per-word links with `onclick="openWordEditor(${w.seq}, '${direction}')"`. These must be changed to `onclick="selectWord(${w.seq}, '${direction}')"` so that clicking a clue selects the word in the grid (committing any current word first) without opening the word editor.

`AppState.selectedWord` is a new field:

```js
{
    seq:         number,
    direction:   string,   // Word.ACROSS or Word.DOWN
    cells:       [[r,c]],
    initialText: string,   // text at the moment this word was selected
    currentText: string,   // updated as the user types
}
```

### 1.2 Puzzle-level keyboard handler

A new function `_peKeydown(e)` handles keyboard input when the puzzle editor is active and the word editor is not open. It is registered with `document.addEventListener('keydown', _peKeydown)` when the puzzle editor is rendered, and removed when it is torn down or when the word editor is opened.

Behaviour:

| Key | Action |
|---|---|
| A–Z | Write letter at `_peCursorIdx` in `selectedWord.currentText`; advance cursor |
| Delete | Clear letter at cursor |
| Backspace | Clear current letter; if cursor > 0, move back and clear that one |
| Arrow keys | Advance/retreat cursor within word (matching current direction), or toggle direction if perpendicular |
| Tab / Shift+Tab | Commit current word (`_peCommitWord`), select next/previous word |
| Escape | Deselect word (`_peCommitWord`, then `AppState.selectedWord = null`) |

After each keystroke, `renderPuzzleEditorLhs()` is called to update the SVG with the new letter(s) visible. The `editState` passed to `buildPuzzleSvg` is extended to carry `selectedWord` and `_peCursorIdx` so the renderer can show highlighted cells and the cursor.

### 1.3 Word-level commit

```js
async function _peCommitWord()
```

Called before:
- Selecting a different word (click or Tab)
- Opening the word editor
- Pressing Escape to deselect
- Any action that navigates away from the puzzle editor (close, save, undo, redo)

Logic:

1. If `AppState.selectedWord` is null, return immediately.
2. Compare `currentText` against `initialText`. If unchanged, return.
3. Fire `PUT /api/puzzles/{workingName}/words/{seq}/{dir}` with `{ text: currentText }` (no clue field).
4. On success, update `AppState.puzzleData` from the response and set `initialText = currentText`.
5. Call `_updatePuzzleUndoRedo()`.

The backend already records a single undo entry per `PUT` with `text`, so puzzle-level undo/redo at word granularity requires no backend changes.

---

## 2. Puzzle-level undo/redo interaction with keyboard entry

No backend changes are needed. The existing `POST /api/puzzles/{name}/undo` and `POST /api/puzzles/{name}/redo` endpoints already operate at word granularity because each `PUT` with `text` creates exactly one undo entry.

The toolbar undo/redo buttons (`#puzzle-undo-btn`, `#puzzle-redo-btn`) must call `_peCommitWord()` before firing the undo/redo request, to avoid losing in-flight keystrokes. After the undo/redo response arrives, `AppState.selectedWord` is cleared (the restored word may differ from whatever was selected).

---

## 3. New "Edit word" toolbar button

Added to the toolbar in `renderPuzzleEditorLhs` (app.js:726–744), after the Redo button:

```html
<a id="puzzle-editword-btn" class="w3-bar-item w3-button crosstb"
   onclick="do_puzzle_edit_word()">
  <i class="material-icons crosstb-icon">edit</i><span>Edit word</span></a>
```

`do_puzzle_edit_word()`:

1. If `AppState.selectedWord` is null, return (silent).
2. Call `await _peCommitWord()` to flush any pending keyboard input.
3. Call `openWordEditor(seq, direction)`.

The button gets `w3-disabled` when `AppState.selectedWord` is null, managed in `_updatePuzzleUndoRedo()` (or a new `_updatePuzzleToolbar()` helper).

---

## 4. Word editor changes

### 4.1 Text input

A new `<input>` is added at the top of the word editor panel (rendered in `renderPuzzleEditorRhs` / the word editor HTML block, app.js:805–903):

```html
<label>Word</label>
<input id="we-text" type="text" class="w3-input w3-border"
       maxlength="{len}" style="font-family:monospace;letter-spacing:0.2em"
       oninput="_weOnTextInput()">
```

Pre-filled in `openWordEditor` with the committed text of the selected word (which is `currentText` after `_peCommitWord()` has run). Since `_peCommitWord` is called before opening, the word editor always starts from the backend-confirmed state.

`_weOnTextInput()` updates the suggestion filter in real time (calls `doWordSuggestFetch()` if the suggest tab is active, or just refreshes the pattern used by the next fetch).

### 4.2 Suggest tab

`doWordSuggestFetch` (app.js:1128) currently derives the search pattern from `AppState.weText`. It is changed to read `document.getElementById('we-text').value` instead. Clicking a suggestion fills `#we-text` (rather than updating `AppState.weText` and re-rendering the grid).

### 4.3 Reset button

The reset button (currently calls `POST .../reset` and updates `AppState.weText`) is simplified: it calls `POST .../reset`, reads the cleared text from the response, and sets `#we-text` value to that cleared text. No undo push needed (the reset itself is undo-tracked on the backend via the `PUT` that OK will fire).

### 4.4 Undo/redo removed

`_weUndoStack`, `_weRedoStack`, `wePush`, `weUndo`, `weRedo`, `_updateWeUndoRedo`, and the undo/redo buttons (`#we-undo-btn`, `#we-redo-btn`) are all removed. The word editor has no local history; the user can cancel to abandon changes.

### 4.5 OK

`doWordEditOK` (app.js:1329) is updated to read text from `#we-text` instead of `AppState.weText`:

```js
const text = document.getElementById('we-text').value.padEnd(len).slice(0, len);
```

The `PUT` call and close sequence are otherwise unchanged.

### 4.6 Cancel

`closeWordEditor` (app.js:1105) is unchanged in effect: it discards the word editor state and re-renders. Because `_peCommitWord()` was called before opening, the puzzle is already at the committed state. No restoration logic is needed and `_weOriginalPuzzleData` is removed.

**Behavior change — Reset then Cancel:** In the current model, Reset fires a backend call that clears the word's letters, and `_weOriginalPuzzleData` is used to restore the puzzle to its pre-open state if the user then cancels. Under the new model, Reset calls `POST .../reset`, reads the cleared text from the response, and places it in `#we-text` — but does not write anything to the backend. Cancelling after Reset therefore truly cancels: the puzzle remains at the committed state from before the word editor was opened. This is a deliberate improvement — Reset is now a local "clear the input" action within the word editor session.

### 4.7 Keyboard handling in the word editor

`_weKeydown` (app.js:1014) is simplified. Letter keys, Delete, Backspace, and navigation within the word are no longer needed — the browser handles them natively inside `#we-text`. What remains:

- **Escape** → cancel (call `closeWordEditor`)
- **Enter** (when focus is NOT on the clue input) → OK (call `doWordEditOK`)
- The existing Enter-in-clue-triggers-OK logic (already present, app.js:~1040) is kept.

`document.addEventListener('keydown', _weKeydown)` is still registered on open and removed on close, but the handler is much smaller.

---

## 5. AppState changes

| Field | Change |
|---|---|
| `selectedWord` | **New.** `{seq, direction, cells, initialText, currentText}` or `null` |
| `editingWord` | Unchanged — set when word editor is open |
| `weText` | **Removed.** Replaced by `#we-text` input value |
| `_weOriginalPuzzleData` | **Removed** (no longer needed; see §4.6) |

Module-level variables removed: `_weUndoStack`, `_weRedoStack`.

New module-level variable: `_peCursorIdx` (cursor position within `selectedWord.cells`).

---

## 6. Rendering changes

`buildPuzzleSvg` (and the `editState` object passed to it) needs to support two display states:

- **Word selected, editor closed** — highlight cells of `selectedWord`, show cursor at `_peCursorIdx`, show letters from `selectedWord.currentText`.
- **Word editor open** — current behaviour (highlight via `AppState.editingWord`).

These map to the same rendering path; the `editState` object is populated from `selectedWord` when the editor is closed and from `editingWord` when it is open.

`AppState.weText` is currently read in the SVG rendering path (app.js:516–524) to overlay in-progress letters onto the puzzle grid. These references must be updated to read from `selectedWord.currentText` (when no word editor is open) or from `document.getElementById('we-text').value` (when the word editor is open). Since `AppState.weText` is removed entirely, a search for all its uses before deletion is essential.

---

## 7. Backend changes

**None.** All required backend behaviour (word-granularity undo, `PUT` accepting `text`, `POST .../reset`) already exists.

---

## 8. File changes summary

| File | Changes |
|---|---|
| `frontend/static/js/app.js` | All changes described above |
| `frontend/index.html` | None (word editor panel HTML is rendered from JS) |
| Backend Python files | None |
