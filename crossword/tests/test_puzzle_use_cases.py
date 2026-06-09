"""
Unit tests for PuzzleUseCases
"""

import pytest
from unittest.mock import Mock
from crossword import Grid, Puzzle
from crossword.domain import puzzle_state as ps
from crossword.tests import TestPuzzle
from crossword.use_cases.puzzle_use_cases import PuzzleUseCases
from crossword.ports.persistence_port import PersistenceError


@pytest.fixture
def mock_persistence():
    """Create a mock persistence adapter"""
    persistence = Mock()
    persistence.list_puzzles.return_value = []
    # Default: puzzles have no recorded state (brand-new name). Individual
    # tests override this when they need a specific current state.
    persistence.get_puzzle_state.return_value = None
    return persistence


@pytest.fixture
def puzzle_uc(mock_persistence):
    """Create a PuzzleUseCases instance with mock persistence"""
    return PuzzleUseCases(mock_persistence)


@pytest.fixture
def test_grid():
    """Create a test grid"""
    grid = Grid(15)
    grid.add_black_cell(1, 1, undo=False)
    return grid


@pytest.fixture
def test_puzzle(test_grid):
    """Create a test puzzle"""
    return Puzzle(test_grid, title="Test Puzzle")


class TestPuzzleUseCasesCreate:
    """Tests for create_puzzle"""

    def test_create_puzzle_from_size_success(self, puzzle_uc, mock_persistence):
        puzzle_uc.create_puzzle(1, "test_puzzle", size=15)

        mock_persistence.save_puzzle.assert_called_once()
        args = mock_persistence.save_puzzle.call_args[0]
        assert args[1] == "test_puzzle"
        assert isinstance(args[2], Puzzle)
        assert args[2].n == 15
        assert args[2].last_mode == "grid"

    def test_create_puzzle_rejects_invalid_size(self, puzzle_uc):
        with pytest.raises(ValueError, match="Grid size must be at least 1"):
            puzzle_uc.create_puzzle(1, "test_puzzle", size=0)

    def test_create_puzzle_rejects_working_copy_prefix(self, puzzle_uc, mock_persistence):
        """Reject names reserved for internal working copies"""
        with pytest.raises(ValueError, match="reserved for internal working copies"):
            puzzle_uc.create_puzzle(1, "__wc__hidden", size=15)

        mock_persistence.save_puzzle.assert_not_called()

    def test_create_puzzle_rejects_existing_name(self, puzzle_uc, mock_persistence):
        """Reject creating a new puzzle over an existing saved puzzle"""
        mock_persistence.list_puzzles.return_value = ["existing"]

        with pytest.raises(ValueError, match="puzzle 'existing' already exists"):
            puzzle_uc.create_puzzle(1, "existing", size=15)

        mock_persistence.save_puzzle.assert_not_called()


class TestPuzzleUseCasesCopy:
    """Tests for copy_puzzle"""

    def test_copy_puzzle_success(self, puzzle_uc, mock_persistence, test_puzzle):
        """Copy a puzzle to a new name"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.copy_puzzle(1, "original", "copy")

        mock_persistence.load_puzzle.assert_called_once_with(1, "original")
        mock_persistence.save_puzzle.assert_called_once_with(1, "copy", test_puzzle)
        assert result is test_puzzle

    def test_copy_puzzle_source_not_found(self, puzzle_uc, mock_persistence):
        """Copy a puzzle that does not exist"""
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            puzzle_uc.copy_puzzle(1, "nonexistent", "copy")

    def test_copy_puzzle_empty_new_name(self, puzzle_uc):
        """Reject an empty new_name"""
        with pytest.raises(ValueError, match="new_name must not be empty"):
            puzzle_uc.copy_puzzle(1, "original", "")

    def test_copy_puzzle_whitespace_new_name(self, puzzle_uc):
        """Reject a whitespace-only new_name"""
        with pytest.raises(ValueError, match="new_name must not be empty"):
            puzzle_uc.copy_puzzle(1, "original", "   ")

    def test_copy_puzzle_rejects_working_copy_prefix(self, puzzle_uc, mock_persistence):
        """Reject copy targets reserved for working copies"""
        with pytest.raises(ValueError, match="reserved for internal working copies"):
            puzzle_uc.copy_puzzle(1, "original", "__wc__copy")

        mock_persistence.load_puzzle.assert_not_called()
        mock_persistence.save_puzzle.assert_not_called()

    def test_copy_puzzle_preserves_clues(self, puzzle_uc, mock_persistence, test_puzzle):
        """Copied puzzle retains clues from the source"""
        # Set a clue on the first across word if any exist
        if test_puzzle.across_words:
            seq = next(iter(test_puzzle.across_words))
            test_puzzle.across_words[seq].set_clue("Test clue")
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.copy_puzzle(1, "original", "copy")

        if result.across_words:
            seq = next(iter(result.across_words))
            assert result.across_words[seq].get_clue() == "Test clue"


class TestPuzzleUseCasesLoad:
    """Tests for load_puzzle"""

    def test_load_puzzle_success(self, puzzle_uc, mock_persistence, test_puzzle):
        """Load puzzle successfully"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.load_puzzle(1, "test_puzzle")

        assert result == test_puzzle
        mock_persistence.load_puzzle.assert_called_once_with(1, "test_puzzle")

    def test_load_puzzle_not_found(self, puzzle_uc, mock_persistence):
        """Load puzzle that doesn't exist"""
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            puzzle_uc.load_puzzle(1, "nonexistent")


