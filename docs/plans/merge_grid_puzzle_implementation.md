# Merge Grid And Puzzle Implementation Plan

This document turns the requirements in `docs/plans/merge_grid_puzzle_requirements.md` into an implementation sequence. It is phase-delimited, and each phase is meant to end in a stable, reviewable checkpoint.

The current codebase still assumes:

- separate `Grid` and `Puzzle` domain objects
- separate grid and puzzle persistence tables
- separate `GridUseCases` and `PuzzleUseCases`
- separate `/api/grids/*` and `/api/puzzles/*` editing flows
- separate `grid-editor` and `puzzle-editor` views in `frontend/static/js/app.js`

The plan below retires those assumptions in controlled steps rather than trying to land the entire redesign at once.

## Phase 0: Prep And Guardrails

- [x] Re-read `docs/plans/merge_grid_puzzle_requirements.md` and freeze the implementation contract.
- [x] Identify every user-visible grid workflow that currently depends on standalone saved grids.
- [x] Inventory all code paths that call `load_grid`, `save_grid`, `list_grids`, or `delete_grid`.
- [x] Inventory all code paths that assume `AppState.view` can be `grid-editor` or `puzzle-editor`.
- [x] Decide whether this work will land behind a temporary feature branch only, or behind a runtime flag.
- [x] Add a short implementation note listing any intentionally deferred cleanup items.

**Primary files/modules**

- `docs/plans/merge_grid_puzzle_requirements.md`
- `crossword/ports/persistence_port.py`
- `crossword/use_cases/grid_use_cases.py`
- `crossword/use_cases/puzzle_use_cases.py`
- `crossword/http_server/grid_handlers.py`
- `crossword/http_server/puzzle_handlers.py`
- `frontend/static/js/app.js`

**Checkpoint**

- [x] The team agrees on phase boundaries, rollout order, and any temporary compatibility strategy.

### Phase 0 Notes

Implementation findings from the Phase 0 inventory:

- Standalone saved-grid behavior is deeply wired into the backend through `PersistencePort`, `SQLitePersistenceAdapter`, `GridUseCases`, `grid_handlers`, route registration in `crossword/http_server/main.py`, export use cases, and a large dedicated test surface.
- The frontend still has a full parallel grid editor flow in `frontend/static/js/app.js` and `frontend/index.html`, including Grid menu items, grid working-copy state, a grid-specific toolbar, and a separate grid statistics panel.
- Documentation also assumes the old split architecture, especially [frontend.md](/home/saspeh/dev/python/crossword/docs/design/frontend.md), [README.md](/home/saspeh/dev/python/crossword/README.md), and [calltree.md](/home/saspeh/dev/python/crossword/docs/design/calltree.md).

Rollout decision:

- Use a compatibility-first branch rollout, not a runtime feature flag.
- The change is architectural enough that maintaining both the old and new editor flows behind a UI flag would add too much temporary complexity across persistence, API shape, and frontend state.
- We should keep temporary compatibility code only where it reduces migration risk during intermediate phases.

Intentionally deferred cleanup items:

- Remove legacy grid export endpoints only after the merged puzzle model is stable.
- Remove `GridUseCases` and grid-specific tests only after puzzle-centered replacements exist.
- Update secondary design docs after the main implementation lands, not during the first backend refactor.
- Decide whether any short-lived JSON backward-compatibility loader is needed during schema migration when Phase 2 begins.

## Phase 1: Unify The Domain Model Around Puzzle

- [x] Extend `Puzzle` so it directly owns all grid structure needed for black-cell editing, numbering, and stats.
- [x] Move or absorb relevant behavior from `Grid` into `Puzzle`.
- [x] Add explicit persisted mode state to `Puzzle`, for example `last_mode`.
- [x] Add mode-local undo/redo state to `Puzzle`, separating Grid-mode history from Puzzle-mode history.
- [x] Define clear `Puzzle` methods for:
- [x] toggling a black cell with symmetry handling
- [x] rotating the grid if rotation is still retained
- [x] entering Grid mode
- [x] entering Puzzle mode
- [x] resetting per-mode undo/redo stacks on mode switch
- [x] recalculating numbering and words after grid edits
- [x] preserving or clearing clues according to the requirements
- [x] preserving surviving letters when entries split, shrink, or merge
- [x] Keep `Grid` temporarily only as a compatibility wrapper if needed during the refactor, but make `Puzzle` the real owner of the behavior.
- [x] Add or update domain tests for all new `Puzzle` behavior before removing compatibility scaffolding.

