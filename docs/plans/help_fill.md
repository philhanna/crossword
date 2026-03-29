# Help Fill Plan

## Goal

Implement the idea from GitHub issue #202: help a constructor choose a better fill order by ranking word slots according to how structurally important they are to the grid.

The first version should be an offline analysis tool, not a UI feature. Given a puzzle name, it should report the best candidate slots to fill first as `(number, A|D)` pairs, along with the reason for their ranking.

## Background

Issue #202 proposes using the interlock idea in reverse:

- Treat the puzzle's white cells as a connectivity graph
- For each open slot, temporarily remove all cells in that slot
- Measure whether the remaining white-cell graph becomes disconnected
- Prefer slots whose removal would break connectivity

The issue comment also suggests this should be a weighted heuristic rather than a rigid rule. Structural criticality should be a major signal, but not the only signal over time.

## Scope For V1

Build a command-line tool that:

- loads a puzzle by name
- enumerates every across and down slot
- computes a structural criticality score for each slot
- prints the ranked slots in descending priority order

V1 should not:

- change puzzle fill automatically
- modify the UI
- require HTTP endpoints
- depend on a full search or backtracking engine

## Output Shape

The initial output can be plain text, for example:

```text
14A score=125 critical=yes components=3 sizes=[18,12,7] len=5 text="     "
7D  score=98  critical=yes components=2 sizes=[21,14]   len=7 text="A  E  "
22A score=40  critical=no  components=1 sizes=[35]      len=4 text="    "
```

This is intentionally simple so the rankings can be compared against human intuition before any UI work.

## Baby Steps

### Step 1: Represent slots in one place

Add a small helper layer that can iterate all puzzle slots and describe each one uniformly.

Suggested fields:

- `seq`
- `direction`
- `length`
- `text`
- `is_complete`
- `cells`

This should work for both across and down words and should avoid duplicating iteration logic in later scoring code.

### Step 2: Add white-cell connectivity analysis

Create a pure helper that:

- builds the set of white cells in the current grid
- optionally excludes a given set of cells
- computes connected components over orthogonal neighbors
- returns component count and component sizes

This should not mutate the grid or the puzzle.

### Step 3: Define slot structural criticality

For each slot:

- remove that slot's cells from the white-cell graph
- compute connected components on the remainder
- record:
  - whether the graph disconnects
  - number of components
  - sizes of components

This gives the core "bridge slot" signal from issue #202.

### Step 4: Rank slots with a simple V1 score

Start with one clear scoring function. For example:

```text
score =
  +100 if removal disconnects
  +20 * (component_count - 1)
  +min(component_sizes) if disconnected
  +10 if slot is incomplete
  +small bonus for shorter slots
```

The exact weights are less important than having a stable first version that is easy to inspect and tune.

### Step 5: Build the offline command

Add a CLI entry point such as:

```bash
python -m crossword.tools.rank_fill_order PUZZLE_NAME
```

Optional later flags:

- `--top 20`
- `--json`
- `--include-complete`

### Step 6: Add focused tests

Write tests for:

- a slot whose removal does not disconnect the graph
- a slot whose removal splits the graph into two components
- a slot whose removal splits the graph into three or more components
- ranking that places a known bridge slot above non-critical slots
- analyzer behavior that does not mutate puzzle state

## Suggested Module Layout

### Domain

Add a new module:

- `crossword/domain/fill_priority.py`

Possible contents:

- `SlotInfo` dataclass
- `SlotPriority` dataclass
- `FillPriorityAnalyzer`

Suggested API:

```python
class FillPriorityAnalyzer:
    def rank_slots(self, puzzle) -> list[SlotPriority]:
        ...
```

### Tooling

Add a small offline command module:

- `crossword/tools/rank_fill_order.py`

Responsibilities:

- load puzzle by name using existing use-case or persistence path
- call `FillPriorityAnalyzer`
- print ranked results

### Tests

Add:

- `crossword/tests/test_fill_priority.py`

If command behavior is tested separately, optionally add:

- `crossword/tests/tools/test_rank_fill_order.py`

## Data Model Sketch

Suggested `SlotInfo` fields:

```python
@dataclass
class SlotInfo:
    seq: int
    direction: str
    length: int
    text: str
    is_complete: bool
    cells: list[tuple[int, int]]
```

Suggested `SlotPriority` fields:

```python
@dataclass
class SlotPriority:
    seq: int
    direction: str
    length: int
    text: str
    is_complete: bool
    critical: bool
    component_count: int
    component_sizes: list[int]
    score: int
```

## Algorithm Sketch

### Enumerate slots

- iterate `puzzle.across_words.values()`
- iterate `puzzle.down_words.values()`
- turn each word into a `SlotInfo`

### Compute connected components

- start with all non-black cells from `puzzle.grid`
- subtract any excluded cells
- if no cells remain, return zero components
- flood fill iteratively over orthogonal neighbors

### Score one slot

- exclude the slot's cells
- compute connected components
- `critical = component_count > 1`
- calculate score using the V1 weighting

### Rank all slots

- score every slot
- sort descending by:
  - `score`
  - `critical`
  - shorter length first
  - lower sequence number as final tie-break

## Why This Fits The Existing Code

- `Grid` already knows which cells are black
- `Puzzle` already exposes across and down words
- `Word.cell_iterator()` already gives the cells for each slot
- the recent interlock work already frames white-cell connectivity as a graph problem

The new analyzer can remain read-only and independent of the existing validation methods.

## Phase 2 Ideas

Once V1 is useful, add fill-oriented signals that go beyond raw structure.

Possible additions:

- candidate count from the dictionary matcher
- crossing pressure: number of unfinished crossing slots
- near-forced bonus for slots with very few candidates
- frontier bonus for slots touching partly filled regions

At that point, ordering can become:

1. forced or near-forced slots
2. structurally critical slots
3. everything else

## Phase 3 Integration

If the offline tool proves useful, expose the analyzer through:

- a use case layer method
- an HTTP endpoint
- an optional UI panel or highlight mode

That should happen only after the ranking logic feels trustworthy in CLI form.

## Risks And Open Questions

- The issue's theory is about fill success, but V1 only measures structure
- A structurally critical slot may still be easy, while a non-critical slot may be nearly forced
- Some grids may rank many slots similarly, so output explanations matter
- Weight tuning will probably require trying the tool against several real construction dead ends

## Recommended Implementation Order

1. Add slot extraction helper
2. Add pure connectivity helper with excluded cells
3. Add `FillPriorityAnalyzer.rank_slots()`
4. Add tests for critical and non-critical cases
5. Add CLI command for a named puzzle
6. Try it on real puzzles and tune weights
7. Only then consider HTTP or UI integration

