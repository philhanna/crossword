# First Grid — initial grid-editor display for a new puzzle

## Goal

Define what the grid editor shows the moment a **new** puzzle is opened,
based on whether the user supplied a theme spec at creation time.

- **No theme spec** → the editor opens on a blank grid. Nothing changes from
  today's behavior.
- **Valid theme spec** → the editor opens with a grid that has already been
  generated to honor the spec, and the user can immediately **Undo** back to
  the blank grid.

## Background — how a new puzzle is created today

Frontend flow (`frontend/static/js/puzzle-editor.js`, `do_puzzle_new` →
`promptForPuzzleDetails` → `createPuzzle`):

1. `promptForPuzzleDetails()` asks for a size and an optional theme spec. The
   spec is validated to be a palindrome of positive integers (e.g. `7,5,5,7`)
   and parsed into `spec` (`int[]`) or `null`.
   See [puzzle-editor.js:1002-1026](../../frontend/static/js/puzzle-editor.js#L1002-L1026).
2. `createPuzzle(size, spec)` posts `POST /api/puzzles`, opens the working copy
   in the editor, then stores the spec on `AppState.puzzleThemeSpec`.
   See [puzzle-editor.js:1034-1046](../../frontend/static/js/puzzle-editor.js#L1034-L1046).

Backend (`crossword/use_cases/puzzle_use_cases.py`):

- `create_puzzle()` builds the puzzle and calls `puzzle.enter_grid_mode()`
  ([puzzle_use_cases.py:76](../../crossword/use_cases/puzzle_use_cases.py#L76)),
  so a freshly-created puzzle's `last_mode` is `"grid"` and its
  `grid_undo_stack` is empty. The editor therefore opens directly in **grid
  mode** showing the blank grid.

So `AppState.puzzleThemeSpec` is already captured, but right now it is only
consumed later if the user manually clicks **Generate**
([puzzle-editor.js:690-707](../../frontend/static/js/puzzle-editor.js#L690-L707)).

## Key insight — the undo push is already free

`do_puzzle_generate_grid()` calls
`POST /api/puzzles/{wn}/grid/generate?spec=...`, which routes to
`generate_grid()` →
`puzzle.apply_generated_grid(newgrid)`
([puzzle.py:212-215](../../crossword/domain/puzzle.py#L212-L215)):

```python
def apply_generated_grid(self, newgrid: Grid):
    self.grid_undo_stack.append(self.grid.to_json())  # push current (blank) grid
    self.grid_redo_stack = []
    self._apply_new_grid(newgrid)
```

Because the puzzle is brand new, `self.grid` at this point **is** the blank
grid. So generating right after creation automatically pushes the empty grid
onto the undo stack — the "first push an empty grid" requirement is satisfied
by the existing backend code. After the auto-generate, `grid_can_undo` is true,
and a single **Undo** restores the blank grid.

No backend change is required.

## Desired behavior

After `createPuzzle()` finishes opening the editor and setting
`AppState.puzzleThemeSpec`:

| Condition | Action | Resulting initial display |
|---|---|---|
| `spec === null` | none (unchanged) | blank grid, undo disabled |
| `spec` is valid | auto-invoke generate once | generated grid, **Undo → blank grid** |

The auto-generate must reuse the existing `do_puzzle_generate_grid()` path so
that the spec query param, the empty-grid undo push, stats/fill-order refresh,
and the generate-button busy state all behave exactly as a manual click.

## Implementation plan

Single change in the frontend, at the end of `createPuzzle()`
([puzzle-editor.js:1034-1046](../../frontend/static/js/puzzle-editor.js#L1034-L1046)):

1. After `AppState.puzzleThemeSpec = spec;` and `renderPuzzleEditorLhs();`,
   add:
   ```js
   if (spec) {
       await do_puzzle_generate_grid();
   }
   ```
2. `do_puzzle_generate_grid()`'s own guard
   (`_currentEditorMode() !== 'grid'`) is satisfied because a new puzzle opens
   in grid mode, so no extra mode check is needed here.
3. `do_puzzle_generate_grid()` already:
   - reads `AppState.puzzleThemeSpec` and appends `?spec=...`,
   - disables/re-enables the Generate button,
   - calls `_applyGridModeUpdate(data)` which re-renders the editor and
     refreshes stats/fill-order.

   So the generated grid and the undo-enabled state appear automatically.

### Edge cases to confirm

- **Generate returns a `notice`** (e.g. generator could not satisfy the spec):
  `do_puzzle_generate_grid()` shows the notice via `showMessageLine` and
  returns without applying a grid. The editor then stays on the blank grid —
  acceptable; the user can edit or retry manually.
- **Generate errors:** same handling — error message, blank grid remains.
- **Spec captured but editor not in grid mode:** cannot happen for a new puzzle
  (always `enter_grid_mode`), but the guard protects against future changes.

## Testing

- New puzzle, **no** spec → blank grid; Undo disabled. (regression)
- New puzzle, spec `7,5,5,7` → grid is filled on open; Undo enabled; one Undo
  yields the blank grid; Redo restores the generated grid.
- New puzzle, spec the generator can't satisfy → notice shown, blank grid
  remains, no spurious undo entry.