**Primary files/modules**

- `crossword/domain/puzzle.py`
- `crossword/domain/grid.py`
- `crossword/domain/word.py`
- `crossword/tests/test_puzzle.py`
- `crossword/tests/test_puzzle_replace_grid.py`
- `crossword/tests/test_puzzle_undo.py`
- new tests as needed for mode switching and merge/split behavior

**Checkpoint**

- [x] `Puzzle` can represent the full merged state without depending on a separately persisted grid object.
- [x] Domain tests cover split, shrink, merge, clue clearing, and mode-local undo/redo.

### Phase 1 Notes

Implemented in this phase:

- `Puzzle` now owns merged-editor domain state for `last_mode`, `grid_undo_stack`, and `grid_redo_stack`.
- Legacy `undo_stack` and `redo_stack` remain as compatibility aliases for Puzzle-mode text history so existing use cases continue to work.
- `Puzzle` now exposes domain methods for `enter_grid_mode`, `enter_puzzle_mode`, `toggle_black_cell`, `rotate_grid`, `undo_grid_change`, and `redo_grid_change`.
- Grid changes now flow through a shared `_apply_new_grid` path that:
- preserves surviving letters in still-white cells
- turns removed black cells into blank spaces
- reinitializes numbering and entries
- preserves clues only when the exact identity rule matches
- clears clues for affected entries by default

Validation completed in this phase:

- `./venv/bin/pytest -q crossword/tests/test_puzzle.py crossword/tests/test_puzzle_undo.py crossword/tests/test_puzzle_replace_grid.py crossword/tests/test_puzzle_modes.py`
- `./venv/bin/pytest -q crossword/tests/test_grid.py crossword/tests/test_grid_rotate.py crossword/tests/test_grid_undo_redo.py`

## Phase 2: Redesign Persistence And Schema

- [x] Update the persistence contract so puzzles are the only persisted construction object.
- [x] Add persisted mode support to puzzle load/save operations.
- [x] Remove grid CRUD responsibilities from the long-term `PersistencePort`.
- [x] Update the SQLite adapter schema to the target `puzzles` table layout, including `last_mode`.
- [x] Implement migration support for old rows whose puzzle JSON does not yet contain embedded unified grid state.
- [x] Decide whether migration happens eagerly at startup, lazily on first load, or via a one-off admin script.
- [x] Ensure working-copy persistence still functions for puzzles after the schema change.
- [x] Remove dependence on the `grids` table once migration is complete.
- [x] Add adapter tests covering:
- [x] new schema initialization
- [x] save/load of unified puzzles
- [x] persisted `last_mode`
- [x] migration of legacy rows
- [x] absence of standalone grid persistence in the new model

**Primary files/modules**

- `crossword/ports/persistence_port.py`
- `crossword/adapters/sqlite_persistence_adapter.py`
- `crossword/tests/adapters/test_sqlite_adapter.py`
- any migration utility scripts under `tools/`

**Checkpoint**

- [x] One database row in `puzzles` is sufficient to reconstruct both Grid mode and Puzzle mode.
- [x] Legacy data migration path is implemented and tested.

### Phase 2 Notes

Implemented in this phase:

- `PersistencePort` now documents unified puzzle persistence as the target architecture, while explicitly treating standalone grid methods as temporary legacy compatibility surface.
- `SQLitePersistenceAdapter` now ensures schema compatibility on connect.
- The `puzzles` table is now created or migrated forward with a persisted `last_mode` column.
- Puzzle save/load now persists `last_mode` both in the dedicated SQL column and in the serialized puzzle JSON.
- Legacy puzzle rows without `last_mode` continue to load successfully and default to `puzzle` mode until rewritten in the new format.
- Migration is eager on adapter initialization rather than deferred to first load.

Compatibility decision in this phase:

- The legacy `grids` table and grid persistence methods are still present temporarily so the rest of the application can keep working while later phases replace grid-specific use cases and routes.
- In that sense, “remove grid CRUD responsibilities from the long-term port” is implemented architecturally and in documentation, but not yet as total code deletion.

Validation completed in this phase:

