"""Tests for the puzzle-state-history migration tool
(tools/dev/migrate_puzzle_state_history.py)."""

import importlib.util
import sqlite3
from pathlib import Path

import pytest

from crossword.tests import TestPuzzle


TOOL_PATH = (
    Path(__file__).resolve().parents[2] / "tools" / "dev" / "migrate_puzzle_state_history.py"
)

# The column-based schema this tool migrates *from* (b67e678-era).
COLUMN_SCHEMA = """
CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle',
    state           TEXT NOT NULL DEFAULT 'draft',
    jsonstr         TEXT NOT NULL,
    publisher       TEXT,
    date_submitted  TEXT,
    date_published  TEXT
);
"""


def load_tool():
    """Import the migration script as a module from its file path."""
    spec = importlib.util.spec_from_file_location("migrate_puzzle_state_history", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def migrate():
    return load_tool()


@pytest.fixture
def old_db(tmp_path):
    """Build a column-schema database with a mix of rows."""
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript(COLUMN_SCHEMA)

    solved = TestPuzzle.create_solved_atlantic_puzzle().to_json()
    empty = TestPuzzle.create_atlantic_puzzle().to_json()

    rows = [
        (1, 1, "solved", "c", "2026-06-06T00:00:00", "puzzle", "finished",
         solved, "NYT", "2026-06-01", None),
        (2, 1, "empty", "c", "2026-01-01T00:00:00", "grid", "draft",
         empty, None, None, None),
        (3, 1, "__wc__solved__abcd1234", "c", "m", "puzzle", "finished",
         solved, None, None, None),
        (4, 1, "__new__deadbeef", "c", "m", "puzzle", "draft", empty, None, None, None),
        (5, 1, None, "c", "m", "puzzle", "draft", empty, None, None, None),
    ]
    conn.executemany(
        "INSERT INTO puzzles (id, userid, puzzlename, created, modified, last_mode,"
        " state, jsonstr, publisher, date_submitted, date_published)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    return path


def test_fetch_real_puzzles_excludes_working_copies_and_nulls(migrate, old_db):
    conn = migrate.open_readonly(str(old_db))
    try:
        names = {row["puzzlename"] for row in migrate.fetch_real_puzzles(conn)}
    finally:
        conn.close()
    assert names == {"solved", "empty"}


def test_new_database_has_history_schema(migrate, tmp_path):
    path = tmp_path / "new.db"
    conn = migrate.create_new_database(str(path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(puzzles)")
        columns = {row[1] for row in cur.fetchall()}
        assert not ({"state", "publisher", "date_submitted", "date_published"} & columns)

        cur.execute("PRAGMA table_info(puzzle_state_history)")
        history_columns = {row[1] for row in cur.fetchall()}
        assert {"puzzle_id", "state", "publisher", "date_submitted",
                "date_published", "changed_at"} <= history_columns
    finally:
        conn.close()


def test_end_to_end_migration(migrate, old_db, tmp_path, monkeypatch):
    new_db = tmp_path / "new.db"
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_state_history.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(new_db)],
    )
    migrate.main()

    conn = sqlite3.connect(new_db)
    conn.row_factory = sqlite3.Row
    puzzles = {r["puzzlename"]: r for r in conn.execute("SELECT * FROM puzzles")}
    history = {r["puzzle_id"]: r for r in conn.execute("SELECT * FROM puzzle_state_history")}
    conn.close()

    # Only real puzzles copied, ids preserved, no state columns.
    assert set(puzzles) == {"solved", "empty"}
    assert "state" not in puzzles["solved"].keys()
    assert puzzles["solved"]["id"] == 1
    assert puzzles["empty"]["id"] == 2

    # Exactly one seeded history row per real puzzle, from its column values.
    assert set(history) == {1, 2}
    assert history[1]["state"] == "finished"
    assert history[1]["publisher"] == "NYT"
    assert history[1]["date_submitted"] == "2026-06-01"
    assert history[1]["date_published"] is None
    assert history[1]["changed_at"] == "2026-06-06T00:00:00"
    assert history[2]["state"] == "draft"


def test_refuses_existing_destination(migrate, old_db, tmp_path, monkeypatch):
    new_db = tmp_path / "existing.db"
    new_db.write_text("not empty")
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_state_history.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(new_db)],
    )
    with pytest.raises(SystemExit):
        migrate.main()


def test_refuses_same_source_and_destination(migrate, old_db, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_state_history.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(old_db)],
    )
    with pytest.raises(SystemExit):
        migrate.main()


def test_dry_run_writes_nothing(migrate, old_db, tmp_path, monkeypatch):
    new_db = tmp_path / "new.db"
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_state_history.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(new_db), "--dry-run"],
    )
    migrate.main()
    assert not new_db.exists()


def test_cascade_delete_removes_history(migrate, old_db, tmp_path, monkeypatch):
    """The new schema's FK should cascade-delete history when a puzzle is deleted."""
    new_db = tmp_path / "new.db"
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_state_history.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(new_db)],
    )
    migrate.main()

    conn = sqlite3.connect(new_db)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("DELETE FROM puzzles WHERE puzzlename = 'solved'")
    conn.commit()
    remaining = {r[0] for r in conn.execute("SELECT puzzle_id FROM puzzle_state_history")}
    conn.close()

    assert 1 not in remaining
    assert 2 in remaining
