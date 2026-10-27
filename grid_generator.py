"""
Generate a random valid 15x15 crossword grid and write it to a PDF.

Standalone: uses only the Python standard library. The output file is
named after the current system time, as yyyymmddhhmmss.pdf, and is written
to the current directory.

Rules enforced on every generated grid:
  - 180-degree rotational symmetry.
  - Every across and down entry is at least 3 letters long.
  - All white cells form a single connected region.
  - No word longer than STACK_MAX letters is directly stacked beside
    another such word in an adjacent row or column.
  - The grid has at most MAX_WORDS across and down entries in total.

Usage:
    python3 grid_generator.py
"""

import random
import sys
from collections import deque
from datetime import datetime

N = 15
BLACK_PCT_MIN = 0.10
BLACK_PCT_MAX = 0.20
MAX_ATTEMPTS = 256
MAX_NODES = 2000  # max candidates tried per attempt before bailing out
STACK_MAX = 7  # words longer than this may not be stacked in adjacent lines
MAX_WORDS = 74  # max across + down entries in the grid

BLACK = "#"
WHITE = "."
UNKNOWN = "?"

PAGE_WIDTH = 612  # US Letter, in points
PAGE_HEIGHT = 792
CELL_SIZE = 32
NUMBER_FONT_SIZE = 7


def main() -> None:
    """Generate a grid and write it to a timestamped PDF."""
    grid = generate_grid(N)
    if grid is None:
        print(f"Failed to generate a valid grid after {MAX_ATTEMPTS} attempts.", file=sys.stderr)
        sys.exit(1)
    filename = datetime.now().strftime("%Y%m%d%H%M%S") + ".pdf"
    write_pdf(grid, filename)
    print(f"Wrote {filename}")


def generate_grid(n: int):
    """Return a valid n x n grid as a list of row strings, or None on failure.

    Each attempt picks a random target black-cell count within the
    configured range and runs a backtracking search that fills rows from
    the outside in (top and bottom together) toward the centre row.
    """
    rng = random.Random()
    top_rows = [r for r in legal_rows(n, palindrome=False) if WHITE in r]
    middle_rows = [r for r in legal_rows(n, palindrome=True) if WHITE in r]
    total = n * n
    lo = int(total * BLACK_PCT_MIN)
    hi = int(total * BLACK_PCT_MAX)

    for _ in range(MAX_ATTEMPTS):
        target = rng.randint(lo, hi)
        raw = [[UNKNOWN] * n for _ in range(n)]
        nodes = [0]
        result = search(raw, 0, target, lo, hi, nodes, top_rows, middle_rows, rng)
        if result is not None and is_valid(result):
            return ["".join(row) for row in result]
    return None


def legal_rows(n: int, palindrome: bool) -> list:
    """Return every row pattern of length n whose white runs are all >= 3 long."""
    rows = []

    def rec(prefix, run):
        if len(prefix) == n:
            if run in (1, 2):
                return
            row = "".join(prefix)
            if not palindrome or row == row[::-1]:
                rows.append(row)
            return
        if run not in (1, 2):
            prefix.append(BLACK)
            rec(prefix, 0)
            prefix.pop()
        prefix.append(WHITE)
        rec(prefix, run + 1)
        prefix.pop()

    rec([], 0)
    return rows


def search(grid, row_index, target, lo, hi, nodes, top_rows, middle_rows, rng):
    """Recursively fill rows row_index..mid (and their mirrors); return the grid or None."""
    n = len(grid)
    mid = n // 2
    current = count_black(grid)
    if current > hi:
        return None
    remaining = 2 * n * (mid - row_index) + n
    if current + remaining < lo:
        return None

    if row_index < mid:

        # Spread the remaining black-cell budget evenly over the remaining
        # placements (each top-row pair weighs 2, the centre row 1).
        step_target = (target - current) * 2 / (2 * (mid - row_index) + 1)
        candidates = top_rows[:]
        rng.shuffle(candidates)
        candidates.sort(key=lambda row: abs(row.count(BLACK) - step_target))
        rr = n - 1 - row_index
        for row in candidates:
            nodes[0] += 1
            if nodes[0] >= MAX_NODES:
                return None
            grid[row_index] = list(row)
            grid[rr] = list(row[::-1])
            stacking_ok = (row_index == 0 or no_long_word_stack(grid[row_index], grid[row_index - 1])) and (
                rr == n - 1 or no_long_word_stack(grid[rr], grid[rr + 1])
            )
            if stacking_ok and columns_feasible(grid):
                result = search(grid, row_index + 1, target, lo, hi, nodes, top_rows, middle_rows, rng)
                if result is not None:
                    return result
            grid[row_index] = [UNKNOWN] * n
            grid[rr] = [UNKNOWN] * n
        return None

    candidates = middle_rows[:]
    rng.shuffle(candidates)
    candidates.sort(key=lambda row: abs(current + row.count(BLACK) - target))
    for row in candidates:
        nodes[0] += 1
        if nodes[0] >= MAX_NODES:
            return None
        grid[mid] = list(row)
        if (
            no_long_word_stack(grid[mid], grid[mid - 1])
            and no_long_word_stack(grid[mid], grid[mid + 1])
            and lo <= count_black(grid) <= hi
            and is_valid(grid)
        ):
            return [list(r) for r in grid]
        grid[mid] = [UNKNOWN] * n
    return None


