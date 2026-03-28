# Merge Grid And Puzzle Editing Requirements

## Summary

The application should replace the separate "grid editor" and "puzzle editor" experiences with a single puzzle-construction UI that supports two editing modes:

- **Grid mode** for defining and revising the black-cell pattern
- **Puzzle mode** for entering answers and clues

New work should begin in Grid mode. Once the constructor switches to Puzzle mode, the primary workflow becomes filling answers and writing clues. Returning to Grid mode is allowed but expected to be uncommon. If a black-cell change splits, shortens, or otherwise invalidates an existing word, the affected answer may be chopped into smaller words and any affected clue must be cleared.

This document defines the functional requirements for that merged experience.

## Goals

- Provide one continuous workflow for constructing a crossword from empty grid through filled puzzle.
- Eliminate the mental overhead of switching between separate editor types.
- Preserve the current strengths of each editor where they still make sense.
- Make late grid edits safe and predictable, even when they invalidate existing fill.

## Non-Goals

- Redesigning clue-writing assistance, suggestions, or constraints logic
- Changing crossword validity rules
- Supporting arbitrary grid resizing inside the merged editor
- Defining backend API details in this document

## Terminology

- **Merged editor**: the new unified UI that replaces the separate grid and puzzle editors
- **Grid mode**: mode in which black cells can be changed
- **Puzzle mode**: mode in which answers and clues can be edited
- **Affected word**: any across or down entry whose span changes because a black cell was added, removed, or moved
- **Working copy**: the editable in-progress object already used by the application

## Product Overview

The merged editor edits a single puzzle working copy. That working copy always contains both:

- a grid definition
- puzzle content derived from that grid, including numbered entries, answer text, and clues

The user no longer opens one editor for grids and another for puzzles. Instead, the user opens one construction surface and changes modes within it.

## Primary User Flow

1. The user creates a new puzzle.
2. The merged editor opens in Grid mode.
3. The user lays out the black-cell pattern.
4. The user switches to Puzzle mode.
5. The user enters answers and clues.
6. The user may occasionally switch back to Grid mode to revise blocks.
7. If a grid revision changes entry boundaries, the puzzle structure is recalculated and affected clues are cleared.
8. The user saves the puzzle from the same editor.

## Functional Requirements

### 1. Single Editor

1. The application shall provide one editor for crossword construction rather than separate grid and puzzle editors.
2. The merged editor shall operate on a puzzle working copy, not on an independent grid object.
3. The editor shall preserve the existing working-copy pattern: edits are made against a temporary working copy until the user saves or closes.

### 2. Modes

1. The merged editor shall expose at least two explicit modes: Grid mode and Puzzle mode.
2. The current mode shall be visually obvious at all times.
3. Switching modes shall not require leaving the current editor or reopening the puzzle.
4. Creating a new puzzle shall always open the merged editor in Grid mode.
5. Opening an existing puzzle shall open the merged editor in the last sensible editing mode or a default mode chosen by implementation; this behavior is not yet fixed.

### 3. Grid Mode

1. In Grid mode, the user shall be able to add and remove black cells.
2. Grid-mode interactions shall continue to enforce the current grid rules, including symmetry, unless a separate future requirement changes that behavior.
3. Grid mode shall provide enough feedback for the user to understand the structural consequences of changes, including numbering and word boundaries.
4. Grid mode shall allow editing even if the puzzle already contains answers and clues.
5. Grid mode is expected to be used heavily at the beginning of construction and rarely after fill has started, but the product must still support late edits reliably.

### 4. Puzzle Mode

1. In Puzzle mode, the user shall be able to select entries and edit answers.
2. In Puzzle mode, the user shall be able to create and edit clues.
3. Existing answer-entry workflow features that remain useful in the merged design, such as suggestion and constraint tools, should continue to be available.
4. Puzzle mode shall not allow accidental black-cell edits through normal answer-entry interactions.

### 5. Mode Switching

1. The user shall be able to switch from Grid mode to Puzzle mode at any time.
2. The user shall be able to switch from Puzzle mode back to Grid mode at any time.
3. Mode switching shall preserve unsaved work already committed to the working copy.
4. If the current mode contains transient local UI state, that state may be committed or discarded on mode switch, but the behavior must be consistent and explicit in implementation.

### 6. Recomputing Puzzle Structure After Grid Changes

