"""
Unit tests for PuzzleUseCases
"""

import pytest
from unittest.mock import Mock
from crossword import Grid, Puzzle
from crossword.use_cases.puzzle_use_cases import PuzzleUseCases
from crossword.ports.persistence import PersistenceError


@pytest.fixture
def mock_persistence():
    """Create a mock persistence adapter"""
    return Mock()


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

    def test_create_puzzle_success(self, puzzle_uc, mock_persistence, test_grid):
        """Create puzzle successfully"""
        mock_persistence.load_grid.return_value = test_grid

        puzzle_uc.create_puzzle(1, "test_puzzle", "test_grid")

        mock_persistence.load_grid.assert_called_once_with(1, "test_grid")
        mock_persistence.save_puzzle.assert_called_once()
        args = mock_persistence.save_puzzle.call_args[0]
        assert args[0] == 1  # user_id
        assert args[1] == "test_puzzle"
        assert isinstance(args[2], Puzzle)

    def test_create_puzzle_grid_not_found(self, puzzle_uc, mock_persistence):
        """Create puzzle with nonexistent grid"""
        mock_persistence.load_grid.side_effect = PersistenceError("Grid not found")

        with pytest.raises(PersistenceError, match="Grid not found"):
            puzzle_uc.create_puzzle(1, "test_puzzle", "nonexistent_grid")


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
        mock_persistence.list_puzzles.assert_called_once_with(1)

    def test_list_puzzles_empty(self, puzzle_uc, mock_persistence):
        """List puzzles when none exist"""
        mock_persistence.list_puzzles.return_value = []

        result = puzzle_uc.list_puzzles(1)

        assert result == []


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
            result = puzzle_uc.set_word_clue(1, "test_puzzle", first_seq, "across", "Test clue")
            assert test_puzzle.across_words[first_seq].get_clue() == "Test clue"
            mock_persistence.save_puzzle.assert_called_once()

    def test_set_word_clue_down(self, puzzle_uc, mock_persistence, test_puzzle):
        """Set clue for down word"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        if test_puzzle.down_words:
            first_seq = list(test_puzzle.down_words.keys())[0]
            result = puzzle_uc.set_word_clue(1, "test_puzzle", first_seq, "down", "Test clue")
            assert test_puzzle.down_words[first_seq].get_clue() == "Test clue"
            mock_persistence.save_puzzle.assert_called_once()

    def test_set_word_clue_invalid_direction(self, puzzle_uc, mock_persistence, test_puzzle):
        """Set clue with invalid direction"""
        mock_persistence.load_puzzle.return_value = test_puzzle

        with pytest.raises(ValueError, match="Direction must be 'across' or 'down'"):
            puzzle_uc.set_word_clue(1, "test_puzzle", 1, "invalid", "Clue")


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


class TestPuzzleUseCasesReplacGrid:
    """Tests for replace_puzzle_grid"""

    def test_replace_puzzle_grid_success(self, puzzle_uc, mock_persistence, test_puzzle, test_grid):
        """Replace puzzle grid successfully"""
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_persistence.load_grid.return_value = test_grid

        result = puzzle_uc.replace_puzzle_grid(1, "test_puzzle", "new_grid")

        mock_persistence.load_puzzle.assert_called_once_with(1, "test_puzzle")
        mock_persistence.load_grid.assert_called_once_with(1, "new_grid")
        mock_persistence.save_puzzle.assert_called_once()

    def test_replace_puzzle_grid_incompatible_size(self, puzzle_uc, mock_persistence, test_puzzle):
        """Replace grid with incompatible size"""
        new_grid = Grid(10)  # Different size
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_persistence.load_grid.return_value = new_grid

        with pytest.raises(ValueError, match="Incompatible grid sizes"):
            puzzle_uc.replace_puzzle_grid(1, "test_puzzle", "new_grid")
