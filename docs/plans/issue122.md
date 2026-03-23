# Issue 122 — Generate Grids Matching Specified Criteria

## Problem

Users want to generate a crossword grid that satisfies structural constraints — e.g.:
- Exactly two 11-letter words
- Exactly two 9-letter words
- No words longer than 11 letters
- Those four long words must not overlap (share no cells)

The issue proposes a random search with a max-iterations limit.

## Approach

Use a **random restart** search (Monte Carlo): repeatedly build candidate grids by randomly placing black cells, check against the criteria after each candidate is complete, and return the first grid that satisfies all constraints. This is the approach suggested in the issue and is practical for typical grid sizes (15×15).

---

## Design

### 1. `GridCriteria` dataclass — `crossword/domain/grid_criteria.py`

```python
@dataclass
class GridCriteria:
    size: int                        # grid is size × size
    exact_counts: dict[int, int]     # {word_length: required_count}
    max_word_length: int | None      # no word longer than this (None = no limit)
    non_overlapping: bool            # if True, words matching exact_counts keys
                                     # must not share any cell
```

Example for the issue's stated requirements:
```python
GridCriteria(
    size=15,
    exact_counts={11: 2, 9: 2},
    max_word_length=11,
    non_overlapping=True,
)
```

The `non_overlapping` flag checks that all words whose lengths appear in `exact_counts` share no cells with each other.

### 2. `GridGenerator` — `crossword/domain/grid_generator.py`

```python
class GridGenerator:
    def generate(self, criteria: GridCriteria, max_iterations: int = 10000) -> Grid | None
```

**Algorithm:**

```
for attempt in range(max_iterations):
    grid = Grid(criteria.size)
    cells = list of all (r, c) in upper-left triangle  # symmetry halves the search
    shuffle(cells)
    for (r, c) in cells:
        grid.add_black_cell(r, c, undo=False)
        if _matches(grid, criteria):
            return grid   # found one
    # optional: check partial progress and prune early
return None
```

**Evaluation — `_matches(grid, criteria) -> bool`:**

1. Compute `grid.get_word_lengths()` → `{length: {alist, dlist}}`
2. Check `max_word_length`: no key in the table > criteria.max_word_length
3. Check `exact_counts`: for each `(length, required)`, sum `len(alist) + len(dlist)` == required
4. If `non_overlapping`: collect the cell sets for each matching word and verify the sets are pairwise disjoint

**Cell set for a word of length L starting at (r, c) across:**
`{(r, c), (r, c+1), ..., (r, c+L-1)}`

Similarly for down words. This can be computed directly from `get_numbered_cells()` without instantiating a `Puzzle`.

### 3. `GridUseCases.generate_grid` — add to existing use cases

```python
def generate_grid(
    self,
    user_id: int,
    name: str,
    criteria: GridCriteria,
    max_iterations: int = 10000,
) -> Grid:
    grid = GridGenerator().generate(criteria, max_iterations)
    if grid is None:
        raise ValueError(f"No grid found after {max_iterations} iterations")
    self.persistence.save_grid(user_id, name, grid)
    return grid
```

### 4. HTTP endpoint — add to router

```
POST /api/grids/generate
```

Request body:
```json
{
  "name": "my-generated-grid",
  "size": 15,
  "exact_counts": {"11": 2, "9": 2},
  "max_word_length": 11,
  "non_overlapping": true,
  "max_iterations": 10000
}
```

Response: same JSON shape as `GET /api/grids/{name}` (200), or 422 with error message if no grid found within the iteration limit.

### 5. Frontend (optional, deferred)

Add a **"Generate…"** option to the Grid menu (enabled in `home` state only). It opens a dialog where the user specifies size and word-length constraints, then calls the endpoint. On success, open the resulting grid in the editor.

---

## Key implementation details

### Symmetry and search space

`add_black_cell` already enforces 180° rotational symmetry, so we only need to iterate over cells in the upper-left triangle (approximately `n²/2` cells), cutting the search space in half.

For a 15×15 grid the upper triangle has ~112 candidate cells. Shuffling and iterating over them gives a different random candidate each attempt.

### Early exit / pruning

After placing each black cell, it's worth checking whether the current partial grid has already violated a hard constraint (e.g., a word longer than `max_word_length` has appeared). If so, abandon this candidate immediately rather than finishing the placement loop.

### Recursion depth

`validate_interlock` uses recursive flood-fill which can hit Python's default recursion limit on large grids. The generator doesn't call `validate()` (which is expensive), it only checks word lengths and counts. This keeps the inner loop fast.

### Max iterations tuning

10,000 is a reasonable default for typical constraints. For very tight constraints (e.g., "exactly one 15-letter word") the user may need to increase it. The endpoint accepts `max_iterations` as a parameter.

---

## File changes

| File | Change |
|------|--------|
| `crossword/domain/grid_criteria.py` | New — `GridCriteria` dataclass |
| `crossword/domain/grid_generator.py` | New — `GridGenerator` class |
| `crossword/use_cases/grid_use_cases.py` | Add `generate_grid()` method |
| `crossword/http_server.py` | Add route `POST /api/grids/generate` |
| `crossword/tests/test_grid_generator.py` | New — unit tests |
| `frontend/static/js/app.js` | (deferred) Add "Generate…" menu item |

---

## Tests

- `test_criteria_exact_counts_pass` — grid whose word lengths match criteria → returns it
- `test_criteria_exact_counts_fail` — grid that doesn't match → returns None (max_iterations=1)
- `test_criteria_max_word_length` — word longer than limit → rejected
- `test_criteria_non_overlapping_pass` — target words have disjoint cells → accepted
- `test_criteria_non_overlapping_fail` — target words share cells → rejected
- `test_generate_finds_grid` — integration test with small grid (e.g., 7×7) and loose criteria
- `test_generate_returns_none_on_impossible` — criteria that can't be satisfied → None after small max_iterations

---

## Out of scope for this issue

- Enumerating *all* matching grids
- Constraint-satisfaction / backtracking solver (smarter than random restart)
- Frontend UI for the generate dialog
