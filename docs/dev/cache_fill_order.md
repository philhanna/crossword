# Server-side fill-order cache

## Goal

`GET /api/puzzles/<name>/fill-order` is the most expensive endpoint in the
server.  Each call runs `FillPriorityAnalyzer.rank_slots()`, which queries the
word list for candidate counts on every incomplete slot and performs a BFS
connectivity check for each one.  The result only changes when the puzzle's
word-text content or grid structure changes.  A server-side cache eliminates
redundant computation when the client polls the endpoint repeatedly without
editing the puzzle in between.

## Current state

`PuzzleUseCases.get_fill_order()` (`puzzle_use_cases.py:435`) constructs a
fresh `FillPriorityAnalyzer` and calls `rank_slots()` on every request.  There
is a small per-call dict (`cache = {}` at `fill_priority.py:94`) that avoids
re-querying identical crossing patterns within a single ranking pass, but
nothing persists across HTTP requests.

## Design

### Where the cache lives

Add a `_fill_order_cache: dict` attribute to `PuzzleUseCases.__init__`.  The
use-case class already owns `get_fill_order()` and every mutating method that
would invalidate it, so no other layer needs to change.  `AppContainer` and all
HTTP handlers are untouched.

```python
def __init__(self, persistence, word_uc=None, grid_generator=None):
    self.persistence = persistence
    self.word_uc = word_uc
    self.grid_generator = grid_generator
    self._fill_order_cache: dict = {}
```

### Cache key

`(user_id, name)` — a 2-tuple.  Each user's working copy of a puzzle is
independent, so user isolation is required.

### Read path

In `get_fill_order()`, check the cache before computing:

```python
def get_fill_order(self, user_id, name, top_n=10):
    key = (user_id, name)
    if key in self._fill_order_cache:
        return self._fill_order_cache[key]
    puzzle = self.persistence.load_puzzle(user_id, name)
    analyzer = FillPriorityAnalyzer(self.word_uc)
    result = {
        "fill_priority": [
            { ... }
            for item in analyzer.rank_slots(puzzle, top_n=top_n)
        ]
    }
    self._fill_order_cache[key] = result
    return result
```

### Invalidation helper

```python
def _invalidate_fill_order(self, user_id, name):
    self._fill_order_cache.pop((user_id, name), None)
```

Call this at the start of every mutating method listed below, before the
persistence or domain operation, so a failed operation leaves no stale entry.

## Invalidation table

| Method | Reason |
|---|---|
| `toggle_black_cell` | Grid structure changes; word slots are added, removed, or resized |
| `rotate_grid` | All slots change position and direction |
| `generate_grid` | Entire grid layout replaced |
| `undo_grid` | Grid structure reverted |
| `redo_grid` | Grid structure reapplied |
| `switch_to_puzzle_mode` | Word slots are rebuilt from the current grid |
| `set_cell_letter` | One or more word patterns change |
| `set_word_clue` (when `text` is provided) | Word text changes; invalidate only when `text is not None` |
| `undo_puzzle` | A word-text change is reverted |
| `redo_puzzle` | A word-text change is reapplied |
| `rename_puzzle` | The old cache key becomes orphaned; drop it |
| `delete_puzzle` | Same — drop the key to avoid unbounded growth |

### Methods that do NOT invalidate

| Method | Reason |
|---|---|
| `set_puzzle_title` | Title is not part of fill analysis |
| `set_word_clue` (clue only, no `text`) | Clue text does not affect word patterns or candidate counts |
| `switch_to_grid_mode` | Only changes the mode flag; word content is unchanged |
| `copy_puzzle` | Source entry remains valid; new name starts with no cache entry |
| `create_puzzle` | New puzzle; no existing cache entry to invalidate |

## Files changed

| File | Change |
|---|---|
| `crossword/use_cases/puzzle_use_cases.py` | Add `_fill_order_cache` in `__init__`; add `_invalidate_fill_order()`; update `get_fill_order()` to check cache; call `_invalidate_fill_order()` in the ten methods listed above |

No other files need to change.

## Testing

Add a test in `crossword/tests/test_puzzle_use_cases.py` that:

1. Calls `get_fill_order()` twice without any edit between calls and asserts
   that `FillPriorityAnalyzer.rank_slots` is only called once (mock or spy on
   the analyzer).
2. Calls `set_cell_letter()` between two `get_fill_order()` calls and asserts
   that `rank_slots` is called both times (cache was invalidated).
3. Calls `set_word_clue()` with a clue only (no `text`) and asserts the cache
   is not invalidated.