1. Any black-cell change made in Grid mode after puzzle content exists shall trigger recalculation of numbering and word boundaries.
2. The recalculation shall update across and down entries to match the new grid.
3. Entry identity shall be treated as structural, not merely numeric. A word is considered unchanged only if its cell span remains meaningfully the same according to implementation rules.
4. When a grid edit causes an existing word to be split into two or more entries, the application may create the resulting entries by chopping the existing answer text to fit the new spans.
5. When a grid edit causes a word to shorten, the answer text may be truncated to the surviving span.
6. When a grid edit causes multiple former entries to merge into a larger entry, the resulting answer/clue behavior is not yet fixed and requires a product decision.
7. The application shall not silently preserve a clue for any entry whose structural meaning has changed.

### 7. Clue Handling For Affected Words

1. If a grid change affects a word's span, start cell, end cell, or segmentation, the clue for that affected word shall be cleared.
2. If a former word is split into multiple new words, each resulting new word shall start with an empty clue.
3. If a word remains structurally unchanged across a grid revision, preserving its clue is allowed and preferred.
4. Clue clearing rules shall be deterministic so that users can predict when a clue will be kept versus removed.

### 8. Answer Handling For Affected Words

1. If a grid edit splits an answer into smaller entries, the new entries may inherit the corresponding chopped text segments.
2. If an inherited text segment contains blanks, those blanks may remain.
3. If a grid edit removes cells from an entry, text outside the surviving cells shall be discarded.
4. If a grid edit creates a new entry from cells that previously were not a standalone word, the new entry may begin with inherited letters where they exist and blanks where they do not.
5. The application shall avoid deleting unaffected answer text elsewhere in the puzzle.

### 9. Undo/Redo

1. The merged editor shall support undo and redo across both grid changes and puzzle-content changes.
2. Undo and redo behavior across mode boundaries shall feel like one continuous editing session.
3. If the implementation cannot provide a single unified history initially, the fallback behavior must be clearly defined before implementation begins.

### 10. Save/Close Behavior

1. Saving shall save the puzzle from the merged editor without requiring separate grid and puzzle save steps.
2. Closing without saving shall discard the working copy, consistent with current application behavior.
3. Save As shall continue to be supported for the merged object.

### 11. Validation And Feedback

1. The merged editor shall continue to expose grid-quality and puzzle-progress information, though the final presentation may differ from today's separate views.
2. If a grid edit clears clues or changes entries, the UI should communicate that consequence to the user.
3. The UI should make it hard to miss that a Grid-mode edit may invalidate clue work done in Puzzle mode.

## Acceptance Criteria

1. A new puzzle opens in the merged editor in Grid mode.
2. The user can design a grid, switch to Puzzle mode, and begin entering answers and clues without leaving the editor.
3. The user can switch back to Grid mode, change black cells, and return to Puzzle mode in the same session.
4. After a late grid edit, numbering and entry boundaries are recalculated correctly.
5. Any word structurally affected by that grid edit has its clue cleared.
6. When a word is split by a new black cell, the resulting entries contain chopped answer text where applicable and empty clues.
7. Words unaffected by the grid edit retain their answer text and clues.
8. Saving from the merged editor persists the revised puzzle correctly.

## Open Questions

1. When opening an existing puzzle, should the editor start in Puzzle mode, Grid mode, or remember the last-used mode?
2. What exact rule should define "word unchanged" for clue preservation: same exact cell span, same text span, same start cell plus direction, or something else?
3. When two former entries merge into one larger entry after a grid edit, should the merged entry's answer be blanked entirely, partially inherited, or reconstructed from surviving letters?
4. Should the user receive a confirmation prompt before a Grid-mode change that will clear clues or restructure entries?
5. Should Grid mode show clue/answer impact previews before the user commits a black-cell change?
6. Should users be allowed to switch back to Grid mode freely, or should the UI add friction once clue-writing has begun?
7. Should undo/redo be one unified stack across both modes, or is mode-local history acceptable for an initial version?
8. Should the merged editor continue to expose the current word editor panel in Puzzle mode, or should answer/clue editing be redesigned further as part of this change?
9. Should grid statistics and puzzle statistics remain separate panels, or be combined into one construction sidebar?
10. Should there still be any first-class concept of a saved standalone grid, or does this feature imply that construction now centers entirely on puzzles?

## Recommended Default Assumptions For Implementation Planning

Unless the answers above change product direction, the planning baseline should be:

- existing puzzles open in Puzzle mode
- clue preservation requires the exact same cell span and direction
- merged entries lose their clue and start with inherited letters only where that behavior is easy to explain
- destructive Grid-mode edits show a lightweight warning, not a blocking multi-step flow
- undo/redo should be unified if practical
