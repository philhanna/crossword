# Issue 196 Questions

These are the open questions I have after reviewing GitHub issue `#196` and comparing it with the current codebase.

## Answered

1. Is "merge concepts of puzzle and grid" meant to be a UI-only change, or a true domain and persistence change too?

   Answer: This is a true data-model merge, not just a UI change.

   The code currently treats them as separate objects end-to-end: separate domain classes, separate use cases, and separate database tables. This answer means the implementation should likely converge those layers rather than only adding a mode toggle in the frontend.

2. Should "new puzzle starts in grid mode" replace the concept of creating standalone grids entirely?

   Answer: Yes. Grids are just early-stage puzzles.

   The UI currently has distinct entry points for `New grid`, `Open grid`, `New puzzle`, and `Open puzzle`, but this answer implies the standalone grid concept should be folded into the puzzle lifecycle rather than preserved as a separate saved object type. And remove those distinct entry points and the whole Grid menu

3. What should happen to existing saved grids?

   Answer: Use a one-time migration tool and treat each saved grid as an early-stage puzzle in `grid` mode.

   The migration should be non-destructive on the first pass: convert saved public grids into merged puzzle records, skip working-copy rows, preserve names when possible, and keep the original `grids` rows until the new flow is verified.

   See [issue-196-migration-design.md](/home/saspeh/dev/python/crossword/docs/notes/issue-196-migration-design.md) for the concrete rollout and migration design.

4. When switching back to grid mode and changing black cells, what exactly should happen to letters in affected cells?

   Answer: Forget the former letters.

   Any letters affected by the grid change should be discarded rather than preserved. Newly black cells lose their contents, and any reshaped word should be treated as new fill rather than an attempt to retain prior letter state.

## Remaining Questions

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

The main open design questions now are persistence shape, unified save semantics, shared undo and redo, and the exact preservation rules for clues and reshaped words after grid edits.
