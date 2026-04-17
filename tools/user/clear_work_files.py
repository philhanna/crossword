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
import sys

sys.path.insert(0, ".")
from crossword import init_config


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


def find_work_files(conn, placeholder: str) -> list[str]:
    cur = conn.cursor()
    cur.execute(
        f"SELECT puzzlename FROM puzzles WHERE puzzlename LIKE {placeholder} ORDER BY puzzlename",
        (WC_PREFIX + "%",)
    )
    return [row[0] for row in cur.fetchall()]


def delete_work_files(conn, placeholder: str, puzzles: list[str]) -> None:
    cur = conn.cursor()
    for name in puzzles:
        cur.execute(f"DELETE FROM puzzles WHERE puzzlename = {placeholder}", (name,))
    conn.commit()


def connect(config: dict):
    database_url = config.get("database_url")
    if database_url:
        import psycopg2
        return psycopg2.connect(database_url), "%s", str(database_url)
    else:
        import sqlite3
        db = config["dbfile"]
        return sqlite3.connect(db), "?", db


def vacuum(conn, is_postgres: bool) -> None:
    if is_postgres:
        old_level = conn.isolation_level
        conn.set_isolation_level(0)
        conn.cursor().execute("VACUUM")
        conn.set_isolation_level(old_level)
    else:
        conn.execute("VACUUM")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="List work files without deleting them")
    args = parser.parse_args()

    config = init_config()
    conn, placeholder, db_label = connect(config)
    is_postgres = config.get("database_url") is not None

    print(f"Database: {db_label}\n")

    try:
        puzzles = find_work_files(conn, placeholder)

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

        delete_work_files(conn, placeholder, puzzles)
        print(f"\nDeleted {total} row(s).")

        print("Vacuuming database...", end=" ", flush=True)
        vacuum(conn, is_postgres)
        print("done.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
