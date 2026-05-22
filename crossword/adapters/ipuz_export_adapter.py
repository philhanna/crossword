# crossword.adapters.ipuz_export_adapter
import json
from datetime import date

from crossword import Puzzle
from crossword.ports.export_port import ExportError


class IpuzExportAdapter:
    """
    Exports a puzzle to ipuz format (http://www.ipuz.org/).

    ipuz is a JSON-based crossword interchange format. The output conforms to
    version 2 of the spec with kind "http://ipuz.org/crossword#1". Black cells
    are represented as "#", numbered cells as the sequence number, and other
    open cells as 0. The solution grid mirrors the puzzle grid with answer
    letters in white cells. Clues are emitted as [seq, text] pairs under
    "Across" and "Down".
    """

    BLOCK = "#"
    EMPTY = 0

    def __init__(self, author_name=None):
        self.author_name = author_name

    def export_puzzle_to_ipuz(self, puzzle: Puzzle) -> str:
        try:
            return self._build_ipuz(puzzle)
        except Exception as e:
            raise ExportError(f"ipuz export failed: {e}") from e

    def _build_ipuz(self, puzzle: Puzzle) -> str:
        n = puzzle.n
        numbered_at = self._numbered_cell_map(puzzle)
        puzzle_grid = self._build_puzzle_grid(puzzle, n, numbered_at)
        solution_grid = self._build_solution_grid(puzzle, n)
        clues = self._build_clues(puzzle)

        doc = {
            "version": "http://ipuz.org/v2",
            "kind": ["http://ipuz.org/crossword#1"],
            "dimensions": {"width": n, "height": n},
            "title": puzzle.title or "",
            "author": self.author_name or "",
            "date": date.today().strftime("%Y-%m-%d"),
            "block": self.BLOCK,
            "empty": self.EMPTY,
            "puzzle": puzzle_grid,
            "solution": solution_grid,
            "clues": clues,
        }
        return json.dumps(doc, indent=2)

    def _numbered_cell_map(self, puzzle: Puzzle) -> dict:
        return {(nc.r, nc.c): nc.seq for nc in puzzle.numbered_cells}

    def _build_puzzle_grid(self, puzzle: Puzzle, n: int, numbered_at: dict) -> list:
        rows = []
        for r in range(1, n + 1):
            row = []
            for c in range(1, n + 1):
                if puzzle.is_black_cell(r, c):
                    row.append(self.BLOCK)
                elif (r, c) in numbered_at:
                    row.append(numbered_at[(r, c)])
                else:
                    row.append(self.EMPTY)
            rows.append(row)
        return rows

    def _build_solution_grid(self, puzzle: Puzzle, n: int) -> list:
        rows = []
        for r in range(1, n + 1):
            row = []
            for c in range(1, n + 1):
                if puzzle.is_black_cell(r, c):
                    row.append(self.BLOCK)
                else:
                    letter = puzzle.get_cell(r, c)
                    row.append(letter.strip().upper() if letter and letter.strip() else "")
            rows.append(row)
        return rows

    def _build_clues(self, puzzle: Puzzle) -> dict:
        across = [
            [seq, puzzle.across_words[seq].get_clue() or ""]
            for seq in sorted(puzzle.across_words)
        ]
        down = [
            [seq, puzzle.down_words[seq].get_clue() or ""]
            for seq in sorted(puzzle.down_words)
        ]
        return {"Across": across, "Down": down}