- `./venv/bin/pytest -q crossword/tests/adapters/test_sqlite_adapter.py crossword/tests/test_wiring.py`
- `./venv/bin/pytest -q crossword/tests/test_puzzle.py crossword/tests/test_puzzle_undo.py crossword/tests/test_puzzle_replace_grid.py crossword/tests/test_puzzle_modes.py crossword/tests/test_grid.py crossword/tests/test_grid_rotate.py crossword/tests/test_grid_undo_redo.py`

## Phase 3: Collapse Use Cases Into Puzzle-Centered Workflows

- [x] Redesign `PuzzleUseCases` so puzzle creation no longer requires an existing saved grid.
- [x] Introduce a puzzle creation path that accepts a size and creates a new puzzle directly in Grid mode.
- [x] Add explicit use cases for mode switching, including persisted `last_mode`.
- [x] Move standalone grid-editing operations into puzzle use cases:
- [x] toggle black cell
- [x] rotate grid if retained
- [x] grid-mode undo/redo
- [x] puzzle-mode undo/redo
- [x] stats retrieval for both modes via puzzle stats
- [x] Remove or deprecate puzzle operations that depend on `replace_puzzle_grid(new_grid_name)`.
- [x] Remove or deprecate `GridUseCases` methods that exist only to manage standalone saved grids.
- [x] Keep any temporary adapter methods only as long as needed to support migration or compatibility.
- [x] Add use-case tests for:
- [x] create new puzzle in Grid mode
- [x] open existing puzzle in persisted mode
- [x] switching Puzzle mode -> Grid mode with confirmation handled at higher layers
- [x] mode-local undo/redo reset on mode switch
- [x] grid edit aftermath on clues and answers

**Primary files/modules**

- `crossword/use_cases/puzzle_use_cases.py`
- `crossword/use_cases/grid_use_cases.py`
- `crossword/tests/test_puzzle_use_cases.py`
- `crossword/tests/test_grid_use_cases.py`

**Checkpoint**

- [x] All editing behavior needed by the UI is available through puzzle-focused use cases.
- [x] No required user flow depends on creating or opening a standalone saved grid.

### Phase 3 Notes

Implemented in this phase:

- `PuzzleUseCases.create_puzzle` now supports puzzle-first creation by `size`, while still accepting `grid_name` as a legacy compatibility path.
- New puzzle-first use cases now exist for:
- `switch_to_grid_mode`
- `switch_to_puzzle_mode`
- `toggle_black_cell`
- `rotate_grid`
- `undo_grid`
- `redo_grid`
- Existing `copy_puzzle` and `open_puzzle_for_editing` now reset both Puzzle-mode and Grid-mode histories when creating a new working session.
- `get_puzzle_stats` already serves both modes, so no separate grid stats use case is needed.

Compatibility decision in this phase:

- `replace_puzzle_grid(new_grid_name)` remains in place temporarily as a legacy compatibility path.
- `GridUseCases` remains in place temporarily because the HTTP layer and frontend still call it in later phases.
- In that sense, the Phase 3 goal is complete at the application-service level, but not yet complete as total old-code removal.

Validation completed in this phase:

- `./venv/bin/pytest -q crossword/tests/test_puzzle_use_cases.py crossword/tests/test_wiring.py`
- `./venv/bin/pytest -q crossword/tests/test_puzzle_modes.py crossword/tests/adapters/test_sqlite_adapter.py`

## Phase 4: Replace Grid HTTP Endpoints With Puzzle-Centric Endpoints

- [x] Define the target puzzle API surface for the merged editor.
- [x] Extend puzzle responses to include persisted mode and mode-specific undo/redo availability.
- [x] Add puzzle endpoints for:
- [x] switching modes
- [x] grid-mode black-cell edits
- [x] grid-mode undo/redo
- [x] puzzle-mode undo/redo
- [x] reading unified stats for either mode
- [x] Keep or reshape existing word/clue endpoints so Puzzle mode can continue using suggestion and constraint features.
- [x] Remove or deprecate HTTP routes that expose standalone grid editing.
- [x] Update any response builders so frontend consumers can render one merged editor instead of two separate editors.
- [x] Add handler tests for both legacy migration behavior and new merged-editor behavior.

**Primary files/modules**

- `crossword/http_server/puzzle_handlers.py`
- `crossword/http_server/grid_handlers.py`
- `crossword/http_server/main.py`
- `crossword/tests/test_http_server.py`

