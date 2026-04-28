"""
Import a puzzle from an old grids.db into the main crossword database.

Usage:
    python tools/dev/impgrid.py --src grids.db --puzzlename <name> [--dest <db>] [--user-id <id>] [--out-name <name>]

Reads the row with the given puzzlename from the source grids.db. The jsonstr
column contains JSON with 'n' (grid size) and 'black_cells' fields. A Grid is
constructed from those, then a Puzzle from the Grid, and saved to the main database.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crossword.adapters.sqlite_persistence_adapter import SQLitePersistenceAdapter
from crossword.domain.grid import Grid
from crossword.domain.puzzle import Puzzle


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--src", required=True, metavar="DB",
                        help="Path to the source grids.db")
    parser.add_argument("--puzzlename", required=True, metavar="NAME",
                        help="puzzlename key to look up in the source grids table")
    parser.add_argument("--dest", metavar="DB",
                        help="Path to destination SQLite database (default: from config)")
    parser.add_argument("--user-id", type=int, default=2, metavar="ID",
                        help="User ID to store the puzzle under (default: 2)")
    parser.add_argument("--out-name", metavar="NAME",
                        help="Name to use in the destination database (default: same as puzzlename)")
    args = parser.parse_args()

    src_conn = sqlite3.connect(args.src)
    row = src_conn.execute(
        "SELECT jsonstr FROM grids WHERE puzzlename = ?", (args.puzzlename,)
    ).fetchone()
    src_conn.close()

    if row is None:
        print(f"error: puzzlename '{args.puzzlename}' not found in {args.src}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(row[0])
    grid = Grid(data["n"])
    for black_cell in data["black_cells"]:
        grid.add_black_cell(*black_cell)
    puzzle = Puzzle(grid)

    if args.dest:
        dest_path = args.dest
    else:
        import crossword
        dest_path = crossword.dbfile()

    out_name = args.out_name or args.puzzlename
    adapter = SQLitePersistenceAdapter(dest_path)
    adapter.save_puzzle(args.user_id, out_name, puzzle)
    print(f"saved '{out_name}' to {dest_path} (user_id={args.user_id})")


if __name__ == "__main__":
    main()
