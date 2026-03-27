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

5. What is the exact preservation rule for answers and clues after a grid edit?

   Answer: Keep the letters of the old word unless they have been changed in the grid editor. Clear the clues.

   Existing letters should survive a grid edit where their cells remain valid and unchanged by the edit. Any clue associated with a reshaped or affected word should be cleared rather than preserved.

6. Should mode switches be allowed on invalid grids?

   Answer: Yes. Mode switches should still be allowed.

   Validation is informational only. The system should report validation status and errors to the user, but should not block mode switches or enforce validity before allowing editing to continue.

7. Should undo and redo span both modes as one shared history?

   Answer: No. Undo and redo should have separate stacks for each mode.

   Grid-mode edits and puzzle-mode edits should keep distinct history, so switching modes does not merge their timelines into a single combined undo and redo sequence.

8. What should `Save` and `Save As` mean in the merged editor?

   Answer: In the new framework, there is only `Save` and `Save As` for puzzles.

   The merged model has a single saved artifact type, so separate grid save behavior goes away. Grid mode is just one editing state of a puzzle, not something with its own persistence operation.

9. Is the goal to merge only creation and editing, or also menus and navigation?

   Answer: Use a single editor screen with a mode toggle.

   The merged flow should not keep separate editor experiences for grids and puzzles. Instead, one editor should support both `grid` mode and `puzzle` mode, with the mode toggle controlling the active editing behavior.

## Remaining Questions

10. If a grid edit splits one answer into two, should both resulting clues be blank even if one side still matches an old word exactly?

    The issue says "clear the clue," but it is ambiguous whether that applies only to changed words in general, or to every resulting fragment after a split.

The main open design question now is persistence shape, plus any edge-case rules for how reshaped words inherit or lose clue state.
