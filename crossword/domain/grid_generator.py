from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .grid import Grid

@dataclass
class GeneratorSettings:
    # User-facing (Could be overridden from YAML)
    BLACK_CELL_PERCENT_MIN: float = 0.10
    BLACK_CELL_PERCENT_MAX: float = 0.20
    THEME_BLACK_CELL_PERCENT_MAX: float = 0.25  # theme specs need more room to fit

    # Internal (Hardcoded safety rails)
    MAX_ITERATIONS: int = 256
    MAX_NODES: int = 2000   # max candidates tried per _search call before bailing out
    STACK_MAX = 7  # words longer than this may not be stacked in adjacent rows/columns

BLACK = "#"
WHITE = "."
UNKNOWN = "?"


class GridGenerator:
    """Generates random valid crossword grids of a given odd size.

    The generator uses a randomised backtracking search over row patterns,
    building the grid from the outside in (top and bottom simultaneously)
    toward the centre row.  180-degree rotational symmetry is maintained
    throughout by always placing each row together with its mirror partner.

    Rules enforced on every generated grid:
      - 180-degree rotational symmetry.
      - Every across and down entry is at least 3 letters long.
      - All white cells form a single connected region.
      - No word longer than STACK_MAX letters is directly stacked above or
        beside another such word in an adjacent row or column.

    Usage::

        gen = GridGenerator(15, seed=42)
        grid = gen.generate()   # returns a domain Grid object
    """

    def __init__(
        self,
        n: int,
        seed: Optional[int] = None,
        min_black_pct: float = GeneratorSettings.BLACK_CELL_PERCENT_MIN,
        max_black_pct: float = GeneratorSettings.BLACK_CELL_PERCENT_MAX,
        max_attempts: int = GeneratorSettings.MAX_ITERATIONS,
        spec: Optional[Sequence[int]] = None,
    ):
        """Initialise the generator and pre-compute legal row templates.

        Args:
            n: Grid size (must be an odd integer >= 5).
            seed: Optional random seed for reproducible output.
            min_black_pct: Minimum fraction of cells that must be BLACK
            max_black_pct: Maximum fraction of cells that may be BLACK
            max_attempts: Number of top-level randomised search attempts
                before giving up.
            spec: Optional palindromic list of theme-word lengths, read top
                to bottom.  When given, the grid has exactly these Across
                theme entries in that order, no entry (either direction)
                longer than the longest theme word or with a length falling
                between two theme lengths, and no Down entry with a theme
                length.

        Raises:
            ValueError: If n is even or < 5, if the black-percentage
                bounds are invalid, or if the spec is not a palindrome or
                cannot be placed in an n x n grid.
            RuntimeError: If no legal row templates can be generated for
                the given n (should not occur in practice).
        """
        if n < 5 or n % 2 == 0:
            raise ValueError("n must be an odd integer >= 5")
        if not (0.0 <= min_black_pct <= max_black_pct <= 1.0):
            raise ValueError("require 0.0 <= min_black_pct <= max_black_pct <= 1.0")

        self.n = n
        self.min_black_pct = min_black_pct
        self.max_black_pct = max_black_pct
        self.max_attempts = max_attempts
        self.rng = random.Random(seed)
        self.mid = n // 2
        self.max_nodes = GeneratorSettings.MAX_NODES

        self.top_rows = [r for r in _generate_legal_rows(n, require_palindrome=False) if WHITE in r]
        self.middle_rows = [r for r in _generate_legal_rows(n, require_palindrome=True) if WHITE in r]

        if not self.top_rows or not self.middle_rows:
            raise RuntimeError("failed to generate legal row templates")

        self.spec = list(spec) if spec else None
        self.free_lengths: Optional[frozenset] = None
        if self.spec:
            self._init_spec()

    def _init_spec(self) -> None:
        """Validate the theme spec and pre-compute the row templates it allows.

        Theme words pair up by 180-degree symmetry: the first half of the
        spec goes in top-half rows (mirrored in the bottom half), and the
        middle element of an odd-length spec goes in the centre row.

        free_lengths is the set of lengths any non-theme entry may have:
        3 up to the longest theme length, minus the gap lengths between
        theme lengths and minus the theme lengths themselves.
        """
        spec = self.spec
        n = self.n
        if spec != spec[::-1]:
            raise ValueError("theme spec must be a palindrome")
        if any(length < 3 or length > n for length in spec):
            raise ValueError(f"theme word lengths must be between 3 and {n}")

        self.theme_pairs = spec[:len(spec) // 2]
        self.theme_middle = spec[len(spec) // 2] if len(spec) % 2 else None
        if len(self.theme_pairs) > self.mid:
            raise ValueError(f"too many theme words for a {n}x{n} grid")

        lengths = sorted(set(spec))
        gaps = {length for a, b in zip(lengths, lengths[1:]) for length in range(a + 1, b)}
        self.free_lengths = frozenset(range(3, lengths[-1] + 1)) - gaps - set(lengths)

        self.filler_top_rows = _rows_matching(self.top_rows, self.free_lengths)
        self.filler_middle_rows = _rows_matching(self.middle_rows, self.free_lengths)
        if not self.filler_top_rows or (self.theme_middle is None and not self.filler_middle_rows):
            raise ValueError("theme spec leaves no legal rows for the rest of the grid")

        self.theme_top_rows = {
            length: _rows_matching(self.top_rows, self.free_lengths, length)
            for length in set(self.theme_pairs)
        }
        if self.theme_middle is not None:
            self.theme_middle_rows = _rows_matching(self.middle_rows, self.free_lengths, self.theme_middle)
            if not self.theme_middle_rows:
                raise ValueError(
                    f"a {self.theme_middle}-letter theme word cannot sit in the centre row of a {n}x{n} grid")
        for length, rows in self.theme_top_rows.items():
            if not rows:
                raise ValueError(f"a {length}-letter theme word cannot be placed in a {n}x{n} grid")

    def generate(self) -> Grid:
        """Generate and return one valid Grid.

        Each call picks a fresh random target black-cell count within the
        configured range and runs the backtracking search.  If the search
        fails, a new target is chosen and the search restarts.  This repeats
        up to max_attempts times.

        Returns:
            A Grid with black cells placed at 1-based (row, col) coordinates
            or NONE, if no valid grid is found within max_attempts attempts.
        """
        total = self.n * self.n
        lo = max(0, int(total * self.min_black_pct))
        hi = min(total, int(total * self.max_black_pct))

        for _ in range(self.max_attempts):
            target = self.rng.randint(lo, hi)
            raw = [[UNKNOWN] * self.n for _ in range(self.n)]
            nodes = [0]
            plan = self._plan_rows()
            result = self._search(raw, row_index=0, target_black=target, min_black=lo, max_black=hi, nodes=nodes,
                                  plan=plan)
            if result is not None:
                ok, _ = _validate_grid(result)
                if ok:
                    return self._to_grid(result)
        return None

    def _plan_rows(self) -> List[List[str]]:
        """Return the candidate row templates for each top-half row 0..mid for one attempt.

        Without a spec every top row draws from top_rows and the centre row
        from middle_rows.  With a spec, a fresh random choice of top-half
        rows (kept in spec order, top to bottom) receives the theme pairs;
        every other row draws from the filler templates.
        """
        if not self.spec:
            return [self.top_rows] * self.mid + [self.middle_rows]
        middle = self.filler_middle_rows if self.theme_middle is None else self.theme_middle_rows
        plan = [self.filler_top_rows] * self.mid + [middle]
        theme_rows = sorted(self.rng.sample(range(self.mid), len(self.theme_pairs)))
        for r, length in zip(theme_rows, self.theme_pairs):
            plan[r] = self.theme_top_rows[length]
        return plan

    def _to_grid(self, raw: List[List[str]]) -> Grid:
        """Convert the internal 0-based raw grid to a domain Grid (1-based coordinates)."""
        grid = Grid(self.n)
        for r, row in enumerate(raw):
            for c, ch in enumerate(row):
                if ch == BLACK:
                    grid.add_black_cell(r + 1, c + 1, undo=False)
        return grid

    def _search(
        self,
        grid: List[List[str]],
        row_index: int,
        target_black: int,
        min_black: int,
        max_black: int,
        nodes: List[int],
        plan: List[List[str]],
    ) -> Optional[List[List[str]]]:
        """Recursive backtracking search that fills rows from the outside in.

        Rows are filled in order 0, 1, …, mid-1, mid.  Filling row r also
        fills its symmetric partner row n-1-r simultaneously.  The centre
        row (mid) is filled last and must be a palindrome.

        Pruning:
          - Abandon if the current black count already exceeds max_black.
          - Abandon if the maximum achievable black count (current + all
            remaining UNKNOWN cells) falls below min_black.
          - After placing each row pair, check that no column has already
            acquired a forced short white run (_partial_columns_feasible).
          - After placing each row pair, check that no long word in the new
            row is stacked with one in its neighbour.

        Args:
            grid: The partially filled grid (modified in place).
            row_index: The next top-half row to fill (0 .. mid).
            target_black: The desired total black-cell count for this attempt.
            min_black: Hard lower bound on black-cell count.
            max_black: Hard upper bound on black-cell count.
            plan: Candidate row templates for each row 0..mid (see _plan_rows).

        Returns:
            The completed grid as a list-of-lists on success, or None if no
            valid completion exists from the current partial assignment.
        """
        n = self.n
        mid = self.mid

        current_black = _count_black_cells(grid)

        if current_black > max_black:
            return None

        remaining_slots = 0
        for r in range(row_index, mid):
            if grid[r][0] == UNKNOWN:
                remaining_slots += 2 * n
        if row_index <= mid and grid[mid][0] == UNKNOWN:
            remaining_slots += n

        if current_black + remaining_slots < min_black:
            return None

        if row_index < mid:
            candidates = self._rank_top_candidates(plan[row_index], target_black, current_black, row_index)

            for row in candidates:
                nodes[0] += 1
                if nodes[0] >= self.max_nodes:
                    return None

                _place_row_pair(grid, row_index, row)

                rr = n - 1 - row_index
                stacking_ok = True
                if row_index > 0 and not _no_long_word_stack(grid[row_index], grid[row_index - 1]):
                    stacking_ok = False
                elif rr < n - 1 and not _no_long_word_stack(grid[rr], grid[rr + 1]):
                    stacking_ok = False

                if stacking_ok and _partial_columns_feasible(grid, self.free_lengths):
                    result = self._search(grid, row_index + 1, target_black, min_black, max_black, nodes, plan)
                    if result is not None:
                        return result

                _clear_row_pair(grid, row_index)

            return None

        if row_index == mid:
            candidates = self._rank_middle_candidates(plan[mid], target_black, current_black)

            for row in candidates:
                nodes[0] += 1
                if nodes[0] >= self.max_nodes:
                    return None

                _place_middle_row(grid, row)

                if (
                    _no_long_word_stack(grid[mid], grid[mid - 1])
                    and _no_long_word_stack(grid[mid], grid[mid + 1])
                    and _partial_columns_feasible(grid, self.free_lengths)
                ):
                    black_count = _count_black_cells(grid)
                    if min_black <= black_count <= max_black:
                        ok, _ = _validate_grid(grid)
                        if ok:
                            return [list(r) for r in grid]

                _clear_middle_row(grid)

            return None

        return None

    def _rank_top_candidates(
        self, rows: List[str], target_black: int, current_black: int, row_index: int
    ) -> List[str]:
        """Return top-half row candidates sorted toward the target black-cell count.

        Rows are pre-shuffled for randomness, then stable-sorted so that rows
        whose black contribution is closest to the proportional share for this
        step come first.  The proportional share spreads the remaining black-cell
        budget evenly over the remaining placements (each top-row pair has weight 2,
        the centre row has weight 1), avoiding front-loading black cells onto the
        first row.
        """
        remaining_weight = 2 * (self.mid - row_index) + 1  # weight of remaining placements
        step_target = (target_black - current_black) * 2 / remaining_weight
        rows = rows[:]
        self.rng.shuffle(rows)
        rows.sort(key=lambda row: abs(row.count(BLACK) - step_target))
        return rows

    def _rank_middle_candidates(self, rows: List[str], target_black: int, current_black: int) -> List[str]:
        """Return centre-row candidates sorted toward the target black-cell count.

        Like _rank_top_candidates but the centre row is placed only once, so
        its black contribution is counted once rather than twice.
        """
        rows = rows[:]
        self.rng.shuffle(rows)
        rows.sort(key=lambda row: abs((current_black + row.count(BLACK)) - target_black))
        return rows


def _generate_legal_rows(n: int, require_palindrome: bool) -> List[str]:
    """Return all legal row patterns of length n.

    A legal row contains only BLACK and WHITE cells, and every maximal
    WHITE run has length >= 3 (so no word shorter than three letters can
    appear in that row).

    If require_palindrome is True, only rows that equal their own reverse
    are returned.  This is used for the centre row of an odd-sized grid,
    where 180-degree rotational symmetry means the centre row must be a
    palindrome.
    """
    rows: List[str] = []

    def rec(prefix: List[str], current_white_run: int) -> None:
        i = len(prefix)
        if i == n:
            if current_white_run in (1, 2):
                return
            row = "".join(prefix)
            if require_palindrome and row != row[::-1]:
                return
            rows.append(row)
            return

        if current_white_run not in (1, 2):
            prefix.append(BLACK)
            rec(prefix, 0)
            prefix.pop()

        prefix.append(WHITE)
        rec(prefix, current_white_run + 1)
        prefix.pop()

    rec([], 0)
    return rows


def _rows_matching(rows: Sequence[str], free_lengths: frozenset, theme_length: Optional[int] = None) -> List[str]:
    """Return the rows whose WHITE runs all have a length in free_lengths.

    If theme_length is given, a row must also contain exactly one run of
    that length (which is exempt from the free_lengths check).
    """
    result: List[str] = []
    for row in rows:
        runs = _white_run_lengths(row)
        if theme_length is not None:
            if runs.count(theme_length) != 1:
                continue
            runs.remove(theme_length)
        if all(length in free_lengths for length in runs):
            result.append(row)
    return result


def _white_run_lengths(line: Sequence[str]) -> List[int]:
    """Return the lengths of the maximal WHITE runs in a fully assigned line."""
    return [len(run) for run in "".join(line).split(BLACK) if run]


def _place_row_pair(grid: List[List[str]], r: int, row: str) -> None:
    """Write row r and its rotationally symmetric partner into the grid.

    For 180-degree rotational symmetry the partner row (at index n-1-r)
    must be the reverse of row r.
    """
    n = len(grid)
    rr = n - 1 - r
    bottom = row[::-1]
    for c, ch in enumerate(row):
        grid[r][c] = ch
    for c, ch in enumerate(bottom):
        grid[rr][c] = ch


def _place_middle_row(grid: List[List[str]], row: str) -> None:
    """Write a candidate pattern into the centre row of the grid."""
    n = len(grid)
    mid = n // 2
    for c, ch in enumerate(row):
        grid[mid][c] = ch


def _clear_row_pair(grid: List[List[str]], r: int) -> None:
    """Reset row r and its symmetric partner to UNKNOWN, undoing _place_row_pair."""
    n = len(grid)
    rr = n - 1 - r
    for c in range(n):
        grid[r][c] = UNKNOWN
        grid[rr][c] = UNKNOWN


def _clear_middle_row(grid: List[List[str]]) -> None:
    """Reset the centre row to UNKNOWN, undoing _place_middle_row."""
    n = len(grid)
    mid = n // 2
    for c in range(n):
        grid[mid][c] = UNKNOWN


def _count_black_cells(grid: Sequence[Sequence[str]]) -> int:
    """Return the total number of BLACK cells in the grid."""
    return sum(cell == BLACK for row in grid for cell in row)


def _no_forced_short_white_runs(line: Sequence[str], allowed: Optional[frozenset] = None) -> bool:
    """Return True if no completed WHITE run of length < 3 already exists in line.

    Used as a pruning check on partially assigned lines (rows or columns).
    UNKNOWN cells do not close a run because they may still become WHITE and
    extend it; only BLACK cells and grid edges act as run boundaries.

    Returns False as soon as a WHITE run is found that is both fully bounded
    (closed on both sides by BLACK or the edge) and shorter than 3.

    If allowed is given, also returns False for a closed run whose length is
    not in allowed, or for any run (closed or not) already longer than the
    largest allowed length, since a run can only grow.
    """
    n = len(line)
    i = 0
    while i < n:
        if line[i] != WHITE:
            i += 1
            continue
        start = i
        while i < n and line[i] == WHITE:
            i += 1
        end = i - 1
        length = end - start + 1
        left_closed = (start == 0) or (line[start - 1] == BLACK)
        right_closed = (end == n - 1) or (line[end + 1] == BLACK)
        if left_closed and right_closed and length < 3:
            return False
        if allowed is not None:
            if length > max(allowed, default=0):
                return False
            if left_closed and right_closed and length not in allowed:
                return False
    return True


def _partial_columns_feasible(grid: Sequence[Sequence[str]], allowed: Optional[frozenset] = None) -> bool:
    """Return True if every column in the partially filled grid still admits a valid completion.

    Applies _no_forced_short_white_runs to each column.  A column that
    already contains a fully bounded WHITE run shorter than 3 can never
    produce a valid grid, so the current partial assignment can be pruned.
    If allowed is given (the theme spec's free lengths), Down runs must
    also stay within it.
    """
    n = len(grid)
    for c in range(n):
        col = [grid[r][c] for r in range(n)]
        if not _no_forced_short_white_runs(col, allowed):
            return False
    return True


def _all_white_cells_connected(grid: Sequence[Sequence[str]]) -> bool:
    """Return True if all WHITE cells form a single orthogonally connected region.

    Uses breadth-first search starting from the first WHITE cell found.
    Returns False if no WHITE cells exist or if the reachable set is smaller
    than the total WHITE cell count.
    """
    n = len(grid)
    start: Optional[Tuple[int, int]] = None
    white_count = 0
    for r in range(n):
        for c in range(n):
            if grid[r][c] == WHITE:
                white_count += 1
                if start is None:
                    start = (r, c)
    if start is None:
        return False
    seen = {start}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n and grid[rr][cc] == WHITE and (rr, cc) not in seen:
                seen.add((rr, cc))
                q.append((rr, cc))
    return len(seen) == white_count


def _line_runs_are_legal(line: Sequence[str]) -> bool:
    """Return True if every maximal WHITE run in line has length >= 3.

    Used for final validation of completed rows and columns.
    """
    n = len(line)
    i = 0
    while i < n:
        if line[i] == WHITE:
            start = i
            while i < n and line[i] == WHITE:
                i += 1
            if i - start < 3:
                return False
        else:
            i += 1
    return True


def _long_spans(line: Sequence[str]) -> List[Tuple[int, int]]:
    """Return the (start, end) index ranges of WHITE runs longer than _STACK_MAX.

    Used to identify runs that must not be stacked in adjacent lines.
    """
    spans: List[Tuple[int, int]] = []
    n = len(line)
    i = 0
    while i < n:
        if line[i] == WHITE:
            start = i
            while i < n and line[i] == WHITE:
                i += 1
            if i - start > GeneratorSettings.STACK_MAX:
                spans.append((start, i - 1))
        else:
            i += 1
    return spans


def _spans_overlap(a: List[Tuple[int, int]], b: List[Tuple[int, int]]) -> bool:
    """Return True if any span in a overlaps (shares at least one index) with any span in b."""
    for s1, e1 in a:
        for s2, e2 in b:
            if s1 <= e2 and s2 <= e1:
                return True
    return False


def _no_long_word_stack(line1: Sequence[str], line2: Sequence[str]) -> bool:
    """Return True if no long WHITE run in line1 is aligned with a long WHITE run in line2.

    Two long runs are considered stacked when their column ranges overlap.
    Stacked long words are rejected because they tend to produce grids that
    are difficult to fill with real words.
    """
    spans1 = _long_spans(line1)
    if not spans1:
        return True
    return not _spans_overlap(spans1, _long_spans(line2))


def _validate_grid(grid: Sequence[Sequence[str]]) -> Tuple[bool, str]:
    """Validate a fully assigned grid against all constructor rules.

    Checks, in order:
      1. 180-degree rotational symmetry.
      2. At least one WHITE cell exists.
      3. Every across run (row) has length >= 3.
      4. Every down run (column) has length >= 3.
      5. All WHITE cells are orthogonally connected.
      6. No long across words (> _STACK_MAX) are stacked in adjacent rows.
      7. No long down words (> _STACK_MAX) are stacked in adjacent columns.

    Returns (True, "ok") on success, or (False, reason) on the first
    failing rule.
    """
    n = len(grid)
    for r in range(n):
        for c in range(n):
            if grid[r][c] != grid[n - 1 - r][n - 1 - c]:
                return False, f"rotational symmetry violated at ({r}, {c})"
    if not any(grid[r][c] == WHITE for r in range(n) for c in range(n)):
        return False, "grid has no white cells"
    for r in range(n):
        if not _line_runs_are_legal(grid[r]):
            return False, f"illegal across run in row {r}"
    for c in range(n):
        col = [grid[r][c] for r in range(n)]
        if not _line_runs_are_legal(col):
            return False, f"illegal down run in column {c}"
    if not _all_white_cells_connected(grid):
        return False, "white cells are not all connected"
    for r in range(n - 1):
        if not _no_long_word_stack(grid[r], grid[r + 1]):
            return False, f"stacked long across words in rows {r} and {r + 1}"
    for c in range(n - 1):
        col1 = [grid[r][c] for r in range(n)]
        col2 = [grid[r][c + 1] for r in range(n)]
        if not _no_long_word_stack(col1, col2):
            return False, f"stacked long down words in columns {c} and {c + 1}"
    return True, "ok"
