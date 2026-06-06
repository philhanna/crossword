"""Tests for the one-off puzzle-state migration tool (tools/dev/migrate_puzzle_state.py)."""

import importlib.util
import sqlite3
from pathlib import Path

import pytest

from crossword.domain import puzzle_state as ps
from crossword.tests import TestPuzzle


TOOL_PATH = Path(__file__).resolve().parents[2] / "tools" / "dev" / "migrate_puzzle_state.py"

LEGACY_SCHEMA = """
CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle',
    jsonstr         TEXT NOT NULL
);
"""


def load_tool():
    """Import the migration script as a module from its file path."""
    spec = importlib.util.spec_from_file_location("migrate_puzzle_state", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def migrate():
    return load_tool()


@pytest.fixture
def old_db(tmp_path):
    """Build a legacy (pre-state-columns) database with a mix of rows."""
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript(LEGACY_SCHEMA)

    solved = TestPuzzle.create_solved_atlantic_puzzle().to_json()
    empty = TestPuzzle.create_atlantic_puzzle().to_json()

    rows = [
        (1, 1, "solved", "c", "m", "puzzle", solved),
        (2, 1, "empty", "c", "m", "grid", empty),
        (3, 1, "__wc__solved__abcd1234", "c", "m", "puzzle", solved),
        (4, 1, "__new__deadbeef", "c", "m", "puzzle", empty),
        (5, 1, None, "c", "m", "puzzle", empty),
    ]
    conn.executemany(
        "INSERT INTO puzzles (id, userid, puzzlename, created, modified, last_mode, jsonstr)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
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


def test_detect_state_uses_completion_ladder(migrate, old_db):
    conn = migrate.open_readonly(str(old_db))
    try:
        rows = {row["puzzlename"]: row for row in migrate.fetch_real_puzzles(conn)}
        assert migrate.detect_state(rows["solved"]) == ps.FINISHED
        assert migrate.detect_state(rows["empty"]) == ps.DRAFT
    finally:
        conn.close()


def test_new_database_has_state_schema(migrate, tmp_path):
    path = tmp_path / "new.db"
    conn = migrate.create_new_database(str(path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(puzzles)")
        columns = {row[1] for row in cur.fetchall()}
        assert {"state", "publisher", "date_submitted", "date_published"} <= columns
    finally:
        conn.close()


def test_end_to_end_migration(migrate, old_db, tmp_path, monkeypatch):
    new_db = tmp_path / "new.db"
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_state.py", "--old-dbfile", str(old_db), "--new-dbfile", str(new_db)],
    )
    migrate.main()

    conn = sqlite3.connect(new_db)
    conn.row_factory = sqlite3.Row
    rows = {r["puzzlename"]: r for r in conn.execute("SELECT * FROM puzzles")}
    conn.close()

    # Only real puzzles copied, ids preserved, state auto-detected.
    assert set(rows) == {"solved", "empty"}
    assert rows["solved"]["id"] == 1
    assert rows["solved"]["state"] == ps.FINISHED
    assert rows["empty"]["id"] == 2
    assert rows["empty"]["state"] == ps.DRAFT
    assert rows["solved"]["publisher"] is None


def test_refuses_existing_destination(migrate, old_db, tmp_path, monkeypatch):
    new_db = tmp_path / "existing.db"
    new_db.write_text("not empty")
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_state.py", "--old-dbfile", str(old_db), "--new-dbfile", str(new_db)],
    )
    with pytest.raises(SystemExit):
        migrate.main()


def test_refuses_same_source_and_destination(migrate, old_db, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_state.py", "--old-dbfile", str(old_db), "--new-dbfile", str(old_db)],
    )
    with pytest.raises(SystemExit):
        migrate.main()


def test_dry_run_writes_nothing(migrate, old_db, tmp_path, monkeypatch):
    new_db = tmp_path / "new.db"
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_state.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(new_db), "--dry-run"],
    )
    migrate.main()
    assert not new_db.exists()