**Checkpoint**

- [x] The frontend can drive both modes using puzzle endpoints only.
- [x] Grid-only editing routes are no longer required by the merged editor UI.

### Phase 4 Notes

Implemented in this phase:

- `_puzzle_response` now includes:
- persisted `mode`
- `grid_can_undo` / `grid_can_redo`
- `puzzle_can_undo` / `puzzle_can_redo`
- `can_undo` / `can_redo` resolved for the current mode
- `POST /api/puzzles` now supports puzzle-first creation with `size`, while still accepting legacy `grid_name`.
- New puzzle-centric endpoints now exist for:
- `POST /api/puzzles/<name>/mode/grid`
- `POST /api/puzzles/<name>/mode/puzzle`
- `PUT /api/puzzles/<name>/grid/cells/<r>/<c>`
- `POST /api/puzzles/<name>/grid/rotate`
- `POST /api/puzzles/<name>/grid/undo`
- `POST /api/puzzles/<name>/grid/redo`
- Route registration in `crossword/http_server/main.py` now exposes those endpoints.

Compatibility decision in this phase:

- Legacy `/api/grids/*` routes still exist temporarily so the current frontend can keep working until the merged-editor UI is implemented in Phase 5.
- Legacy puzzle endpoints such as `/api/puzzles/<name>/grid` also remain temporarily for compatibility.
- In that sense, the new API surface is complete for the merged editor, but old HTTP entry points are not deleted yet.

Validation completed in this phase:

- `./venv/bin/pytest -q crossword/tests/test_http_server.py crossword/tests/test_puzzle_use_cases.py`
- `./venv/bin/pytest -q crossword/tests/test_wiring.py crossword/tests/test_puzzle_modes.py`

## Phase 5: Replace The Two SPA Editors With One Merged Editor

- [x] Redesign `AppState` to track one active puzzle editor rather than separate grid and puzzle editors.
- [x] Remove `gridWorkingName`, `gridData`, `gridSavedHash`, `showingGridStats`, and other state that exists only for standalone grid editing.
- [x] Introduce a single editor state model, for example:
- [x] current puzzle working name
- [x] current editor mode
- [x] unified puzzle payload
- [x] current selected word for Puzzle mode
- [x] grid-mode UI state
- [x] puzzle-mode UI state
- [x] Update menu logic so standalone Grid menu actions disappear or are rehomed under Puzzle workflows.
- [x] Replace `showView('grid-editor')` and `showView('puzzle-editor')` with one merged editor view.
- [x] Split rendering into one shared editor shell plus mode-specific panels/toolbars.
- [x] Ensure the toolbar changes with the mode, per requirements.
- [x] Use the puzzle statistics panel in both modes.
- [x] Remove the old grid statistics panel implementation from the active UI path.

**Primary files/modules**

- `frontend/static/js/app.js`
- `frontend/index.html`
- `frontend/static/css/style.css`
- `docs/design/frontend.md` if kept up to date

**Checkpoint**

- [x] The app renders one construction editor with mode switching rather than two independent editors.

### Phase 5 Notes

Implemented in this phase:

- The active SPA now uses a single `editor` view for puzzle construction.
- `AppState` now keeps only puzzle-centered editor state on the active path.
- The top-level menu no longer exposes standalone Grid actions.
- `do_puzzle_new()` now creates a puzzle directly from a requested size instead of requiring a saved grid first.
- Puzzle open/create flows now share `_openPuzzleInEditor()` so both paths land in the same merged editor shell.
- The editor now renders a shared shell with explicit Grid/Puzzle mode buttons and mode-specific toolbars.
- Grid mode now uses the shared puzzle statistics panel instead of the old grid statistics panel.
- Undo/redo buttons now resolve against the current mode's availability flags from the puzzle payload.

Intentional deferrals to Phase 6:

- The old standalone grid functions still exist in the file as inactive compatibility code.
- Grid-mode black-cell click handling, rotation controls, and entry invalidation messaging remain for the next phase.
- The required confirmation dialog before switching into Grid mode has not been added yet.

Validation completed in this phase:

- `node --check frontend/static/js/app.js`
- `./venv/bin/pytest -q crossword/tests/test_http_server.py crossword/tests/test_puzzle_use_cases.py crossword/tests/test_wiring.py`

