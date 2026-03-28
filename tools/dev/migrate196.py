"""
Migrate a pre-196 crossword database to the merged puzzle-only layout.

This tool never mutates the source database. It opens the source database
read-only, copies it to a new destination database, rewrites the construction
tables in the destination, validates the migrated puzzle rows, and drops the
legacy standalone `grids` table from the destination.

Usage:
    python3 tools/dev/migrate196.py SOURCE_DB DEST_DB [--force] [--keep-failed-output] [--verbose]
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crossword import Grid, Puzzle


CREATE_PUZZLES_SQL = """
CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT NOT NULL,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle'
                        CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr         TEXT NOT NULL,
    UNIQUE (userid, puzzlename)
)
"""


class MigrationError(RuntimeError):
    """Raised when the migration cannot safely continue."""


@dataclass
class MigrationReport:
    source_db: str
    dest_db: str
    migrated_puzzles: int
    dropped_grids_table: bool


def connect_readonly(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{Path(path).resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def connect_rw(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return cur.fetchone() is not None


def column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return any(row["name"] == column_name for row in cur.fetchall())


def source_puzzle_columns(conn: sqlite3.Connection) -> set[str]:
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(puzzles)")
    return {row["name"] for row in cur.fetchall()}


def normalize_last_mode(*candidates: Any) -> str:
    for candidate in candidates:
        if candidate in {"grid", "puzzle"}:
            return candidate
    return "puzzle"


def decode_json_field(value: Any, *, context: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise MigrationError(f"{context}: invalid JSON payload") from exc
        if isinstance(decoded, dict):
            return decoded
    raise MigrationError(f"{context}: unsupported embedded JSON field")


def build_grid_lookups(conn: sqlite3.Connection) -> tuple[dict[tuple[int, str], sqlite3.Row], dict[int, sqlite3.Row]]:
    if not table_exists(conn, "grids"):
        return {}, {}

    cur = conn.cursor()
    cur.execute("SELECT * FROM grids")
    rows = cur.fetchall()

    by_user_and_name: dict[tuple[int, str], sqlite3.Row] = {}
    by_id: dict[int, sqlite3.Row] = {}
    for row in rows:
        by_user_and_name[(row["userid"], row["gridname"])] = row
        by_id[row["id"]] = row
    return by_user_and_name, by_id


def resolve_grid_image(
    user_id: int,
    image: dict[str, Any],
    grids_by_user_and_name: dict[tuple[int, str], sqlite3.Row],
    grids_by_id: dict[int, sqlite3.Row],
    *,
    puzzle_name: str,
) -> dict[str, Any]:
    if "n" in image and "black_cells" in image:
        return image

    grid_payload = image.get("grid")
    if isinstance(grid_payload, dict):
        if "n" in grid_payload and "black_cells" in grid_payload:
            return grid_payload
        if "jsonstr" in grid_payload:
            decoded = decode_json_field(
                grid_payload["jsonstr"],
                context=f"puzzle '{puzzle_name}' embedded grid",
            )
            if "n" in decoded and "black_cells" in decoded:
                return decoded
    if isinstance(grid_payload, str):
        if grid_payload.lstrip().startswith("{"):
            decoded = decode_json_field(
                grid_payload,
                context=f"puzzle '{puzzle_name}' embedded grid",
            )
            if "n" in decoded and "black_cells" in decoded:
                return decoded
        grid_row = grids_by_user_and_name.get((user_id, grid_payload))
        if grid_row:
            return decode_json_field(
                grid_row["jsonstr"],
                context=f"grid '{grid_payload}' for puzzle '{puzzle_name}'",
            )

    for key in ("grid_name", "gridname", "source_grid_name", "original_grid_name"):
        grid_name = image.get(key)
        if isinstance(grid_name, str):
            grid_row = grids_by_user_and_name.get((user_id, grid_name))
            if grid_row:
                return decode_json_field(
                    grid_row["jsonstr"],
                    context=f"grid '{grid_name}' for puzzle '{puzzle_name}'",
                )

    for key in ("grid_id", "gridid"):
        grid_id = image.get(key)
        if isinstance(grid_id, int) and grid_id in grids_by_id:
            return decode_json_field(
                grids_by_id[grid_id]["jsonstr"],
                context=f"grid id {grid_id} for puzzle '{puzzle_name}'",
            )

    raise MigrationError(
        f"Puzzle '{puzzle_name}' does not contain embedded grid data and no matching legacy grid reference was found"
    )


def normalize_word_entries(entries: Any, *, label: str, puzzle_name: str) -> list[dict[str, Any]]:
    if entries is None:
        return []
    if not isinstance(entries, list):
        raise MigrationError(f"Puzzle '{puzzle_name}' has invalid {label} data")
    normalized: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise MigrationError(f"Puzzle '{puzzle_name}' has invalid {label} entry")
        if "seq" not in entry:
            raise MigrationError(f"Puzzle '{puzzle_name}' has {label} entry without seq")
        normalized.append(entry)
    return normalized


def set_word_entries(
    puzzle: Puzzle,
    entries: list[dict[str, Any]],
    *,
    direction: str,
    puzzle_name: str,
) -> None:
    for entry in entries:
        seq = entry["seq"]
        text = entry.get("text", "") or ""
        clue = entry.get("clue")
        if direction == "across":
            word = puzzle.get_across_word(seq)
        else:
            word = puzzle.get_down_word(seq)
        if word is None:
            raise MigrationError(
                f"Puzzle '{puzzle_name}' references missing {direction} word {seq} after grid reconstruction"
            )
        word.set_text(text)
        word.set_clue(clue)


def build_canonical_puzzle(
    row: sqlite3.Row,
    image: dict[str, Any],
    grid_image: dict[str, Any],
) -> Puzzle:
    puzzle_name = row["puzzlename"]
    if "n" not in grid_image or "black_cells" not in grid_image:
        raise MigrationError(f"Puzzle '{puzzle_name}' grid data is missing n/black_cells")

    n = grid_image["n"]
    if not isinstance(n, int):
        raise MigrationError(f"Puzzle '{puzzle_name}' has non-integer grid size")

    grid = Grid(n)
    black_cells = set()
    for cell in grid_image["black_cells"]:
        if not isinstance(cell, (list, tuple)) or len(cell) != 2:
            raise MigrationError(f"Puzzle '{puzzle_name}' has invalid black cell entry")
        black_cells.add((cell[0], cell[1]))
    grid.black_cells = black_cells
    grid.numbered_cells = None

    puzzle = Puzzle(grid, title=image.get("title"))
    puzzle.last_mode = normalize_last_mode(
        row["last_mode"] if "last_mode" in row.keys() else None,
        image.get("last_mode"),
    )

    across_words = normalize_word_entries(
        image.get("across_words", []),
        label="across_words",
        puzzle_name=puzzle_name,
    )
    down_words = normalize_word_entries(
        image.get("down_words", []),
        label="down_words",
        puzzle_name=puzzle_name,
    )
    set_word_entries(puzzle, across_words, direction="across", puzzle_name=puzzle_name)
    set_word_entries(puzzle, down_words, direction="down", puzzle_name=puzzle_name)

    puzzle.undo_stack = copy.deepcopy(
        image.get("puzzle_undo_stack", image.get("undo_stack", [])) or []
    )
    puzzle.redo_stack = copy.deepcopy(
        image.get("puzzle_redo_stack", image.get("redo_stack", [])) or []
    )
    puzzle.grid_undo_stack = copy.deepcopy(
        image.get("grid_undo_stack", grid_image.get("undo_stack", [])) or []
    )
    puzzle.grid_redo_stack = copy.deepcopy(
        image.get("grid_redo_stack", grid_image.get("redo_stack", [])) or []
    )

    return puzzle


def create_destination_puzzles_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS puzzles_migrated_196")
    cur.execute(CREATE_PUZZLES_SQL.replace("puzzles", "puzzles_migrated_196", 1))


def insert_migrated_puzzle(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    puzzle: Puzzle,
) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO puzzles_migrated_196
            (id, userid, puzzlename, created, modified, last_mode, jsonstr)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["id"],
            row["userid"],
            row["puzzlename"],
            row["created"],
            row["modified"],
            puzzle.last_mode,
            puzzle.to_json(),
        ),
    )


def validate_migrated_puzzles(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("SELECT puzzlename, last_mode, jsonstr FROM puzzles_migrated_196 ORDER BY id")
    for row in cur.fetchall():
        puzzle = Puzzle.from_json(row["jsonstr"])
        if puzzle.last_mode != row["last_mode"]:
            raise MigrationError(f"Puzzle '{row['puzzlename']}' did not round-trip last_mode correctly")
        if puzzle.last_mode not in {"grid", "puzzle"}:
            raise MigrationError(f"Puzzle '{row['puzzlename']}' has invalid last_mode after migration")
        if puzzle.n <= 0:
            raise MigrationError(f"Puzzle '{row['puzzlename']}' has invalid grid size after migration")


def replace_legacy_tables(conn: sqlite3.Connection) -> bool:
    cur = conn.cursor()
    cur.execute("DROP TABLE puzzles")
    cur.execute("ALTER TABLE puzzles_migrated_196 RENAME TO puzzles")
    cur.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_puzzles_userid_puzzlename
        ON puzzles(userid, puzzlename)
        """
    )

    dropped_grids = False
    if table_exists(conn, "grids"):
        cur.execute("DROP TABLE grids")
        dropped_grids = True
    return dropped_grids


