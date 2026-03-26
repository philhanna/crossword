"""
Unit tests for GridUseCases
"""

import pytest
from unittest.mock import Mock, MagicMock, call
from crossword import Grid, Puzzle
from crossword.use_cases.grid_use_cases import GridUseCases
from crossword.ports.persistence_port import PersistenceError


@pytest.fixture
def mock_persistence():
    """Create a mock persistence adapter"""
    persistence = Mock()
    persistence.list_grids.return_value = []
    persistence.list_puzzles.return_value = []
    return persistence


@pytest.fixture
def grid_uc(mock_persistence):
    """Create a GridUseCases instance with mock persistence"""
    return GridUseCases(mock_persistence)


class TestGridUseCasesCreate:
    """Tests for create_grid"""

    def test_create_grid_valid_size(self, grid_uc, mock_persistence):
        """Create a grid with valid size"""
        grid_uc.create_grid(1, "test_grid", 15)
        mock_persistence.save_grid.assert_called_once()
        args = mock_persistence.save_grid.call_args[0]
        assert args[0] == 1  # user_id
        assert args[1] == "test_grid"  # name
        assert isinstance(args[2], Grid)
        assert args[2].n == 15

    def test_create_grid_invalid_size_zero(self, grid_uc):
        """Create a grid with invalid size (0)"""
        with pytest.raises(ValueError, match="Grid size must be at least 1"):
            grid_uc.create_grid(1, "test", 0)

    def test_create_grid_invalid_size_negative(self, grid_uc):
        """Create a grid with invalid size (negative)"""
        with pytest.raises(ValueError, match="Grid size must be at least 1"):
            grid_uc.create_grid(1, "test", -5)

    def test_create_grid_persistence_error(self, grid_uc, mock_persistence):
        """Handle persistence error during save"""
        mock_persistence.save_grid.side_effect = PersistenceError("Disk full")
        with pytest.raises(PersistenceError, match="Disk full"):
            grid_uc.create_grid(1, "test", 15)

    def test_create_grid_rejects_working_copy_prefix(self, grid_uc, mock_persistence):
        """Reject names reserved for internal working copies"""
        with pytest.raises(ValueError, match="reserved for internal working copies"):
            grid_uc.create_grid(1, "__wc__hidden", 15)

        mock_persistence.save_grid.assert_not_called()

    def test_create_grid_rejects_existing_name(self, grid_uc, mock_persistence):
        """Reject creating a new grid over an existing saved grid"""
        mock_persistence.list_grids.return_value = ["existing"]

        with pytest.raises(ValueError, match="grid 'existing' already exists"):
            grid_uc.create_grid(1, "existing", 15)

        mock_persistence.save_grid.assert_not_called()


class TestGridUseCasesLoad:
    """Tests for load_grid"""

    def test_load_grid_success(self, grid_uc, mock_persistence):
        """Load grid successfully"""
        test_grid = Grid(15)
        mock_persistence.load_grid.return_value = test_grid

        result = grid_uc.load_grid(1, "test_grid")

        assert result == test_grid
        mock_persistence.load_grid.assert_called_once_with(1, "test_grid")

    def test_load_grid_not_found(self, grid_uc, mock_persistence):
        """Load grid that doesn't exist"""
        mock_persistence.load_grid.side_effect = PersistenceError("Grid not found")
        with pytest.raises(PersistenceError, match="Grid not found"):
            grid_uc.load_grid(1, "nonexistent")


class TestGridUseCasesDelete:
    """Tests for delete_grid"""

    def test_delete_grid_success(self, grid_uc, mock_persistence):
        """Delete grid successfully"""
        grid_uc.delete_grid(1, "test_grid")
        mock_persistence.delete_grid.assert_called_once_with(1, "test_grid")

    def test_delete_grid_not_found(self, grid_uc, mock_persistence):
        """Delete grid that doesn't exist"""
        mock_persistence.delete_grid.side_effect = PersistenceError("Grid not found")
        with pytest.raises(PersistenceError, match="Grid not found"):
            grid_uc.delete_grid(1, "nonexistent")


class TestGridUseCasesList:
    """Tests for list_grids"""

    def test_list_grids_success(self, grid_uc, mock_persistence):
        """List grids successfully"""
        mock_persistence.list_grids.return_value = ["grid1", "grid2", "grid3"]

        result = grid_uc.list_grids(1)

        assert result == ["grid1", "grid2", "grid3"]
        mock_persistence.list_grids.assert_called_once_with(1)

    def test_list_grids_empty(self, grid_uc, mock_persistence):
        """List grids when none exist"""
        mock_persistence.list_grids.return_value = []

        result = grid_uc.list_grids(1)

        assert result == []


