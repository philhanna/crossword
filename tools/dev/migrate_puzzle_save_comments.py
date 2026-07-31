"""
Rebuild the crossword database into a new file with a `comment` column on
puzzle_state_history.

This is a one-off migration. It reads the existing database (read-only,
never modified) and writes a brand-new SQLite file with the same `puzzles`
table and the same `puzzle_state_history` rows, plus one new nullable
column: `puzzle_state_history.comment`, holding the free-form note a user
enters when saving (see docs/dev/puzzle_save_comments.md).

Like migrate_puzzle_content_snapshots.py, this is a straight copy of both
tables (ids preserved) with one column added. Unlike that migration, the
source database here already has a `content` column, so this one carries
it over unchanged rather than leaving it NULL. `comment` is left NULL for
every copied row: there is nothing to backfill, since no comment was ever
collected before this feature shipped. From this point on, every save
made through Save/Save As requires one.

Uses plain sqlite3 for the schema and row copy; does not import
SQLitePersistenceAdapter.

The schema DDL below is copied from
crossword/adapters/sqlite_persistence_adapter.py::_ensure_schema_compatibility
(see docs/dev/puzzle_save_comments.md), which remains the source of truth
for the running app. Keep them in sync by hand.

Usage:
    python3 tools/dev/migrate_puzzle_save_comments.py --new-dbfile PATH [--old-dbfile PATH] [--dry-run]

Options:
    --new-dbfile PATH   Destination DB. Required. Must not already exist.
    --old-dbfile PATH   Source DB. Defaults to the app's configured dbfile.
    --dry-run           Report counts and write nothing.

After it finishes, point the app at the new file: update 'dbfile' in
~/.config/crossword/config.yaml (or rename the new file into place).
"""

import argparse
import os
import sqlite3
import sys

sys.path.insert(0, ".")
from crossword import init_config


SCHEMA_DDL = """
CREATE TABLE puzzles (
    id          INTEGER PRIMARY KEY,
    userid      INTEGER NOT NULL,
    puzzlename  TEXT NOT NULL,
    created     TEXT NOT NULL,
    modified    TEXT NOT NULL,
    last_mode   TEXT NOT NULL DEFAULT 'puzzle'
                    CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr     TEXT NOT NULL
);

CREATE UNIQUE INDEX idx_puzzles_userid_puzzlename
    ON puzzles(userid, puzzlename);

CREATE TABLE puzzle_state_history (
    id              INTEGER PRIMARY KEY,
    puzzle_id       INTEGER NOT NULL REFERENCES puzzles(id) ON DELETE CASCADE,
    state           TEXT NOT NULL CHECK (state IN (
                        'draft','filled','finished',
                        'submitted','published','archived')),
    publisher       TEXT,
    date_submitted  TEXT,
    date_published  TEXT,
    content         TEXT,
    comment         TEXT,
    changed_at      TEXT NOT NULL
);

CREATE INDEX idx_puzzle_state_history_puzzle
    ON puzzle_state_history(puzzle_id, id DESC);
"""


def main() -> None:
    """Read the old DB and rebuild it into a new file with a comment column on puzzle_state_history."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--new-dbfile", required=True, help="Destination DB (must not exist)")
    parser.add_argument("--old-dbfile", help="Source DB (defaults to configured dbfile)")
    parser.add_argument("--dry-run", action="store_true", help="Report counts without writing")
    args = parser.parse_args()

    old_path = resolve_old_dbfile(args.old_dbfile)
    new_path = os.path.abspath(args.new_dbfile)

    if not os.path.exists(old_path):
        sys.exit(f"Source database not found: {old_path}")
    if os.path.abspath(old_path) == new_path:
        sys.exit("--new-dbfile must differ from the source database")
    if os.path.exists(new_path):
        sys.exit(f"Destination already exists (refusing to overlay): {new_path}")

    print(f"Source:      {old_path}")
    print(f"Destination: {new_path}\n")

    old_conn = open_readonly(old_path)
    try:
        puzzles = fetch_puzzles(old_conn)
        history = fetch_history(old_conn)
    finally:
        old_conn.close()

    print(f"Puzzles to copy:      {len(puzzles)}")
    print(f"History rows to copy: {len(history)}")

    if args.dry_run:
        print(f"\nDry run — would create {new_path}. Nothing written.")
        return

    new_conn = create_new_database(new_path)
    try:
        copy_data(new_conn, puzzles, history)
        new_conn.commit()
    finally:
        new_conn.close()

    print(f"\nCreated {new_path} with {len(puzzles)} puzzle(s) and {len(history)} history row(s).")
    print("Point the app at it: update 'dbfile' in ~/.config/crossword/config.yaml.")


def resolve_old_dbfile(explicit: str | None) -> str:
    """Return the source dbfile: the --old-dbfile argument or the app's configured dbfile."""
    if explicit:
        return explicit
    return init_config()["dbfile"]


def open_readonly(path: str) -> sqlite3.Connection:
    """Open an existing database read-only so the source can never be modified."""
    uri = f"file:{os.path.abspath(path)}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_puzzles(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return every row of the puzzles table, unfiltered — this migration only adds a column."""
    cur = conn.cursor()
    cur.execute(
        "SELECT id, userid, puzzlename, created, modified, last_mode, jsonstr"
        " FROM puzzles ORDER BY id"
    )
    return cur.fetchall()


def fetch_history(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return every row of the puzzle_state_history table, unfiltered, including content."""
    cur = conn.cursor()
    cur.execute(
        "SELECT id, puzzle_id, state, publisher, date_submitted, date_published,"
        " content, changed_at"
        " FROM puzzle_state_history ORDER BY id"
    )
    return cur.fetchall()


def create_new_database(path: str) -> sqlite3.Connection:
    """Create the destination DB and define the complete schema in one pass."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_DDL)
    conn.commit()
    return conn


def copy_data(conn: sqlite3.Connection, puzzles: list[sqlite3.Row], history: list[sqlite3.Row]) -> None:
    """Insert the puzzle and history rows into the new DB, preserving ids and
    existing content. `comment` is left NULL."""
    conn.executemany(
        "INSERT INTO puzzles"
        " (id, userid, puzzlename, created, modified, last_mode, jsonstr)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (row["id"], row["userid"], row["puzzlename"], row["created"],
             row["modified"], row["last_mode"], row["jsonstr"])
            for row in puzzles
        ],
    )
    conn.executemany(
        "INSERT INTO puzzle_state_history"
        " (id, puzzle_id, state, publisher, date_submitted, date_published, content, changed_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (row["id"], row["puzzle_id"], row["state"], row["publisher"],
             row["date_submitted"], row["date_published"], row["content"], row["changed_at"])
            for row in history
        ],
    )


if __name__ == "__main__":
    main()