class TestPuzzleUseCasesDelete:
    """Tests for delete_puzzle"""

    def test_delete_puzzle_success(self, puzzle_uc, mock_persistence):
        """Delete puzzle successfully"""
        puzzle_uc.delete_puzzle(1, "test_puzzle")

        mock_persistence.delete_puzzle.assert_called_once_with(1, "test_puzzle")

    def test_delete_puzzle_not_found(self, puzzle_uc, mock_persistence):
        """Delete puzzle that doesn't exist"""
        mock_persistence.delete_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            puzzle_uc.delete_puzzle(1, "nonexistent")


class TestPuzzleUseCasesList:
    """Tests for list_puzzles"""

    def test_list_puzzles_success(self, puzzle_uc, mock_persistence):
        """List puzzles successfully"""
        mock_persistence.list_puzzles.return_value = ["puzzle1", "puzzle2"]

        result = puzzle_uc.list_puzzles(1)

        assert result == ["puzzle1", "puzzle2"]
        mock_persistence.list_puzzles.assert_called_once_with(1, state=None)

    def test_list_puzzles_empty(self, puzzle_uc, mock_persistence):
        """List puzzles when none exist"""
        mock_persistence.list_puzzles.return_value = []

        result = puzzle_uc.list_puzzles(1)

        assert result == []

    def test_list_puzzles_all_maps_to_no_filter(self, puzzle_uc, mock_persistence):
        puzzle_uc.list_puzzles(1, state="all")

        mock_persistence.list_puzzles.assert_called_once_with(1, state=None)

    def test_list_puzzles_specific_state_filters(self, puzzle_uc, mock_persistence):
        puzzle_uc.list_puzzles(1, state=ps.DRAFT)

        mock_persistence.list_puzzles.assert_called_once_with(1, state=ps.DRAFT)

    def test_list_puzzles_invalid_state_raises(self, puzzle_uc):
        with pytest.raises(ValueError, match="Invalid state"):
            puzzle_uc.list_puzzles(1, state="bogus")


class TestPuzzleUseCasesGetDashboard:
    """Tests for get_dashboard"""

    def test_get_dashboard_one_row_per_summary(self, puzzle_uc, mock_persistence, test_puzzle):
        mock_persistence.list_puzzle_summaries.return_value = [
            {"name": "alpha", "modified": "2026-06-06T00:00:00", "state": "draft",
             "publisher": None, "date_submitted": None, "date_published": None},
            {"name": "beta", "modified": "2026-01-01T00:00:00", "state": "submitted",
             "publisher": "NYT", "date_submitted": "2026-01-01", "date_published": None},
        ]
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_dashboard(1)

        assert [r["name"] for r in result["puzzles"]] == ["alpha", "beta"]

    def test_get_dashboard_row_shape(self, puzzle_uc, mock_persistence, test_puzzle):
        mock_persistence.list_puzzle_summaries.return_value = [
            {"name": "alpha", "modified": "2026-06-06T00:00:00", "state": "submitted",
             "publisher": "NYT", "date_submitted": "2026-06-06", "date_published": None},
        ]
        mock_persistence.load_puzzle.return_value = test_puzzle

        row = puzzle_uc.get_dashboard(1)["puzzles"][0]

        assert set(row.keys()) == {
            "name", "title", "state", "publisher", "date_submitted",
            "date_published", "modified", "size", "word_count",
            "top_lengths", "fill_pct",
        }
        assert row["title"] == test_puzzle.title
        assert row["state"] == "submitted"
        assert row["publisher"] == "NYT"
        assert row["size"] == test_puzzle.n
        assert row["word_count"] == test_puzzle.get_word_count()
        assert row["fill_pct"] == 0  # blank puzzle

    def test_get_dashboard_top_lengths_are_two_largest(self, puzzle_uc, mock_persistence, test_puzzle):
        mock_persistence.list_puzzle_summaries.return_value = [
            {"name": "alpha", "modified": "2026-06-06T00:00:00", "state": "draft",
             "publisher": None, "date_submitted": None, "date_published": None},
        ]
        mock_persistence.load_puzzle.return_value = test_puzzle

        top = puzzle_uc.get_dashboard(1)["puzzles"][0]["top_lengths"]

        wlens = test_puzzle.get_word_lengths()
        expected = sorted(wlens.keys(), reverse=True)[:2]
        assert [t["length"] for t in top] == expected
        assert len(top) <= 2
        for t in top:
            wlen = t["length"]
            assert t["count"] == len(wlens[wlen]["alist"]) + len(wlens[wlen]["dlist"])

    def test_get_dashboard_empty(self, puzzle_uc, mock_persistence):
        mock_persistence.list_puzzle_summaries.return_value = []

        result = puzzle_uc.get_dashboard(1)

        assert result == {"puzzles": []}


