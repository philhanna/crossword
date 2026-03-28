# crossword.adapters.json_export_adapter
import json

from crossword import Puzzle
from crossword.ports.export_port import ExportError


class JsonExportAdapter:
    """
    Exports a puzzle to JSON format.

    Produces a clean, human-readable JSON document containing the puzzle
    title, grid size, cell layout, and all across/down words with their
    text and clues. Internal state (undo/redo stacks, mode) is omitted.
    """

    def export_puzzle_to_json(self, puzzle: Puzzle) -> str:
        try:
            return self._build_json(puzzle)
        except Exception as e:
            raise ExportError(f"JSON export failed: {e}") from e

    def _build_json(self, puzzle: Puzzle) -> str:
        n = puzzle.n

        grid_rows = []
        for r in range(1, n + 1):
            row = ""
            for c in range(1, n + 1):
                if puzzle.is_black_cell(r, c):
                    row += "."
                else:
                    letter = puzzle.get_cell(r, c)
                    row += letter.strip() if letter and letter.strip() else " "
            grid_rows.append(row)

        across = [
            {
                "seq": seq,
                "text": puzzle.across_words[seq].get_text(),
                "clue": puzzle.across_words[seq].get_clue(),
            }
            for seq in sorted(puzzle.across_words)
        ]

        down = [
            {
                "seq": seq,
                "text": puzzle.down_words[seq].get_text(),
                "clue": puzzle.down_words[seq].get_clue(),
            }
            for seq in sorted(puzzle.down_words)
        ]

        doc = {
            "title": puzzle.title or "",
            "size": n,
            "grid": grid_rows,
            "across": across,
            "down": down,
        }

        return json.dumps(doc, indent=2)
