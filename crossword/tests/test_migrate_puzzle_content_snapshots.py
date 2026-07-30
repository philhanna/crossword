"""Tests for the puzzle-content-snapshots migration tool
(tools/dev/migrate_puzzle_content_snapshots.py)."""

import importlib.util
import sqlite3
from pathlib import Path

import pytest

from crossword.tests import TestPuzzle


TOOL_PATH = (
    Path(__file__).resolve().parents[2] / "tools" / "dev" / "migrate_puzzle_content_snapshots.py"
)

# The pre-content-column schema this tool migrates *from* (7b1f46d-era).
NO_CONTENT_SCHEMA = """
CREATE TABLE puzzles (
    id          INTEGER PRIMARY KEY,
    userid      INTEGER NOT NULL,
    puzzlename  TEXT NOT NULL,
    created     TEXT NOT NULL,
    modified    TEXT NOT NULL,
    last_mode   TEXT NOT NULL DEFAULT 'puzzle',
    jsonstr     TEXT NOT NULL
);

CREATE TABLE puzzle_state_history (
    id              INTEGER PRIMARY KEY,
    puzzle_id       INTEGER NOT NULL REFERENCES puzzles(id) ON DELETE CASCADE,
    state           TEXT NOT NULL,
    publisher       TEXT,
    date_submitted  TEXT,
    date_published  TEXT,
    changed_at      TEXT NOT NULL
);
"""


def load_tool():
    """Import the migration script as a module from its file path."""
    spec = importlib.util.spec_from_file_location("migrate_puzzle_content_snapshots", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def migrate():
    return load_tool()


@pytest.fixture
def old_db(tmp_path):
    """Build a no-content-column database with a puzzle that has several history rows."""
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript(NO_CONTENT_SCHEMA)

    solved = TestPuzzle.create_solved_atlantic_puzzle().to_json()
    empty = TestPuzzle.create_atlantic_puzzle().to_json()

    conn.executemany(
        "INSERT INTO puzzles (id, userid, puzzlename, created, modified, last_mode, jsonstr)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (1, 1, "solved", "c", "2026-06-06T00:00:00", "puzzle", solved),
            (2, 1, "empty", "c", "2026-01-01T00:00:00", "grid", empty),
        ],
    )
    conn.executemany(
        "INSERT INTO puzzle_state_history"
        " (id, puzzle_id, state, publisher, date_submitted, date_published, changed_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (1, 1, "draft", None, None, None, "2026-01-01T00:00:00"),
            (2, 1, "finished", None, None, None, "2026-06-01T00:00:00"),
            (3, 1, "submitted", "NYT", "2026-06-06", None, "2026-06-06T00:00:00"),
            (4, 2, "draft", None, None, None, "2026-01-01T00:00:00"),
        ],
    )
    conn.commit()
    conn.close()
    return path


def test_new_database_has_content_column(migrate, tmp_path):
    path = tmp_path / "new.db"
    conn = migrate.create_new_database(str(path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(puzzle_state_history)")
        columns = {row[1] for row in cur.fetchall()}
        assert "content" in columns
    finally:
        conn.close()


def test_end_to_end_migration(migrate, old_db, tmp_path, monkeypatch):
    new_db = tmp_path / "new.db"
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_content_snapshots.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(new_db)],
    )
    migrate.main()

    conn = sqlite3.connect(new_db)
    conn.row_factory = sqlite3.Row
    puzzles = {r["puzzlename"]: r for r in conn.execute("SELECT * FROM puzzles")}
    history = {r["id"]: r for r in conn.execute("SELECT * FROM puzzle_state_history")}
    conn.close()

    # All puzzles and all history rows carried across unchanged, ids preserved.
    assert set(puzzles) == {"solved", "empty"}
    assert puzzles["solved"]["id"] == 1
    assert puzzles["empty"]["id"] == 2
    assert set(history) == {1, 2, 3, 4}
    assert history[3]["state"] == "submitted"
    assert history[3]["publisher"] == "NYT"

    # Nothing to backfill — every copied row has a NULL content snapshot.
    assert all(row["content"] is None for row in history.values())


def test_refuses_existing_destination(migrate, old_db, tmp_path, monkeypatch):
    new_db = tmp_path / "existing.db"
    new_db.write_text("not empty")
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_content_snapshots.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(new_db)],
    )
    with pytest.raises(SystemExit):
        migrate.main()


def test_refuses_same_source_and_destination(migrate, old_db, monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_content_snapshots.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(old_db)],
    )
    with pytest.raises(SystemExit):
        migrate.main()


def test_dry_run_writes_nothing(migrate, old_db, tmp_path, monkeypatch):
    new_db = tmp_path / "new.db"
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_content_snapshots.py", "--old-dbfile", str(old_db),
         "--new-dbfile", str(new_db), "--dry-run"],
    )
    migrate.main()
    assert not new_db.exists()


def test_cascade_delete_removes_history(migrate, old_db, tmp_path, monkeypatch):
    """The rebuilt schema's FK should still cascade-delete history when a puzzle is deleted."""
    new_db = tmp_path / "new.db"
    monkeypatch.setattr(
        "sys.argv",
        ["migrate_puzzle_content_snapshots.py", "--old-dbfile", str(old_db),
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
