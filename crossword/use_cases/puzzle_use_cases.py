"""
Puzzle use cases - CRUD operations on puzzles and word editing.

Public interface:
  create_puzzle(user_id, name, grid_name) -> None
  load_puzzle(user_id, name) -> Puzzle
  delete_puzzle(user_id, name) -> None
  list_puzzles(user_id) -> list[str]
  set_cell_letter(user_id, name, r, c, letter) -> Puzzle
  get_word_at(user_id, name, seq, direction) -> Word
  set_word_clue(user_id, name, seq, direction, clue) -> Puzzle
  undo_puzzle(user_id, name) -> Puzzle
  redo_puzzle(user_id, name) -> Puzzle
  replace_puzzle_grid(user_id, name, new_grid_name) -> Puzzle
"""

from crossword import Puzzle
from crossword.ports.persistence import PersistencePort, PersistenceError


class PuzzleUseCases:
    """
    Orchestrates puzzle operations via the persistence port.

    Constructor injection: takes a PersistencePort instance.
    """

    def __init__(self, persistence: PersistencePort):
        self.persistence = persistence

    def create_puzzle(self, user_id: int, name: str, grid_name: str) -> None:
        """
        Create a new puzzle from a grid and save it.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            grid_name: Name of the grid to base the puzzle on

        Raises:
            PersistenceError: If grid not found or save fails
        """
        grid = self.persistence.load_grid(user_id, grid_name)
        puzzle = Puzzle(grid)
        self.persistence.save_puzzle(user_id, name, puzzle)

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
        return self.persistence.load_puzzle(user_id, name)

    def delete_puzzle(self, user_id: int, name: str) -> None:
        """
        Delete a puzzle from persistent storage.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Raises:
            PersistenceError: If puzzle not found or deletion fails
        """
        self.persistence.delete_puzzle(user_id, name)

    def list_puzzles(self, user_id: int) -> list[str]:
        """
        List all puzzle names owned by the user.

        Args:
            user_id: The user who owns the puzzles

        Returns:
            List of puzzle names, sorted most recent first

        Raises:
            PersistenceError: If listing fails
        """
        return self.persistence.list_puzzles(user_id)

    def set_cell_letter(self, user_id: int, name: str, r: int, c: int, letter: str) -> Puzzle:
        """
        Set the letter in a puzzle cell and save the change.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            r: Row (1-indexed)
            c: Column (1-indexed)
            letter: Single character ('A'-'Z'), or ' ' for empty

        Returns:
            Updated Puzzle object

        Raises:
            PersistenceError: If load/save fails
            ValueError: If letter is invalid or cell is black
        """
        puzzle = self.persistence.load_puzzle(user_id, name)

        if puzzle.is_black_cell(r, c):
            raise ValueError(f"Cannot set letter in black cell ({r}, {c})")

        if not isinstance(letter, str) or len(letter) != 1:
            raise ValueError(f"Letter must be a single character, got {repr(letter)}")

        letter_upper = letter.upper()
        if letter_upper != ' ' and not letter_upper.isalpha():
            raise ValueError(f"Letter must be A-Z or space, got {repr(letter)}")

        puzzle.set_cell(r, c, letter_upper)
        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def get_word_at(self, user_id: int, name: str, seq: int, direction: str):
        """
        Get a word (across or down) at the specified numbered cell.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            seq: Numbered cell sequence number
            direction: 'across' or 'down'

        Returns:
            Word object (AcrossWord or DownWord)

        Raises:
            PersistenceError: If puzzle not found
            ValueError: If seq or direction is invalid
        """
        puzzle = self.persistence.load_puzzle(user_id, name)

        if direction.lower() == "across":
            if seq not in puzzle.across_words:
                raise ValueError(f"No across word at {seq}")
            return puzzle.across_words[seq]
        elif direction.lower() == "down":
            if seq not in puzzle.down_words:
                raise ValueError(f"No down word at {seq}")
            return puzzle.down_words[seq]
        else:
            raise ValueError(f"Direction must be 'across' or 'down', got {repr(direction)}")

    def set_word_clue(self, user_id: int, name: str, seq: int, direction: str, clue: str) -> Puzzle:
        """
        Set the clue for a word and save the change.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            seq: Numbered cell sequence number
            direction: 'across' or 'down'
            clue: The clue text

        Returns:
            Updated Puzzle object

        Raises:
            PersistenceError: If load/save fails
            ValueError: If seq or direction is invalid
        """
        puzzle = self.persistence.load_puzzle(user_id, name)

        if direction.lower() == "across":
            if seq not in puzzle.across_words:
                raise ValueError(f"No across word at {seq}")
            puzzle.across_words[seq].set_clue(clue)
        elif direction.lower() == "down":
            if seq not in puzzle.down_words:
                raise ValueError(f"No down word at {seq}")
            puzzle.down_words[seq].set_clue(clue)
        else:
            raise ValueError(f"Direction must be 'across' or 'down', got {repr(direction)}")

        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def undo_puzzle(self, user_id: int, name: str) -> Puzzle:
        """
        Undo the last operation on a puzzle.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            Updated Puzzle object

        Raises:
            PersistenceError: If load/save fails
        """
        puzzle = self.persistence.load_puzzle(user_id, name)

        if puzzle.undo_stack:
            puzzle.undo()
            self.persistence.save_puzzle(user_id, name, puzzle)

        return puzzle

    def redo_puzzle(self, user_id: int, name: str) -> Puzzle:
        """
        Redo the last undone operation on a puzzle.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            Updated Puzzle object

        Raises:
            PersistenceError: If load/save fails
        """
        puzzle = self.persistence.load_puzzle(user_id, name)

        if puzzle.redo_stack:
            puzzle.redo()
            self.persistence.save_puzzle(user_id, name, puzzle)

        return puzzle

    def replace_puzzle_grid(self, user_id: int, name: str, new_grid_name: str) -> Puzzle:
        """
        Replace the grid of a puzzle with a new grid, preserving clues where possible.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            new_grid_name: Name of the new grid to use

        Returns:
            Updated Puzzle object

        Raises:
            PersistenceError: If puzzle/grid not found or save fails
            ValueError: If grids have incompatible sizes
        """
        puzzle = self.persistence.load_puzzle(user_id, name)
        new_grid = self.persistence.load_grid(user_id, new_grid_name)

        puzzle.replace_grid(new_grid)
        self.persistence.save_puzzle(user_id, name, puzzle)

        return puzzle
