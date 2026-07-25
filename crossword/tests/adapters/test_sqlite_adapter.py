"""
Tests for SQLitePersistenceAdapter - Persistence adapter tests
"""

import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from crossword import Grid, Puzzle
from crossword.adapters.sqlite_persistence_adapter import SQLitePersistenceAdapter
from crossword.domain import puzzle_state as ps
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

    def test_list_puzzles_filters_by_state(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="drafty", puzzle=sample_puzzle)
        adapter.save_puzzle(user_id=1, name="submittedy", puzzle=sample_puzzle)
        adapter.set_puzzle_state(user_id=1, name="submittedy", state=ps.SUBMITTED,
                                 publisher="NYT", date_submitted="2026-06-06")

        puzzles = adapter.list_puzzles(user_id=1, state=ps.SUBMITTED)

        assert puzzles == ["submittedy"]

    def test_list_puzzles_filtered_results_stay_most_recent_first(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="older", puzzle=sample_puzzle)
        adapter.save_puzzle(user_id=1, name="newer", puzzle=sample_puzzle)
        adapter.set_puzzle_state(user_id=1, name="older", state=ps.DRAFT)
        adapter.set_puzzle_state(user_id=1, name="newer", state=ps.DRAFT)

        cur = adapter.conn.cursor()
        cur.execute("UPDATE puzzles SET modified = ? WHERE userid = ? AND puzzlename = ?",
                    ("2026-01-01T00:00:00", 1, "older"))
        cur.execute("UPDATE puzzles SET modified = ? WHERE userid = ? AND puzzlename = ?",
                    ("2026-06-06T00:00:00", 1, "newer"))
        adapter.conn.commit()

        puzzles = adapter.list_puzzles(user_id=1, state=ps.DRAFT)

        assert puzzles == ["newer", "older"]

    def test_list_puzzle_summaries_returns_columns(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="p1", puzzle=sample_puzzle)
        adapter.set_puzzle_state(user_id=1, name="p1", state=ps.SUBMITTED,
                                 publisher="NYT", date_submitted="2026-06-06")

        summaries = adapter.list_puzzle_summaries(user_id=1)

        assert len(summaries) == 1
        row = summaries[0]
        assert row["name"] == "p1"
        assert row["state"] == ps.SUBMITTED
        assert row["publisher"] == "NYT"
        assert row["date_submitted"] == "2026-06-06"
        assert row["date_published"] is None
        assert row["modified"]

    def test_list_puzzle_summaries_excludes_working_copies(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="real", puzzle=sample_puzzle)
        adapter.save_puzzle(user_id=1, name="__wc__real__abcd1234", puzzle=sample_puzzle)
        adapter.save_puzzle(user_id=1, name="__new__scratch", puzzle=sample_puzzle)

        names = [r["name"] for r in adapter.list_puzzle_summaries(user_id=1)]

        assert names == ["real"]

    def test_list_puzzle_summaries_ordered_most_recent_first(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="older", puzzle=sample_puzzle)
        adapter.save_puzzle(user_id=1, name="newer", puzzle=sample_puzzle)

        cur = adapter.conn.cursor()
        cur.execute("UPDATE puzzles SET modified = ? WHERE userid = ? AND puzzlename = ?",
                    ("2026-01-01T00:00:00", 1, "older"))
        cur.execute("UPDATE puzzles SET modified = ? WHERE userid = ? AND puzzlename = ?",
                    ("2026-06-06T00:00:00", 1, "newer"))
        adapter.conn.commit()

        names = [r["name"] for r in adapter.list_puzzle_summaries(user_id=1)]

        assert names == ["newer", "older"]

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

    # ======================================================================
    # Puzzle state columns
    # ======================================================================

    def test_schema_has_no_state_columns_on_puzzles(self, adapter):
        cur = adapter.conn.cursor()
        cur.execute("PRAGMA table_info(puzzles)")
        columns = {row["name"] for row in cur.fetchall()}
        assert not ({"state", "publisher", "date_submitted", "date_published"} & columns)

    def test_schema_has_puzzle_state_history_table_and_index(self, adapter):
        cur = adapter.conn.cursor()
        cur.execute("PRAGMA table_info(puzzle_state_history)")
        columns = {row["name"] for row in cur.fetchall()}
        assert {"id", "puzzle_id", "state", "publisher",
                "date_submitted", "date_published", "changed_at"} <= columns

        cur.execute("PRAGMA index_list(puzzle_state_history)")
        assert any(row["name"] == "idx_puzzle_state_history_puzzle" for row in cur.fetchall())

    def test_new_puzzle_has_no_state_until_set(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="p", puzzle=sample_puzzle)
        assert adapter.get_puzzle_state(user_id=1, name="p") is None

    def test_get_puzzle_state_none_when_absent(self, adapter):
        assert adapter.get_puzzle_state(user_id=1, name="nope") is None

    def test_set_puzzle_state_appends_history_row(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="p", puzzle=sample_puzzle)
        adapter.set_puzzle_state(
            user_id=1, name="p", state="submitted",
            publisher="NYT", date_submitted="2026-06-06",
        )
        state = adapter.get_puzzle_state(user_id=1, name="p")
        assert state == {
            "state": "submitted",
            "publisher": "NYT",
            "date_submitted": "2026-06-06",
            "date_published": None,
        }

    def test_set_puzzle_state_grows_history_row_count(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="p", puzzle=sample_puzzle)
        adapter.set_puzzle_state(user_id=1, name="p", state="draft")
        adapter.set_puzzle_state(user_id=1, name="p", state="filled")
        adapter.set_puzzle_state(user_id=1, name="p", state="finished")

        cur = adapter.conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM puzzle_state_history")
        assert cur.fetchone()["n"] == 3

    def test_get_puzzle_state_returns_latest_of_several_rows(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="p", puzzle=sample_puzzle)
        adapter.set_puzzle_state(user_id=1, name="p", state="draft")
        adapter.set_puzzle_state(user_id=1, name="p", state="filled")
        adapter.set_puzzle_state(user_id=1, name="p", state="finished")

        state = adapter.get_puzzle_state(user_id=1, name="p")

        assert state["state"] == "finished"

    def test_set_puzzle_state_not_found_raises(self, adapter):
        with pytest.raises(PersistenceError, match="not found"):
            adapter.set_puzzle_state(user_id=1, name="nope", state="draft")

    def test_rename_puzzle_preserves_id_and_state(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="old", puzzle=sample_puzzle)
        adapter.set_puzzle_state(user_id=1, name="old", state="archived")
        cur = adapter.conn.cursor()
        cur.execute("SELECT id FROM puzzles WHERE userid = 1 AND puzzlename = 'old'")
        old_id = cur.fetchone()["id"]

        adapter.rename_puzzle(user_id=1, old_name="old", new_name="new")

        cur.execute("SELECT id FROM puzzles WHERE userid = 1 AND puzzlename = 'new'")
        row = cur.fetchone()
        assert row["id"] == old_id
        assert adapter.get_puzzle_state(user_id=1, name="new")["state"] == "archived"
        assert adapter.get_puzzle_state(user_id=1, name="old") is None

    def test_rename_puzzle_not_found_raises(self, adapter):
        with pytest.raises(PersistenceError, match="not found"):
            adapter.rename_puzzle(user_id=1, old_name="nope", new_name="new")

    def test_rename_puzzle_rejects_clashing_name(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="a", puzzle=sample_puzzle)
        adapter.save_puzzle(user_id=1, name="b", puzzle=sample_puzzle)
        with pytest.raises(PersistenceError, match="already exists"):
            adapter.rename_puzzle(user_id=1, old_name="a", new_name="b")

    def test_delete_removes_row_and_state(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="p", puzzle=sample_puzzle)
        adapter.set_puzzle_state(user_id=1, name="p", state="published",
                                 date_published="2026-06-06")
        adapter.delete_puzzle(user_id=1, name="p")
        assert adapter.get_puzzle_state(user_id=1, name="p") is None

    def test_delete_cascades_to_history_table(self, adapter, sample_puzzle):
        adapter.save_puzzle(user_id=1, name="p", puzzle=sample_puzzle)
        adapter.set_puzzle_state(user_id=1, name="p", state="published",
                                 date_published="2026-06-06")

        cur = adapter.conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM puzzle_state_history")
        assert cur.fetchone()["n"] == 1

        adapter.delete_puzzle(user_id=1, name="p")

        cur.execute("SELECT COUNT(*) AS n FROM puzzle_state_history")
        assert cur.fetchone()["n"] == 0

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
        Integration test: Load a puzzle from the production crossword.db.
        This validates the schema hasn't drifted.
        """
        db_path = Path(__file__).resolve().parents[3] / "samples" / "crossword.db"
        if not db_path.exists():
            pytest.skip(f"crossword.db not found at {db_path}")

        adapter = SQLitePersistenceAdapter(str(db_path))

        puzzles = adapter.list_puzzles(user_id=1)
        if not puzzles:
            pytest.skip("No puzzles found in crossword.db")

        loaded = adapter.load_puzzle(user_id=1, name=puzzles[0])

        assert isinstance(loaded, Puzzle)
        assert loaded.n > 0
        assert loaded.last_mode in {"grid", "puzzle"}