class TestPuzzleUseCasesOpenForEditing:
    """Tests for open_puzzle_for_editing"""

    def test_open_puzzle_returns_working_name(self, puzzle_uc, mock_persistence, test_puzzle):
        """Returns a working copy name with the __wc__ prefix"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        working_name = puzzle_uc.open_puzzle_for_editing(1, "mypuzzle")

        assert working_name.startswith("__wc__mypuzzle__")

    def test_open_puzzle_creates_working_copy(self, puzzle_uc, mock_persistence, test_puzzle):
        """Saves a working copy under the returned name"""
        test_puzzle.grid_undo_stack = ["old"]
        test_puzzle.grid_redo_stack = ["old"]
        test_puzzle.undo_stack = [["text", 1, "A", "OLD"]]
        test_puzzle.redo_stack = [["text", 1, "A", "NEW"]]
        mock_persistence.load_puzzle.return_value = test_puzzle

        working_name = puzzle_uc.open_puzzle_for_editing(1, "mypuzzle")

        mock_persistence.load_puzzle.assert_called_once_with(1, "mypuzzle")
        mock_persistence.save_puzzle.assert_called_once_with(1, working_name, test_puzzle)
        assert test_puzzle.grid_undo_stack == []
        assert test_puzzle.grid_redo_stack == []
        assert test_puzzle.undo_stack == []
        assert test_puzzle.redo_stack == []

    def test_open_puzzle_unique_names(self, puzzle_uc, mock_persistence, test_puzzle):
        """Each call returns a different working name"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        name1 = puzzle_uc.open_puzzle_for_editing(1, "mypuzzle")
        name2 = puzzle_uc.open_puzzle_for_editing(1, "mypuzzle")

        assert name1 != name2

    def test_open_puzzle_not_found(self, puzzle_uc, mock_persistence):
        """Raises PersistenceError if puzzle does not exist"""
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            puzzle_uc.open_puzzle_for_editing(1, "nonexistent")


