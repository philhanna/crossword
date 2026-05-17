# Server-side fill-order cache

## Goal

`GET /api/puzzles/<name>/fill-order` is one of the more expensive puzzle
endpoints. Each call runs `FillPriorityAnalyzer.rank_slots()`, which asks the
word list for candidate counts across incomplete slots and performs
connectivity analysis. The result only changes when the puzzle's grid layout
or fill text changes, so repeated polling is a good fit for a server-side
cache.

## Implementation

The cache now lives in
[`PuzzleUseCases`](../../crossword/use_cases/puzzle_use_cases.py) as
`self._fill_order_cache: dict`, keyed by `(user_id, name)`.

```python
def __init__(self, persistence, word_uc=None, grid_generator=None):
    self.persistence = persistence
    self.word_uc = word_uc
    self.grid_generator = grid_generator
    self._fill_order_cache: dict = {}

def _invalidate_fill_order(self, user_id, name):
    self._fill_order_cache.pop((user_id, name), None)
```

`get_fill_order()` checks the cache before loading the puzzle or constructing a
new analyzer. On a miss, it computes the API payload, stores it under the
`(user_id, name)` key, and returns it.

## Invalidation rules

The use-case layer owns both cache reads and all puzzle mutations that can
change fill-order analysis, so invalidation stays local to
`puzzle_use_cases.py`.

These methods invalidate the cache before mutating or deleting puzzle state:

| Method | Reason |
|---|---|
| `delete_puzzle` | Removes the entry and avoids orphaned cache growth |
| `rename_puzzle` | Drops the old `(user_id, old_name)` key |
| `switch_to_puzzle_mode` | Rebuilds puzzle-mode word structures from the grid |
| `toggle_black_cell` | Changes slot boundaries and crossings |
| `rotate_grid` | Repositions and reshapes all slots |
| `generate_grid` | Replaces the grid layout entirely |
| `undo_grid` | Reverts a grid edit that may alter slot structure |
| `redo_grid` | Reapplies a grid edit that may alter slot structure |
| `set_cell_letter` | Changes one or more crossing patterns |
| `set_word_clue` when `text is not None` | Changes the stored fill text |
| `undo_puzzle` | Reverts a fill-text edit |
| `redo_puzzle` | Reapplies a fill-text edit |

These methods intentionally do not invalidate:

| Method | Reason |
|---|---|
| `create_puzzle` | No prior cache entry exists |
| `copy_puzzle` | Source entry remains valid; copy starts cold |
| `set_puzzle_title` | Title is not part of fill analysis |
| `set_word_clue` with clue-only updates | Clue text does not affect patterns or candidate counts |
| `switch_to_grid_mode` | Only flips editing mode; puzzle content is unchanged |

## Behavior notes

- The cached value is the final API-shaped dict, not raw analyzer objects.
- The cache is process-local and in-memory; restarting the server clears it.
- `top_n` is not part of the cache key today, so callers should continue using
  the endpoint's standard access pattern rather than mixing multiple limits for
  the same puzzle in one process.

## Tests

Coverage lives in
[`crossword/tests/test_puzzle_use_cases.py`](../../crossword/tests/test_puzzle_use_cases.py):

1. `test_get_fill_order_cached_on_second_call` verifies repeated reads reuse
   the cached result.
2. `test_get_fill_order_invalidated_by_set_cell_letter` verifies a fill edit
   forces recomputation.
3. `test_get_fill_order_not_invalidated_by_clue_only_set_word_clue` verifies
   clue-only updates keep the cached result.
