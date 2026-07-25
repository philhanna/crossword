"""
Puzzle use cases - CRUD operations on puzzles and word editing.

Public interface:
  create_puzzle(user_id, name, size) -> None
  load_puzzle(user_id, name) -> Puzzle
  delete_puzzle(user_id, name) -> None
  list_puzzles(user_id, state=None) -> list[str]
  copy_puzzle(user_id, source_name, new_name) -> Puzzle
  rename_puzzle(user_id, old_name, new_name) -> None
  get_puzzle_state(user_id, name) -> dict
  set_puzzle_state(user_id, name, state, **fields) -> dict
  open_puzzle_for_editing(user_id, name) -> str
  switch_to_grid_mode(user_id, name) -> Puzzle
  switch_to_puzzle_mode(user_id, name) -> Puzzle
  toggle_black_cell(user_id, name, r, c) -> Puzzle
  rotate_grid(user_id, name) -> Puzzle
  generate_grid(user_id, name) -> Puzzle
  undo_grid(user_id, name) -> Puzzle
  redo_grid(user_id, name) -> Puzzle
  set_puzzle_title(user_id, name, title) -> Puzzle
  set_cell_letter(user_id, name, r, c, letter) -> Puzzle
  get_word_at(user_id, name, seq, direction) -> Word
  set_word_clue(user_id, name, seq, direction, clue) -> Puzzle
  undo_puzzle(user_id, name) -> Puzzle
  redo_puzzle(user_id, name) -> Puzzle
  clear_unlocked(user_id, name) -> Puzzle
  get_puzzle_preview(user_id, name) -> dict
  get_puzzle_stats(user_id, name) -> dict
  get_fill_order(user_id, name, top_n=10) -> dict
  get_dashboard(user_id) -> dict
"""

import logging
import uuid

from crossword import Grid, Puzzle, PuzzleToSVG
from crossword.domain import puzzle_state as ps
from crossword.domain.fill_priority import FillPriorityAnalyzer
from crossword.domain.word import Word
from crossword.ports.persistence_port import PersistencePort, PersistenceError
from crossword.use_cases._name_validation import validate_new_public_name, validate_public_name

logger = logging.getLogger(__name__)