class TestPuzzleUseCasesSetTitle:
    """Tests for set_puzzle_title"""

    def test_set_title_success(self, puzzle_uc, mock_persistence, test_puzzle):
        """Set a title and save"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.set_puzzle_title(1, "test_puzzle", "My Great Puzzle")

        assert result.title == "My Great Puzzle"
        mock_persistence.save_puzzle.assert_called_once_with(1, "test_puzzle", test_puzzle)

    def test_set_title_empty_string(self, puzzle_uc, mock_persistence, test_puzzle):
        """Empty string is a valid title (clears it)"""
        test_puzzle.title = "Old Title"
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.set_puzzle_title(1, "test_puzzle", "")

        assert result.title == ""
        mock_persistence.save_puzzle.assert_called_once()

    def test_set_title_not_found(self, puzzle_uc, mock_persistence):
        """Raises PersistenceError if puzzle does not exist"""
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            puzzle_uc.set_puzzle_title(1, "nonexistent", "Title")


class TestPuzzleUseCasesModes:
    """Tests for puzzle mode switching and grid-mode editing"""

    def test_switch_to_grid_mode(self, puzzle_uc, mock_persistence, test_puzzle):
        test_puzzle.last_mode = "puzzle"
        test_puzzle.grid_undo_stack = ["old"]
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.switch_to_grid_mode(1, "test_puzzle")

        assert result.last_mode == "grid"
        assert result.grid_undo_stack == []
        mock_persistence.save_puzzle.assert_called_once_with(1, "test_puzzle", test_puzzle)

    def test_switch_to_puzzle_mode(self, puzzle_uc, mock_persistence, test_puzzle):
        test_puzzle.last_mode = "grid"
        test_puzzle.undo_stack = [["text", 1, "A", "OLD"]]
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.switch_to_puzzle_mode(1, "test_puzzle")

        assert result.last_mode == "puzzle"
        assert result.undo_stack == []
        assert result.redo_stack == []
        mock_persistence.save_puzzle.assert_called_once_with(1, "test_puzzle", test_puzzle)

    def test_toggle_black_cell_on_puzzle(self, puzzle_uc, mock_persistence, test_puzzle):
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.toggle_black_cell(1, "test_puzzle", 2, 2)

        assert result.is_black_cell(2, 2)
        mock_persistence.save_puzzle.assert_called_once_with(1, "test_puzzle", test_puzzle)

    def test_rotate_grid_on_puzzle(self, puzzle_uc, mock_persistence, test_puzzle):
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.rotate_grid(1, "test_puzzle")

        assert result is test_puzzle
        mock_persistence.save_puzzle.assert_called_once_with(1, "test_puzzle", test_puzzle)

    def test_undo_grid_on_puzzle(self, puzzle_uc, mock_persistence, test_puzzle):
        test_puzzle.toggle_black_cell(2, 2)
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.undo_grid(1, "test_puzzle")

        assert not result.is_black_cell(2, 2)
        mock_persistence.save_puzzle.assert_called_once_with(1, "test_puzzle", test_puzzle)

    def test_redo_grid_on_puzzle(self, puzzle_uc, mock_persistence, test_puzzle):
        test_puzzle.toggle_black_cell(2, 2)
        test_puzzle.undo_grid_change()
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.redo_grid(1, "test_puzzle")

        assert result.is_black_cell(2, 2)
        mock_persistence.save_puzzle.assert_called_once_with(1, "test_puzzle", test_puzzle)



class TestPuzzleUseCasesSetCellLetter:
    """Tests for set_cell_letter"""

    def test_set_cell_letter_valid(self, puzzle_uc, mock_persistence, test_puzzle):
        """Set cell letter with valid input"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.set_cell_letter(1, "test_puzzle", 2, 2, "A")

        assert result.get_cell(2, 2) == "A"
        mock_persistence.save_puzzle.assert_called_once()

    def test_set_cell_letter_lowercase_converted(self, puzzle_uc, mock_persistence, test_puzzle):
        """Set cell letter converts lowercase to uppercase"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.set_cell_letter(1, "test_puzzle", 2, 2, "a")

        assert result.get_cell(2, 2) == "A"

    def test_set_cell_letter_space(self, puzzle_uc, mock_persistence, test_puzzle):
        """Set cell letter to space (empty)"""
        test_puzzle.set_cell(2, 2, "A")
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.set_cell_letter(1, "test_puzzle", 2, 2, " ")

        assert result.get_cell(2, 2) == " "

    def test_set_cell_letter_black_cell(self, puzzle_uc, mock_persistence, test_puzzle):
        """Cannot set letter in black cell"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        # (1, 1) is black due to test_grid fixture
        with pytest.raises(ValueError, match="Cannot set letter in black cell"):
            puzzle_uc.set_cell_letter(1, "test_puzzle", 1, 1, "A")

    def test_set_cell_letter_invalid_character(self, puzzle_uc, mock_persistence, test_puzzle):
        """Cannot set invalid character"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        with pytest.raises(ValueError, match="Letter must be A-Z or space"):
            puzzle_uc.set_cell_letter(1, "test_puzzle", 2, 2, "1")

    def test_set_cell_letter_multiple_characters(self, puzzle_uc, mock_persistence, test_puzzle):
        """Cannot set multiple characters"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        with pytest.raises(ValueError, match="Letter must be a single character"):
            puzzle_uc.set_cell_letter(1, "test_puzzle", 2, 2, "AB")


