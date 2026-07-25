"""
Persistence Port - CRUD operations for persisted crossword puzzle data.

The merged editor persists unified Puzzle objects only. Standalone saved
grids are no longer part of the architecture.

Single-threaded access is assumed. No transactions are defined.
"""

from abc import ABC, abstractmethod
from crossword import Puzzle


class PersistenceError(Exception):
    """Base exception for all persistence operations"""
    pass


class PersistencePort(ABC):
    """
    Abstract interface for persistent storage.

    Assumes single-threaded access and a single hardcoded user (user_id).
    All operations are synchronous.
    """

    # ======================================================================
    # Puzzle Operations
    # ======================================================================

    @abstractmethod
    def save_puzzle(self, user_id: int, name: str, puzzle: Puzzle) -> None:
        """
        Save a puzzle to persistent storage.

        If a puzzle with the same name already exists, it is overwritten.
        Updated timestamps and persisted mode metadata should be maintained
        by the adapter.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            puzzle: Puzzle object to save

        Raises:
            PersistenceError: If storage fails (e.g., permission denied, disk full)
        """
        pass

    @abstractmethod
    def load_puzzle(self, user_id: int, name: str) -> Puzzle:
        """
        Load a puzzle from persistent storage.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            Puzzle object

        Raises:
            PersistenceError: If puzzle not found or loading fails
        """
        pass

    @abstractmethod
    def delete_puzzle(self, user_id: int, name: str) -> None:
        """
        Delete a puzzle from persistent storage.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Raises:
            PersistenceError: If puzzle not found or deletion fails
        """
        pass

    @abstractmethod
    def set_puzzle_state(self, user_id: int, name: str, state: str, *,
                         publisher: str | None = None,
                         date_submitted: str | None = None,
                         date_published: str | None = None) -> None:
        """
        Append a new state-history row for this puzzle.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            state: The new lifecycle state
            publisher: Free-form publisher text (for 'submitted')
            date_submitted: ISO date (for 'submitted')
            date_published: ISO date (for 'published')

        Raises:
            PersistenceError: If the puzzle is not found or the write fails
        """
        pass

    @abstractmethod
    def get_puzzle_state(self, user_id: int, name: str) -> dict | None:
        """
        Return the most recent state-history row for this puzzle as a dict,
        or None if the puzzle doesn't exist (or has no history row yet).

        Keys: state, publisher, date_submitted, date_published.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Raises:
            PersistenceError: If the read fails
        """
        pass

    @abstractmethod
    def rename_puzzle(self, user_id: int, old_name: str, new_name: str) -> None:
        """
        Rename a puzzle in place, preserving its id and all columns (state
        included).

        Args:
            user_id: The user who owns this puzzle
            old_name: Current name of the puzzle
            new_name: Desired new name

        Raises:
            PersistenceError: If the puzzle is not found or new_name is taken
        """
        pass

    @abstractmethod
    def list_puzzles(self, user_id: int, state: str | None = None) -> list[str]:
        """
        Get list of puzzle names for a user.

        Results are sorted with most recently modified first.

        Args:
            user_id: The user who owns these puzzles
            state: Optional lifecycle-state filter, matched against each
                puzzle's latest state-history row

        Returns:
            List of puzzle name strings, sorted most recent first

        Raises:
            PersistenceError: If listing fails
        """
        pass

    @abstractmethod
    def list_puzzle_summaries(self, user_id: int) -> list[dict]:
        """
        Return summary rows for the user's real puzzles, most recent first.

        Each row is a dict with keys: name, modified, state, publisher,
        date_submitted, date_published, sourced from each puzzle's latest
        state-history row. Excludes working copies
        (puzzlename LIKE '__wc__%' / '__new__%') and legacy NULL names.

        Args:
            user_id: The user who owns these puzzles

        Returns:
            List of summary dicts, sorted most recently modified first

        Raises:
            PersistenceError: If listing fails
        """
        pass
