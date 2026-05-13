# Grid Generator Port Plan

## Goal

Extract grid generation out of `Puzzle.generate_grid()` into a driven-side port
so that `PuzzleUseCases` can delegate to either of two adapters:

1. **`RandomGridGeneratorAdapter`** — the current algorithmic generator
2. **`XdGridGeneratorAdapter`** — picks a grid of the correct size at random
   from the xdfile archive database (details TBD)

The HTTP handler and all frontend code are unchanged.

---

## Port — `crossword/ports/grid_generator_port.py` (new)

```python
class GridGeneratorPort(ABC):
    @abstractmethod
    def generate(self, n: int) -> Grid:
        """
        Return a valid crossword grid of size n×n.
        Raises RuntimeError if no grid can be produced.
        """
```

The contract is minimal: takes a size, returns a `Grid`. The `RuntimeError`
convention matches what the existing handler already catches and turns into a
`{"notice": ...}` response.

---

## Adapter 1 — `crossword/adapters/random_grid_generator_adapter.py` (new)

Thin wrapper around the existing `GridGenerator`:

```python
class RandomGridGeneratorAdapter(GridGeneratorPort):
    def generate(self, n: int) -> Grid:
        grid = GridGenerator(n).generate()
        if grid is None:
            raise RuntimeError("Grid generation failed: ran out of attempts")
        return grid
```

No logic change — this is exactly what `Puzzle.generate_grid()` does today.

---

## Adapter 2 — `crossword/adapters/xd_grid_generator_adapter.py` (new)

Opens the xdfile SQLite database and picks a random grid of size `n`:

```sql
SELECT   *
FROM     grids
WHERE    size = $n
ORDER BY RAND()
LIMIT    1;
```

The `grid_text` column is a newline-separated string of `n` rows, each of
length `n`, using `"."` for white cells and `"#"` for black cells.

To build the `Grid`:

1. Split `grid_text` on `"\n"` to get a list of row strings.
2. Iterate rows and columns (converting to 1-based indices) and collect every
   `[row, col]` tuple where the character is `"#"` into a `black_cells` list.
3. Build `{"n": size, "black_cells": black_cells}`.
4. Call `Grid.from_json(...)` with that dict to get the domain `Grid` object.

If no row is found for the requested size, raise `RuntimeError` so the handler
returns a `{"notice": ...}` response.

```python
class XdGridGeneratorAdapter(GridGeneratorPort):
    def __init__(self, xdfile: str):
        self.xdfile = xdfile

    def generate(self, n: int) -> Grid:
        # query xdfile DB for a random grid of size n
        # parse grid_text JSON → black_cells list of 1-based [row, col] tuples
        # return Grid.from_json({"n": n, "black_cells": black_cells})
        # raise RuntimeError if no grid of that size exists
        ...
```

---

## Domain change — `crossword/domain/puzzle.py`

Remove the adapter import from `generate_grid()`; accept a `Grid` directly.
Rename the method to `apply_generated_grid()` to reflect that the domain no
longer controls how the grid was produced:

```python
def apply_generated_grid(self, newgrid: Grid):
    self.grid_undo_stack.append(self.grid.to_json())
    self.grid_redo_stack = []
    self._apply_new_grid(newgrid)
```

---

## Use case change — `crossword/use_cases/puzzle_use_cases.py`

Inject the port via `__init__` and delegate in `generate_grid()`:

```python
class PuzzleUseCases:
    def __init__(self, persistence, word_uc=None, grid_generator=None):
        ...
        self.grid_generator = grid_generator   # GridGeneratorPort

    def generate_grid(self, user_id, name):
        puzzle = self.persistence.load_puzzle(user_id, name)
        newgrid = self.grid_generator.generate(puzzle.n)  # raises RuntimeError if unavailable
        puzzle.apply_generated_grid(newgrid)
        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle
```

---

## Wiring — `crossword/wiring/__init__.py`

Select the adapter based on whether `xdfile` is configured:

```python
xdfile = config.get("xdfile")
if xdfile:
    grid_generator = XdGridGeneratorAdapter(xdfile)
else:
    grid_generator = RandomGridGeneratorAdapter()

puzzle_uc = PuzzleUseCases(persistence, word_uc=word_uc, grid_generator=grid_generator)
```

`XdGridGeneratorAdapter` is only instantiated when `xdfile` is present in
config; otherwise the random adapter is the default.

---

## Export — `crossword/ports/__init__.py`

Export `GridGeneratorPort` alongside the other ports.

---

## Files touched

| File | Change |
|---|---|
| `ports/grid_generator_port.py` | **new** — port ABC |
| `adapters/random_grid_generator_adapter.py` | **new** — wraps `GridGenerator` |
| `adapters/xd_grid_generator_adapter.py` | **new** — xdfile adapter (TBD) |
| `domain/puzzle.py` | rename `generate_grid` → `apply_generated_grid`, remove internal import |
| `use_cases/puzzle_use_cases.py` | inject `grid_generator`, delegate to it |
| `wiring/__init__.py` | select adapter based on `config["xdfile"]` |
| `ports/__init__.py` | export new port |
