# Issue 187 — Server-side Logging of Puzzle Undo/Redo Requests

## Problem

When a user undoes or redoes a word-text change in the puzzle editor, the server silently applies the operation and saves. There is no log record of what changed, which makes debugging and auditing difficult.

## Current flow

```
Frontend POST /api/puzzles/{name}/undo
  → handle_undo_puzzle
    → puzzle_uc.undo_puzzle(user_id, name)
      → puzzle.undo()          # pops undo_stack, restores old text
      → persistence.save_puzzle(...)
  ← _puzzle_response(puzzle)   # nothing logged anywhere
```

The undo stack stores frames of the form `['text', seq, direction, old_text]`. Before `puzzle.undo()` is called, the top of the stack tells us exactly what is about to be reverted.

## Existing logging infrastructure

The project already uses Python's standard `logging` module. `log_level` is set via `~/.config/crossword/config.yaml` (default `INFO`) and initialised in `crossword/__init__.py`. No new infrastructure is needed — we just need a module-level logger in `puzzle_use_cases.py`.

---

## Design

### What to log

Each log entry includes the **full contents of the stack** at the time of the request, plus which frame is being applied.

**Stack non-empty (action taken):**
```
INFO  undo: puzzle=<name> stack=[['text',3,'a','CRANE'],['text',5,'d','TABLE']] applying=['text',5,'d','TABLE']
INFO  redo: puzzle=<name> stack=[['text',3,'a','CRANE']] applying=['text',3,'a','CRANE']
```

**Stack empty (no-op):**
```
INFO  undo requested but stack empty: puzzle=<name>
INFO  redo requested but stack empty: puzzle=<name>
```

The full stack gives the complete picture of pending operations at the moment the request arrives — the `applying` field highlights which frame is about to be popped.

### Where to log

**`crossword/use_cases/puzzle_use_cases.py`** — the use case is the right layer. The handler only knows the puzzle name; the use case has the loaded puzzle and can inspect the stack before acting.

### How to read the stack

The undo/redo stacks hold frames: `['text', seq, direction, old_text]`

- **Before `puzzle.undo()`**: `puzzle.undo_stack` is the full stack; `puzzle.undo_stack[-1]` is the frame about to be applied.
- **Before `puzzle.redo()`**: same, using `puzzle.redo_stack`.

Capture the stack as a copy before the mutation so the log reflects the pre-operation state.

---

## Implementation

### `puzzle_use_cases.py`

Add at module level:
```python
import logging
logger = logging.getLogger(__name__)
```

Update `undo_puzzle`:
```python
def undo_puzzle(self, user_id: int, name: str) -> Puzzle:
    puzzle = self.persistence.load_puzzle(user_id, name)

    if puzzle.undo_stack:
        stack_snapshot = list(puzzle.undo_stack)
        applying = puzzle.undo_stack[-1]
        puzzle.undo()
        self.persistence.save_puzzle(user_id, name, puzzle)
        logger.info(
            "undo: puzzle=%s stack=%s applying=%s",
            name, stack_snapshot, applying,
        )
    else:
        logger.info("undo requested but stack empty: puzzle=%s", name)

    return puzzle
```

Update `redo_puzzle` identically (swapping `undo_stack` → `redo_stack` and `"undo"` → `"redo"`).

---

## File changes

| File | Change |
|------|--------|
| `crossword/use_cases/puzzle_use_cases.py` | Add `import logging`, module-level logger, log calls in `undo_puzzle` and `redo_puzzle` |

No other files need to change.

---

## Tests

Add to `crossword/tests/test_puzzle_use_cases.py` (or a new `test_puzzle_undo_redo_logging.py`):

- `test_undo_logs_full_stack` — asserts the log message contains the complete undo stack and the applying frame
- `test_undo_logs_empty_stack` — asserts the "stack empty" message is logged when undo_stack is empty
- `test_redo_logs_full_stack` — same for redo with non-empty redo_stack
- `test_redo_logs_empty_stack` — same for redo with empty redo_stack
- `test_undo_logs_stack_snapshot_not_mutated` — stack captured in the log reflects pre-undo state even though `puzzle.undo()` mutates the list

Use `unittest.mock.patch` on `crossword.use_cases.puzzle_use_cases.logger` to capture calls without touching the real logging system.

---

## Notes

- `list(puzzle.undo_stack)` makes a shallow copy before `puzzle.undo()` mutates the stack, so the logged snapshot is always the pre-operation state.
- Log level is `INFO` — undo/redo are normal user actions, not errors. Use `DEBUG` instead if the volume becomes noisy in production.
- Only `'text'` frames are currently pushed onto the stacks. If other frame types are added in future, the logging still works unchanged since it logs the raw frame list.