def migrate_database(
    source_db: str,
    dest_db: str,
    *,
    force: bool = False,
    keep_failed_output: bool = False,
    verbose: bool = False,
) -> MigrationReport:
    source_path = Path(source_db)
    dest_path = Path(dest_db)

    if not source_path.exists():
        raise MigrationError(f"Source database does not exist: {source_path}")

    if dest_path.exists():
        if not force:
            raise MigrationError(f"Destination database already exists: {dest_path}")
        dest_path.unlink()

    source_conn = connect_readonly(str(source_path))
    dest_conn: sqlite3.Connection | None = None

    try:
        dest_conn = connect_rw(str(dest_path))
        source_conn.backup(dest_conn)
        dest_conn.row_factory = sqlite3.Row

        if not table_exists(dest_conn, "puzzles"):
            raise MigrationError("Source database does not contain a puzzles table")

        grids_by_user_and_name, grids_by_id = build_grid_lookups(dest_conn)
        create_destination_puzzles_table(dest_conn)

        cur = dest_conn.cursor()
        cur.execute("SELECT * FROM puzzles ORDER BY id")
        source_rows = cur.fetchall()

        for row in source_rows:
            legacy_image = decode_json_field(
                row["jsonstr"],
                context=f"puzzle '{row['puzzlename']}'",
            )
            grid_image = resolve_grid_image(
                row["userid"],
                legacy_image,
                grids_by_user_and_name,
                grids_by_id,
                puzzle_name=row["puzzlename"],
            )
            canonical_puzzle = build_canonical_puzzle(row, legacy_image, grid_image)
            insert_migrated_puzzle(dest_conn, row, canonical_puzzle)
            if verbose:
                print(f"Migrated puzzle: {row['puzzlename']}")

        validate_migrated_puzzles(dest_conn)
        dropped_grids = replace_legacy_tables(dest_conn)
        dest_conn.commit()

        return MigrationReport(
            source_db=str(source_path),
            dest_db=str(dest_path),
            migrated_puzzles=len(source_rows),
            dropped_grids_table=dropped_grids,
        )
    except Exception:
        if dest_conn is not None:
            dest_conn.rollback()
            dest_conn.close()
        source_conn.close()
        if dest_path.exists() and not keep_failed_output:
            dest_path.unlink()
        raise
    finally:
        source_conn.close()
        if dest_conn is not None:
            try:
                dest_conn.close()
            except sqlite3.Error:
                pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_db", help="Path to the old database to read")
    parser.add_argument("dest_db", help="Path to the new migrated database to create")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the destination file if it already exists",
    )
    parser.add_argument(
        "--keep-failed-output",
        action="store_true",
        help="Keep the partially written destination database if migration fails",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each migrated puzzle name",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = migrate_database(
            args.source_db,
            args.dest_db,
            force=args.force,
            keep_failed_output=args.keep_failed_output,
            verbose=args.verbose,
        )
    except MigrationError as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1

    print(f"Source database: {report.source_db}")
    print(f"Destination database: {report.dest_db}")
    print(f"Migrated puzzles: {report.migrated_puzzles}")
    print(f"Dropped grids table: {'yes' if report.dropped_grids_table else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