class TestPuzzleUseCasesGetWordAt:
    """Tests for get_word_at"""

    def test_get_word_at_across(self, puzzle_uc, mock_persistence, test_puzzle):
        """Get across word at numbered cell"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        # Since test_puzzle has numbered cells, get the first one
        if test_puzzle.across_words:
            first_seq = list(test_puzzle.across_words.keys())[0]
            result = puzzle_uc.get_word_at(1, "test_puzzle", first_seq, "across")
            assert result == test_puzzle.across_words[first_seq]

    def test_get_word_at_down(self, puzzle_uc, mock_persistence, test_puzzle):
        """Get down word at numbered cell"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        if test_puzzle.down_words:
            first_seq = list(test_puzzle.down_words.keys())[0]
            result = puzzle_uc.get_word_at(1, "test_puzzle", first_seq, "down")
            assert result == test_puzzle.down_words[first_seq]

    def test_get_word_at_invalid_direction(self, puzzle_uc, mock_persistence, test_puzzle):
        """Get word with invalid direction"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        with pytest.raises(ValueError, match="Direction must be 'across' or 'down'"):
            puzzle_uc.get_word_at(1, "test_puzzle", 1, "diagonal")

    def test_get_word_at_nonexistent_seq_across(self, puzzle_uc, mock_persistence, test_puzzle):
        """Get nonexistent across word"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        with pytest.raises(ValueError, match="No across word at"):
            puzzle_uc.get_word_at(1, "test_puzzle", 9999, "across")

    def test_get_word_at_nonexistent_seq_down(self, puzzle_uc, mock_persistence, test_puzzle):
        """Get nonexistent down word"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        with pytest.raises(ValueError, match="No down word at"):
            puzzle_uc.get_word_at(1, "test_puzzle", 9999, "down")


class TestPuzzleUseCasesSetWordClue:
    """Tests for set_word_clue"""

    def test_set_word_clue_across(self, puzzle_uc, mock_persistence, test_puzzle):
        """Set clue for across word"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        if test_puzzle.across_words:
            first_seq = list(test_puzzle.across_words.keys())[0]
            word = test_puzzle.across_words[first_seq]
            word.set_text("A" * word.length)
            result = puzzle_uc.set_word_clue(1, "test_puzzle", first_seq, "across", "Test clue")
            assert test_puzzle.across_words[first_seq].get_clue() == "Test clue"
            mock_persistence.save_puzzle.assert_called_once()

    def test_set_word_clue_down(self, puzzle_uc, mock_persistence, test_puzzle):
        """Set clue for down word"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        if test_puzzle.down_words:
            first_seq = list(test_puzzle.down_words.keys())[0]
            word = test_puzzle.down_words[first_seq]
            word.set_text("A" * word.length)
            result = puzzle_uc.set_word_clue(1, "test_puzzle", first_seq, "down", "Test clue")
            assert test_puzzle.down_words[first_seq].get_clue() == "Test clue"
            mock_persistence.save_puzzle.assert_called_once()

    def test_set_word_clue_invalid_direction(self, puzzle_uc, mock_persistence, test_puzzle):
        """Set clue with invalid direction"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        with pytest.raises(ValueError, match="Direction must be 'across' or 'down'"):
            puzzle_uc.set_word_clue(1, "test_puzzle", 1, "invalid", "Clue")

    def test_set_word_clue_clears_clue_for_incomplete_word_when_text_saved(
            self, puzzle_uc, mock_persistence, test_puzzle):
        """Incomplete words cannot keep clues when text save leaves blanks."""
        mock_persistence.load_puzzle.return_value = test_puzzle

        first_seq = list(test_puzzle.across_words.keys())[0]
        word = test_puzzle.across_words[first_seq]
        incomplete_text = "A" + (" " * (word.length - 1))

        puzzle_uc.set_word_clue(
            1, "test_puzzle", first_seq, "across", "Should be cleared", incomplete_text
        )

        assert word.get_text() == incomplete_text
        assert word.get_clue() is None
        mock_persistence.save_puzzle.assert_called_once()

    def test_set_word_clue_clears_clue_for_existing_incomplete_word(
            self, puzzle_uc, mock_persistence, test_puzzle):
        """Incomplete words cannot keep clues even when only clue text is saved."""
        mock_persistence.load_puzzle.return_value = test_puzzle

        first_seq = list(test_puzzle.across_words.keys())[0]
        word = test_puzzle.across_words[first_seq]
        word.set_text("B" + (" " * (word.length - 1)))

        puzzle_uc.set_word_clue(1, "test_puzzle", first_seq, "across", "Should be cleared")

        assert word.get_clue() is None
        mock_persistence.save_puzzle.assert_called_once()


class TestPuzzleUseCasesUndo:
    """Tests for undo_puzzle"""

    def test_undo_puzzle_with_operations(self, puzzle_uc, mock_persistence, test_puzzle):
        """Undo puzzle operation"""
        # Manually set up an undo operation without triggering domain logic
        test_puzzle.undo_stack = [["text", 1, "across", "OLDVALUE"]]
        mock_persistence.load_puzzle.return_value = test_puzzle

        # Mock the undo method to avoid domain logic errors
        test_puzzle.undo = Mock()

        result = puzzle_uc.undo_puzzle(1, "test_puzzle")

        # Should call undo and save
        test_puzzle.undo.assert_called_once()
        mock_persistence.save_puzzle.assert_called_once_with(1, "test_puzzle", test_puzzle)

    def test_undo_puzzle_empty_stack(self, puzzle_uc, mock_persistence, test_puzzle):
        """Undo puzzle when stack is empty"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        # Should not raise
        result = puzzle_uc.undo_puzzle(1, "test_puzzle")

        assert result == test_puzzle
        # save_puzzle is NOT called when undo_stack is empty
        mock_persistence.save_puzzle.assert_not_called()


class TestPuzzleUseCasesRedo:
    """Tests for redo_puzzle"""

    def test_redo_puzzle_with_operations(self, puzzle_uc, mock_persistence, test_puzzle):
        """Redo puzzle operation"""
        # Manually set up a redo operation without triggering domain logic
        test_puzzle.redo_stack = [["text", 1, "across", "NEWVALUE"]]
        mock_persistence.load_puzzle.return_value = test_puzzle

        # Mock the redo method to avoid domain logic errors
        test_puzzle.redo = Mock()

        result = puzzle_uc.redo_puzzle(1, "test_puzzle")

        # Should call redo and save
        test_puzzle.redo.assert_called_once()
        mock_persistence.save_puzzle.assert_called_once_with(1, "test_puzzle", test_puzzle)

    def test_redo_puzzle_empty_stack(self, puzzle_uc, mock_persistence, test_puzzle):
        """Redo puzzle when stack is empty"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        # Should not raise
        result = puzzle_uc.redo_puzzle(1, "test_puzzle")

        assert result == test_puzzle
        # save_puzzle is NOT called when redo_stack is empty
        mock_persistence.save_puzzle.assert_not_called()


