"""
Puzzle use cases - CRUD operations on puzzles and word editing.

Public interface:
  create_puzzle(user_id, name, grid_name) -> None
  load_puzzle(user_id, name) -> Puzzle
  delete_puzzle(user_id, name) -> None
  list_puzzles(user_id) -> list[str]
  copy_puzzle(user_id, source_name, new_name) -> Puzzle
  open_puzzle_for_editing(user_id, name) -> str
  set_puzzle_title(user_id, name, title) -> Puzzle
  reset_word(user_id, name, seq, direction) -> Puzzle
  set_cell_letter(user_id, name, r, c, letter) -> Puzzle
  get_word_at(user_id, name, seq, direction) -> Word
  set_word_clue(user_id, name, seq, direction, clue) -> Puzzle
  undo_puzzle(user_id, name) -> Puzzle
  redo_puzzle(user_id, name) -> Puzzle
  replace_puzzle_grid(user_id, name, new_grid_name) -> Puzzle
  get_puzzle_preview(user_id, name) -> dict
  get_puzzle_stats(user_id, name) -> dict
"""

import logging
import uuid

from crossword import Puzzle, PuzzleToSVG
from crossword.domain.word import Word
from crossword.ports.persistence import PersistencePort, PersistenceError

logger = logging.getLogger(__name__)


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

    def copy_puzzle(self, user_id: int, source_name: str, new_name: str) -> Puzzle:
        """
        Copy a puzzle to a new name.

        Args:
            user_id: The user who owns the puzzle
            source_name: Name of the puzzle to copy
            new_name: Name for the copy

        Returns:
            The copied Puzzle object

        Raises:
            PersistenceError: If source not found or save fails
            ValueError: If new_name is empty
        """
        if not new_name or not new_name.strip():
            raise ValueError("new_name must not be empty")
        puzzle = self.persistence.load_puzzle(user_id, source_name)
        puzzle.undo_stack = []
        puzzle.redo_stack = []
        self.persistence.save_puzzle(user_id, new_name, puzzle)
        return puzzle

    def open_puzzle_for_editing(self, user_id: int, name: str) -> str:
        """
        Open a puzzle for editing by creating a working copy.

        The working copy is a snapshot of the puzzle at the time of opening.
        All edits should target the working copy name. On Save, copy the
        working copy back over the original. On Close, delete the working copy.

        Args:
            user_id: The user who owns this puzzle
            name: Name of the puzzle to open

        Returns:
            working_name: The name of the working copy (e.g. '__wc__a1b2c3d4')

        Raises:
            PersistenceError: If puzzle not found or save fails
        """
        working_name = f"__wc__{uuid.uuid4().hex[:8]}"
        puzzle = self.persistence.load_puzzle(user_id, name)
        puzzle.undo_stack = []
        puzzle.redo_stack = []
        self.persistence.save_puzzle(user_id, working_name, puzzle)
        return working_name

    def set_puzzle_title(self, user_id: int, name: str, title: str) -> Puzzle:
        """
        Set the title of a puzzle and save the change.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            title: New title string (may be empty)

        Returns:
            Updated Puzzle object

        Raises:
            PersistenceError: If load/save fails
        """
        puzzle = self.persistence.load_puzzle(user_id, name)
        puzzle.title = title
        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def reset_word(self, user_id: int, name: str, seq: int, direction: str) -> Puzzle:
        """
        Clear all letters in a word that are not shared with a completed crossing word.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            seq: Numbered cell sequence number
            direction: 'across' or 'down'

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
            word = puzzle.across_words[seq]
        elif direction.lower() == "down":
            if seq not in puzzle.down_words:
                raise ValueError(f"No down word at {seq}")
            word = puzzle.down_words[seq]
        else:
            raise ValueError(f"Direction must be 'across' or 'down', got {repr(direction)}")

        cleared_text = word.get_clear_word()
        old_text = word.get_text()
        if old_text != cleared_text:
            puzzle.undo_stack.append(["text", seq, direction.lower(), old_text])
        word.set_text(cleared_text)
        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

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

    def set_word_clue(self, user_id: int, name: str, seq: int, direction: str,
                      clue: str, text: str = None) -> Puzzle:
        """
        Set the clue (and optionally the text) for a word and save the change.

        If text is provided it is applied via puzzle.set_text(), which pushes
        the previous value onto the undo stack so the change can be undone.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            seq: Numbered cell sequence number
            direction: 'across' or 'down'
            clue: The clue text
            text: Optional new word text (A-Z and spaces); tracked by undo

        Returns:
            Updated Puzzle object

        Raises:
            PersistenceError: If load/save fails
            ValueError: If seq or direction is invalid
        """
        puzzle = self.persistence.load_puzzle(user_id, name)
        dir_lower = direction.lower()

        if dir_lower == "across":
            if seq not in puzzle.across_words:
                raise ValueError(f"No across word at {seq}")
        elif dir_lower == "down":
            if seq not in puzzle.down_words:
                raise ValueError(f"No down word at {seq}")
        else:
            raise ValueError(f"Direction must be 'across' or 'down', got {repr(direction)}")

        if text is not None:
            word_dir = Word.ACROSS if dir_lower == "across" else Word.DOWN
            puzzle.set_text(seq, word_dir, text)

        if dir_lower == "across":
            puzzle.across_words[seq].set_clue(clue)
        else:
            puzzle.down_words[seq].set_clue(clue)

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
            undo_snapshot = list(puzzle.undo_stack)
            redo_snapshot = list(puzzle.redo_stack)
            applying = puzzle.undo_stack[-1]
            puzzle.undo()
            self.persistence.save_puzzle(user_id, name, puzzle)
            logger.info("undo: puzzle=%s applying=%s", name, applying)
            logger.info("  undo_stack: %s", undo_snapshot)
            logger.info("  redo_stack: %s", redo_snapshot)
        else:
            logger.info("undo requested but stack empty: puzzle=%s", name)

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
            undo_snapshot = list(puzzle.undo_stack)
            redo_snapshot = list(puzzle.redo_stack)
            applying = puzzle.redo_stack[-1]
            puzzle.redo()
            self.persistence.save_puzzle(user_id, name, puzzle)
            logger.info("redo: puzzle=%s applying=%s", name, applying)
            logger.info("  undo_stack: %s", undo_snapshot)
            logger.info("  redo_stack: %s", redo_snapshot)
        else:
            logger.info("redo requested but stack empty: puzzle=%s", name)

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

    def get_puzzle_stats(self, user_id: int, name: str) -> dict:
        """
        Return statistics and validation results for a puzzle.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            Dict with keys: valid, errors, size, wordcount, blockcount,
            wordlengths

        Raises:
            PersistenceError: If puzzle not found
        """
        puzzle = self.persistence.load_puzzle(user_id, name)
        return puzzle.get_statistics()

    def get_puzzle_preview(self, user_id: int, name: str) -> dict:
        """
        Return a scaled-down SVG and summary heading for a puzzle.

        Used by the chooser to display a thumbnail for each puzzle.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            Dict with keys: name, heading, width, svgstr

        Raises:
            PersistenceError: If puzzle not found
        """
        puzzle = self.persistence.load_puzzle(user_id, name)
        scale = 0.75
        svg = PuzzleToSVG(puzzle, scale=scale)
        width = (svg.boxsize * puzzle.n + 32) * scale
        svgstr = svg.generate_xml()

        heading_parts = [f"{puzzle.get_word_count()} words"]
        wlens = puzzle.get_word_lengths()
        for wlen in sorted(wlens.keys(), reverse=True)[:2]:
            total = len(wlens[wlen]['alist']) + len(wlens[wlen]['dlist'])
            heading_parts.append(f"{wlen}-letter: {total}")
        heading = f"{name} ({', '.join(heading_parts)})"

        return {
            "name": name,
            "heading": heading,
            "width": width,
            "svgstr": svgstr,
        }
