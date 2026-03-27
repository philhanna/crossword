# Issue 196 Questions

These are the open questions I have after reviewing GitHub issue `#196` and comparing it with the current codebase.

## Answered

1. Is "merge concepts of puzzle and grid" meant to be a UI-only change, or a true domain and persistence change too?

   Answer: This is a true data-model merge, not just a UI change.

   The code currently treats them as separate objects end-to-end: separate domain classes, separate use cases, and separate database tables. This answer means the implementation should likely converge those layers rather than only adding a mode toggle in the frontend.

## Remaining Questions

2. Should "new puzzle starts in grid mode" replace the concept of creating standalone grids entirely?

   The UI currently has distinct entry points for `New grid`, `Open grid`, `New puzzle`, and `Open puzzle`. Since this is now a true model merge, it is unclear whether saved grids remain a first-class concept or become just an early-stage puzzle.

3. What should happen to existing saved grids?

   If the model is unified, should old grids open as draft puzzles in grid mode, or should they remain available through a separate legacy path?

4. When switching back to grid mode and changing black cells, what exactly should happen to letters in affected cells?

   The issue says it is OK to chop words in two and clear the clue, but it does not say whether letters in newly black cells are discarded immediately, and whether newly white cells start blank.

5. What is the exact preservation rule for answers and clues after a grid edit?

   There is already a `replace_grid()` path, but it currently tries to preserve clues by matching word text, which is fairly loose. Should preservation be by unchanged cell span, by same clue number and direction, by exact answer text, or only for unaffected words?

6. Should mode switches be allowed on invalid grids?

   The grid validator enforces crossword rules now. It is unclear whether puzzle mode should be allowed before the grid is fully valid, or whether the mode switch should be blocked until validation passes.

7. Should undo and redo span both modes as one shared history?

   Today grid edits and puzzle edits have separate working copies and separate undo stacks. In a unified editor, should a black-cell change, a typed answer, and a clue edit all live in one timeline?

8. What should `Save` and `Save As` mean in the merged editor?

   Saving a grid and saving a puzzle are currently different operations with different names. In the merged model, is there only one saved artifact and one persistence path?

9. Is the goal to merge only creation and editing, or also menus and navigation?

   The requirement says "Create them in one UI, differentiating them with different modes," but it is unclear whether that means a single editor screen with a mode toggle, or keeping the current separate menu structure and only linking the flows more tightly.

10. If a grid edit splits one answer into two, should both resulting clues be blank even if one side still matches an old word exactly?

    The issue says "clear the clue," but it is ambiguous whether that applies only to changed words in general, or to every resulting fragment after a split.

The main open design questions now are migration, persistence shape, unified save semantics, shared undo and redo, and how existing standalone grids should map into the merged model.
