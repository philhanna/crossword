# crossword.adapters.ipuz_import_adapter
import html
import json
import re

from crossword import Grid, Puzzle

_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
from crossword.domain.word import Word
from crossword.ports.import_port import ImportPort, PuzzleImportError


class IpuzImportAdapter(ImportPort):
    """
    Imports a puzzle from the ipuz JSON format (http://www.ipuz.org/).

    Supports v1 and v2 of the crossword kind. The puzzle grid may use
    integers, 0, or strings for cells; black cells may be the document's
    declared block marker (defaults to "#"). Solution letters are taken from
    the optional `solution` grid; if absent, cells stay empty. Clues are read
    from the `Across` and `Down` lists under `clues` and accept either
    [seq, text] pairs or {number, clue} objects.
    """

    DEFAULT_BLOCK = "#"

    def import_puzzle(self, content: str) -> tuple[str, str, Puzzle]:
        doc = self._parse_json(content)
        self._validate_kind(doc)

        title = (doc.get("title") or "").strip()
        author = (doc.get("author") or "").strip()
        block_marker = doc.get("block", self.DEFAULT_BLOCK)

        puzzle_grid = doc.get("puzzle")
        if not isinstance(puzzle_grid, list) or not puzzle_grid:
            raise PuzzleImportError("Missing or empty 'puzzle' grid")

        n = self._grid_size(doc, puzzle_grid)
        self._validate_square(puzzle_grid, n)

        black_cells = self._collect_black_cells(puzzle_grid, n, block_marker)
        self._validate_symmetry(black_cells, n)

        grid = Grid(n)
        for r, c in black_cells:
            grid.add_black_cell(r, c)

        puzzle = Puzzle(grid, title=title or None)
        puzzle.enter_puzzle_mode()

        solution = doc.get("solution")
        if solution is not None:
            self._apply_solution(puzzle, solution, n, block_marker)

        clues = doc.get("clues") or {}
        across_clues = self._parse_clue_list(clues.get("Across"))
        down_clues = self._parse_clue_list(clues.get("Down"))

        for seq in sorted(puzzle.across_words):
            if seq in across_clues:
                puzzle.set_clue(seq, Word.ACROSS, across_clues[seq])
        for seq in sorted(puzzle.down_words):
            if seq in down_clues:
                puzzle.set_clue(seq, Word.DOWN, down_clues[seq])

        return title, author, puzzle

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_json(self, content: str) -> dict:
        text = content.strip()
        if text.startswith("ipuz(") and text.endswith(")"):
            text = text[len("ipuz("):-1]
        try:
            doc = json.loads(text)
        except json.JSONDecodeError as e:
            raise PuzzleImportError(f"Not a valid ipuz file: {e}") from e
        if not isinstance(doc, dict):
            raise PuzzleImportError("ipuz root must be a JSON object")
        return doc

    def _validate_kind(self, doc: dict) -> None:
        kinds = doc.get("kind")
        if not isinstance(kinds, list) or not kinds:
            raise PuzzleImportError("ipuz file missing 'kind'")
        if not any("crossword" in str(k) for k in kinds):
            raise PuzzleImportError(f"Unsupported ipuz kind: {kinds}")

    def _grid_size(self, doc: dict, puzzle_grid: list) -> int:
        dims = doc.get("dimensions") or {}
        width = dims.get("width")
        height = dims.get("height")
        if width is not None and height is not None:
            if width != height:
                raise PuzzleImportError(
                    f"Only square grids are supported (got {width}x{height})"
                )
            return int(width)
        return len(puzzle_grid)

    def _validate_square(self, puzzle_grid: list, n: int) -> None:
        if len(puzzle_grid) != n:
            raise PuzzleImportError(
                f"Grid has {len(puzzle_grid)} rows, expected {n}"
            )
        for i, row in enumerate(puzzle_grid, 1):
            if not isinstance(row, list) or len(row) != n:
                raise PuzzleImportError(
                    f"Grid row {i} has wrong length, expected {n}"
                )

    def _collect_black_cells(self, puzzle_grid: list, n: int, block_marker) -> list:
        black = []
        for r in range(n):
            for c in range(n):
                if self._is_block(puzzle_grid[r][c], block_marker):
                    black.append((r + 1, c + 1))
        return black

    def _is_block(self, cell, block_marker) -> bool:
        if cell == block_marker:
            return True
        if isinstance(cell, dict) and cell.get("cell") == block_marker:
            return True
        return False

    def _validate_symmetry(self, black_cells: list, n: int) -> None:
        black_set = set(black_cells)
        for r, c in black_cells:
            mirror = (n + 1 - r, n + 1 - c)
            if mirror not in black_set:
                raise PuzzleImportError(
                    f"Grid lacks 180° rotational symmetry: black cell at row {r}, col {c}"
                    f" has no matching black cell at row {mirror[0]}, col {mirror[1]}"
                )

    def _apply_solution(self, puzzle: Puzzle, solution: list, n: int, block_marker) -> None:
        if not isinstance(solution, list) or len(solution) != n:
            return
        for r in range(n):
            row = solution[r]
            if not isinstance(row, list) or len(row) != n:
                continue
            for c in range(n):
                if puzzle.is_black_cell(r + 1, c + 1):
                    continue
                letter = self._extract_letter(row[c], block_marker)
                if letter:
                    puzzle.set_cell(r + 1, c + 1, letter)

    def _extract_letter(self, cell, block_marker) -> str:
        if cell is None or cell == block_marker:
            return ""
        if isinstance(cell, dict):
            cell = cell.get("value") or cell.get("cell") or ""
        if not isinstance(cell, str):
            return ""
        letter = cell.strip().upper()
        if len(letter) == 1 and letter.isalpha():
            return letter
        return ""

    def _parse_clue_list(self, raw) -> dict:
        clues: dict[int, str] = {}
        if not isinstance(raw, list):
            return clues
        for entry in raw:
            seq, text = self._parse_clue_entry(entry)
            if seq is not None:
                clues[seq] = text
        return clues

    def _parse_clue_entry(self, entry) -> tuple[int | None, str]:
        if isinstance(entry, list) and len(entry) >= 2:
            try:
                return int(entry[0]), _clean_clue(entry[1])
            except (TypeError, ValueError):
                return None, ""
        if isinstance(entry, dict):
            num = entry.get("number")
            clue = entry.get("clue", "")
            try:
                return int(num), _clean_clue(clue)
            except (TypeError, ValueError):
                return None, ""
        return None, ""


def _clean_clue(value) -> str:
    text = html.unescape(str(value))
    return _TAG_RE.sub("", text)
