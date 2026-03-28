"""
Tests for SQLitePersistenceAdapter - Persistence adapter tests
"""

import pytest
from pathlib import Path
from crossword import Grid, Puzzle
from crossword.adapters.sqlite_persistence_adapter import SQLitePersistenceAdapter
from crossword.ports.persistence_port import PersistenceError


class TestSQLitePersistenceAdapter:
    """Test suite for SQLitePersistenceAdapter"""

    @pytest.fixture
    def adapter(self):
        """Create an in-memory SQLite adapter for testing"""
        adapter = SQLitePersistenceAdapter(":memory:")
        adapter.init_schema()
        return adapter

    @pytest.fixture
    def sample_grid(self):
        """Create a sample grid for testing"""
        grid = Grid(5)
        grid.add_black_cell(1, 1)
        grid.add_black_cell(2, 2)
        return grid

    @pytest.fixture
    def sample_puzzle(self, sample_grid):
        """Create a sample puzzle for testing"""
        puzzle = Puzzle(sample_grid)
        puzzle.title = "Test Puzzle"
        return puzzle

    # ======================================================================
    # Grid Tests
    # ======================================================================

    def test_save_and_load_grid(self, adapter, sample_grid):
        """Test saving and loading a grid"""
        adapter.save_grid(user_id=1, name="test_grid", grid=sample_grid)
        loaded = adapter.load_grid(user_id=1, name="test_grid")

        assert loaded.n == sample_grid.n
        assert loaded.black_cells == sample_grid.black_cells

    def test_save_grid_overwrites(self, adapter, sample_grid):
        """Test that saving a grid with same name overwrites it"""
        adapter.save_grid(user_id=1, name="test_grid", grid=sample_grid)

        # Modify and save again
        sample_grid.add_black_cell(3, 3)
        adapter.save_grid(user_id=1, name="test_grid", grid=sample_grid)

        loaded = adapter.load_grid(user_id=1, name="test_grid")
        assert (3, 3) in loaded.black_cells

    def test_load_nonexistent_grid(self, adapter):
        """Test that loading a nonexistent grid raises error"""
        with pytest.raises(PersistenceError):
            adapter.load_grid(user_id=1, name="nonexistent")

    def test_delete_grid(self, adapter, sample_grid):
        """Test deleting a grid"""
        adapter.save_grid(user_id=1, name="test_grid", grid=sample_grid)
        adapter.delete_grid(user_id=1, name="test_grid")

        with pytest.raises(PersistenceError):
            adapter.load_grid(user_id=1, name="test_grid")

    def test_delete_nonexistent_grid(self, adapter):
        """Test that deleting a nonexistent grid raises error"""
        with pytest.raises(PersistenceError):
            adapter.delete_grid(user_id=1, name="nonexistent")

    def test_list_grids(self, adapter, sample_grid):
        """Test listing grids for a user"""
        adapter.save_grid(user_id=1, name="grid1", grid=sample_grid)
        adapter.save_grid(user_id=1, name="grid2", grid=sample_grid)

        grids = adapter.list_grids(user_id=1)
        assert len(grids) == 2
        assert "grid1" in grids
        assert "grid2" in grids

    def test_list_grids_different_users(self, adapter, sample_grid):
        """Test that grids are isolated by user"""
        adapter.save_grid(user_id=1, name="grid1", grid=sample_grid)
        adapter.save_grid(user_id=2, name="grid2", grid=sample_grid)

        grids_user1 = adapter.list_grids(user_id=1)
        grids_user2 = adapter.list_grids(user_id=2)

        assert len(grids_user1) == 1
        assert "grid1" in grids_user1
        assert len(grids_user2) == 1
        assert "grid2" in grids_user2

    # ======================================================================
    # Puzzle Tests
    # ======================================================================

    def test_save_and_load_puzzle(self, adapter, sample_puzzle):
        """Test saving and loading a puzzle"""
        adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)
        loaded = adapter.load_puzzle(user_id=1, name="test_puzzle")

        assert loaded.grid.n == sample_puzzle.grid.n
        assert loaded.title == sample_puzzle.title
        assert len(loaded.across_words) == len(sample_puzzle.across_words)
        assert len(loaded.down_words) == len(sample_puzzle.down_words)
        assert loaded.last_mode == sample_puzzle.last_mode

    def test_save_puzzle_overwrites(self, adapter, sample_puzzle):
        """Test that saving a puzzle with same name overwrites it"""
        adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)

        # Modify and save again
        sample_puzzle.title = "Modified Puzzle"

        adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)

        loaded = adapter.load_puzzle(user_id=1, name="test_puzzle")
        assert loaded.title == "Modified Puzzle"

    def test_delete_puzzle(self, adapter, sample_puzzle):
        """Test deleting a puzzle"""
        adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)
        adapter.delete_puzzle(user_id=1, name="test_puzzle")

        with pytest.raises(PersistenceError):
            adapter.load_puzzle(user_id=1, name="test_puzzle")

    def test_list_puzzles(self, adapter, sample_puzzle):
        """Test listing puzzles for a user"""
        adapter.save_puzzle(user_id=1, name="puzzle1", puzzle=sample_puzzle)
        adapter.save_puzzle(user_id=1, name="puzzle2", puzzle=sample_puzzle)

        puzzles = adapter.list_puzzles(user_id=1)
        assert len(puzzles) == 2
        assert "puzzle1" in puzzles
        assert "puzzle2" in puzzles

    def test_init_schema_adds_last_mode_column(self, adapter):
        cur = adapter.conn.cursor()
        cur.execute("PRAGMA table_info(puzzles)")
        columns = {row["name"] for row in cur.fetchall()}
        assert "last_mode" in columns

    def test_save_puzzle_persists_last_mode_column(self, adapter, sample_puzzle):
        sample_puzzle.enter_puzzle_mode()
        adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)

        cur = adapter.conn.cursor()
        cur.execute(
            "SELECT last_mode FROM puzzles WHERE userid = ? AND puzzlename = ?",
            (1, "test_puzzle")
        )
        row = cur.fetchone()
        assert row["last_mode"] == "puzzle"

    def test_load_legacy_puzzle_row_migrates_missing_last_mode(self, tmp_path, sample_puzzle):
        db_path = tmp_path / "legacy.db"

        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE puzzles (
                id          INTEGER PRIMARY KEY,
                userid      INTEGER,
                puzzlename  TEXT,
                created     TEXT,
                modified    TEXT,
                jsonstr     TEXT
            )
        """)
        legacy_json = sample_puzzle.to_json()
        import json
        image = json.loads(legacy_json)
        image.pop("last_mode", None)
        image.pop("grid_undo_stack", None)
        image.pop("grid_redo_stack", None)
        legacy_json = json.dumps(image)
        conn.execute(
            """INSERT INTO puzzles (userid, puzzlename, created, modified, jsonstr)
               VALUES (?, ?, ?, ?, ?)""",
            (1, "legacy_puzzle", "2026-01-01T00:00:00", "2026-01-01T00:00:00", legacy_json)
        )
        conn.commit()
        conn.close()

        adapter = SQLitePersistenceAdapter(str(db_path))
        loaded = adapter.load_puzzle(user_id=1, name="legacy_puzzle")

        assert loaded.last_mode == "puzzle"

        cur = adapter.conn.cursor()
        cur.execute("PRAGMA table_info(puzzles)")
        columns = {row["name"] for row in cur.fetchall()}
        assert "last_mode" in columns

    # ======================================================================
    # Integration with Production Database
    # ======================================================================

    def test_load_grid_from_samples_db(self):
        """
        Integration test: Load a grid from the production samples.db
        This validates the schema hasn't drifted.
        """
        db_path = Path(__file__).resolve().parents[3] / "samples.db"
        if not db_path.exists():
            pytest.skip(f"samples.db not found at {db_path}")

        adapter = SQLitePersistenceAdapter(str(db_path))

        # Try to load a grid (there should be at least one)
        grids = adapter.list_grids(user_id=1)
        if not grids:
            pytest.skip("No grids found in samples.db")

        # Load the first grid
        loaded = adapter.load_grid(user_id=1, name=grids[0])

        # Validate it's a valid Grid object
        assert isinstance(loaded, Grid)
        assert loaded.n > 0
        assert isinstance(loaded.black_cells, set)
