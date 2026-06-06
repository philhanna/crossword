"""
Rebuild the crossword database into a new file with the puzzle_state schema.

This is a one-off migration. It reads the existing database (read-only, never
modified) and writes a brand-new SQLite file containing the full target schema
(puzzles + puzzle_state). Because the destination is fresh, the schema is created
once, unconditionally — there is no CREATE TABLE IF NOT EXISTS, no ALTER TABLE,
and no column-existence probing.

It copies every real puzzle (preserving its id, so puzzle_state foreign keys line
up), skipping working copies (__wc__ / __new__) and legacy NULL names, and seeds
one puzzle_state row per copied puzzle using the puzzle's created timestamp. The
seeded state is auto-detected from the puzzle's contents via the completion
ladder (draft/filled/finished) — see docs/dev/dashboard.md §2-§3 — so a fully
filled-and-clued puzzle migrates as 'finished', not 'draft'.

Uses plain sqlite3 for the schema and row copy, and reuses the domain code
(Puzzle.from_json + crossword.domain.puzzle_state.detect_completion_state) to
classify each puzzle. It does not import SQLitePersistenceAdapter.

The schema DDL below is copied from
crossword/adapters/sqlite_persistence_adapter.py::_ensure_schema_compatibility
(plus the puzzle_state table from docs/dev/dashboard.md §1), which remains the
source of truth for the running app. Keep them in sync by hand.

Usage:
    python3 tools/dev/migrate_puzzle_state.py --new-dbfile PATH [--old-dbfile PATH] [--dry-run]

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
from crossword.domain.puzzle import Puzzle
from crossword.domain import puzzle_state as ps


WC_PREFIX = "__wc__"
NEW_PREFIX = "__new__"

SCHEMA_DDL = """
CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT NOT NULL,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle'
                        CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr         TEXT NOT NULL
);

CREATE UNIQUE INDEX idx_puzzles_userid_puzzlename
    ON puzzles(userid, puzzlename);

CREATE TABLE puzzle_state (
    ts              TEXT    NOT NULL,
    puzzle_id       INTEGER NOT NULL,
    state           TEXT    NOT NULL
                        CHECK (state IN (
                            'draft','filled','finished',
                            'submitted','published','archived')),
    publisher       TEXT,
    date_submitted  TEXT,
    date_published  TEXT,
    PRIMARY KEY (ts, puzzle_id),
    FOREIGN KEY (puzzle_id) REFERENCES puzzles(id) ON DELETE CASCADE
);

CREATE INDEX idx_puzzle_state_puzzle
    ON puzzle_state(puzzle_id, ts DESC);
"""


def main() -> None:
    """Read the old DB and rebuild it into a new file with the puzzle_state schema."""
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
        puzzles = fetch_real_puzzles(old_conn)
    finally:
        old_conn.close()

    states = [(row, detect_state(row)) for row in puzzles]

    print(f"Real puzzles to copy: {len(puzzles)}")
    print("State rows to seed (auto-detected):")
    for state in ps.COMPLETION_LADDER:
        count = sum(1 for _, s in states if s == state)
        print(f"  {state:<9} {count}")

    if args.dry_run:
        print(f"\nDry run — would create {new_path}. Nothing written.")
        return

    new_conn = create_new_database(new_path)
    try:
        copy_puzzles(new_conn, puzzles)
        backfill_states(new_conn, states)
        new_conn.commit()
    finally:
        new_conn.close()

    print(f"\nCreated {new_path} with {len(puzzles)} puzzle(s) and {len(states)} state row(s).")
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


def fetch_real_puzzles(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Return all real puzzle rows, excluding working copies and legacy NULL names."""
    cur = conn.cursor()
    cur.execute(
        "SELECT id, userid, puzzlename, created, modified, last_mode, jsonstr"
        " FROM puzzles"
        " WHERE puzzlename IS NOT NULL"
        " AND puzzlename NOT LIKE ?"
        " AND puzzlename NOT LIKE ?"
        " ORDER BY id",
        (WC_PREFIX + "%", NEW_PREFIX + "%"),
    )
    return cur.fetchall()


def detect_state(row: sqlite3.Row) -> str:
    """Auto-detect a puzzle's completion-ladder state from its stored JSON."""
    puzzle = Puzzle.from_json(row["jsonstr"])
    return ps.detect_completion_state(puzzle)


def create_new_database(path: str) -> sqlite3.Connection:
    """Create the destination DB and define the complete schema in one pass."""
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_DDL)
    conn.commit()
    return conn


def copy_puzzles(conn: sqlite3.Connection, puzzles: list[sqlite3.Row]) -> None:
    """Insert the given puzzle rows into the new DB, preserving each id."""
    conn.executemany(
        "INSERT INTO puzzles"
        " (id, userid, puzzlename, created, modified, last_mode, jsonstr)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row["id"],
                row["userid"],
                row["puzzlename"],
                row["created"],
                row["modified"],
                row["last_mode"],
                row["jsonstr"],
            )
            for row in puzzles
        ],
    )


def backfill_states(conn: sqlite3.Connection, states: list[tuple[sqlite3.Row, str]]) -> None:
    """Seed one puzzle_state row per puzzle (auto-detected state), dated at created ts."""
    conn.executemany(
        "INSERT INTO puzzle_state (ts, puzzle_id, state) VALUES (?, ?, ?)",
        [(row["created"], row["id"], state) for row, state in states],
    )


if __name__ == "__main__":
    main()
