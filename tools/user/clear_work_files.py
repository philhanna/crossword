"""
Clear working-copy and new-puzzle rows from the puzzles table.

Working copies are rows whose name starts with '__wc__'. They are created
when a puzzle is opened for editing and should be cleaned up on close, but
can accumulate if the app is killed or crashes.

New-puzzle rows start with '__new__' and are similarly temporary.

Usage:
    python3 tools/clear_work_files.py [--dry-run]

Options:
    --dry-run   List what would be deleted without making any changes.
"""

import argparse
import sys

sys.path.insert(0, ".")
from crossword import init_config


WC_PREFIX = "__wc__"
NEW_PREFIX = "__new__"
TEMP_PREFIXES = (WC_PREFIX, NEW_PREFIX)


def source_name(wc_name: str) -> str:
    """Extract the original name from a working-copy name.

    New format: __wc__<name>__<uuid8>  → returns <name>
    Old format: __wc__<uuid8>          → returns '(unknown)'
    __new__ rows → returns '(new)'
    """
    if wc_name.startswith(NEW_PREFIX):
        return "(new)"
    body = wc_name[len(WC_PREFIX):]       # strip leading __wc__
    if "__" in body:
        return body.rsplit("__", 1)[0]    # everything before the last __<uuid8>
    return "(unknown)"


def find_work_files(conn) -> list[tuple[str, str]]:
    """Return (name, modified) pairs for work-copy and new-puzzle rows ordered by name."""
    cur = conn.cursor()
    cur.execute(
        "SELECT puzzlename, modified FROM puzzles"
        " WHERE puzzlename LIKE ? OR puzzlename LIKE ?"
        " ORDER BY puzzlename",
        (WC_PREFIX + "%", NEW_PREFIX + "%")
    )
    return [(row[0], row[1] or "") for row in cur.fetchall()]


def delete_work_files(conn, puzzles: list[tuple[str, str]]) -> None:
    """Delete the given work-copy puzzle rows and commit the transaction."""
    cur = conn.cursor()
    for name, _ in puzzles:
        cur.execute("DELETE FROM puzzles WHERE puzzlename = ?", (name,))
    conn.commit()


def connect(config: dict):
    """Connect to the SQLite database and return the connection."""
    import sqlite3
    db = config["dbfile"]
    return sqlite3.connect(db), db


def main() -> None:
    """List and optionally delete stale work-copy puzzle rows from the database."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="List work files without deleting them")
    args = parser.parse_args()

    config = init_config()
    conn, db_label = connect(config)

    print(f"Database: {db_label}\n")

    try:
        puzzles = find_work_files(conn)

        print(f"Temporary puzzles ({len(puzzles)}):")
        for name, modified in puzzles:
            print(f"  {name}  (source: {source_name(name)}, modified: {modified})")
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
