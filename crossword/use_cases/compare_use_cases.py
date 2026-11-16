# crossword.use_cases.compare_use_cases
"""
Compare use cases — show the differences between two puzzles.

Public interface:
  compare_puzzles(user_id, first, second) -> list[str]
"""

import difflib

from crossword.ports.import_port import PuzzleImportError
from crossword.ports.persistence_port import PersistencePort, PersistenceError
from crossword.use_cases.import_use_cases import ImportUseCases
from crossword.use_cases.puzzle_source import PuzzleSource


class PuzzleCompareError(Exception):
    """Raised when two puzzles cannot be compared."""
    pass


class CompareUseCases:
    """
    Compares the title, words and clues of two puzzles of the same shape.

    Constructor injection: takes a PersistencePort and an ImportUseCases
    (used to read puzzle files).
    """

    def __init__(self, persistence: PersistencePort, import_uc: ImportUseCases):
        self.persistence = persistence
        self.import_uc = import_uc

    def compare_puzzles(self, user_id: int, first: PuzzleSource, second: PuzzleSource) -> list[str]:
        """
        Return the changed lines between two puzzles.

        Args:
            user_id: Owner of any database puzzles
            first: Source of the first puzzle
            second: Source of the second puzzle

        Returns:
            Lines starting with '-' (first puzzle only) or '+' (second puzzle
            only), without line endings, no context. Empty if the puzzles match.

        Raises:
            PuzzleCompareError: If a puzzle cannot be loaded, or the two puzzles
                differ in size or black squares
        """
        puzzle1 = self._load(user_id, first)
        puzzle2 = self._load(user_id, second)
        self._check_same_shape(puzzle1, puzzle2)

        lines1 = self.puzzle_lines(puzzle1)
        lines2 = self.puzzle_lines(puzzle2)
        diff = list(difflib.unified_diff(lines1, lines2, lineterm="", n=0))

        # Keep only the changed lines: skip the two ---/+++ file header lines
        # and the @@ hunk headers.
        return [line for line in diff[2:] if not line.startswith("@@")]

    def _load(self, user_id, source: PuzzleSource):
        """Load one puzzle from the database or a file."""
        try:
            if source.kind == PuzzleSource.FILE:
                return self.import_uc.read_puzzle_from_file(source.value)
            return self.persistence.load_puzzle(user_id, source.value)
        except (PuzzleImportError, PersistenceError) as e:
            raise PuzzleCompareError(f"Cannot load {source.value}: {e}") from e

    @staticmethod
    def _check_same_shape(puzzle1, puzzle2) -> None:
        """Raise PuzzleCompareError unless sizes and black squares match."""
        if puzzle1.n != puzzle2.n:
            raise PuzzleCompareError(
                f"Puzzle sizes differ: {puzzle1.n}x{puzzle1.n} and {puzzle2.n}x{puzzle2.n}"
            )
        black1 = set(puzzle1.black_cells)
        black2 = set(puzzle2.black_cells)
        if black1 != black2:
            where = sorted(black1 ^ black2)
            shown = ", ".join(f"row {r} col {c}" for r, c in where[:5])
            if len(where) > 5:
                shown += ", ..."
            raise PuzzleCompareError(f"Black squares differ at {shown}")

    @staticmethod
    def puzzle_lines(puzzle) -> list[str]:
        """The text compared: title, then Across words, then Down words."""
        lines = [f"Title: {(puzzle.title or '').strip()}", "Across"]
        for seq in sorted(puzzle.across_words):
            lines.append(CompareUseCases._word_line(seq, puzzle.across_words[seq]))
        lines.append("Down")
        for seq in sorted(puzzle.down_words):
            lines.append(CompareUseCases._word_line(seq, puzzle.down_words[seq]))
        return lines

    @staticmethod
    def _word_line(seq, word) -> str:
        """'<number> <ANSWER>  <clue>', blank squares shown as '.'."""
        text = word.get_text().replace(" ", ".")
        clue = (word.get_clue() or "").strip()
        return f"{seq} {text}  {clue}".rstrip()