class PuzzleUseCases:
    """
    Orchestrates puzzle operations via the persistence port.

    Constructor injection: takes a PersistencePort instance.
    """

    def __init__(self, persistence: PersistencePort, word_uc=None, grid_generator=None):
        self.persistence = persistence
        self.word_uc = word_uc
        self.grid_generator = grid_generator
        self._fill_order_cache: dict = {}

    def _invalidate_fill_order(self, user_id, name):
        self._fill_order_cache.pop((user_id, name), None)

    def create_puzzle(self, user_id: int, name: str, size: int) -> None:
        """
        Create a new puzzle and save it.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            size: New puzzle size

        Raises:
            PersistenceError: If save fails
        """
        validate_new_public_name("puzzle", name, self.persistence.list_puzzles(user_id))
        if size < 1:
            raise ValueError(f"Grid size must be at least 1, got {size}")

        grid = Grid(size)

        puzzle = Puzzle(grid)
        puzzle.enter_grid_mode()
        self.persistence.save_puzzle(user_id, name, puzzle)
        self.persistence.set_puzzle_state(user_id, name, ps.DRAFT)

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
        self._invalidate_fill_order(user_id, name)
        self.persistence.delete_puzzle(user_id, name)

    def list_puzzles(self, user_id: int, state: str | None = None) -> list[str]:
        """
        List all puzzle names owned by the user.

        Args:
            user_id: The user who owns the puzzles
            state: Optional lifecycle-state filter; "all"/None means no filter

        Returns:
            List of puzzle names, sorted most recent first

        Raises:
            PersistenceError: If listing fails
            ValueError: If state is not "all" or a valid lifecycle state
        """
        if state in (None, "", "all"):
            return self.persistence.list_puzzles(user_id, state=None)
        if state not in ps.ALL_STATES:
            raise ValueError(f"Invalid state: {state!r}")
        return self.persistence.list_puzzles(user_id, state=state)

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
        validate_public_name("puzzle", new_name)
        puzzle = self.persistence.load_puzzle(user_id, source_name)
        puzzle.grid_undo_stack = []
        puzzle.grid_redo_stack = []
        puzzle.undo_stack = []
        puzzle.redo_stack = []
        self.persistence.save_puzzle(user_id, new_name, puzzle)
        self._auto_set_state_on_save(user_id, new_name, puzzle)
        return puzzle

    def _auto_set_state_on_save(self, user_id: int, name: str, puzzle: Puzzle) -> None:
        """Advance a puzzle's state along the completion ladder after a save.

        Skips the write if it would just repeat the latest history row —
        otherwise every autosave of an unchanged ladder state (the common
        case) would add a row.
        """
        computed = ps.detect_completion_state(puzzle)
        current = self.persistence.get_puzzle_state(user_id, name)
        if current is not None and current["state"] == computed:
            return
        self.persistence.set_puzzle_state(user_id, name, computed)

    def rename_puzzle(self, user_id: int, old_name: str, new_name: str) -> None:
        """
        Rename a puzzle in place, preserving its id and state.

        Args:
            user_id: The user who owns the puzzle
            old_name: Current name of the puzzle
            new_name: Desired new name

        Raises:
            PersistenceError: If source not found or new_name is taken
            ValueError: If new_name is empty or invalid
        """
        if not new_name or not new_name.strip():
            raise ValueError("new_name must not be empty")
        validate_public_name("puzzle", new_name)
        self._invalidate_fill_order(user_id, old_name)
        self.persistence.rename_puzzle(user_id, old_name, new_name)

    def get_puzzle_state(self, user_id: int, name: str) -> dict:
        """
        Return the puzzle's current state columns.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            Dict with keys: state, publisher, date_submitted, date_published

        Raises:
            PersistenceError: If the puzzle is not found
        """
        state = self.persistence.get_puzzle_state(user_id, name)
        if state is None:
            raise PersistenceError(f"Puzzle '{name}' not found for user {user_id}")
        return state

    def set_puzzle_state(self, user_id: int, name: str, state: str, *,
                         publisher: str = None, date_submitted: str = None,
                         date_published: str = None) -> dict:
        """
        Apply a user-driven state transition and return the new state dict.

        Validates `state` against ALL_STATES and enforces the required fields
        for each target state: 'submitted' needs a non-empty free-form
        `publisher` plus `date_submitted`; 'published' needs `date_published`.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            state: Target lifecycle state (must be in ALL_STATES)
            publisher: Free-form publisher text (required for 'submitted')
            date_submitted: ISO date (required for 'submitted')
            date_published: ISO date (required for 'published')

        Returns:
            Dict with keys: state, publisher, date_submitted, date_published

        Raises:
            ValueError: If state is invalid or a required field is missing
            PersistenceError: If the puzzle is not found
        """
        if state not in ps.ALL_STATES:
            raise ValueError(f"Invalid state: {state!r}")

        if state == ps.SUBMITTED:
            if not (publisher or "").strip():
                raise ValueError("publisher is required when submitting")
            if not (date_submitted or "").strip():
                raise ValueError("date_submitted is required when submitting")
        elif state == ps.PUBLISHED:
            if not (date_published or "").strip():
                raise ValueError("date_published is required when publishing")

        self._invalidate_fill_order(user_id, name)
        self.persistence.set_puzzle_state(
            user_id, name, state,
            publisher=publisher,
            date_submitted=date_submitted,
            date_published=date_published,
        )
        return self.get_puzzle_state(user_id, name)

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
        working_name = f"__wc__{name}__{uuid.uuid4().hex[:8]}"
        puzzle = self.persistence.load_puzzle(user_id, name)
        puzzle.grid_undo_stack = []
        puzzle.grid_redo_stack = []
        puzzle.undo_stack = []
        puzzle.redo_stack = []
        self.persistence.save_puzzle(user_id, working_name, puzzle)
        return working_name

    def switch_to_grid_mode(self, user_id: int, name: str) -> Puzzle:
        """Enter Grid mode and reset Grid-mode history for this session."""
        puzzle = self.persistence.load_puzzle(user_id, name)
        puzzle.enter_grid_mode()
        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def switch_to_puzzle_mode(self, user_id: int, name: str) -> Puzzle:
        """Enter Puzzle mode and reset Puzzle-mode history for this session."""
        self._invalidate_fill_order(user_id, name)
        puzzle = self.persistence.load_puzzle(user_id, name)
        puzzle.enter_puzzle_mode()
        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def toggle_black_cell(self, user_id: int, name: str, r: int, c: int) -> Puzzle:
        """Toggle a black cell in the puzzle grid and save the change."""
        self._invalidate_fill_order(user_id, name)
        puzzle = self.persistence.load_puzzle(user_id, name)
        puzzle.toggle_black_cell(r, c)
        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def rotate_grid(self, user_id: int, name: str) -> Puzzle:
        """Rotate the puzzle grid and save the change."""
        self._invalidate_fill_order(user_id, name)
        puzzle = self.persistence.load_puzzle(user_id, name)
        puzzle.rotate_grid()
        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def generate_grid(self, user_id: int, name: str, spec: list[int] | None = None) -> Puzzle:
        """Generate a random valid grid for the puzzle and save the change."""
        self._invalidate_fill_order(user_id, name)
        puzzle = self.persistence.load_puzzle(user_id, name)
        newgrid = self.grid_generator.generate(puzzle.n, spec)
        puzzle.apply_generated_grid(newgrid)
        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def undo_grid(self, user_id: int, name: str) -> Puzzle:
        """Undo the last Grid-mode operation."""
        self._invalidate_fill_order(user_id, name)
        puzzle = self.persistence.load_puzzle(user_id, name)
        if puzzle.grid_undo_stack:
            puzzle.undo_grid_change()
            self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def redo_grid(self, user_id: int, name: str) -> Puzzle:
        """Redo the last undone Grid-mode operation."""
        self._invalidate_fill_order(user_id, name)
        puzzle = self.persistence.load_puzzle(user_id, name)
        if puzzle.grid_redo_stack:
            puzzle.redo_grid_change()
            self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

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
        self._invalidate_fill_order(user_id, name)
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
                      clue: str, text: str = None, locked: bool = None) -> Puzzle:
        """
        Set the clue (and optionally the text and locked state) for a word
        and save the change.

        If text is provided it is applied via puzzle.set_text(), which pushes
        the previous value onto the undo stack so the change can be undone.
        If locked is provided it is applied via puzzle.set_locked(), which is
        also tracked on the undo stack.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            seq: Numbered cell sequence number
            direction: 'across' or 'down'
            clue: The clue text
            text: Optional new word text (A-Z and spaces); tracked by undo
            locked: Optional new locked state; tracked by undo

        Returns:
            Updated Puzzle object

        Raises:
            PersistenceError: If load/save fails
            ValueError: If seq or direction is invalid
        """
        if text is not None:
            self._invalidate_fill_order(user_id, name)
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

        word_dir = Word.ACROSS if dir_lower == "across" else Word.DOWN
        word = puzzle.get_word(seq, word_dir)

        # If the text is actually changing and the word is currently locked,
        # unlock it first so the cell writes below aren't silently dropped by
        # Puzzle.set_cell. (The UI never does this - the Answer field is
        # disabled while a word is locked - but guard against it anyway.)
        if text is not None and text != word.get_text() and word.is_locked():
            puzzle.set_locked(seq, word_dir, False)

        if text is not None:
            puzzle.set_text(seq, word_dir, text)

        if locked is not None:
            puzzle.set_locked(seq, word_dir, locked)

        word.set_clue(clue if word.is_complete() else None)

        self.persistence.save_puzzle(user_id, name, puzzle)
        return puzzle

    def clear_unlocked(self, user_id: int, name: str) -> Puzzle:
        """
        Blank the text and clue of every unlocked word in a puzzle, leaving
        locked words untouched, and save the change if anything changed.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            Updated Puzzle object

        Raises:
            PersistenceError: If load/save fails
        """
        self._invalidate_fill_order(user_id, name)
        puzzle = self.persistence.load_puzzle(user_id, name)

        if puzzle.clear_unlocked():
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
        self._invalidate_fill_order(user_id, name)
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
        self._invalidate_fill_order(user_id, name)
        puzzle = self.persistence.load_puzzle(user_id, name)

        if puzzle.redo_stack:
            puzzle.redo()
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

    def get_fill_order(self, user_id: int, name: str, top_n: int = 10) -> dict:
        """
        Return a ranked list of slots that are good candidates to fill next.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle
            top_n: Maximum number of rows to return

        Returns:
            Dict with key:
            fill_priority

        Raises:
            PersistenceError: If puzzle not found
        """
        key = (user_id, name)
        if key in self._fill_order_cache:
            return self._fill_order_cache[key]
        puzzle = self.persistence.load_puzzle(user_id, name)
        analyzer = FillPriorityAnalyzer(self.word_uc)
        result = {
            "fill_priority": [
                {
                    "seq": item.seq,
                    "direction": item.direction,
                    "label": item.label,
                    "pattern": item.pattern,
                    "candidate_count": item.candidate_count,
                    "critical": item.critical,
                    "reason": item.reason,
                }
                for item in analyzer.rank_slots(puzzle, top_n=top_n)
            ]
        }
        self._fill_order_cache[key] = result
        return result

    def get_dashboard(self, user_id: int) -> dict:
        """Return all real puzzles with the summary metadata the dashboard needs.

        Excludes working copies (__wc__ / __new__) and legacy NULL names — the
        same set list_puzzles already returns. One row per puzzle, sorted most
        recently modified first.

        Returns:
            {"puzzles": [ {name, title, state, publisher, date_submitted,
                           date_published, modified, size, word_count,
                           top_lengths: [{length, count}, ...],   # top 2 desc
                           fill_pct}  ... ]}
        """
        summaries = self.persistence.list_puzzle_summaries(user_id)
        return {"puzzles": [self._dashboard_row(user_id, s) for s in summaries]}

    def _dashboard_row(self, user_id: int, summary: dict) -> dict:
        """Build one dashboard row from a summary plus the loaded puzzle."""
        name = summary["name"]
        puzzle = self.persistence.load_puzzle(user_id, name)

        wlens = puzzle.get_word_lengths()
        top_lengths = []
        for wlen in sorted(wlens.keys(), reverse=True)[:2]:
            count = len(wlens[wlen]["alist"]) + len(wlens[wlen]["dlist"])
            top_lengths.append({"length": wlen, "count": count})

        return {
            "name": name,
            "title": puzzle.title or "",
            "state": summary["state"],
            "publisher": summary["publisher"],
            "date_submitted": summary["date_submitted"],
            "date_published": summary["date_published"],
            "modified": summary["modified"],
            "size": puzzle.n,
            "word_count": puzzle.get_word_count(),
            "top_lengths": top_lengths,
            "fill_pct": round(puzzle.fill_fraction() * 100),
        }

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
