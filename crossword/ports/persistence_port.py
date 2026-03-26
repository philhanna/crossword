"""
Persistence Port - CRUD operations for grids and puzzles

This port defines the contract that any persistence adapter (SQLite, file-based, etc.)
must implement to save and load grids and puzzles.

Single-threaded access is assumed. No transactions are defined.
"""

from abc import ABC, abstractmethod
from crossword import Grid, Puzzle


class PersistenceError(Exception):
    """Base exception for all persistence operations"""
    pass


class PersistencePort(ABC):
    """
    Abstract interface for persistent storage of grids and puzzles.

    Assumes single-threaded access and a single hardcoded user (user_id).
    All operations are synchronous.
    """

    # ======================================================================
    # Grid Operations
    # ======================================================================

    @abstractmethod
    def save_grid(self, user_id: int, name: str, grid: Grid) -> None:
        """
        Save a grid to persistent storage.

        If a grid with the same name already exists, it is overwritten.
        Updated timestamps should be maintained by the adapter.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid
            grid: Grid object to save

        Raises:
            PersistenceError: If storage fails (e.g., permission denied, disk full)
        """
        pass

    @abstractmethod
    def load_grid(self, user_id: int, name: str) -> Grid:
        """
        Load a grid from persistent storage.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Returns:
            Grid object

        Raises:
            PersistenceError: If grid not found or loading fails
        """
        pass

    @abstractmethod
    def delete_grid(self, user_id: int, name: str) -> None:
        """
        Delete a grid from persistent storage.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Raises:
            PersistenceError: If grid not found or deletion fails
        """
        pass

    @abstractmethod
    def list_grids(self, user_id: int) -> list[str]:
        """
        Get list of grid names for a user.

        Results are sorted with most recently modified first.

        Args:
            user_id: The user who owns these grids

        Returns:
            List of grid name strings, sorted most recent first

        Raises:
            PersistenceError: If listing fails
        """
        pass

    # ======================================================================
    # Puzzle Operations
    # ======================================================================

    @abstractmethod
    def save_puzzle(self, user_id: int, name: str, puzzle: Puzzle) -> None:
        """
        Save a puzzle to persistent storage.

        If a puzzle with the same name already exists, it is overwritten.
        Updated timestamps should be maintained by the adapter.

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
    def list_puzzles(self, user_id: int) -> list[str]:
        """
        Get list of puzzle names for a user.

        Results are sorted with most recently modified first.

        Args:
            user_id: The user who owns these puzzles

        Returns:
            List of puzzle name strings, sorted most recent first

        Raises:
            PersistenceError: If listing fails
        """
        pass
