from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

from .grid import Grid


BLACK = "#"
WHITE = "."
UNKNOWN = "?"
_STACK_MAX = 7  # words longer than this may not be stacked in adjacent rows/columns


def _generate_legal_rows(n: int, require_palindrome: bool) -> List[str]:
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


def _place_row_pair(grid: List[List[str]], r: int, row: str) -> None:
    n = len(grid)
    rr = n - 1 - r
    bottom = row[::-1]
    for c, ch in enumerate(row):
        grid[r][c] = ch
    for c, ch in enumerate(bottom):
        grid[rr][c] = ch


def _place_middle_row(grid: List[List[str]], row: str) -> None:
    n = len(grid)
    mid = n // 2
    for c, ch in enumerate(row):
        grid[mid][c] = ch


def _clear_row_pair(grid: List[List[str]], r: int) -> None:
    n = len(grid)
    rr = n - 1 - r
    for c in range(n):
        grid[r][c] = UNKNOWN
        grid[rr][c] = UNKNOWN


def _clear_middle_row(grid: List[List[str]]) -> None:
    n = len(grid)
    mid = n // 2
    for c in range(n):
        grid[mid][c] = UNKNOWN


def _count_black_cells(grid: Sequence[Sequence[str]]) -> int:
    return sum(cell == BLACK for row in grid for cell in row)


def _no_forced_short_white_runs(line: Sequence[str]) -> bool:
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
    return True


def _partial_columns_feasible(grid: Sequence[Sequence[str]]) -> bool:
    n = len(grid)
    for c in range(n):
        col = [grid[r][c] for r in range(n)]
        if not _no_forced_short_white_runs(col):
            return False
    return True


def _all_white_cells_connected(grid: Sequence[Sequence[str]]) -> bool:
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
    spans: List[Tuple[int, int]] = []
    n = len(line)
    i = 0
    while i < n:
        if line[i] == WHITE:
            start = i
            while i < n and line[i] == WHITE:
                i += 1
            if i - start > _STACK_MAX:
                spans.append((start, i - 1))
        else:
            i += 1
    return spans


def _spans_overlap(a: List[Tuple[int, int]], b: List[Tuple[int, int]]) -> bool:
    for s1, e1 in a:
        for s2, e2 in b:
            if s1 <= e2 and s2 <= e1:
                return True
    return False


def _no_long_word_stack(line1: Sequence[str], line2: Sequence[str]) -> bool:
    spans1 = _long_spans(line1)
    if not spans1:
        return True
    return not _spans_overlap(spans1, _long_spans(line2))


def _validate_grid(grid: Sequence[Sequence[str]]) -> Tuple[bool, str]:
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


class GridGenerator:
    """Generates a random valid crossword grid."""

    def __init__(
        self,
        n: int,
        seed: Optional[int] = None,
        min_black_pct: float = 0.14,
        max_black_pct: float = 0.22,
        max_attempts: int = 200,
    ):
        if n < 9 or n % 2 == 0:
            raise ValueError("n must be an odd integer >= 9")
        if not (0.0 <= min_black_pct <= max_black_pct <= 1.0):
            raise ValueError("require 0.0 <= min_black_pct <= max_black_pct <= 1.0")

        self.n = n
        self.min_black_pct = min_black_pct
        self.max_black_pct = max_black_pct
        self.max_attempts = max_attempts
        self.rng = random.Random(seed)
        self.mid = n // 2

        self.top_rows = [r for r in _generate_legal_rows(n, require_palindrome=False) if WHITE in r]
        self.middle_rows = [r for r in _generate_legal_rows(n, require_palindrome=True) if WHITE in r]

        if not self.top_rows or not self.middle_rows:
            raise RuntimeError("failed to generate legal row templates")

    def generate(self) -> Grid:
        """Generate and return a valid Grid, raising RuntimeError if unsuccessful."""
        total = self.n * self.n
        lo = max(0, int(total * self.min_black_pct))
        hi = min(total, int(total * self.max_black_pct))

        for _ in range(self.max_attempts):
            target = self.rng.randint(lo, hi)
            raw = [[UNKNOWN] * self.n for _ in range(self.n)]
            result = self._search(raw, row_index=0, target_black=target, min_black=lo, max_black=hi)
            if result is not None:
                ok, _ = _validate_grid(result)
                if ok:
                    return self._to_grid(result)

        raise RuntimeError("failed to generate a valid grid; try increasing max_attempts")

    def _to_grid(self, raw: List[List[str]]) -> Grid:
        grid = Grid(self.n)
        for r, row in enumerate(raw):
            for c, ch in enumerate(row):
                if ch == BLACK:
                    grid.add_black_cell(r + 1, c + 1, undo=False)  # convert to 1-based
        return grid

    def _search(
        self,
        grid: List[List[str]],
        row_index: int,
        target_black: int,
        min_black: int,
        max_black: int,
    ) -> Optional[List[List[str]]]:
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
            candidates = self._rank_top_candidates(target_black, current_black)
            self.rng.shuffle(candidates)

            for row in candidates:
                _place_row_pair(grid, row_index, row)

                rr = n - 1 - row_index
                stacking_ok = True
                if row_index > 0 and not _no_long_word_stack(grid[row_index], grid[row_index - 1]):
                    stacking_ok = False
                elif rr < n - 1 and not _no_long_word_stack(grid[rr], grid[rr + 1]):
                    stacking_ok = False

                if stacking_ok and _partial_columns_feasible(grid):
                    result = self._search(grid, row_index + 1, target_black, min_black, max_black)
                    if result is not None:
                        return result

                _clear_row_pair(grid, row_index)

            return None

        if row_index == mid:
            candidates = self._rank_middle_candidates(target_black, current_black)
            self.rng.shuffle(candidates)

            for row in candidates:
                _place_middle_row(grid, row)

                if (
                    _no_long_word_stack(grid[mid], grid[mid - 1])
                    and _no_long_word_stack(grid[mid], grid[mid + 1])
                    and _partial_columns_feasible(grid)
                ):
                    black_count = _count_black_cells(grid)
                    if min_black <= black_count <= max_black:
                        ok, _ = _validate_grid(grid)
                        if ok:
                            return [list(r) for r in grid]

                _clear_middle_row(grid)

            return None

        return None

    def _rank_top_candidates(self, target_black: int, current_black: int) -> List[str]:
        rows = self.top_rows[:]
        self.rng.shuffle(rows)
        rows.sort(key=lambda row: abs((current_black + 2 * row.count(BLACK)) - target_black))
        return rows

    def _rank_middle_candidates(self, target_black: int, current_black: int) -> List[str]:
        rows = self.middle_rows[:]
        self.rng.shuffle(rows)
        rows.sort(key=lambda row: abs((current_black + row.count(BLACK)) - target_black))
        return rows
