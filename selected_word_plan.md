# Selected Word Update Plan

## Goal

Ensure that changing a word's text follows one consistent frontend path whether the user is:

- typing directly in the puzzle editor
- editing the word in the word editor
- switching from one word to another by keyboard or mouse

The key behavioral rule is that a word edit is only sent to the server when the current edit is considered complete.

## Current State

The current frontend splits this behavior across two state objects in [frontend/static/js/state.js](/home/saspeh/dev/python/crossword/frontend/static/js/state.js:22) and two save paths in [frontend/static/js/word-editor.js](/home/saspeh/dev/python/crossword/frontend/static/js/word-editor.js:152) and [frontend/static/js/word-editor.js](/home/saspeh/dev/python/crossword/frontend/static/js/word-editor.js:792):

- `AppState.selectedWord`
  Used by puzzle-mode typing and selection.
- `AppState.editingWord`
  Used by the word editor panel.
- `_peCommitWord()`
  Saves puzzle-mode edits.
- `doWordEditOK()`
  Saves word-editor edits.

That split causes two related problems:

1. There is no single notion of the currently selected word.
2. The system has different ideas about when an edit is finished and should be saved.

## Desired Model

### 1. One shared selected-word state

Replace the split between `selectedWord` and `editingWord` with a single word-session object in `AppState`.

Suggested shape:

```js
selectedWord: {
    seq,
    direction,
    cells,
    originalText,
    draftText,
    originalClue,
    draftClue,
    cursorIdx,
    editorMode,   // 'puzzle' | 'word'
    dirtyText,
    dirtyClue,
    saving
}
```

This object becomes the single source of truth for:

- which word is selected
- what its current draft text is
- what clue draft is being edited
- where the cursor is
- whether the user is editing in the puzzle surface or in the word editor panel

`AppState.editingWord` should be removed after the new model is in place.

### 2. One completion path

All word updates should go through one function, conceptually:

```js
completeSelectedWordEdit(reason)
```

Responsibilities:

- determine whether the current selected word is dirty
- normalize `draftText` and `draftClue`
- send a single `PUT /api/puzzles/{workingName}/words/{seq}/{direction}`
- replace `AppState.puzzleData` with the server response
- refresh the selected word from the returned puzzle data
- preserve or clear selection depending on the completion reason

This should replace both `_peCommitWord()` and `doWordEditOK()` as the authoritative save path.

## Completion Rules

An edit is complete, and must be sent to the server if dirty, in the following cases.

### Puzzle editor

1. Typing letters, spaces, backspace, or delete updates only the local draft.
   It does not send to the server immediately.

2. Arrow keys that move within the current word update only `cursorIdx`.
   They do not change selection and do not save.

3. For an across word, pressing `ArrowUp` or `ArrowDown`:
   If this changes to a different down word, it completes the current edit first, then selects the new word.

4. For a down word, pressing `ArrowLeft` or `ArrowRight`:
   If this changes to a different across word, it completes the current edit first, then selects the new word.

5. Clicking any puzzle cell outside the currently selected word completes the current edit first, then selects the clicked word if one exists.

6. Clicking outside the puzzle grid completes the current edit and leaves the current selection behavior explicit:
   either keep the selected word highlighted or clear it. The implementation should choose one rule and use it everywhere.

### Word editor

7. Clicking `Apply` completes the current edit and sends it to the server.
   The word remains the currently selected word.

8. Keyboard actions in the word editor that switch to another word should first complete the current edit, then move selection.
   This already partially exists in `_weApplyAndClose()`, but it should call the shared completion function.

### Shared rule

9. If the edit is not dirty, completion is still a state transition, but it should not call the server.

## Selection Rules

The selected word should continue to exist independently from whether the sidebar word editor is open.

That means:

- opening the word editor does not create a second selection object
- closing the word editor does not discard the selected word
- moving from puzzle typing to word-editor editing only changes `editorMode`
- rendering code for the grid and sidebar reads from the same selected-word object

## Proposed Refactor Steps

### Phase 1: Introduce unified state

1. Expand `AppState.selectedWord` to hold both puzzle-mode and word-editor draft state.
2. Stop storing duplicated answer/clue data in `AppState.editingWord`.
3. Add helper functions such as:
   `getSelectedWordFromPuzzleData()`
   `hydrateSelectedWord(seq, direction, options)`
   `refreshSelectedWordFromPuzzleData()`

### Phase 2: Centralize edit completion

4. Add one shared function for completion, for example:
   `completeSelectedWordEdit({ keepSelected, nextSelection, closeWordEditor })`
5. Move the normalization logic from `_peCommitWord()` and `doWordEditOK()` into that function.
6. Move the API call into that function so there is one server write path.

### Phase 3: Rewire puzzle editor behavior

7. Update `_peKeydown()` so:
   typing changes `draftText`
   same-direction arrows move only the cursor
   cross-direction arrows call the shared completion flow before changing selection
8. Update `puzzleClickAt()` so clicking outside the current word triggers completion before switching words.
9. Update `_peOutsideMousedown()` so outside clicks use the same completion helper instead of fire-and-forget save logic.

### Phase 4: Rewire word editor behavior

10. Update `openWordEditor()` to switch the shared selected word into `editorMode: 'word'` instead of creating `editingWord`.
11. Update the word editor inputs so they read and write `draftText` and `draftClue` on the shared object.
12. Replace `doWordEditOK()` and `_weApplyAndClose()` with wrappers around the shared completion helper.

### Phase 5: Simplify rendering

13. Update `renderPuzzleEditorLhs()` to derive its `editState` from one object.
14. Update `renderPuzzleEditorRhs()` and `renderWordEditorPanel()` to treat "word editor open" as a mode of the selected word, not a separate selected entity.
15. Remove `AppState.editingWord` and dead branches that exist only to keep the two models in sync.

## Implementation Notes

### Completion result should be explicit

The shared completion helper should return a structured result, for example:

```js
{ saved: true, changedSelection: false, cancelled: false }
```

That makes keyboard and mouse handlers easier to reason about.

### Only switch selection after completion succeeds

If the server rejects the update:

- keep the current word selected
- keep the editor open in its current mode
- show the error
- do not move to the requested next word

This avoids losing the user's draft mentally and visually.

### Keep server ownership of puzzle truth

After a successful save, always rebuild the selected-word draft from the returned `data.puzzle.words` entry instead of trusting the old local draft. That keeps cursor/display logic aligned with server-normalized data.

## Test Cases To Add

Frontend tests are limited here, so this work should at least be covered with targeted behavior tests where possible and a manual checklist.

### Manual checks

1. Type letters in puzzle mode and verify nothing is saved until completion.
2. Move within an across word using left/right and verify no save occurs.
3. Move from across to down using up/down and verify the old word saves before selection changes.
4. Move from down to across using left/right and verify the old word saves before selection changes.
5. Click another word in the grid and verify the old word saves first.
6. Click outside the current word and verify the old word saves first.
7. Click `Apply` in the word editor and verify the save occurs while selection remains on that word.
8. Open the word editor, change text, then switch words by keyboard and verify save-then-switch behavior.
9. Trigger a server-side save error and verify selection does not move away.

## Recommended Order

Implement this in three small PR-sized chunks even if it lands together:

1. Unify selected-word state without changing behavior.
2. Centralize completion/save logic.
3. Rewire keyboard and mouse transitions to use the shared completion rules.

That order reduces the chance of breaking both editors at once and makes regressions easier to isolate.
