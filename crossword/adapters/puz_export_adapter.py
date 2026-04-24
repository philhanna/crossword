# crossword.adapters.puz_export_adapter
from datetime import date

import puz

from crossword import Puzzle
from crossword.ports.export_port import ExportError


class PuzExportAdapter:
    """
    Exports a puzzle to AcrossLite binary format (.puz) using puzpy.
    """

    def __init__(self, author_name=None):
        self.author_name = author_name

    def export_puzzle_to_puz(self, puzzle: Puzzle) -> bytes:
        try:
            return self._build_puz(puzzle)
        except Exception as e:
            raise ExportError(f".puz export failed: {e}") from e

    def _build_puz(self, puzzle: Puzzle) -> bytes:
        n = puzzle.n
        black = "."

        solution_chars = []
        fill_chars = []
        for r in range(1, n + 1):
            for c in range(1, n + 1):
                if puzzle.is_black_cell(r, c):
                    solution_chars.append(black)
                    fill_chars.append(black)
                else:
                    letter = puzzle.get_cell(r, c)
                    solution_chars.append(letter if letter and letter.strip() else "-")
                    fill_chars.append("-")

        all_seqs = sorted(set(puzzle.across_words) | set(puzzle.down_words))
        clues = []
        for seq in all_seqs:
            if seq in puzzle.across_words:
                clues.append(puzzle.across_words[seq].get_clue() or "")
            if seq in puzzle.down_words:
                clues.append(puzzle.down_words[seq].get_clue() or "")

        p = puz.Puzzle()
        p.title = puzzle.title or ""
        p.author = self.author_name or ""
        p.copyright = str(date.today().year)
        p.width = n
        p.height = n
        p.solution = "".join(solution_chars)
        p.fill = "".join(fill_chars)
        p.clues = clues

        return p.tobytes()
