# crossword.use_cases.compare_use_cases
"""
Compare use cases — show the differences between two puzzles.

Public interface:
  compare_puzzles(user_id, first, second) -> list[str]
  list_versions(user_id, name) -> list[dict]
"""

from crossword import Puzzle
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
            only), without line endings, no context. Each
            '-' line is immediately followed by its '+' line. Empty if the
            puzzles match.

        Raises:
            PuzzleCompareError: If a puzzle cannot be loaded, or the two puzzles
                differ in size or black squares
        """
        puzzle1 = self._load(user_id, first)
        puzzle2 = self._load(user_id, second)
        self._check_same_shape(puzzle1, puzzle2)

        lines1 = self.puzzle_lines(puzzle1)
        lines2 = self.puzzle_lines(puzzle2)

        # Same size and black squares means the same word numbers, so the two
        # line lists match up one-to-one. Show each changed pair together.
        diff = []
        for old, new in zip(lines1, lines2):
            if old != new:
                diff.append(f"-{old}")
                diff.append(f"+{new}")
        return diff

    def list_versions(self, user_id: int, name: str) -> list[dict]:
        """
        List the saved versions of a database puzzle that can be compared.

        Only history rows that kept a content snapshot count. Versions are
        numbered 1 (oldest) upward; `back` is 0 for the newest, -1 for the
        one before it, and so on.

        Returns:
            Dicts with keys: number, back, id, state, comment, changed_at

        Raises:
            PuzzleCompareError: If the puzzle cannot be found
        """
        try:
            history = self.persistence.get_puzzle_state_history(user_id, name)
        except PersistenceError as e:
            raise PuzzleCompareError(f"Cannot load {name}: {e}") from e
        if history is None:
            raise PuzzleCompareError(f"Cannot load {name}: puzzle not found")

        rows = [h for h in history if h["has_content"]]
        return [
            {
                "number": i,
                "back": i - len(rows),
                "id": h["id"],
                "state": h["state"],
                "comment": h["comment"],
                "changed_at": h["changed_at"],
            }
            for i, h in enumerate(rows, start=1)
        ]

    def _load(self, user_id, source: PuzzleSource):
        """Load one puzzle from the database (live or an old version) or a file."""
        try:
            if source.kind == PuzzleSource.FILE:
                return self.import_uc.read_puzzle_from_file(source.value)
            if source.version is not None:
                return self._load_version(user_id, source)
            return self.persistence.load_puzzle(user_id, source.value)
        except (PuzzleImportError, PersistenceError) as e:
            raise PuzzleCompareError(f"Cannot load {source.value}: {e}") from e

    def _load_version(self, user_id, source: PuzzleSource):
        """Load a saved version of a database puzzle from its history."""
        versions = self.list_versions(user_id, source.value)
        if not versions:
            raise PuzzleCompareError(f"{source.value} has no saved versions")

        n = source.version
        index = n - 1 if n >= 1 else len(versions) - 1 + n
        if not 0 <= index < len(versions):
            raise PuzzleCompareError(
                f"{source.value} has no version {n} "
                f"(it has {len(versions)}, numbered 1 to {len(versions)}, "
                f"or 0 to {1 - len(versions)} counting back)"
            )

        content = self.persistence.get_puzzle_state_history_content(
            user_id, source.value, versions[index]["id"]
        )
        if content is None:
            raise PuzzleCompareError(f"{source.value}@{n} has no saved content")
        return Puzzle.from_json(content)

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
            lines.append(CompareUseCases._word_line(seq, "A", puzzle.across_words[seq]))
        lines.append("Down")
        for seq in sorted(puzzle.down_words):
            lines.append(CompareUseCases._word_line(seq, "D", puzzle.down_words[seq]))
        return lines

    @staticmethod
    def _word_line(seq, direction, word) -> str:
        """'<number><A or D> <ANSWER>  <clue>', blank squares shown as '.'."""
        text = word.get_text().replace(" ", ".")
        clue = (word.get_clue() or "").strip()
        return f"{seq}{direction} {text}  {clue}".rstrip()
