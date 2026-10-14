# Even-sized grids and grids without symmetry — project plan

## The problem this solves

Right now every puzzle has to follow the classic newspaper rules: the grid
has an odd size (15×15, 21×21, …), and its black squares are arranged with
180° rotational symmetry. That suits puzzles meant for the NYT and similar
outlets. It gets in the way of other kinds of puzzles:

- **Even sizes** such as 4×4 or 6×6 minis, 10×10 or 16×16 grids, and
  some variety puzzles.
- **Freestyle grids** whose black squares follow no pattern at all. A lot
  of indie and themeless puzzles drop symmetry so the theme entries fit, or
  so a corner can be filled more cleanly.

This plan lets a puzzle have **any size, odd or even**, and lets each
puzzle **turn symmetry on or off**. Symmetry stays **on** by default, so
anyone who doesn't touch the new setting keeps today's behaviour.

Out of scope: rectangular (non-square) grids. The code stores a single `n`
for both width and height almost everywhere. Supporting rectangles is a
separate, much bigger project.

## Where these rules are enforced today

Odd sizes and symmetry are enforced in a few separate places, not one:

**Symmetry is built into the Grid itself.**
- `Grid.add_black_cell()` and `Grid.remove_black_cell()`
  ([grid.py:50](../crossword/domain/grid.py#L50),
  [grid.py:64](../crossword/domain/grid.py#L64)) always change the
  mirror cell too, and `Grid.undoredo()`
  ([grid.py:195](../crossword/domain/grid.py#L195)) does the same.
- **The most important one:** `Grid.from_json()`
  ([grid.py:228](../crossword/domain/grid.py#L228)) and
  `Puzzle.from_json()`
  ([puzzle.py:438](../crossword/domain/puzzle.py#L438)) rebuild the
  grid by calling `add_black_cell()`, so they add the mirror cells back.
  Even if an asymmetric grid could be created, it would turn symmetric the
  first time it was saved and reloaded. Every grid edit makes that round
  trip (`Puzzle.toggle_black_cell()` copies the grid through JSON,
  [puzzle.py:252](../crossword/domain/puzzle.py#L252)), and so does the
  xd grid generator ([xd_grid_generator_adapter.py](../crossword/adapters/xd_grid_generator_adapter.py)).
- `Grid.validate()` ([grid.py:252](../crossword/domain/grid.py#L252))
  never checks symmetry. Its comment says symmetry is "taken care of" by
  the mirroring above.

**Three importers reject asymmetric grids.**
- `_validate_symmetry()` in the ipuz, xd and Crossword Compiler XML
  importers ([ipuz_import_adapter.py:43](../crossword/adapters/ipuz_import_adapter.py#L43),
  [xd_import_adapter.py:40](../crossword/adapters/xd_import_adapter.py#L40),
  [ccxml_import_adapter.py:44](../crossword/adapters/ccxml_import_adapter.py#L44)).

**Odd sizes are enforced by the UI and the grid generator, not the backend.**
- `PuzzleUseCases.create_puzzle()`
  ([puzzle_use_cases.py:86](../crossword/use_cases/puzzle_use_cases.py#L86))
  accepts any size of 1 or more already. Even sizes work in the domain
  model as they are: with an even size, no cell is its own mirror.
- The New puzzle dialog refuses even numbers
  ([lifecycle.js:92](../frontend/static/js/puzzle-file/lifecycle.js#L92)),
  and its label says "an odd positive integer"
  ([lifecycle.js:67](../frontend/static/js/puzzle-file/lifecycle.js#L67)).
- `GridGenerator` raises an error for even `n`
  ([grid_generator.py:80](../crossword/domain/grid_generator.py#L80)).
  It fills rows in mirror pairs from the outside in and finishes with a
  palindromic centre row, so it assumes both an odd size and symmetry.
  Its final check tests symmetry too
  ([grid_generator.py:613](../crossword/domain/grid_generator.py#L613)).
- The Generate button and the "Auto-generate" line in grid info are only
  enabled for odd sizes of 9 or more
  ([editor.js:179](../frontend/static/js/editor/editor.js#L179),
  [grid-mode.js:30](../frontend/static/js/editor/grid-mode.js#L30)).
- The theme-spec field must be a palindrome. The middle number of an
  odd-length spec goes in the centre row, and an even-sized grid has no
  centre row.

## The design

### A per-puzzle `symmetric` flag that lives on the Grid

Add a `symmetric: bool = True` attribute to `Grid`.

- `add_black_cell()`, `remove_black_cell()` and `undoredo()` change the
  mirror cell **only when `symmetric` is true**.
- `to_json()` writes `"symmetric"`. `from_json()` reads it and **defaults
  it to `True` when it is missing**, so every puzzle already in the
  database loads exactly as it does now.
- `from_json()` (in both `Grid` and `Puzzle`) stops depending on
  mirroring: it puts the stored black cells in **directly**, without
  adding mirrors. The stored list is already complete because
  `get_black_cells()` writes every black cell, so nothing is lost for
  symmetric grids. Asymmetric grids then survive the round trip.
- `Puzzle` gets a read-only `symmetric` property that passes through to
  its grid, like `symmetric_point()` does now.

The flag goes on the Grid, not in a new database column, for two reasons.
First, the puzzle's JSON blob already holds the grid, so **no schema
migration is needed**. Second, the puzzle's grid undo stack stores
complete grid JSON snapshots. Turning symmetry on or off therefore
becomes an ordinary grid edit that Undo and Redo handle with no extra
code.

### Turning symmetry on and off

New domain method `Puzzle.set_symmetric(on: bool)`. It follows the same
copy, push to undo, apply pattern as `toggle_black_cell()`.

- **Turning it off** always works. The black squares stay where they are;
  from then on, clicking a square changes only that square.
- **Turning it on** for a grid that isn't currently symmetric: the
  recommendation is to **refuse** with a clear message ("Grid isn't
  symmetric — cell (3, 7) has no partner at (13, 9)"). The alternative,
  quietly adding the missing mirror squares, could break word lengths or
  connectivity without the user noticing. A helper
  `Grid.find_asymmetric_cells()` returns the offending cells and is reused
  by the validator (below) and by the importers.

New use-case method `PuzzleUseCases.set_symmetry(user_id, name, on)`,
built with the existing `_edit` helper, and a new route
`PUT /api/puzzles/{name}/grid/symmetry` with body `{ "symmetric": bool }`.
The puzzle data the API returns gains `grid.symmetric` so the frontend can
show the current setting.

### Validation and statistics

- Turn the comment in `Grid.validate()` into a real check: when
  `symmetric` is true, report any asymmetric cells under a new `symmetry`
  error key. This should never fire in normal use, but it protects against
  hand-edited or imported data.
- When `symmetric` is false, asymmetry is **not** an error.
- `get_statistics()` gains a `symmetry` entry ("180° rotational" or
  "None") for the stats panel.

### Creating a puzzle

- `CreatePuzzle` schema
  ([schemas.py](../crossword/http_server/schemas.py)) gains an
  optional `symmetric: bool = True`, passed through `create_puzzle()` to
  `Grid(size, symmetric=...)`.
- New puzzle dialog: remove the odd-number check and change the label to
  "a positive integer, e.g. 15". Add a **Symmetric** checkbox, checked by
  default.

### Importing

- The ipuz, xd and CCXML importers stop rejecting asymmetric grids.
  Instead they set `symmetric` from what they find: true when
  `find_asymmetric_cells()` returns nothing, false otherwise. The
  `_validate_symmetry()` method copied into each importer goes away.
- The AcrossLite and .puz importers get the same detection so all formats
  behave the same.
- Grids of any size already import as long as the file's size is
  consistent; check this with even-sized test files.

### Exporting

No functional change is expected. The exporters write the grid cell by
cell and none of them is known to assume symmetry or an odd size. Phase 4
confirms this with even-sized and asymmetric round-trip tests for every
format. AcrossLite text, .puz, ipuz, xd, CCXML, NYT, and both PDFs.

### Grid generator

This is the part with the most uncertainty, so it comes last and is split
in two.

1. **Even sizes, symmetric.** Generalise `GridGenerator` so that for even
   `n` it fills `n/2` mirror row pairs and has **no centre row** (skip
   `_rank_middle_candidates` and the palindrome step). Theme specs for
   even `n` must have an even number of entries, because there is no
   centre row for a middle entry. Reject odd-length specs with a clear
   message. Relax the `n % 2 == 0` guard to "n >= 5". The xd generator
   adapter already falls back to the random generator for sizes outside
   {15, 21}, so it needs no change.
2. **Asymmetric generation is out of scope for this project.** For a
   puzzle with symmetry off, Generate still produces a symmetric grid. The
   generated grid comes back with `symmetric=True`; `apply_generated_grid()`
   then sets the flag back to the puzzle's own setting so the user's choice
   isn't overwritten. A truly freeform generator would be a separate
   project. It needs a different search, because each row can no longer
   be placed together with its mirror.

Frontend: enable Generate for any size of 9 or more (not only odd sizes),
and update the "Auto-generate" line in grid info to match.

### Frontend (grid mode)

- Add a **Symmetry: On / Off** toggle to the grid-mode toolbar or grid info
  panel. It calls the new route and re-renders through
  `_applyGridModeUpdate()`.
- Show the current symmetry in the grid info panel and the stats card.
- Clicking a cell needs no change. The backend decides whether to mirror.
- Optional: when symmetry is on, briefly highlight the mirror cell on
  hover so the user can see what a click will change.

## Phases

Each phase can ship by itself, with its own tests and commit.

| # | Phase | Main files | Result for the user |
|---|-------|------------|---------------------|
| 1 | **Even sizes in the UI** | `puzzle-editor.js` | New puzzle accepts 4, 10, 16, … (still symmetric). Smallest useful change. |
| 2 | **`symmetric` flag in the domain** | `grid.py`, `puzzle.py`, `test_grid.py`, `test_puzzle*.py` | Not visible yet. Grids stay asymmetric through save and reload; old puzzles load unchanged. |
| 3 | **Turning symmetry on and off** | `puzzle_use_cases.py`, `puzzle_routes.py`, `schemas.py`, `puzzle-editor.js`, `index.html` | Checkbox in New puzzle, toggle in grid mode, shown in stats; Undo and Redo work. |
| 4 | **Import / export** | the 5 import adapters, export tests | Asymmetric ipuz/xd/CCXML files import instead of being rejected; round trips verified. |
| 5 | **Generator for even sizes** | `grid_generator.py`, `test_grid_generator.py`, `puzzle-editor.js` | Generate works on even sizes of 9 or more; theme spec rules explained for even sizes. |
| 6 | **Docs** | `docs/dev/usecases.md`, `endpoints.md` (regenerate), wiki: User-Guide, Puzzle-Guidelines, API-Reference | Documentation matches the new behaviour. |

## Testing

- **Grid:** with symmetry off, adding or removing a cell changes only that
  cell; with it on, behaviour is unchanged. Even-sized grids mirror
  correctly, and no cell is its own mirror.
- **JSON:** an asymmetric grid survives `to_json` → `from_json` unchanged;
  JSON without the key loads as symmetric; a symmetric grid's black cells
  are identical before and after the `from_json` change.
- **Puzzle:** `set_symmetric(False)` → toggle a cell → undo → redo puzzle
  state and flag both restored. `set_symmetric(True)` on an asymmetric
  grid raises an error and leaves the puzzle unchanged.
- **Rotate:** rotating an asymmetric grid keeps it asymmetric and doesn't
  add mirror cells (`Grid.rotate()` calls `add_black_cell()`, so this is
  easy to get wrong).
- **Validate:** a symmetric grid with a hand-made asymmetry reports a
  `symmetry` error; the same grid with symmetry off doesn't.
- **Importers:** asymmetric files import with `symmetric=False`; the
  existing "rejects asymmetric" tests in `test_ipuz_import_adapter.py` and
  `test_ccxml_import_adapter.py` are rewritten to match.
- **Generator:** many seeds at n = 10, 12, 16 produce valid symmetric
  grids; an odd-length spec at even `n` is rejected.
- **Manual:** create a 10×10 asymmetric puzzle, fill it, save, reopen,
  export in every format.

## Open questions

1. **Turning symmetry back on for an asymmetric grid:** refuse (the
   recommendation above), or offer to "symmetrise" by adding the missing
   mirror squares?
2. **Default for the New puzzle checkbox:** always checked, or remember
   the last choice in settings?
3. **Other kinds of symmetry** (left–right mirror, diagonal) are sometimes
   used. Should the flag be a mode (`"rotational" | "none"`) from the
   start, so mirror symmetry can be added later without another format
   change? This costs little now and would avoid a second migration of
   the JSON key.
4. **Smallest allowed size:** creation currently allows 1×1. Should there
   be a sensible minimum, such as 3?
