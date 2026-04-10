#!/usr/bin/env python3
"""
Random crossword grid generator.

Rules enforced:
1. 180-degree rotational symmetry
2. No across or down words of length < 3
3. All-over interlock (all white cells connected orthogonally)
4. Every white cell belongs to both an across and a down entry
   (this follows automatically once all across/down runs are length >= 3)

Representation:
    '#' = black
    '.' = white

Example:
    python gridgen.py 15
    python gridgen.py 15 --count 5
    python gridgen.py 21 --min-black-pct 0.14 --max-black-pct 0.22
"""

from __future__ import annotations

import argparse
import random
from collections import deque
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple


BLACK = "#"
WHITE = "."
UNKNOWN = "?"


def is_odd_int_ge_9(value: str) -> int:
    n = int(value)
    if n < 9 or n % 2 == 0:
        raise argparse.ArgumentTypeError("n must be an odd integer >= 9")
    return n


def row_has_only_legal_white_runs(row: Sequence[str]) -> bool:
    """Return True iff every maximal WHITE run in the row has length >= 3."""
    n = len(row)
    c = 0
    while c < n:
        if row[c] == WHITE:
            start = c
            while c < n and row[c] == WHITE:
                c += 1
            if c - start < 3:
                return False
        else:
            c += 1
    return True


def generate_legal_rows(n: int, require_palindrome: bool) -> List[str]:
    """
    Generate all legal row patterns of length n.

    Legal means:
      - cells are only BLACK/WHITE
      - every maximal WHITE run has length >= 3

    If require_palindrome is True, only rows equal to their reverse are kept.
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

        # Try BLACK
        if current_white_run not in (1, 2):
            prefix.append(BLACK)
            rec(prefix, 0)
            prefix.pop()

        # Try WHITE
        prefix.append(WHITE)
        rec(prefix, current_white_run + 1)
        prefix.pop()

    rec([], 0)
    return rows


def reverse_row(row: str) -> str:
    return row[::-1]


def place_row_pair(grid: List[List[str]], r: int, row: str) -> None:
    """
    Place row r and its rotational partner row n-1-r.
    For rotational symmetry, bottom row is reverse(top row).
    """
    n = len(grid)
    rr = n - 1 - r
    bottom = reverse_row(row)

    for c, ch in enumerate(row):
        grid[r][c] = ch
    for c, ch in enumerate(bottom):
        grid[rr][c] = ch


def place_middle_row(grid: List[List[str]], row: str) -> None:
    n = len(grid)
    mid = n // 2
    for c, ch in enumerate(row):
        grid[mid][c] = ch


def clear_row_pair(grid: List[List[str]], r: int) -> None:
    n = len(grid)
    rr = n - 1 - r
    for c in range(n):
        grid[r][c] = UNKNOWN
        grid[rr][c] = UNKNOWN


def clear_middle_row(grid: List[List[str]]) -> None:
    n = len(grid)
    mid = n // 2
    for c in range(n):
        grid[mid][c] = UNKNOWN


def count_black_cells_in_grid(grid: Sequence[Sequence[str]]) -> int:
    return sum(cell == BLACK for row in grid for cell in row)


def no_forced_short_white_runs_in_partial_line(line: Sequence[str]) -> bool:
    """
    Necessary condition for eventual validity in a partially assigned line.

    We reject if there exists a completed WHITE run of length 1 or 2 that is
    already bounded on both sides by BLACK or grid edge.

    UNKNOWN does *not* close a run, because it may later become WHITE and extend it.
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

    return True


def partial_columns_feasible(grid: Sequence[Sequence[str]]) -> bool:
    n = len(grid)
    for c in range(n):
        col = [grid[r][c] for r in range(n)]
        if not no_forced_short_white_runs_in_partial_line(col):
            return False
    return True


def all_white_cells_connected(grid: Sequence[Sequence[str]]) -> bool:
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
        return False  # no white cells

    seen = set([start])
    q = deque([start])

    while q:
        r, c = q.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n and grid[rr][cc] == WHITE and (rr, cc) not in seen:
                seen.add((rr, cc))
                q.append((rr, cc))

    return len(seen) == white_count


def line_runs_are_legal(line: Sequence[str]) -> bool:
    """Final check: every maximal WHITE run has length >= 3."""
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


def validate_grid(grid: Sequence[Sequence[str]]) -> Tuple[bool, str]:
    n = len(grid)

    # 1. Rotational symmetry
    for r in range(n):
        for c in range(n):
            if grid[r][c] != grid[n - 1 - r][n - 1 - c]:
                return False, f"rotational symmetry violated at ({r}, {c})"

    # Require at least one white cell
    if not any(grid[r][c] == WHITE for r in range(n) for c in range(n)):
        return False, "grid has no white cells"

    # 2. No across words shorter than 3
    for r in range(n):
        if not line_runs_are_legal(grid[r]):
            return False, f"illegal across run in row {r}"

    # 2. No down words shorter than 3
    for c in range(n):
        col = [grid[r][c] for r in range(n)]
        if not line_runs_are_legal(col):
            return False, f"illegal down run in column {c}"

    # 3. Connectivity
    if not all_white_cells_connected(grid):
        return False, "white cells are not all connected"

    # 4. Every white cell must be in an across and a down entry.
    # This is implied by the row/column run rule, but we check explicitly anyway.
    for r in range(n):
        for c in range(n):
            if grid[r][c] != WHITE:
                continue

            # horizontal span
            left = c
            while left - 1 >= 0 and grid[r][left - 1] == WHITE:
                left -= 1
            right = c
            while right + 1 < n and grid[r][right + 1] == WHITE:
                right += 1
            if right - left + 1 < 3:
                return False, f"cell ({r}, {c}) is not in a valid across entry"

            # vertical span
            up = r
            while up - 1 >= 0 and grid[up - 1][c] == WHITE:
                up -= 1
            down = r
            while down + 1 < n and grid[down + 1][c] == WHITE:
                down += 1
            if down - up + 1 < 3:
                return False, f"cell ({r}, {c}) is not in a valid down entry"

    return True, "ok"