## Phase 6: Implement Grid Mode In The Merged UI

- [x] Make new puzzles open directly into Grid mode.
- [x] Make existing puzzles open in their persisted `last_mode`.
- [x] Implement the Puzzle mode -> Grid mode confirmation dialog with exact text:
- [x] `Are you sure you want to modify the grid?`
- [x] buttons `OK` and `Cancel`
- [x] On entry to Grid mode, reset Grid-mode undo/redo state for that session.
- [x] Render the puzzle grid in Grid mode using the unified puzzle payload.
- [x] Wire click handling for black-cell edits through puzzle endpoints, not grid endpoints.
- [x] Preserve symmetry behavior from the current grid editor.
- [x] Ensure Grid mode does not show:
- [x] word editor panel
- [x] clue list editing affordances
- [x] answer editing controls
- [x] If rotation is retained, add it to the Grid-mode toolbar only.
- [x] Use the unified stats panel on the RHS while in Grid mode.
- [x] Communicate clue/entry invalidation after edits, but do not show previews before the edit.

**Primary files/modules**

- `frontend/static/js/app.js`
- `frontend/static/css/style.css`

**Checkpoint**

- [x] Grid mode behaves like the old grid editor where intended, but inside the merged puzzle editor.

### Phase 6 Notes

Implemented in this phase:

- The merged editor now attaches click-to-toggle behavior in Grid mode through `PUT /api/puzzles/<working>/grid/cells/<r>/<c>`.
- The Grid-mode toolbar now includes `Rotate`, wired through `POST /api/puzzles/<working>/grid/rotate`.
- Puzzle-to-Grid mode switching now shows the required confirmation prompt text:
- `Are you sure you want to modify the grid?`
- When switching from Puzzle mode, in-progress puzzle edits are settled before the mode change request is sent.
- Grid updates now show a notice explaining that entries were recomputed and affected clues were cleared.
- If the shared stats panel is open while editing the grid, it is refreshed after each grid change so the panel stays current.

Compatibility notes:

- Old standalone-grid functions still remain in `frontend/static/js/app.js`, but they are no longer on the active UI path.
- The active merged editor now satisfies the intended Grid-mode workflow; dead standalone-grid code removal stays in later cleanup phases.

Validation completed in this phase:

- `node --check frontend/static/js/app.js`
- `./venv/bin/pytest -q crossword/tests/test_http_server.py crossword/tests/test_puzzle_use_cases.py crossword/tests/test_wiring.py`

## Phase 7: Implement Puzzle Mode In The Merged UI

- [x] Keep direct word selection and keyboard fill in Puzzle mode.
- [x] Keep word/clue editing tools that are still in scope.
- [x] Persist `last_mode = 'puzzle'` when the user leaves the editor in Puzzle mode.
- [x] On entry to Puzzle mode, reset Puzzle-mode undo/redo state for that session.
- [x] Ensure Puzzle mode cannot accidentally toggle black cells.
- [x] Keep clue lists, word editing, suggestions, constraints, and reset behavior working against the merged puzzle backend.
- [x] Make sure switching back from Grid mode reflects any recomputed entries, preserved letters, and cleared clues correctly.
- [x] Confirm that unchanged entries preserve clues only when the exact identity rule passes.

**Primary files/modules**

- `frontend/static/js/app.js`
- `crossword/http_server/puzzle_handlers.py`
- `crossword/use_cases/puzzle_use_cases.py`

**Checkpoint**

- [x] Puzzle mode remains fully usable after late grid edits and reflects the recomputed puzzle structure correctly.

### Phase 7 Notes

Implemented in this phase:

- Selecting a word from the grid now dismisses the stats panel and brings the clue/editing side back into view, so direct selection remains reliable in Puzzle mode.
- The clue lists now support direct word selection separately from explicit word editing, and cleared clues are shown as `(no clue)` to make post-grid invalidation visible.
- Returning from Grid mode to Puzzle mode now shows a notice when the puzzle structure changed, prompting review of recomputed entries and cleared clues.
- Puzzle-only actions such as opening the word editor are now explicitly guarded so Grid mode cannot trigger them accidentally.

Notes on previously completed support that this phase depends on:

