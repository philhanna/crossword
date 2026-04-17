# crossword.tests.adapters.test_postgres_adapter
"""Tests for PostgresPersistenceAdapter — mirrors test_sqlite_adapter.py."""
import os

import pytest

from crossword import Grid, Puzzle
from crossword.ports.persistence_port import PersistenceError

pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL not set",
)


@pytest.fixture(scope="module")
def pg_conn():
    import psycopg2
    conn = psycopg2.connect(os.environ["TEST_DATABASE_URL"])
    yield conn
    conn.close()


@pytest.fixture
def adapter(pg_conn):
    from crossword.adapters.postgres_persistence_adapter import PostgresPersistenceAdapter
    adp = PostgresPersistenceAdapter(pg_conn)
    yield adp
    # Clean up all test puzzles after each test
    with pg_conn.cursor() as cur:
        cur.execute("DELETE FROM puzzles WHERE userid = 1")
    pg_conn.commit()


@pytest.fixture
def sample_grid():
    grid = Grid(5)
    grid.add_black_cell(1, 1)
    grid.add_black_cell(2, 2)
    return grid


@pytest.fixture
def sample_puzzle(sample_grid):
    puzzle = Puzzle(sample_grid)
    puzzle.title = "Test Puzzle"
    return puzzle


def test_save_and_load_puzzle(adapter, sample_puzzle):
    adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)
    loaded = adapter.load_puzzle(user_id=1, name="test_puzzle")

    assert loaded.grid.n == sample_puzzle.grid.n
    assert loaded.title == sample_puzzle.title
    assert len(loaded.across_words) == len(sample_puzzle.across_words)
    assert len(loaded.down_words) == len(sample_puzzle.down_words)
    assert loaded.last_mode == sample_puzzle.last_mode


def test_save_puzzle_overwrites(adapter, sample_puzzle):
    adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)
    sample_puzzle.title = "Modified Puzzle"
    adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)
    loaded = adapter.load_puzzle(user_id=1, name="test_puzzle")
    assert loaded.title == "Modified Puzzle"


def test_delete_puzzle(adapter, sample_puzzle):
    adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)
    adapter.delete_puzzle(user_id=1, name="test_puzzle")
    with pytest.raises(PersistenceError):
        adapter.load_puzzle(user_id=1, name="test_puzzle")


def test_list_puzzles(adapter, sample_puzzle):
    adapter.save_puzzle(user_id=1, name="puzzle1", puzzle=sample_puzzle)
    adapter.save_puzzle(user_id=1, name="puzzle2", puzzle=sample_puzzle)
    puzzles = adapter.list_puzzles(user_id=1)
    assert len(puzzles) == 2
    assert "puzzle1" in puzzles
    assert "puzzle2" in puzzles


def test_load_puzzle_not_found(adapter):
    with pytest.raises(PersistenceError, match="not found"):
        adapter.load_puzzle(1, "nonexistent")


def test_delete_puzzle_not_found(adapter):
    with pytest.raises(PersistenceError, match="not found"):
        adapter.delete_puzzle(1, "nonexistent")


def test_save_puzzle_persists_last_mode(adapter, sample_puzzle):
    sample_puzzle.enter_puzzle_mode()
    adapter.save_puzzle(user_id=1, name="test_puzzle", puzzle=sample_puzzle)
    with adapter._cursor() as cur:
        cur.execute(
            "SELECT last_mode FROM puzzles WHERE userid = %s AND puzzlename = %s",
            (1, "test_puzzle"),
        )
        row = cur.fetchone()
    assert row["last_mode"] == "puzzle"