class TestPuzzleUseCasesGetPreview:
    """Tests for get_puzzle_preview"""

    def test_get_puzzle_preview_returns_dict(self, puzzle_uc, mock_persistence, test_puzzle):
        """get_puzzle_preview returns a dict with required keys"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_puzzle_preview(1, "my_puzzle")

        assert isinstance(result, dict)
        assert result["name"] == "my_puzzle"
        assert "heading" in result
        assert "width" in result
        assert "svgstr" in result

    def test_get_puzzle_preview_svgstr_is_xml(self, puzzle_uc, mock_persistence, test_puzzle):
        """svgstr should be an SVG XML string"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_puzzle_preview(1, "my_puzzle")

        assert "<svg" in result["svgstr"]

    def test_get_puzzle_preview_heading_contains_name(self, puzzle_uc, mock_persistence, test_puzzle):
        """heading should contain the puzzle name"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_puzzle_preview(1, "my_puzzle")

        assert "my_puzzle" in result["heading"]

    def test_get_puzzle_preview_width_is_positive(self, puzzle_uc, mock_persistence, test_puzzle):
        """width should be a positive number"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_puzzle_preview(1, "my_puzzle")

        assert result["width"] > 0

    def test_get_puzzle_preview_not_found(self, puzzle_uc, mock_persistence):
        """get_puzzle_preview raises PersistenceError if puzzle not found"""
        mock_persistence.load_puzzle.side_effect = PersistenceError("not found")

        with pytest.raises(PersistenceError):
            puzzle_uc.get_puzzle_preview(1, "missing_puzzle")


class TestPuzzleUseCasesGetStats:
    """Tests for get_puzzle_stats"""

    def test_get_puzzle_stats_returns_required_keys(self, puzzle_uc, mock_persistence, test_puzzle):
        """get_puzzle_stats returns dict with all required keys"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_puzzle_stats(1, "my_puzzle")

        assert "valid" in result
        assert "errors" in result
        assert "size" in result
        assert "wordcount" in result
        assert "blockcount" in result
        assert "wordlengths" in result

    def test_get_puzzle_stats_valid_is_bool(self, puzzle_uc, mock_persistence, test_puzzle):
        """valid field is a boolean"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_puzzle_stats(1, "my_puzzle")

        assert isinstance(result["valid"], bool)

    def test_get_puzzle_stats_size_contains_n(self, puzzle_uc, mock_persistence, test_puzzle):
        """size field reflects puzzle dimensions"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_puzzle_stats(1, "my_puzzle")

        assert "15" in result["size"]

    def test_get_puzzle_stats_wordcount_is_int(self, puzzle_uc, mock_persistence, test_puzzle):
        """wordcount is an integer"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_puzzle_stats(1, "my_puzzle")

        assert isinstance(result["wordcount"], int)

    def test_get_puzzle_stats_not_found(self, puzzle_uc, mock_persistence):
        """get_puzzle_stats raises PersistenceError if puzzle not found"""
        mock_persistence.load_puzzle.side_effect = PersistenceError("not found")

        with pytest.raises(PersistenceError):
            puzzle_uc.get_puzzle_stats(1, "missing")

