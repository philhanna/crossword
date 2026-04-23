# crossword.ports.import_port
from abc import ABC, abstractmethod
from crossword import Puzzle


class PuzzleImportError(Exception):
    """Raised when a puzzle file cannot be parsed or is invalid."""
    pass


class ImportPort(ABC):
    """Abstract interface for importing puzzles from external formats."""

    @abstractmethod
    def import_puzzle(self, content: str) -> tuple[str, str, Puzzle]:
        """
        Parse format-specific content and return (title, author, puzzle).

        Args:
            content: Full text content of the file to import

        Returns:
            (title, author, puzzle) — title and author are stripped strings
            (may be empty); puzzle is a fully initialized Puzzle in puzzle mode.

        Raises:
            PuzzleImportError: If the content is malformed or missing required data
        """
        pass
