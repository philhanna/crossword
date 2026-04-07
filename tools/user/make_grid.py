"""
Generate random crossword grids with 180-degree rotational symmetry.

Usage:
    python tools/user/make_grid.py [options]

Options:
    -n, --size N        Grid size (odd integer > 7, default: 11)
    -c, --count K       Number of grids to generate (default: 1)
    -r, --ratio R       Black-cell probability per cell (default: 0.30)
    -i, --iterations I  Max random attempts before giving up (default: 10000000)
    -o, --output DIR    Directory for output .txt files (default: current directory)

Each valid grid is written as an AcrossLite text (.txt) file named grid-001.txt,
grid-002.txt, etc.  The path of each written file is printed to stdout.
Exit code 1 if fewer than --count grids were found within the iteration limit.

Example:
    python tools/user/make_grid.py -n 15 -c 3 -o /tmp/grids
"""

import argparse
import random
import sys
from pathlib import Path

# Grid cell values
WHITE = 0x20  # space
BLACK = 0x2E  # dot

DEFAULT_MAX_ITERATIONS = 10_000_000
DEFAULT_RATIO = 0.30


def main():
    parser = argparse.ArgumentParser(
        description="Generate random symmetric crossword grids.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--size", type=int, default=11,
                        metavar="N", help="Grid size (odd integer > 7, default: 11)")
    parser.add_argument("-c", "--count", type=int, default=1,
                        metavar="K", help="Number of grids to generate (default: 1)")
    parser.add_argument("-r", "--ratio", type=float, default=DEFAULT_RATIO,
                        metavar="R", help="Black-cell probability per cell (default: 0.30)")
    parser.add_argument("-i", "--iterations", type=int, default=DEFAULT_MAX_ITERATIONS,
                        metavar="I", help="Max random attempts (default: 10000000)")
    parser.add_argument("-o", "--output", default=".",
                        metavar="DIR", help="Output directory for .txt files (default: current directory)")
    args = parser.parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    found = 0
    for grid in get_grids(args.size, max_iterations=args.iterations, ratio=args.ratio):
        found += 1
        path = out_dir / f"grid-{found:03d}.txt"
        print_grid(grid, args.size, path)
        print(path)
        if found >= args.count:
            break

    if found < args.count:
        print(
            f"Only {found} of {args.count} grids found within {args.iterations} iterations.",
            file=sys.stderr,
        )
        sys.exit(1)


def print_grid(grid, n, path):
    """Write an AcrossLite text (.txt) file for the grid at *path*."""
    indent = "     "
    across_count, down_count = _count_words(grid, n)
    lines = [
        "<ACROSS PUZZLE>",
        "<TITLE>",
        indent,
        "<AUTHOR>",
        indent,
        "<COPYRIGHT>",
        indent,
        "<SIZE>",
        f"{indent}{n}x{n}",
        "<GRID>",
    ]
    for row in grid:
        lines.append(indent + "".join(chr(cell) for cell in row))
    lines.append("<ACROSS>")
    lines.extend(indent for _ in range(across_count))
    lines.append("<DOWN>")
    lines.extend(indent for _ in range(down_count))
    lines.append("<NOTEPAD>")
    lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def get_grids(n, max_iterations=DEFAULT_MAX_ITERATIONS, ratio=DEFAULT_RATIO):
    """
    Yield random n×n crossword grids with 180-degree rotational symmetry.

    Each yielded grid satisfies:
    - All white-cell runs (across and down) are at least 3 cells long.
    - The middle row is left-right symmetric.
    - All white cells are 4-connected (one contiguous region).

    Args:
        n: Grid size — must be an odd integer greater than 7.
        max_iterations: Maximum random attempts before the generator returns.
        ratio: Probability that any given cell is placed as a black cell.

    Raises:
        ValueError: If n is even or <= 7.
    """
    if n % 2 == 0 or n <= 7:
        raise ValueError("n must be an odd integer greater than 7")

    m = (n + 1) // 2  # number of rows in the top half (including middle)

    for _ in range(max_iterations):
        grid = [[WHITE] * n for _ in range(n)]
        valid = True

        # Phase 1: place black cells with 180-degree symmetry; check row runs
        for i in range(m):
            for j in range(n):
                if random.random() < ratio:
                    grid[i][j] = BLACK
                    grid[n - 1 - i][n - 1 - j] = BLACK

            row_str = "".join(chr(cell) for cell in grid[i])
            for run in row_str.split(chr(BLACK)):
                if run and len(run) < 3:
                    valid = False
                    break
            if not valid:
                break

        if not valid:
            continue

        # Phase 2: middle row must be left-right symmetric
        mid = m - 1
        for j in range(n // 2):
            if grid[mid][j] != grid[mid][n - 1 - j]:
                valid = False
                break

        if not valid:
            continue

        # Phase 3: every white cell must belong to words of length >= 3
        for i in range(n):
            for j in range(n):
                if grid[i][j] == WHITE:
                    if _word_length(grid, i, j, "across") < 3:
                        valid = False
                        break
                    if _word_length(grid, i, j, "down") < 3:
                        valid = False
                        break
            if not valid:
                break

        if not valid:
            continue

        # Phase 4: all white cells must be 4-connected
        if not _is_connected(grid, n):
            continue

        yield grid


def _count_words(grid, n):
    """Return (across_count, down_count) for the grid."""
    across = 0
    down = 0
    for i in range(n):
        for j in range(n):
            if grid[i][j] == WHITE:
                if (j == 0 or grid[i][j - 1] == BLACK) and j + 1 < n and grid[i][j + 1] == WHITE:
                    across += 1
                if (i == 0 or grid[i - 1][j] == BLACK) and i + 1 < n and grid[i + 1][j] == WHITE:
                    down += 1
    return across, down


def _word_length(grid, r, c, axis):
    """Return the length of the white-cell run that contains (r, c)."""
    n = len(grid)
    length = 0
    if axis == "across":
        j = c
        while j >= 0 and grid[r][j] == WHITE:
            length += 1
            j -= 1
        j = c + 1
        while j < n and grid[r][j] == WHITE:
            length += 1
            j += 1
    else:
        i = r
        while i >= 0 and grid[i][c] == WHITE:
            length += 1
            i -= 1
        i = r + 1
        while i < n and grid[i][c] == WHITE:
            length += 1
            i += 1
    return length


def _is_connected(grid, n):
    """Return True if all white cells form a single 4-connected region."""
    white_cells = [(r, c) for r in range(n) for c in range(n) if grid[r][c] == WHITE]
    if not white_cells:
        return True

    visited = {white_cells[0]}
    queue = [white_cells[0]]
    while queue:
        r, c = queue.pop()
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == WHITE and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))

    return len(visited) == len(white_cells)


if __name__ == "__main__":
    main()
