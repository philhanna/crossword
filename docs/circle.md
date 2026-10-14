# Circled squares — project plan

## The problem this solves

Many themed puzzles circle some of their squares. The circled letters
spell a hidden word, trace a shape, or point at the theme. Right now a
puzzle has no way to mark a square as circled, so these puzzles can't be
built here or exported with their circles.

This plan lets the user circle or un-circle any white square while in
**Puzzle mode**. In **Grid mode** the circles are still shown but can't
be changed. Circles appear in the editor, in the dashboard thumbnails, and
in every PDF export (Solver PDF, Solution PDF and New York Times).

Out of scope for the first version: other square markings (shading,
coloured backgrounds, thick bars), and circles in the file-format exports
and imports. The last section describes how those formats could be added
later.

## How squares are drawn today

There are two separate SVG renderers, one in Python and one in the browser.

**Python: `ToSVG` in [to_svg.py](../crossword/domain/to_svg.py).**
`ToSVG.generate_cells()` ([to_svg.py:102](../crossword/domain/to_svg.py#L102))
draws a black rectangle for black squares and calls `generate_cell()` for
white ones. Word numbers are drawn afterwards by `generate_word_numbers()`.
There are two subclasses:

- `GridToSVG` draws an empty grid. It is used by the **Solver PDF**
  ([solver_pdf_export_adapter.py:50](../crossword/adapters/solver_pdf_export_adapter.py#L50)).
  Note that it is handed `puzzle.grid`, not the puzzle, so it can't see
  anything that is stored on the puzzle.
- `PuzzleToSVG` also draws the letters. It is used by the **Solution PDF**
  ([solved_pdf_export_adapter.py:48](../crossword/adapters/solved_pdf_export_adapter.py#L48)),
  the **New York Times** PDF
  ([nytimes_export_adapter.py:74](../crossword/adapters/nytimes_export_adapter.py#L74)),
  and the dashboard thumbnail
  (`PuzzleUseCases.get_puzzle_preview()`,
  [puzzle_use_cases.py:793](../crossword/use_cases/puzzle_use_cases.py#L793)).

**Browser: `buildPuzzleSvg()` in [grid-svg.js](../frontend/static/js/svg/grid-svg.js#L7).**
It builds the editor grid from the API response, in both Puzzle mode and
Grid mode. (There is also a `buildGridSvg()` in the same file, but nothing
calls it.) The data it reads comes from `_puzzle_response()`
([puzzle_routes.py:302](../crossword/http_server/puzzle_routes.py#L302)),
which sends `puzzle.cells` as a map from square index to
`{number?, letter?}`.

**Where puzzle-mode data lives.** Letters are stored on the `Puzzle`
(`Puzzle.cells`), not on the `Grid`. The grid only knows which squares are
black. A puzzle is saved as the JSON from `Puzzle.to_json()`
([puzzle.py:392](../crossword/domain/puzzle.py#L392)).

## The design

### Circles are stored on the Puzzle, like letters

Add a set of circled squares to `Puzzle`:

```python
self.circled_cells = set()      # {(r, c), ...}
```

Circles are part of the *fill* (they depend on the theme answers), not
the *grid structure*. Storing them next to the letters means they follow
the same rules letters already follow, so there are no new special cases
to explain:

- They stay at their `(r, c)` when the grid changes in Grid mode.
- A circle on a square that turns black is removed, just as the letter
  there is replaced by `*`. This happens in `Puzzle._apply_new_grid()`
  ([puzzle.py:510](../crossword/domain/puzzle.py#L510)): after it works out
  `new_black_cells`, it also does
  `self.circled_cells -= new_black_cells`.
- Grid undo/redo doesn't bring a removed circle back, in the same way it
  doesn't bring back a removed letter. This is acceptable because circles
  are added after the grid is settled.
- **Clear** (`clear_unlocked`) leaves circles alone. Circles belong to
  the puzzle's design, not to a particular fill attempt.

The alternative, storing circles on the `Grid`, would carry them through
grid undo/redo automatically and would let `GridToSVG(puzzle.grid)` see
them without changes. But it would put puzzle-mode data into the
structure that Grid mode owns, and it would mean changing `Grid.to_json()`,
which the grid undo stack and the grid generators also use. The extra
work in the Solver PDF (below) is a single argument, so the Puzzle is the
better home.

### Puzzle methods

```python
def is_circled(self, r, c) -> bool
def toggle_circle(self, r, c, undo=True)
```

`toggle_circle()` raises `ValueError` if `(r, c)` is black or outside the
grid. When `undo` is true it pushes `['circle', r, c]` onto the puzzle
undo stack. Toggling is its own opposite, so `undo()` and `redo()` handle
a `'circle'` entry the same way: toggle the square, then push the same
entry onto the other stack.

Circles are allowed in squares covered by a locked word. Locking protects
the letters, and a circle doesn't change any letter. (See open question 2.)

### JSON

`Puzzle.to_json()` adds a sorted list:

```json
"circled_cells": [[1, 5], [3, 7]]
```

`Puzzle.from_json()` reads it with `image.get('circled_cells', [])`, so
puzzles saved before this change load with no circles. No migration is
needed. Because the key is part of `to_json()`, circles are carried
through working copies, Save, Save As, content snapshots and history
restores without any further changes.

### Use case

Add to `PuzzleUseCases`, next to `set_cell_letter()`:

```python
def toggle_circle(self, user_id: int, name: str, r: int, c: int) -> Puzzle:
    """ Circle or un-circle a white square (Puzzle mode only) """
```

It uses the existing `_edit()` helper with `invalidate=False`, because
circles don't affect the fill order. Before changing anything it raises
`ValueError` if `puzzle.last_mode == "grid"`, with the message "Circles
can only be changed in Puzzle mode". This means the "not in Grid mode"
rule is enforced by the backend as well as the UI.

`_replay()` ([puzzle_use_cases.py:663](../crossword/use_cases/puzzle_use_cases.py#L663))
needs no change: it compares word texts before and after, and a circle
changes no text, so no clues are cleared.

### HTTP route

```
PUT /api/puzzles/{name}/cells/{r}/{c}/circle
```

This sits next to the existing `PUT /api/puzzles/{name}/cells/{r}/{c}`
(set letter). It has no body, toggles the circle, and returns the usual
`_puzzle_response()`. A `ValueError` becomes the normal `{"error": ...}`
response. Regenerate [docs/dev/endpoints.md](dev/endpoints.md) afterwards
(it is generated, not hand-edited), and add the method to
[docs/dev/usecases.md](dev/usecases.md).

`_puzzle_response()` marks circled squares inside the existing cell map:

```json
"cells": { "4": {"number": 5, "letter": "A", "circled": true} }
```

Putting it there, rather than in a separate list, has a useful side
effect. The editor decides whether there are unsaved changes by hashing
`puzzleData.puzzle` (`AppState.puzzleSavedHash`). Since the circle flag is
inside `puzzle.cells`, adding or removing a circle makes the puzzle
"dirty", and Save will prompt for a comment as it should.

### Drawing circles in Python (`ToSVG`)

Give the base class a set of circled squares, empty by default:

```python
self.circled_cells = kwargs.get('circled_cells', set())
```

- `PuzzleToSVG.__init__()` sets it from `puzzle.circled_cells`.
- `GridToSVG.__init__()` takes it from the `circled_cells` keyword
  argument, since a bare `Grid` has no circles.

In `generate_cells()`, for a white square, draw the circle **before**
calling `generate_cell()`. Numbers are drawn after all the cells, so the
order on the page is: square → circle → letter → number. The letter and
number then sit on top of the circle line:

```python
def generate_circle(self, r, c):
    """ Draws a circle inside the square at (r, c) """
    xbase, ybase = self.get_x_y_base(r, c)
    half = self.boxsize / 2
    elem = ET.SubElement(self.root, "circle")
    elem.set("cx", str(xbase + half))
    elem.set("cy", str(ybase + half))
    elem.set("r", str(half - 1))
    elem.set("fill", "none")
    elem.set("stroke", "black")
    elem.set("stroke-width", "1")
```

A radius of `half - 1` keeps the circle just inside the square's border,
which is how newspaper puzzles usually draw it.

### PDF exports

- **Solution PDF** and **New York Times**: no change. They already use
  `PuzzleToSVG(puzzle)`, which now draws the circles.
- **Solver PDF**: change the one line at
  [solver_pdf_export_adapter.py:50](../crossword/adapters/solver_pdf_export_adapter.py#L50) to
  ```python
  GridToSVG(puzzle.grid, circled_cells=puzzle.circled_cells)
  ```
- `_prepare_svg()` in both clue-sheet adapters rewrites the first
  `width=`/`height=` it finds with a regex. `<circle>` elements have no
  `width` or `height`, and the root `<svg>` element comes first anyway, so
  this is safe. A test should confirm it.
- The dashboard thumbnail gets circles for free through `PuzzleToSVG`.

### Drawing circles in the browser (`buildPuzzleSvg`)

In [grid-svg.js](../frontend/static/js/svg/grid-svg.js), after pushing a white square's
`<rect>` and before its number and letter, add:

```js
if (cd.circled) {
    parts.push(
        `<circle cx="${x + BOXSIZE / 2}" cy="${y + BOXSIZE / 2}" r="${BOXSIZE / 2 - 1.5}" ` +
        `fill="none" stroke="#555" stroke-width="1" pointer-events="none"/>`
    );
}
```

`cd` must be read before this point (today it is read inside the
`if (!black)` block, so the circle goes at the top of that block).
Notes:

- The circle is drawn on top of the square's fill, so it stays visible on
  the selected-word, cursor and locked-word highlights.
- `pointer-events="none"` keeps clicks working exactly as they do now.
- A mid-grey line matches the grey used for numbers, so the circle doesn't
  overpower the letters on screen. The PDFs use black.
- `buildPuzzleSvg()` is also used in Grid mode, so circles show there too,
  read-only. That lets the user see what a grid change would affect.
- The word editor dialog calls the same function
  ([editor.js:127](../frontend/static/js/editor/editor.js#L127)), so
  circles show there as well.

### Toggling circles in Puzzle mode

Clicks in Puzzle mode already mean something: one click selects the
across word, a double click selects the down word, and letter keys type
into the cursor square. So circling needs its own gesture. Offer two:

1. **A "Circle" button in the Puzzle-mode action bar**, in the group with
   Edit word / Fill order / Stats (`renderActionBar()`,
   [editor.js:165](../frontend/static/js/editor/editor.js#L165)),
   using the `radio_button_unchecked` icon. It toggles the circle on the
   **cursor square** of the selected word. It is disabled when no word is
   selected or the word editor dialog is open, in the same way
   `_updatePuzzleToolbar()` handles Edit word. It isn't rendered in Grid
   mode at all.
2. **Shift+click** on any white square. In `handlePuzzleClick()`
   ([grid-clicks.js:22](../frontend/static/js/editor/grid-clicks.js#L22)), check
   `event.shiftKey` first, before the single/double-click timer logic. If
   it is set, toggle the circle at the clicked square and return without
   changing the selection. Add `<kbd>Shift</kbd>+<kbd>Click</kbd> circle`
   to the Puzzle-mode keyboard hints in `renderPuzzleEditorLhs()`.

Both call a new `do_puzzle_toggle_circle(r, c)` in `puzzle-editor.js`. It
first commits any pending letters in the selected word (`_peCommitWord()`,
as undo/redo does), calls the new route, and on success sets
`AppState.puzzleData` and re-renders, **keeping** the current word
selection. On error it shows the message with `showMessageLine()`.

Grid mode needs no frontend guard beyond not offering the gestures:
`handleGridModeClick()` doesn't look at Shift, and the backend refuses the
call in Grid mode anyway.

### Undo/redo

Circle toggles go on the Puzzle-mode undo stack, so the existing Undo and
Redo buttons handle them with no frontend changes. As with every other
puzzle-mode edit, switching into Puzzle mode clears that stack
(`enter_puzzle_mode()`).

## Phases

1. **Domain:** `circled_cells`, `is_circled()`, `toggle_circle()`,
   undo/redo, JSON, and removing circles when a square turns black.
2. **SVG and PDFs:** `ToSVG.generate_circle()`, the `PuzzleToSVG` and
   `GridToSVG` changes, and the one-line Solver PDF change. At this point
   circles in a hand-edited puzzle show up in every PDF.
3. **API:** the use case, the route, `"circled"` in `_puzzle_response()`,
   and the regenerated endpoint docs.
4. **Frontend:** drawing in `buildPuzzleSvg()`, the Circle button,
   Shift+click, and the keyboard hint.

Each phase can be merged on its own. Phases 1–2 change no behaviour for
puzzles that have no circles.

## Testing

- **Puzzle:** toggle on → `is_circled` is true; toggle again → false.
  Toggling a black square raises `ValueError`. Toggle → undo → redo
  restores each state, and the redo stack gets the right entry.
- **JSON:** circles survive `to_json` → `from_json`; JSON without the key
  loads with no circles; `Puzzle.__eq__` treats puzzles that differ only in
  circles as different.
- **Grid changes:** circle a square, turn it black in Grid mode → the
  circle is gone. Circles on squares that stay white are unchanged after
  toggling a different square, rotating and generating.
- **Use case:** `toggle_circle` in Grid mode raises `ValueError` and
  doesn't save. In Puzzle mode it saves, and reloading shows the circle.
  The circle survives `copy_puzzle` (Save).
- **HTTP:** the route returns `"circled": true` for the square; a black
  square or Grid mode gives a 4xx with `{"error": ...}`.
- **SVG:** `PuzzleToSVG` output has one `<circle>` per circled square and
  none for a puzzle without circles. `GridToSVG` with `circled_cells`
  draws them, and without it draws none. In the output, each `<circle>`
  comes before its square's letter `<text>`.
- **PDF:** `_build_html()` for each of the three PDF adapters contains
  `<circle` when the puzzle has circles. (Checking the HTML avoids having
  to run Chrome in the tests.)
- **Manual:** circle a few squares with both gestures; undo and redo;
  switch to Grid mode and check the circles show but Shift+click and the
  button don't exist; save, close, reopen; check the dashboard thumbnail;
  export all three PDFs and look at them.

## Later: circles in the file formats

These are not part of this plan, but the data model above supports them
without changes. AcrossLite binary (`.puz`) has since been done, for both
export and import; the others remain open.

| Format | How circles are stored |
|---|---|
| AcrossLite binary (`.puz`) | `GEXT` extra section, flag `0x80` per square. The `puz` library already used by the adapters reads and writes it through `puzzle.markup()`. **Done** (export and import). |
| ipuz | A cell in `"puzzle"` becomes an object: `{"cell": 5, "style": {"shapebg": "circle"}}`. |
| Crossword Compiler XML | `background-shape="circle"` on the `<cell>` element. |
| xd | No standard form. Some files use lowercase letters in the grid plus a header note; check the spec before supporting it. |
| AcrossLite text | Not supported by the format. |

## Open questions

1. **Keyboard shortcut.** Letter keys already type into the grid, so a
   shortcut needs a non-letter key. Is the button plus Shift+click enough,
   or should there be a key (for example `.` or `Insert`) that toggles the
   cursor square?
2. **Locked words.** Should circling be allowed in squares covered by a
   locked word? This plan says yes, because circles don't change letters.
   Say so if locking should freeze circles too.
3. **Circles in Grid mode.** This plan shows them read-only. Would you
   rather hide them in Grid mode to keep that view clean?
4. **Statistics.** Should the Stats panel show the number of circled
   squares, or list the circled letters in reading order (handy for
   checking a hidden-word theme)?
