"""
Import .xd puzzle files into a crossword database as blank grids.

Reads .xd file paths from stdin (one per line) — suitable for use with find:

    find <path> -name '*.xd' | python tools/dev/import_grid.py --db crossword.db

Each puzzle is stripped of all filled letters and clues before storage,
leaving only the black-cell pattern (the grid structure).

Puzzle names have the form "Grid<n><hash8>" where <n> is the grid size and
<hash8> is the first 8 hex digits of a SHA-256 hash of the sorted black-cell
coordinates.  Grids with identical structure get the same name and are skipped
on re-import.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from crossword.adapters.sqlite_persistence_adapter import SQLitePersistenceAdapter
from crossword.adapters.xd_import_adapter import XdImportAdapter
from crossword.domain.word import Word


def _grid_name(puzzle) -> str:
    black = sorted(puzzle.grid.get_black_cells())
    digest = hashlib.sha256(str(black).encode()).hexdigest()[:8]
    return f"Grid{puzzle.n}{digest}"


def _prepare_puzzle(path: Path):
    content = path.read_text(encoding="utf-8", errors="replace")
    _title, _author, puzzle = XdImportAdapter().import_puzzle(content)

    for seq in puzzle.across_words:
        puzzle.set_clue(seq, Word.ACROSS, None)
    for seq in puzzle.down_words:
        puzzle.set_clue(seq, Word.DOWN, None)

    for r in range(1, puzzle.n + 1):
        for c in range(1, puzzle.n + 1):
            if not puzzle.is_black_cell(r, c):
                puzzle.set_cell(r, c, " ")

    puzzle.last_mode = "grid"
    return puzzle


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--db", required=True, help="Path to the SQLite database file")
    parser.add_argument(
        "--user-id",
        type=int,
        default=1,
        metavar="ID",
        help="User ID to store grids under (default: 1)",
    )
    args = parser.parse_args()

    db = SQLitePersistenceAdapter(args.db)
    user_id = args.user_id
    existing = set(db.list_puzzles(user_id))

    ok = 0
    skipped = 0
    errors = 0
    for line in sys.stdin:
        path_str = line.rstrip("\n")
        if not path_str:
            continue
        path = Path(path_str)
        try:
            puzzle = _prepare_puzzle(path)
            name = _grid_name(puzzle)
            if name in existing:
                print(f"skip {name}  ({path})", file=sys.stderr)
                skipped += 1
                continue
            db.save_puzzle(user_id, name, puzzle)
            existing.add(name)
            print(f"ok   {name}  ({path.name})", file=sys.stderr)
            ok += 1
        except Exception as exc:
            print(f"err  {path}: {exc}", file=sys.stderr)
            errors += 1

    print(f"\n{ok} imported, {skipped} skipped, {errors} errors", file=sys.stderr)


if __name__ == "__main__":
    main()
