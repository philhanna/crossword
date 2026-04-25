from datetime import date
from io import StringIO

from crossword import Puzzle
from crossword.ports.export_port import ExportError


class XdExportAdapter:
    """
    Exports a puzzle to the .xd crossword format.

    Format spec: https://github.com/century-arcade/xd/blob/master/doc/xd-format.md
    Sections are separated by two blank lines (three consecutive newlines).
    Grid: uppercase A-Z for filled cells, '#' for black cells, '.' for empty cells.
    Clues: 'A<n>. text ~ ANSWER' (across) or 'D<n>. text ~ ANSWER' (down).
    """

    def __init__(self, author_name=None):
        self.author_name = author_name

    def export_puzzle_to_xd(self, puzzle: Puzzle) -> str:
        try:
            return self._build_xd(puzzle)
        except Exception as e:
            raise ExportError(f"xd export failed: {e}") from e

    def _build_xd(self, puzzle: Puzzle) -> str:
        n = puzzle.n

        with StringIO() as fp:
            # Metadata
            fp.write(f"Title: {puzzle.title or ''}\n")
            fp.write(f"Author: {self.author_name or ''}\n")
            fp.write(f"Date: {date.today().strftime('%Y-%m-%d')}\n")

            # Grid section (two blank lines = separator)
            fp.write("\n\n")
            for r in range(1, n + 1):
                row = ""
                for c in range(1, n + 1):
                    if puzzle.is_black_cell(r, c):
                        row += "#"
                    else:
                        letter = puzzle.get_cell(r, c)
                        row += letter.strip().upper() if letter and letter.strip() else "."
                fp.write(row + "\n")

            # Clues section (two blank lines = separator)
            fp.write("\n\n")
            for seq in sorted(puzzle.across_words):
                word = puzzle.across_words[seq]
                clue = word.get_clue() or ""
                answer = word.get_text().replace(" ", ".").upper()
                fp.write(f"A{seq}. {clue} ~ {answer}\n")

            fp.write("\n")
            for seq in sorted(puzzle.down_words):
                word = puzzle.down_words[seq]
                clue = word.get_clue() or ""
                answer = word.get_text().replace(" ", ".").upper()
                fp.write(f"D{seq}. {clue} ~ {answer}\n")

            return fp.getvalue()