def count_black(grid) -> int:
    """Return the number of black cells in the grid."""
    return sum(cell == BLACK for row in grid for cell in row)


def no_long_word_stack(line1, line2) -> bool:
    """Return True if no long white run in line1 overlaps a long white run in line2."""
    spans1 = long_spans(line1)
    if not spans1:
        return True
    spans2 = long_spans(line2)
    return not any(s1 <= e2 and s2 <= e1 for s1, e1 in spans1 for s2, e2 in spans2)


def long_spans(line) -> list:
    """Return (start, end) index ranges of white runs longer than STACK_MAX."""
    return [(start, end) for start, end in white_runs(line) if end - start + 1 > STACK_MAX]


def white_runs(line) -> list:
    """Return (start, end) index ranges of the maximal white runs in line."""
    runs = []
    n = len(line)
    i = 0
    while i < n:
        if line[i] == WHITE:
            start = i
            while i < n and line[i] == WHITE:
                i += 1
            runs.append((start, i - 1))
        else:
            i += 1
    return runs


def columns_feasible(grid) -> bool:
    """Return True if no column already contains a closed white run shorter than 3.

    UNKNOWN cells may still become white, so only black cells and the
    grid edges close a run.
    """
    n = len(grid)
    for c in range(n):
        col = [grid[r][c] for r in range(n)]
        for start, end in white_runs(col):
            left_closed = start == 0 or col[start - 1] == BLACK
            right_closed = end == n - 1 or col[end + 1] == BLACK
            if left_closed and right_closed and end - start + 1 < 3:
                return False
    return True


def is_valid(grid) -> bool:
    """Return True if a fully assigned grid satisfies every rule."""
    n = len(grid)
    cols = [[grid[r][c] for r in range(n)] for c in range(n)]
    if any(grid[r][c] != grid[n - 1 - r][n - 1 - c] for r in range(n) for c in range(n)):
        return False
    runs = [run for line in list(grid) + cols for run in white_runs(line)]
    if any(end - start + 1 < 3 for start, end in runs):
        return False
    if len(runs) > MAX_WORDS:
        return False
    if not white_cells_connected(grid):
        return False
    for lines in (grid, cols):
        if any(not no_long_word_stack(lines[i], lines[i + 1]) for i in range(n - 1)):
            return False
    return True


def white_cells_connected(grid) -> bool:
    """Return True if all white cells form one orthogonally connected region."""
    n = len(grid)
    whites = [(r, c) for r in range(n) for c in range(n) if grid[r][c] == WHITE]
    if not whites:
        return False
    seen = {whites[0]}
    queue = deque([whites[0]])
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n and grid[rr][cc] == WHITE and (rr, cc) not in seen:
                seen.add((rr, cc))
                queue.append((rr, cc))
    return len(seen) == len(whites)


def write_pdf(grid, filename: str) -> None:
    """Write the grid, with word numbers, to a one-page PDF."""
    content = page_content(grid).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ).encode("latin-1"),
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % (len(objects) + 1)
    out += b"startxref\n%d\n%%%%EOF\n" % xref

    with open(filename, "wb") as f:
        f.write(out)


def page_content(grid) -> str:
    """Return the PDF drawing commands for the grid, centred on the page."""
    n = len(grid)
    size = n * CELL_SIZE
    left = (PAGE_WIDTH - size) / 2
    top = (PAGE_HEIGHT + size) / 2
    ops = ["0.5 w"]

    for r in range(n):
        for c in range(n):
            x = left + c * CELL_SIZE
            y = top - (r + 1) * CELL_SIZE
            if grid[r][c] == BLACK:
                ops.append(f"{x:.2f} {y:.2f} {CELL_SIZE} {CELL_SIZE} re B")
            else:
                ops.append(f"{x:.2f} {y:.2f} {CELL_SIZE} {CELL_SIZE} re S")

    ops.append(f"1.5 w {left:.2f} {top - size:.2f} {size} {size} re S")

    ops.append(f"BT /F1 {NUMBER_FONT_SIZE} Tf")
    for number, (r, c) in enumerate(numbered_cells(grid), start=1):
        x = left + c * CELL_SIZE + 2
        y = top - r * CELL_SIZE - NUMBER_FONT_SIZE - 1
        ops.append(f"1 0 0 1 {x:.2f} {y:.2f} Tm ({number}) Tj")
    ops.append("ET")
    return "\n".join(ops)


def numbered_cells(grid) -> list:
    """Return (row, col) of each cell that starts an across or down word, in reading order."""
    n = len(grid)
    cells = []
    for r in range(n):
        for c in range(n):
            if grid[r][c] == BLACK:
                continue
            starts_across = (c == 0 or grid[r][c - 1] == BLACK) and c + 1 < n and grid[r][c + 1] == WHITE
            starts_down = (r == 0 or grid[r - 1][c] == BLACK) and r + 1 < n and grid[r + 1][c] == WHITE
            if starts_across or starts_down:
                cells.append((r, c))
    return cells


if __name__ == "__main__":
    main()