class TestPuzzleUseCasesGetFillOrder:
    """Tests for get_fill_order"""

    class _StubWordUseCases:
        def get_all_words(self):
            return ["aaa"]

        def get_candidate_count(self, word, cache=None):
            return 3

    def test_get_fill_order_returns_ranked_items(self, mock_persistence, test_puzzle):
        puzzle_uc = PuzzleUseCases(mock_persistence, word_uc=self._StubWordUseCases())
        mock_persistence.load_puzzle.return_value = test_puzzle

        result = puzzle_uc.get_fill_order(1, "my_puzzle")

        assert "fill_priority" in result
        assert isinstance(result["fill_priority"], list)
        if result["fill_priority"]:
            first = result["fill_priority"][0]
            assert "label" in first
            assert "pattern" in first
            assert "candidate_count" in first
            assert "reason" in first

    def test_get_fill_order_cached_on_second_call(self, mock_persistence, test_puzzle):
        """rank_slots is only called once when called twice with no edit between"""
        from unittest.mock import patch
        puzzle_uc = PuzzleUseCases(mock_persistence, word_uc=self._StubWordUseCases())
        mock_persistence.load_puzzle.return_value = test_puzzle

        with patch("crossword.use_cases.puzzle_use_cases.FillPriorityAnalyzer") as MockAnalyzer:
            mock_instance = MockAnalyzer.return_value
            mock_instance.rank_slots.return_value = []
            puzzle_uc.get_fill_order(1, "my_puzzle")
            puzzle_uc.get_fill_order(1, "my_puzzle")

        mock_instance.rank_slots.assert_called_once()

    def test_get_fill_order_invalidated_by_set_cell_letter(self, mock_persistence, test_puzzle):
        """rank_slots is called twice when set_cell_letter is called between get_fill_order calls"""
        from unittest.mock import patch
        puzzle_uc = PuzzleUseCases(mock_persistence, word_uc=self._StubWordUseCases())
        mock_persistence.load_puzzle.return_value = test_puzzle

        with patch("crossword.use_cases.puzzle_use_cases.FillPriorityAnalyzer") as MockAnalyzer:
            mock_instance = MockAnalyzer.return_value
            mock_instance.rank_slots.return_value = []
            puzzle_uc.get_fill_order(1, "my_puzzle")
            puzzle_uc.set_cell_letter(1, "my_puzzle", 1, 2, "A")
            puzzle_uc.get_fill_order(1, "my_puzzle")

        assert mock_instance.rank_slots.call_count == 2

    def test_get_fill_order_not_invalidated_by_clue_only_set_word_clue(self, mock_persistence, test_puzzle):
        """rank_slots is called once when set_word_clue is called with no text"""
        from unittest.mock import patch
        puzzle_uc = PuzzleUseCases(mock_persistence, word_uc=self._StubWordUseCases())
        mock_persistence.load_puzzle.return_value = test_puzzle

        with patch("crossword.use_cases.puzzle_use_cases.FillPriorityAnalyzer") as MockAnalyzer:
            mock_instance = MockAnalyzer.return_value
            mock_instance.rank_slots.return_value = []
            puzzle_uc.get_fill_order(1, "my_puzzle")
            # clue-only update — no text argument
            seq = next(iter(test_puzzle.across_words)) if test_puzzle.across_words else None
            if seq is not None:
                puzzle_uc.set_word_clue(1, "my_puzzle", seq, "across", "A clue")
            puzzle_uc.get_fill_order(1, "my_puzzle")

        mock_instance.rank_slots.assert_called_once()


class TestPuzzleUseCasesAutoState:
    """copy_puzzle auto-advances state along the completion ladder."""

    def test_copy_empty_puzzle_sets_draft(self, puzzle_uc, mock_persistence):
        mock_persistence.load_puzzle.return_value = TestPuzzle.create_atlantic_puzzle()
        puzzle_uc.copy_puzzle(1, "src", "dest")
        mock_persistence.set_puzzle_state.assert_called_once_with(1, "dest", ps.DRAFT)

    def test_copy_filled_no_clues_sets_filled(self, puzzle_uc, mock_persistence):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        for word in list(puzzle.across_words.values()) + list(puzzle.down_words.values()):
            word.set_clue(None)
        mock_persistence.load_puzzle.return_value = puzzle
        puzzle_uc.copy_puzzle(1, "src", "dest")
        mock_persistence.set_puzzle_state.assert_called_once_with(1, "dest", ps.FILLED)

    def test_copy_solved_puzzle_sets_finished(self, puzzle_uc, mock_persistence):
        mock_persistence.load_puzzle.return_value = TestPuzzle.create_solved_atlantic_puzzle()
        puzzle_uc.copy_puzzle(1, "src", "dest")
        mock_persistence.set_puzzle_state.assert_called_once_with(1, "dest", ps.FINISHED)

    def test_copy_allows_backward_move(self, puzzle_uc, mock_persistence):
        """A previously finished puzzle whose clues were cleared moves back to filled."""
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        for word in list(puzzle.across_words.values()) + list(puzzle.down_words.values()):
            word.set_clue(None)
        mock_persistence.load_puzzle.return_value = puzzle
        mock_persistence.get_puzzle_state.return_value = {"state": ps.FINISHED}
        puzzle_uc.copy_puzzle(1, "src", "dest")
        mock_persistence.set_puzzle_state.assert_called_once_with(1, "dest", ps.FILLED)

    def test_copy_recomputes_state_regardless_of_source(self, puzzle_uc, mock_persistence):
        mock_persistence.load_puzzle.return_value = TestPuzzle.create_solved_atlantic_puzzle()
        mock_persistence.get_puzzle_state.return_value = {"state": ps.SUBMITTED}
        puzzle_uc.copy_puzzle(1, "src", "dest")
        mock_persistence.set_puzzle_state.assert_called_once_with(1, "dest", ps.FINISHED)