@dataclass
class SearchConfig:
    min_black_pct: float
    max_black_pct: float
    max_attempts: int = 200


class GridGenerator:
    def __init__(self, n: int, rng: random.Random, config: SearchConfig):
        self.n = n
        self.rng = rng
        self.config = config
        self.mid = n // 2

        self.top_rows = generate_legal_rows(n, require_palindrome=False)
        self.middle_rows = generate_legal_rows(n, require_palindrome=True)

        # Avoid degenerate all-black rows by default; they make useful grids rarer.
        self.top_rows = [row for row in self.top_rows if WHITE in row]
        self.middle_rows = [row for row in self.middle_rows if WHITE in row]

        if not self.top_rows or not self.middle_rows:
            raise RuntimeError("failed to generate legal row templates")

    def random_target_black_range(self) -> Tuple[int, int]:
        total = self.n * self.n
        lo = max(0, int(total * self.config.min_black_pct))
        hi = min(total, int(total * self.config.max_black_pct))
        if lo > hi:
            raise ValueError("invalid black percentage range")
        return lo, hi

    def generate(self) -> List[str]:
        for _ in range(self.config.max_attempts):
            lo, hi = self.random_target_black_range()
            target = self.rng.randint(lo, hi)

            grid = [[UNKNOWN] * self.n for _ in range(self.n)]
            result = self._search(grid, row_index=0, target_black=target, min_black=lo, max_black=hi)
            if result is not None:
                ok, reason = validate_grid(result)
                if ok:
                    return ["".join(row) for row in result]
                # Should not happen, but keep searching if it does.

        raise RuntimeError("failed to generate a valid grid; try increasing max_attempts")

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

        current_black = count_black_cells_in_grid(grid)

        # Too many blacks already
        if current_black > max_black:
            return None

        # Maximum additional blacks possible from remaining unassigned rows
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
                place_row_pair(grid, row_index, row)

                if partial_columns_feasible(grid):
                    result = self._search(grid, row_index + 1, target_black, min_black, max_black)
                    if result is not None:
                        return result

                clear_row_pair(grid, row_index)

            return None

        if row_index == mid:
            candidates = self._rank_middle_candidates(target_black, current_black)
            self.rng.shuffle(candidates)

            for row in candidates:
                place_middle_row(grid, row)

                if partial_columns_feasible(grid):
                    black_count = count_black_cells_in_grid(grid)
                    if min_black <= black_count <= max_black:
                        ok, _ = validate_grid(grid)
                        if ok:
                            return [list(r) for r in grid]

                clear_middle_row(grid)

            return None

        return None

    def _rank_top_candidates(self, target_black: int, current_black: int) -> List[str]:
        """
        Favor rows whose black counts keep us roughly near the random target.
        """
        rows = self.top_rows[:]
        self.rng.shuffle(rows)
        rows.sort(key=lambda row: abs((current_black + 2 * row.count(BLACK)) - target_black))
        return rows

    def _rank_middle_candidates(self, target_black: int, current_black: int) -> List[str]:
        rows = self.middle_rows[:]
        self.rng.shuffle(rows)
        rows.sort(key=lambda row: abs((current_black + row.count(BLACK)) - target_black))
        return rows


def print_grid(rows: Sequence[str]) -> None:
    for row in rows:
        print(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate random valid crossword grids.")
    parser.add_argument("n", type=is_odd_int_ge_9, help="odd grid size >= 9")
    parser.add_argument("--count", type=int, default=1, help="number of grids to generate")
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    parser.add_argument(
        "--min-black-pct",
        type=float,
        default=0.14,
        help="minimum black-square fraction (default: 0.14)",
    )
    parser.add_argument(
        "--max-black-pct",
        type=float,
        default=0.22,
        help="maximum black-square fraction (default: 0.22)",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=200,
        help="number of top-level randomized search attempts per grid",
    )
    args = parser.parse_args()

    if not (0.0 <= args.min_black_pct <= args.max_black_pct <= 1.0):
        parser.error("require 0.0 <= min-black-pct <= max-black-pct <= 1.0")

    rng = random.Random(args.seed)
    config = SearchConfig(
        min_black_pct=args.min_black_pct,
        max_black_pct=args.max_black_pct,
        max_attempts=args.max_attempts,
    )

    gen = GridGenerator(args.n, rng, config)

    for i in range(args.count):
        rows = gen.generate()
        if i > 0:
            print()
        print_grid(rows)


if __name__ == "__main__":
    main()