class TestGridUseCasesCopy:
    """Tests for copy_grid"""

    def test_copy_grid_success(self, grid_uc, mock_persistence):
        """Copy a grid to a new name"""
        source = Grid(15)
        source.add_black_cell(3, 3, undo=False)
        mock_persistence.load_grid.return_value = source

        result = grid_uc.copy_grid(1, "original", "copy")

        mock_persistence.load_grid.assert_called_once_with(1, "original")
        mock_persistence.save_grid.assert_called_once_with(1, "copy", source)
        assert result is source

    def test_copy_grid_source_not_found(self, grid_uc, mock_persistence):
        """Copy a grid that does not exist"""
        mock_persistence.load_grid.side_effect = PersistenceError("Grid not found")

        with pytest.raises(PersistenceError, match="Grid not found"):
            grid_uc.copy_grid(1, "nonexistent", "copy")

    def test_copy_grid_empty_new_name(self, grid_uc):
        """Reject an empty new_name"""
        with pytest.raises(ValueError, match="new_name must not be empty"):
            grid_uc.copy_grid(1, "original", "")

    def test_copy_grid_whitespace_new_name(self, grid_uc):
        """Reject a whitespace-only new_name"""
        with pytest.raises(ValueError, match="new_name must not be empty"):
            grid_uc.copy_grid(1, "original", "   ")

    def test_copy_grid_rejects_working_copy_prefix(self, grid_uc, mock_persistence):
        """Reject copy targets reserved for working copies"""
        with pytest.raises(ValueError, match="reserved for internal working copies"):
            grid_uc.copy_grid(1, "original", "__wc__copy")

        mock_persistence.load_grid.assert_not_called()
        mock_persistence.save_grid.assert_not_called()

    def test_copy_grid_preserves_black_cells(self, grid_uc, mock_persistence):
        """Copied grid retains the source's black cells"""
        source = Grid(15)
        source.add_black_cell(5, 5, undo=False)
        mock_persistence.load_grid.return_value = source

        result = grid_uc.copy_grid(1, "original", "copy")

        assert (5, 5) in result.black_cells


class TestGridUseCasesOpenForEditing:
    """Tests for open_grid_for_editing"""

    def test_open_grid_returns_working_name(self, grid_uc, mock_persistence):
        """Returns a working copy name with the __wc__ prefix"""
        mock_persistence.load_grid.return_value = Grid(15)

        working_name = grid_uc.open_grid_for_editing(1, "mygrid")

        assert working_name.startswith("__wc__")
        assert len(working_name) == len("__wc__") + 8

    def test_open_grid_creates_working_copy(self, grid_uc, mock_persistence):
        """Saves a working copy under the returned name"""
        source = Grid(15)
        source.add_black_cell(3, 3, undo=False)
        mock_persistence.load_grid.return_value = source

        working_name = grid_uc.open_grid_for_editing(1, "mygrid")

        mock_persistence.load_grid.assert_called_once_with(1, "mygrid")
        mock_persistence.save_grid.assert_called_once_with(1, working_name, source)

    def test_open_grid_unique_names(self, grid_uc, mock_persistence):
        """Each call returns a different working name"""
        mock_persistence.load_grid.return_value = Grid(15)

        name1 = grid_uc.open_grid_for_editing(1, "mygrid")
        name2 = grid_uc.open_grid_for_editing(1, "mygrid")

        assert name1 != name2

    def test_open_grid_not_found(self, grid_uc, mock_persistence):
        """Raises PersistenceError if grid does not exist"""
        mock_persistence.load_grid.side_effect = PersistenceError("Grid not found")

        with pytest.raises(PersistenceError, match="Grid not found"):
            grid_uc.open_grid_for_editing(1, "nonexistent")


class TestGridUseCasesCreateFromPuzzle:
    """Tests for create_grid_from_puzzle"""

    def test_create_grid_from_puzzle_rejects_working_copy_prefix(self, grid_uc, mock_persistence):
        """Reject target names reserved for working copies"""
        with pytest.raises(ValueError, match="reserved for internal working copies"):
            grid_uc.create_grid_from_puzzle(1, "source-puzzle", "__wc__grid")

        mock_persistence.load_puzzle.assert_not_called()
        mock_persistence.save_grid.assert_not_called()

    def test_create_grid_from_puzzle_rejects_existing_name(self, grid_uc, mock_persistence):
        """Reject creating a new grid from a puzzle over an existing saved grid"""
        mock_persistence.list_grids.return_value = ["newgrid"]

        with pytest.raises(ValueError, match="grid 'newgrid' already exists"):
            grid_uc.create_grid_from_puzzle(1, "source-puzzle", "newgrid")

        mock_persistence.load_puzzle.assert_not_called()
        mock_persistence.save_grid.assert_not_called()


