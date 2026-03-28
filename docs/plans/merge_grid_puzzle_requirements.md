# Merge Grid And Puzzle Editing Requirements

## Summary

The application should replace the separate "grid editor" and "puzzle editor" experiences with a single puzzle-construction UI that supports two editing modes:

- **Grid mode** for defining and revising the black-cell pattern
- **Puzzle mode** for entering answers and clues

A new puzzle should begin in Grid mode. Once the constructor switches to Puzzle mode, the primary workflow becomes filling answers and writing clues. Returning to Grid mode is allowed but expected to be uncommon. If a black-cell change splits, shortens, or otherwise invalidates an existing word, the affected answer may be chopped into smaller words and any affected clue must be cleared.

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
- Defining detailed backend API or persistence migration steps in this document

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
There is no longer any first-class saved standalone grid object.

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
4. The product shall no longer persist standalone saved grids as first-class objects.

### 2. Modes

1. The merged editor shall expose at least two explicit modes: Grid mode and Puzzle mode.
2. The current mode shall be visually obvious at all times.
3. Switching modes shall not require leaving the current editor or reopening the puzzle.
4. Creating a new puzzle shall always open the merged editor in Grid mode.
5. Opening an existing puzzle shall restore the same mode in which that puzzle was last edited.
6. The last-used mode for an existing puzzle shall be persisted as part of the saved puzzle data so that it survives close/reopen cycles.
6. The toolbar must change back and forth with the mode.

### 3. Grid Mode

1. In Grid mode, the user shall be able to add and remove black cells.
2. Grid-mode interactions shall continue to enforce the current grid rules, including symmetry, unless a separate future requirement changes that behavior.
3. Grid mode shall provide enough feedback for the user to understand the structural consequences of changes, including numbering and word boundaries.
4. Grid mode shall allow editing even if the puzzle already contains answers and clues.
5. Grid mode is expected to be used heavily at the beginning of construction and rarely after fill has started, but the product must still support late edits reliably.
6. Grid mode shall not show the word editor panel.
7. Grid mode shall not allow answer editing or clue editing.
8. Grid mode should otherwise behave like the current standalone grid editor wherever that behavior is still compatible with the merged-editor design.

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
5. Users shall be allowed to switch back to Grid mode freely.
6. Switching from Puzzle mode to Grid mode shall show a confirmation dialog before the mode change occurs.
7. The confirmation dialog text shall be: `Are you sure you want to modify the grid?`
8. The confirmation dialog shall offer `OK` and `Cancel`.
9. Choosing `OK` shall complete the switch to Grid mode.
10. Choosing `Cancel` shall leave the editor in Puzzle mode with no changes applied.

### 6. Recomputing Puzzle Structure After Grid Changes

1. Any black-cell change made in Grid mode after puzzle content exists shall trigger recalculation of numbering and word boundaries.
2. The recalculation shall update across and down entries to match the new grid.
3. Entry identity shall be treated as structural, not merely numeric.
4. A word shall be considered unchanged only if it has the same exact cell span, the same text span, and the same start cell plus direction before and after the grid edit.
5. When a grid edit causes an existing word to be split into two or more entries, the application may create the resulting entries by chopping the existing answer text to fit the new spans.
6. When a grid edit causes a word to shorten, the answer text may be truncated to the surviving span.
7. When a grid edit causes multiple former entries to merge into a larger entry, the resulting entry shall keep all surviving letters from the former entries, with spaces inserted where removed black cells formerly separated them.
8. The application shall not silently preserve a clue for any entry whose structural meaning has changed.

### 7. Clue Handling For Affected Words

1. If a grid change affects a word's span, start cell, end cell, or segmentation, the clue for that affected word shall be cleared.
2. If a former word is split into multiple new words, each resulting new word shall start with an empty clue.
3. If a word has the same exact cell span, the same text span, and the same start cell plus direction across a grid revision, preserving its clue is allowed and preferred.
4. Clue clearing rules shall be deterministic so that users can predict when a clue will be kept versus removed.
5. If two or more former entries merge into a single new entry, the clues of all former entries shall be cleared.

### 8. Answer Handling For Affected Words

1. If a grid edit splits an answer into smaller entries, the new entries may inherit the corresponding chopped text segments.
2. If an inherited text segment contains blanks, those blanks may remain.
3. If a grid edit removes cells from an entry, text outside the surviving cells shall be discarded.
4. If a grid edit creates a new entry from cells that previously were not a standalone word, the new entry may begin with inherited letters where they exist and blanks where they do not.
5. The application shall avoid deleting unaffected answer text elsewhere in the puzzle.

### 9. Undo/Redo

1. The merged editor shall support undo and redo across both grid changes and puzzle-content changes.
2. Undo and redo shall be local to the current editing mode rather than shared across modes.
3. When the user switches into Grid mode, the Grid-mode undo/redo history shall start fresh from the beginning of that Grid-mode session.
4. Grid-mode undo and redo shall apply only to edits made since entering Grid mode most recently.
5. When the user switches back into Puzzle mode, the Puzzle-mode undo/redo history shall start fresh from the beginning of that Puzzle-mode session.
6. Puzzle-mode undo and redo shall apply only to edits made since entering Puzzle mode most recently.

### 10. Save/Close Behavior

1. Saving shall save the puzzle from the merged editor without requiring separate grid and puzzle save steps.
2. Closing without saving shall discard the working copy, consistent with current application behavior.
3. Save As shall continue to be supported for the merged object.

