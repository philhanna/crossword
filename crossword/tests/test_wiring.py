"""
Unit tests for dependency wiring - verify make_app() assembles and injected correctly.
"""

import pytest
import tempfile
import os
from crossword.wiring import make_app, AppContainer
from crossword.ports.persistence_port import PersistenceError


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database with schema."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Initialize schema
    from crossword.adapters.sqlite_persistence_adapter import SQLitePersistenceAdapter
    adapter = SQLitePersistenceAdapter(path)
    adapter.init_schema()

    yield path

    # Cleanup
    try:
        os.remove(path)
    except:
        pass


class TestMakeApp:
    """Tests for make_app() wiring function"""

    def test_make_app_creates_container(self, temp_db):
        """make_app() returns AppContainer with all use cases"""
        config = {"dbfile": temp_db}
        app = make_app(config)

        assert isinstance(app, AppContainer)
        assert app.grid_uc is not None
        assert app.puzzle_uc is not None
        assert app.word_uc is not None

    def test_make_app_initializes_grid_use_case(self, temp_db):
        """Grid use case is wired correctly"""
        config = {"dbfile": temp_db}
        app = make_app(config)

        # Grid use case should have a persistence port
        assert app.grid_uc.persistence is not None

    def test_make_app_initializes_puzzle_use_case(self, temp_db):
        """Puzzle use case is wired correctly"""
        config = {"dbfile": temp_db}
        app = make_app(config)

        # Puzzle use case should have a persistence port
        assert app.puzzle_uc.persistence is not None

    def test_make_app_initializes_word_use_case(self, temp_db):
        """Word use case is wired correctly"""
        config = {"dbfile": temp_db}
        app = make_app(config)

        # Word use case should have a word list port
        assert app.word_uc.word_list is not None

    def test_make_app_missing_dbfile(self):
        """make_app() raises error if dbfile not in config"""
        config = {}
        with pytest.raises(ValueError, match="dbfile.*required"):
            make_app(config)

    def test_make_app_invalid_dbfile(self):
        """make_app() raises error if database connection fails"""
        config = {"dbfile": "/nonexistent/path/to/database.db"}
        with pytest.raises(Exception):  # PersistenceError
            make_app(config)


class TestEndToEndWiring:
    """End-to-end tests with wired app"""

    def test_grid_crud_end_to_end(self, temp_db):
        """Can create, load, delete grids via wired app"""
        config = {"dbfile": temp_db}
        app = make_app(config)

        # Create grid
        app.grid_uc.create_grid(1, "test_grid", 15)

        # Load grid
        grid = app.grid_uc.load_grid(1, "test_grid")
        assert grid.n == 15

        # List grids
        grids = app.grid_uc.list_grids(1)
        assert "test_grid" in grids

        # Delete grid
        app.grid_uc.delete_grid(1, "test_grid")
        grids = app.grid_uc.list_grids(1)
        assert "test_grid" not in grids

    def test_puzzle_crud_end_to_end(self, temp_db):
        """Can create, load, delete puzzles via wired app"""
        config = {"dbfile": temp_db}
        app = make_app(config)

        # Create grid first
        app.grid_uc.create_grid(1, "grid1", 15)

        # Create puzzle from grid
        app.puzzle_uc.create_puzzle(1, "puzzle1", "grid1")

        # Load puzzle
        puzzle = app.puzzle_uc.load_puzzle(1, "puzzle1")
        assert puzzle.n == 15

        # List puzzles
        puzzles = app.puzzle_uc.list_puzzles(1)
        assert "puzzle1" in puzzles

        # Delete puzzle
        app.puzzle_uc.delete_puzzle(1, "puzzle1")
        puzzles = app.puzzle_uc.list_puzzles(1)
        assert "puzzle1" not in puzzles

    def test_grid_toggle_cell_end_to_end(self, temp_db):
        """Can toggle black cells via wired app"""
        config = {"dbfile": temp_db}
        app = make_app(config)

        # Create grid
        app.grid_uc.create_grid(1, "grid1", 15)

        # Toggle a cell
        grid = app.grid_uc.toggle_black_cell(1, "grid1", 5, 5)
        assert (5, 5) in grid.black_cells

        # Load again to verify persistence
        grid = app.grid_uc.load_grid(1, "grid1")
        assert (5, 5) in grid.black_cells

    def test_puzzle_set_cell_letter_end_to_end(self, temp_db):
        """Can set cell letters in puzzle via wired app"""
        config = {"dbfile": temp_db}
        app = make_app(config)

        # Create grid and puzzle
        app.grid_uc.create_grid(1, "grid1", 15)
        app.puzzle_uc.create_puzzle(1, "puzzle1", "grid1")

        # Set cell letter
        puzzle = app.puzzle_uc.set_cell_letter(1, "puzzle1", 2, 2, "A")
        assert puzzle.get_cell(2, 2) == "A"

        # Load again to verify persistence
        puzzle = app.puzzle_uc.load_puzzle(1, "puzzle1")
        assert puzzle.get_cell(2, 2) == "A"

    def test_word_validation_end_to_end(self, temp_db):
        """Can validate words via wired app"""
        config = {"dbfile": temp_db}
        app = make_app(config)

        # Validation works (with empty dictionary)
        result = app.word_uc.validate_word("HELLO")
        # Result depends on whether words are in DB, but should not raise
        assert isinstance(result, bool)

        # Get all words (should be empty or have words from DB)
        words = app.word_uc.get_all_words()
        assert isinstance(words, list)
