# crossword.adapters.puz_export_adapter
from datetime import date
from typing import Optional

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

    @staticmethod
    def _sanitize_text(text: Optional[str]) -> str:
        if not text:
            return ""

        translated = text.translate(
            str.maketrans(
                {
                    "\u2018": "'",
                    "\u2019": "'",
                    "\u201c": '"',
                    "\u201d": '"',
                    "\u2013": "-",
                    "\u2014": "-",
                    "\u2026": "...",
                    "\u00a0": " ",
                }
            )
        )
        return translated.encode("latin-1", "replace").decode("latin-1")

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
                clues.append(self._sanitize_text(puzzle.across_words[seq].get_clue()))
            if seq in puzzle.down_words:
                clues.append(self._sanitize_text(puzzle.down_words[seq].get_clue()))

        p = puz.Puzzle()
        p.title = self._sanitize_text(puzzle.title)
        p.author = self._sanitize_text(self.author_name)
        p.copyright = str(date.today().year)
        p.width = n
        p.height = n
        p.solution = "".join(solution_chars)
        p.fill = "".join(fill_chars)
        p.clues = clues

        return p.tobytes()
