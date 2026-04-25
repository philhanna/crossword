import re

from crossword import Grid, Puzzle
from crossword.domain.word import Word
from crossword.ports.import_port import ImportPort, PuzzleImportError


class XdImportAdapter(ImportPort):
    """
    Imports a puzzle from the .xd crossword format.

    Format spec: https://github.com/century-arcade/xd/blob/master/doc/xd-format.md
    Sections are delimited by 2+ blank lines (3+ consecutive newlines).
    Grid: uppercase A-Z = letter, '#' or '_' = black cell.
    Clues: 'A<n>. text ~ ANSWER' (across) or 'D<n>. text ~ ANSWER' (down).
    """

    def import_puzzle(self, content: str) -> tuple[str, str, Puzzle]:
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        blocks = re.split(r'\n{3,}', content.strip())

        if len(blocks) < 3:
            raise PuzzleImportError(
                "Not an xd file: expected at least 3 sections separated by two blank lines"
            )

        meta = self._parse_metadata(blocks[0])
        title = meta.get('Title', '')
        author = meta.get('Author', '')

        grid_lines = self._parse_grid_lines(blocks[1])
        if not grid_lines:
            raise PuzzleImportError("Empty grid section")

        n = len(grid_lines)
        self._validate_grid(grid_lines, n)
        self._validate_symmetry(grid_lines, n)

        grid = Grid(n)
        for r, row in enumerate(grid_lines, 1):
            for c, ch in enumerate(row, 1):
                if ch in ('#', '_'):
                    grid.add_black_cell(r, c)

        puzzle = Puzzle(grid, title=title or None)
        puzzle.enter_puzzle_mode()

        for r, row in enumerate(grid_lines, 1):
            for c, ch in enumerate(row, 1):
                if ch.isupper():
                    puzzle.set_cell(r, c, ch)

        clues_block = '\n'.join(blocks[2:])
        across_clues, down_clues = self._parse_clues(clues_block)

        across_seqs = sorted(puzzle.across_words.keys())
        down_seqs = sorted(puzzle.down_words.keys())

        for seq in across_seqs:
            if seq in across_clues:
                puzzle.set_clue(seq, Word.ACROSS, across_clues[seq])
        for seq in down_seqs:
            if seq in down_clues:
                puzzle.set_clue(seq, Word.DOWN, down_clues[seq])

        return title, author, puzzle

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_metadata(self, block: str) -> dict[str, str]:
        meta: dict[str, str] = {}
        for line in block.splitlines():
            if ':' in line:
                key, _, value = line.partition(':')
                meta[key.strip()] = value.strip()
        return meta

    def _parse_grid_lines(self, block: str) -> list[str]:
        lines = []
        for line in block.splitlines():
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
        return lines

    def _validate_grid(self, grid_lines: list[str], n: int) -> None:
        for i, row in enumerate(grid_lines, 1):
            if len(row) != n:
                raise PuzzleImportError(
                    f"Grid row {i} has {len(row)} characters, expected {n}"
                )
            for ch in row:
                if ch not in ('#', '_', '.', ' ') and not ch.isupper():
                    raise PuzzleImportError(
                        f"Invalid character in grid row {i}: {ch!r}"
                    )

    def _validate_symmetry(self, grid_lines: list[str], n: int) -> None:
        for r in range(n):
            for c in range(n):
                if grid_lines[r][c] in ('#', '_'):
                    if grid_lines[n - 1 - r][n - 1 - c] not in ('#', '_'):
                        raise PuzzleImportError(
                            f"Grid lacks 180° rotational symmetry: black cell at row {r + 1}, col {c + 1}"
                            f" has no matching black cell at row {n - r}, col {n - c}"
                        )

    def _parse_clues(self, block: str) -> tuple[dict[int, str], dict[int, str]]:
        across: dict[int, str] = {}
        down: dict[int, str] = {}
        for line in block.splitlines():
            line = line.strip()
            m = re.match(r'^([AD])(\d+)\.\s+(.+)$', line)
            if not m:
                continue
            direction, seq, clue_text = m.group(1), int(m.group(2)), m.group(3)
            clue_text = clue_text.split(' ~ ')[0].strip()
            clue_text = re.sub(r'\{[/*_-](.*?)[/*_-]\}', r'\1', clue_text)
            if direction == 'A':
                across[seq] = clue_text
            else:
                down[seq] = clue_text
        return across, down