class TestPuzzleUseCasesOpen:
    """open_puzzle_for_editing creates a working copy for any state."""

    @pytest.mark.parametrize("state", [ps.SUBMITTED, ps.PUBLISHED, ps.ARCHIVED])
    def test_open_any_state_succeeds(self, puzzle_uc, mock_persistence, state):
        mock_persistence.get_puzzle_state.return_value = {"state": state}
        mock_persistence.load_puzzle.return_value = TestPuzzle.create_atlantic_puzzle()
        working_name = puzzle_uc.open_puzzle_for_editing(1, "p")
        assert working_name.startswith("__wc__p__")

    @pytest.mark.parametrize("state", [ps.DRAFT, ps.FILLED, ps.FINISHED])
    def test_open_editable_state_succeeds(self, puzzle_uc, mock_persistence, state):
        mock_persistence.get_puzzle_state.return_value = {"state": state}
        mock_persistence.load_puzzle.return_value = TestPuzzle.create_atlantic_puzzle()
        working_name = puzzle_uc.open_puzzle_for_editing(1, "p")
        assert working_name.startswith("__wc__p__")

    def test_open_unknown_state_succeeds(self, puzzle_uc, mock_persistence):
        mock_persistence.get_puzzle_state.return_value = None
        mock_persistence.load_puzzle.return_value = TestPuzzle.create_atlantic_puzzle()
        working_name = puzzle_uc.open_puzzle_for_editing(1, "p")
        assert working_name.startswith("__wc__p__")


class TestPuzzleUseCasesRename:
    """rename_puzzle delegates to a true in-place rename."""

    def test_rename_calls_persistence_rename(self, puzzle_uc, mock_persistence):
        puzzle_uc.rename_puzzle(1, "old", "new")
        mock_persistence.rename_puzzle.assert_called_once_with(1, "old", "new")
        mock_persistence.copy_puzzle.assert_not_called()
        mock_persistence.delete_puzzle.assert_not_called()

    def test_rename_rejects_empty_name(self, puzzle_uc, mock_persistence):
        with pytest.raises(ValueError):
            puzzle_uc.rename_puzzle(1, "old", "   ")
        mock_persistence.rename_puzzle.assert_not_called()


class TestPuzzleUseCasesSetState:
    """set_puzzle_state validates targets and required fields."""

    def test_invalid_state_raises(self, puzzle_uc):
        with pytest.raises(ValueError, match="Invalid state"):
            puzzle_uc.set_puzzle_state(1, "p", "bogus")

    def test_submitted_requires_publisher(self, puzzle_uc):
        with pytest.raises(ValueError, match="publisher is required"):
            puzzle_uc.set_puzzle_state(1, "p", ps.SUBMITTED, date_submitted="2026-06-06")

    def test_submitted_requires_date(self, puzzle_uc):
        with pytest.raises(ValueError, match="date_submitted is required"):
            puzzle_uc.set_puzzle_state(1, "p", ps.SUBMITTED, publisher="NYT")

    def test_published_requires_date(self, puzzle_uc):
        with pytest.raises(ValueError, match="date_published is required"):
            puzzle_uc.set_puzzle_state(1, "p", ps.PUBLISHED)

    def test_submitted_success(self, puzzle_uc, mock_persistence):
        mock_persistence.get_puzzle_state.return_value = {
            "state": ps.SUBMITTED, "publisher": "NYT",
            "date_submitted": "2026-06-06", "date_published": None,
        }
        result = puzzle_uc.set_puzzle_state(
            1, "p", ps.SUBMITTED, publisher="NYT", date_submitted="2026-06-06")
        mock_persistence.set_puzzle_state.assert_called_once_with(
            1, "p", ps.SUBMITTED, publisher="NYT",
            date_submitted="2026-06-06", date_published=None)
        assert result["state"] == ps.SUBMITTED

    def test_reopen_to_draft_clears_fields(self, puzzle_uc, mock_persistence):
        mock_persistence.get_puzzle_state.return_value = {
            "state": ps.DRAFT, "publisher": None,
            "date_submitted": None, "date_published": None,
        }
        result = puzzle_uc.set_puzzle_state(1, "p", ps.DRAFT)
        mock_persistence.set_puzzle_state.assert_called_once_with(
            1, "p", ps.DRAFT, publisher=None,
            date_submitted=None, date_published=None)
        assert result["state"] == ps.DRAFT