### 11. Domain Model And Persistence

1. The `Grid` class and its relevant methods shall be merged into the `Puzzle` class.
2. The unified `Puzzle` class shall own both grid structure and puzzle content.
3. Grid-related behavior currently implemented through the standalone `Grid` domain object shall be moved into `Puzzle` or otherwise absorbed by the unified puzzle model.
4. The persistence layer shall be updated to reflect that puzzles, not standalone grids, are the persisted construction unit.
5. This change is expected to require SQL schema changes, persistence-port changes, or both.

### 12. Proposed Puzzle Persistence Layout

The current SQLite adapter stores grids and puzzles in separate tables, each with a `jsonstr` payload. Under the merged design, the standalone `grids` table goes away and the `puzzles` table becomes the single persisted construction object.

The new persisted puzzle row should include:

- puzzle identity and ownership
- created/modified timestamps
- persisted last-used editor mode
- one JSON payload containing both grid structure and puzzle content

Proposed SQLite DDL:

```sql
CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT NOT NULL,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr         TEXT NOT NULL,
    UNIQUE (userid, puzzlename)
);
```

Notes on this layout:

- `last_mode` is required because existing puzzles must reopen in the same mode in which they were last edited.
- `jsonstr` remains the serialized representation of the unified `Puzzle` object, but now that JSON must include the black-cell pattern that previously lived in the standalone `Grid`.
- `UNIQUE (userid, puzzlename)` reflects the lookup pattern already used by the persistence adapter and should be enforced by the schema rather than only by application behavior.
- The old `grids` table is no longer part of the target design.

The serialized puzzle JSON stored in `jsonstr` should now represent a single object that includes at least:

- grid size
- black-cell layout
- answer cells
- clues
- title
- any mode-specific state that is intentionally persisted with the puzzle

This document does not define the exact JSON shape, but it does require that the persisted `Puzzle` object contain enough information to reconstruct both Grid mode and Puzzle mode from one database row.

#### Migration From The Old Schema

The current schema has both:

- a `grids` table containing serialized `Grid` objects
- a `puzzles` table containing serialized `Puzzle` objects that reference grid data indirectly through the current domain model

The target migration should move the system to a puzzle-only persistence model.

Recommended migration shape:

1. Add the new `last_mode` column to `puzzles`, initially defaulting existing rows to `'puzzle'` or another chosen safe default.
2. Update puzzle serialization so each saved `Puzzle` row contains its own grid structure directly in `jsonstr`.
3. Update persistence code so all create, load, save, copy, open, and delete operations work only through persisted puzzles.
4. Remove application dependence on `load_grid`, `save_grid`, `list_grids`, and `delete_grid`.
5. After code and data migration are complete, drop the obsolete `grids` table.

Illustrative migration DDL:

```sql
ALTER TABLE puzzles
ADD COLUMN last_mode TEXT NOT NULL DEFAULT 'puzzle'
    CHECK (last_mode IN ('grid', 'puzzle'));

DROP TABLE grids;
```

Notes:

- The `ALTER TABLE` statement alone is not sufficient, because existing `jsonstr` payloads must also be rewritten to the new unified `Puzzle` format.
- If backward compatibility is needed during rollout, the application may temporarily support reading both old and new puzzle JSON shapes, but the end state should be one canonical persisted puzzle format.
- The default `'puzzle'` value above is only a migration placeholder. Newly created puzzles must still begin in Grid mode, and persisted puzzles must thereafter remember their true last-used mode.

### 13. Validation And Feedback

1. The merged editor shall continue to expose grid-quality and puzzle-progress information.
2. If a grid edit clears clues or changes entries, the UI should communicate that consequence to the user.
3. The UI should make it hard to miss that a Grid-mode edit may invalidate clue work done in Puzzle mode.
4. The editor shall not show clue-impact or answer-impact previews before committing an individual black-cell change.
5. The application shall use the puzzle statistics display in both Grid mode and Puzzle mode.
6. The old standalone grid statistics display shall not be carried forward into the merged editor.

## Acceptance Criteria

1. A new puzzle opens in the merged editor in Grid mode.
2. An existing puzzle reopens in the same mode in which it was last edited.
3. The user can design a grid, switch to Puzzle mode, and begin entering answers and clues without leaving the editor.
4. The user can switch back to Grid mode, change black cells, and return to Puzzle mode in the same session.
5. After a late grid edit, numbering and entry boundaries are recalculated correctly.
6. Any word structurally affected by that grid edit has its clue cleared.
7. When a word is split by a new black cell, the resulting entries contain chopped answer text where applicable and empty clues.
8. Words unaffected by the grid edit retain their answer text and clues.
9. Saving from the merged editor persists the revised puzzle correctly, including the last-used mode.

## Open Questions

None at present.

## Recommended Default Assumptions For Implementation Planning

Unless the answers above change product direction, the planning baseline should be:

- existing puzzles reopen in their last-used persisted mode
- clue preservation requires the same exact cell span, the same text span, and the same start cell plus direction
- merged entries keep surviving letters, insert spaces where removed black cells used to be, and clear the clues of all former entries
- entering Grid mode from Puzzle mode requires a confirmation dialog: `Are you sure you want to modify the grid?`
- individual black-cell edits do not show impact previews before they are applied
- undo/redo is local to the current mode and resets each time the user switches modes
- there are no saved standalone grids; grid behavior is absorbed into `Puzzle` and persistence changes are expected