class TestGridUseCasesToggleBlackCell:
    """Tests for toggle_black_cell"""

    def test_toggle_black_cell_add(self, grid_uc, mock_persistence):
        """Toggle cell from white to black"""
        test_grid = Grid(15)
        mock_persistence.load_grid.return_value = test_grid

        result = grid_uc.toggle_black_cell(1, "test_grid", 5, 5)

        assert (5, 5) in result.black_cells
        mock_persistence.load_grid.assert_called_once_with(1, "test_grid")
        mock_persistence.save_grid.assert_called_once()

    def test_toggle_black_cell_remove(self, grid_uc, mock_persistence):
        """Toggle cell from black to white"""
        test_grid = Grid(15)
        test_grid.add_black_cell(5, 5, undo=False)
        mock_persistence.load_grid.return_value = test_grid

        result = grid_uc.toggle_black_cell(1, "test_grid", 5, 5)

        # After removing (5,5), it should be white again
        # Note: symmetric point was also added, so check both are removed
        assert (5, 5) not in result.black_cells
        mock_persistence.save_grid.assert_called_once()

    def test_toggle_black_cell_applies_symmetry(self, grid_uc, mock_persistence):
        """Toggle applies 180-degree symmetry"""
        test_grid = Grid(15)
        mock_persistence.load_grid.return_value = test_grid

        result = grid_uc.toggle_black_cell(1, "test_grid", 5, 5)

        # Both (5,5) and its symmetric point should be black
        symmetric = test_grid.symmetric_point(5, 5)
        assert (5, 5) in result.black_cells
        assert symmetric in result.black_cells


class TestGridUseCasesRotate:
    """Tests for rotate_grid"""

    def test_rotate_grid_success(self, grid_uc, mock_persistence):
        """Rotate grid successfully"""
        test_grid = Grid(15)
        test_grid.add_black_cell(1, 1, undo=False)
        mock_persistence.load_grid.return_value = test_grid

        result = grid_uc.rotate_grid(1, "test_grid")

        # Grid should be rotated
        assert result.n == 15
        mock_persistence.save_grid.assert_called_once()


class TestGridUseCasesUndo:
    """Tests for undo_grid"""

    def test_undo_grid_with_operations(self, grid_uc, mock_persistence):
        """Undo when there are operations in undo stack"""
        test_grid = Grid(15)
        test_grid.add_black_cell(5, 5, undo=True)
        # Now undo_stack has (5, 5)
        mock_persistence.load_grid.return_value = test_grid

        assert len(test_grid.undo_stack) > 0, "Test setup: should have undo operations"
        result = grid_uc.undo_grid(1, "test_grid")

        # Should call save_grid
        mock_persistence.save_grid.assert_called_once()

    def test_undo_grid_empty_stack(self, grid_uc, mock_persistence):
        """Undo when undo stack is empty"""
        test_grid = Grid(15)
        mock_persistence.load_grid.return_value = test_grid

        # Should not raise, just do nothing
        result = grid_uc.undo_grid(1, "test_grid")

        assert result == test_grid
        mock_persistence.save_grid.assert_called_once()


