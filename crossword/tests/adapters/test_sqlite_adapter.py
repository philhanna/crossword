"""
Tests for SQLitePersistenceAdapter - Persistence adapter tests
"""

import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
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
    # Error paths
    # ======================================================================

    def test_init_connect_failure_raises_persistence_error(self):
        with patch('sqlite3.connect', side_effect=sqlite3.Error("no connection")):
            with pytest.raises(PersistenceError, match="Failed to connect"):
                SQLitePersistenceAdapter(":memory:")

    def test_ensure_schema_sqlite_error_raises_persistence_error(self, adapter):
        adapter.conn = MagicMock()
        adapter.conn.cursor.return_value.execute.side_effect = sqlite3.Error("schema error")
        with pytest.raises(PersistenceError, match="Failed to ensure schema"):
            adapter._ensure_schema_compatibility()

    def test_init_schema_reraises_persistence_error(self, adapter):
        with patch.object(adapter, '_ensure_schema_compatibility',
                          side_effect=PersistenceError("inner")):
            with pytest.raises(PersistenceError, match="inner"):
                adapter.init_schema()

    def test_init_schema_wraps_sqlite_error(self, adapter):
        with patch.object(adapter, '_ensure_schema_compatibility',
                          side_effect=sqlite3.Error("raw")):
            with pytest.raises(PersistenceError, match="Failed to initialize schema"):
                adapter.init_schema()

    def test_save_puzzle_sqlite_error_raises_persistence_error(self, adapter, sample_puzzle):
        adapter.conn = MagicMock()
        adapter.conn.cursor.return_value.execute.side_effect = sqlite3.Error("write error")
        with pytest.raises(PersistenceError, match="Failed to save puzzle"):
            adapter.save_puzzle(1, "test", sample_puzzle)

    def test_load_puzzle_not_found_raises_persistence_error(self, adapter):
        with pytest.raises(PersistenceError, match="not found"):
            adapter.load_puzzle(1, "nonexistent")

    def test_load_puzzle_sqlite_error_raises_persistence_error(self, adapter):
        adapter.conn = MagicMock()
        adapter.conn.cursor.return_value.execute.side_effect = sqlite3.Error("read error")
        with pytest.raises(PersistenceError, match="Failed to load puzzle"):
            adapter.load_puzzle(1, "test")

    def test_load_puzzle_deserialization_error_raises_persistence_error(self, adapter, sample_puzzle):
        adapter.save_puzzle(1, "test", sample_puzzle)
        with patch('crossword.Puzzle.from_json', side_effect=ValueError("bad json")):
            with pytest.raises(PersistenceError, match="Failed to deserialize"):
                adapter.load_puzzle(1, "test")

    def test_delete_puzzle_not_found_raises_persistence_error(self, adapter):
        with pytest.raises(PersistenceError, match="not found"):
            adapter.delete_puzzle(1, "nonexistent")

    def test_delete_puzzle_sqlite_error_raises_persistence_error(self, adapter):
        adapter.conn = MagicMock()
        adapter.conn.cursor.return_value.execute.side_effect = sqlite3.Error("delete error")
        with pytest.raises(PersistenceError, match="Failed to delete puzzle"):
            adapter.delete_puzzle(1, "test")

    def test_list_puzzles_sqlite_error_raises_persistence_error(self, adapter):
        adapter.conn = MagicMock()
        adapter.conn.cursor.return_value.execute.side_effect = sqlite3.Error("list error")
        with pytest.raises(PersistenceError, match="Failed to list puzzles"):
            adapter.list_puzzles(1)

    # ======================================================================
    # Integration with Production Database
    # ======================================================================

    def test_load_puzzle_from_samples_db(self):
        """
        Integration test: Load a puzzle from the production sample.crossword.db.
        This validates the schema hasn't drifted.
        """
        db_path = Path(__file__).resolve().parents[3] / "examples" / "sample.crossword.db"
        if not db_path.exists():
            pytest.skip(f"sample.crossword.db not found at {db_path}")

        adapter = SQLitePersistenceAdapter(str(db_path))

        puzzles = adapter.list_puzzles(user_id=1)
        if not puzzles:
            pytest.skip("No puzzles found in sample.crossword.db")

        loaded = adapter.load_puzzle(user_id=1, name=puzzles[0])

        assert isinstance(loaded, Puzzle)
        assert loaded.n > 0
        assert loaded.last_mode in {"grid", "puzzle"}
