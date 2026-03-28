# crossword.adapters.acrosslite_export_adapter
from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile

from crossword import Puzzle
from crossword.ports.export_port import ExportError


class AcrossLiteExportAdapter:
    """
    Exports a puzzle to AcrossLite text format.

    Produces a ZIP archive containing:
      - puzzle.txt  (AcrossLite text format)
      - puzzle.json (full JSON backup)
    """

    def export_puzzle_to_acrosslite(self, puzzle: Puzzle) -> bytes:
        try:
            txt = self._build_acrosslite_txt(puzzle)
            json_str = puzzle.to_json()

            buf = BytesIO()
            with ZipFile(buf, mode="w", compression=ZIP_DEFLATED) as zf:
                zf.writestr("puzzle.txt", txt)
                zf.writestr("puzzle.json", json_str)
            return buf.getvalue()
        except Exception as e:
            raise ExportError(f"AcrossLite export failed: {e}") from e

    def _build_acrosslite_txt(self, puzzle: Puzzle) -> str:
        n = puzzle.n
        indent = "     "

        with StringIO() as fp:
            fp.write("<ACROSS PUZZLE>\n")

            fp.write("<TITLE>\n")
            fp.write(indent + (puzzle.title or "") + "\n")

            fp.write("<AUTHOR>\n")
            fp.write(indent + "\n")

            fp.write("<COPYRIGHT>\n")
            fp.write(indent + "\n")

            fp.write("<SIZE>\n")
            fp.write(indent + f"{n}x{n}\n")

            fp.write("<GRID>\n")
            for r in range(1, n + 1):
                row = ""
                for c in range(1, n + 1):
                    if puzzle.is_black_cell(r, c):
                        row += "."
                    else:
                        letter = puzzle.get_cell(r, c)
                        row += letter if letter and letter.strip() else "X"
                fp.write(indent + row + "\n")

            fp.write("<ACROSS>\n")
            for seq in sorted(puzzle.across_words):
                clue = puzzle.across_words[seq].get_clue() or ""
                fp.write(indent + clue + "\n")

            fp.write("<DOWN>\n")
            for seq in sorted(puzzle.down_words):
                clue = puzzle.down_words[seq].get_clue() or ""
                fp.write(indent + clue + "\n")

            fp.write("<NOTEPAD>\n")
            fp.write("Created with Crossword Puzzle Editor, by Phil Hanna\n")
            fp.write("See https://github.com/philhanna/crossword\n")

            return fp.getvalue()