class TestGridUseCasesCreateFromPuzzle:
    """Tests for create_grid_from_puzzle"""

    def _make_puzzle_with_black_cells(self, n, black_cells):
        """Helper: create a puzzle whose grid has the given black cells"""
        grid = Grid(n)
        for r, c in black_cells:
            grid.add_black_cell(r, c, undo=False)
        return Puzzle(grid)

    def test_creates_grid_with_correct_black_cells(self, grid_uc, mock_persistence):
        """New grid inherits the puzzle's black cell layout"""
        puzzle = self._make_puzzle_with_black_cells(15, [(3, 3), (5, 7)])
        mock_persistence.load_puzzle.return_value = puzzle

        result = grid_uc.create_grid_from_puzzle(1, "mypuzzle", "newgrid")

        assert (3, 3) in result.black_cells
        assert (5, 7) in result.black_cells

    def test_saves_grid_under_given_name(self, grid_uc, mock_persistence):
        """Grid is saved using the provided grid_name"""
        puzzle = self._make_puzzle_with_black_cells(15, [])
        mock_persistence.load_puzzle.return_value = puzzle

        grid_uc.create_grid_from_puzzle(1, "mypuzzle", "newgrid")

        mock_persistence.save_grid.assert_called_once()
        args = mock_persistence.save_grid.call_args[0]
        assert args[0] == 1
        assert args[1] == "newgrid"
        assert isinstance(args[2], Grid)

    def test_clears_undo_stack(self, grid_uc, mock_persistence):
        """Undo stack is empty on the new grid regardless of puzzle's grid history"""
        grid = Grid(15)
        grid.add_black_cell(3, 3, undo=True)  # populates undo_stack
        assert len(grid.undo_stack) > 0
        mock_persistence.load_puzzle.return_value = Puzzle(grid)

        result = grid_uc.create_grid_from_puzzle(1, "mypuzzle", "newgrid")

        assert result.undo_stack == []

    def test_clears_redo_stack(self, grid_uc, mock_persistence):
        """Redo stack is empty on the new grid"""
        grid = Grid(15)
        grid.add_black_cell(3, 3, undo=True)
        grid.undo()  # populates redo_stack
        assert len(grid.redo_stack) > 0
        mock_persistence.load_puzzle.return_value = Puzzle(grid)

        result = grid_uc.create_grid_from_puzzle(1, "mypuzzle", "newgrid")

        assert result.redo_stack == []

    def test_puzzle_not_found(self, grid_uc, mock_persistence):
        """Raises PersistenceError if puzzle does not exist"""
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            grid_uc.create_grid_from_puzzle(1, "nonexistent", "newgrid")

    def test_empty_grid_name_raises(self, grid_uc):
        """Raises ValueError if grid_name is empty"""
        with pytest.raises(ValueError, match="grid_name must not be empty"):
            grid_uc.create_grid_from_puzzle(1, "mypuzzle", "")

    def test_whitespace_grid_name_raises(self, grid_uc):
        """Raises ValueError if grid_name is whitespace only"""
        with pytest.raises(ValueError, match="grid_name must not be empty"):
            grid_uc.create_grid_from_puzzle(1, "mypuzzle", "   ")

    def test_preserves_grid_size(self, grid_uc, mock_persistence):
        """New grid has the same size as the puzzle's grid"""
        puzzle = self._make_puzzle_with_black_cells(21, [])
        mock_persistence.load_puzzle.return_value = puzzle

        result = grid_uc.create_grid_from_puzzle(1, "mypuzzle", "newgrid")

        assert result.n == 21


class TestGridUseCasesRedo:
    """Tests for redo_grid"""

    def test_redo_grid_with_operations(self, grid_uc, mock_persistence):
        """Redo when there are operations in redo stack"""
        test_grid = Grid(15)
        test_grid.add_black_cell(5, 5, undo=True)
        test_grid.undo()
        # Now redo_stack has (5, 5)
        mock_persistence.load_grid.return_value = test_grid

        initial_stack_len = len(test_grid.redo_stack)
        result = grid_uc.redo_grid(1, "test_grid")

        # After redo, stack should be shorter
        assert len(result.redo_stack) == initial_stack_len - 1
        mock_persistence.save_grid.assert_called_once()

    def test_redo_grid_empty_stack(self, grid_uc, mock_persistence):
        """Redo when redo stack is empty"""
        test_grid = Grid(15)
        mock_persistence.load_grid.return_value = test_grid

        # Should not raise, just do nothing
        result = grid_uc.redo_grid(1, "test_grid")

        assert result == test_grid
        mock_persistence.save_grid.assert_called_once()


class TestGridUseCasesGetPreview:
    """Tests for get_grid_preview"""

    def test_get_grid_preview_returns_dict(self, grid_uc, mock_persistence):
        """get_grid_preview returns a dict with required keys"""
        test_grid = Grid(15)
        mock_persistence.load_grid.return_value = test_grid

        result = grid_uc.get_grid_preview(1, "my_grid")

        assert isinstance(result, dict)
        assert result["name"] == "my_grid"
        assert "heading" in result
        assert "width" in result
        assert "svgstr" in result

    def test_get_grid_preview_svgstr_is_xml(self, grid_uc, mock_persistence):
        """svgstr should be an SVG XML string"""
        test_grid = Grid(15)
        mock_persistence.load_grid.return_value = test_grid

        result = grid_uc.get_grid_preview(1, "my_grid")

        assert "<svg" in result["svgstr"]

    def test_get_grid_preview_heading_contains_name(self, grid_uc, mock_persistence):
        """heading should contain the grid name"""
        test_grid = Grid(15)
        mock_persistence.load_grid.return_value = test_grid

        result = grid_uc.get_grid_preview(1, "my_grid")

        assert "my_grid" in result["heading"]

    def test_get_grid_preview_width_is_positive(self, grid_uc, mock_persistence):
        """width should be a positive number"""
        test_grid = Grid(15)
        mock_persistence.load_grid.return_value = test_grid

        result = grid_uc.get_grid_preview(1, "my_grid")

        assert result["width"] > 0

    def test_get_grid_preview_not_found(self, grid_uc, mock_persistence):
        """get_grid_preview raises PersistenceError if grid not found"""
        mock_persistence.load_grid.side_effect = PersistenceError("not found")

        with pytest.raises(PersistenceError):
            grid_uc.get_grid_preview(1, "missing_grid")
