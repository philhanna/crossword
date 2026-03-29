"""
Clear working-copy rows from the puzzles table.

Working copies are rows whose name starts with '__wc__'. They are created
when a puzzle is opened for editing and should be cleaned up on close, but
can accumulate if the app is killed or crashes.

Usage:
    python3 tools/clear_work_files.py [--dry-run]

Options:
    --dry-run   List what would be deleted without making any changes.
"""

import argparse
import sqlite3
import sys

sys.path.insert(0, ".")
from crossword import dbfile


WC_PREFIX = "__wc__"


def source_name(wc_name: str) -> str:
    """Extract the original name from a working-copy name.

    New format: __wc__<name>__<uuid8>  → returns <name>
    Old format: __wc__<uuid8>          → returns '(unknown)'
    """
    body = wc_name[len(WC_PREFIX):]       # strip leading __wc__
    if "__" in body:
        return body.rsplit("__", 1)[0]    # everything before the last __<uuid8>
    return "(unknown)"


def find_work_files(conn: sqlite3.Connection) -> list[str]:
    cur = conn.cursor()
    cur.execute("SELECT puzzlename FROM puzzles WHERE puzzlename LIKE ? ORDER BY puzzlename", (WC_PREFIX + "%",))
    return [row[0] for row in cur.fetchall()]


def delete_work_files(conn: sqlite3.Connection, puzzles: list[str]) -> None:
    cur = conn.cursor()
    for name in puzzles:
        cur.execute("DELETE FROM puzzles WHERE puzzlename = ?", (name,))
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="List work files without deleting them")
    args = parser.parse_args()

    db = dbfile()
    print(f"Database: {db}\n")

    conn = sqlite3.connect(db)
    try:
        puzzles = find_work_files(conn)

        print(f"Work-copy puzzles ({len(puzzles)}):")
        for name in puzzles:
            print(f"  {name}  (source: {source_name(name)})")
        if not puzzles:
            print("  (none)")

        total = len(puzzles)
        if total == 0:
            print("\nNothing to clean up.")
            return

        if args.dry_run:
            print(f"\nDry run — {total} row(s) would be deleted. Pass without --dry-run to delete.")
            return

        answer = input(f"\nDelete {total} row(s)? [Y/n] ").strip().lower()
        if answer not in ("", "y", "yes"):
            print("Cancelled.")
            return

        delete_work_files(conn, puzzles)
        print(f"\nDeleted {total} row(s).")

        print("Vacuuming database...", end=" ", flush=True)
        conn.execute("VACUUM")
        print("done.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