- Persisting `last_mode = 'puzzle'` and resetting Puzzle-mode undo/redo on mode entry are handled by the domain and use-case work completed earlier.
- The exact clue-preservation rule for unchanged entries is enforced by the Phase 1 domain behavior and remains covered by domain tests.

Validation completed in this phase:

- `node --check frontend/static/js/app.js`
- `./venv/bin/pytest -q crossword/tests/test_http_server.py crossword/tests/test_puzzle_use_cases.py crossword/tests/test_puzzle_modes.py crossword/tests/test_wiring.py`

## Phase 8: Remove Standalone Grid Features

- [ ] Remove dead frontend menu items for standalone grid creation, opening, saving, save-as, deletion, and `new grid from puzzle`.
- [ ] Remove obsolete grid chooser and preview flows from the active UI.
- [ ] Remove backend routes and handlers that exist only for standalone saved grids.
- [ ] Remove unused `GridUseCases` methods and tests once migration is complete.
- [ ] Remove persistence-port methods that are no longer part of the final architecture.
- [ ] Remove `grids` table creation and any admin/documentation references that assume saved grids still exist.
- [ ] Update exports if any still depend on loading standalone grids.
- [ ] Update README and design docs to describe the merged editor as the only construction workflow.

**Primary files/modules**

- `frontend/static/js/app.js`
- `crossword/http_server/grid_handlers.py`
- `crossword/use_cases/grid_use_cases.py`
- `crossword/ports/persistence_port.py`
- `crossword/adapters/sqlite_persistence_adapter.py`
- `README.md`
- relevant docs under `docs/design/`

**Checkpoint**

- [ ] The codebase no longer presents standalone grids as a persisted user-facing concept.

## Phase 9: End-To-End Verification And Cleanup

- [ ] Add or update integration tests for the full merged flow:
- [ ] create new puzzle -> starts in Grid mode
- [ ] switch to Puzzle mode -> enter answers and clues
- [ ] switch back to Grid mode -> confirm dialog appears
- [ ] modify black cells -> entries recompute
- [ ] affected clues clear
- [ ] surviving letters are preserved correctly
- [ ] switch back to Puzzle mode -> new structure is rendered
- [ ] save -> reload -> last-used mode is restored
- [ ] verify mode-local undo/redo in both directions
- [ ] verify old puzzle rows can still be opened after migration
- [ ] verify working-copy save/close/discard behavior still works
- [ ] remove temporary compatibility shims, feature flags, or migration fallbacks that are no longer needed
- [ ] update docs and screenshots if maintained

**Primary files/modules**

- `crossword/tests/test_http_server.py`
- `crossword/tests/test_puzzle_use_cases.py`
- `crossword/tests/adapters/test_sqlite_adapter.py`
- `README.md`
- docs as needed

**Checkpoint**

- [ ] The merged editor is shippable without relying on the old standalone grid workflow.

## Suggested Delivery Slices

- [ ] Slice 1: Domain and persistence groundwork without changing the UI
- [ ] Slice 2: New puzzle-only backend endpoints with compatibility still in place
- [ ] Slice 3: Frontend merged editor shell and mode switching
- [ ] Slice 4: Grid mode in merged UI
- [ ] Slice 5: Puzzle mode integration after grid edits
- [ ] Slice 6: Removal of standalone grid features and final cleanup

## Major Risks To Watch

- [ ] Hidden coupling between `Puzzle` and `Grid` in numbering, validation, and SVG generation
- [ ] Migration complexity for existing puzzle JSON payloads
- [ ] Frontend state bugs during mode switching and working-copy save/close flows
- [ ] Undo/redo regressions when mode-local history resets
- [ ] Incomplete cleanup leaving dead grid routes or menu items reachable

## Definition Of Done

- [ ] New puzzles start in Grid mode.
- [ ] Existing puzzles reopen in their last-used persisted mode.
- [ ] One merged editor handles both black-cell editing and answer/clue editing.
- [ ] Grid mode has no word editor panel and no answer/clue editing.
- [ ] Puzzle mode supports answer/clue editing and reflects grid edits correctly.
- [ ] Mode switching includes the required confirmation when entering Grid mode from Puzzle mode.
- [ ] Undo/redo is local to the current mode and resets on each mode switch.
- [ ] The persisted `puzzles` layout includes `last_mode` and unified puzzle JSON.
- [ ] The standalone saved-grid model is removed from the final architecture.
