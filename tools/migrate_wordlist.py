"""
Migrate word list from the puzzle database to a dedicated words database.

Reads the `words` table from the puzzle database and writes it to a new
`words.db` file.  Run this once when separating the word list from the
puzzle database.

Usage:
    python3 tools/migrate_wordlist.py [SRC_DB [DEST_DB]]

    SRC_DB   Path to existing puzzle database (default: from ~/.config/crossword/config.yaml)
    DEST_DB  Path to write word database (default: words.db next to SRC_DB)

Example:
    python3 tools/migrate_wordlist.py ~/.crossword/samples.db ~/.crossword/words.db
"""

import os
import sqlite3
import sys


WORDS_SCHEMA = """
CREATE TABLE IF NOT EXISTS words (
    word  TEXT UNIQUE NOT NULL
);
"""


def resolve_src_db(arg):
    if arg:
        return arg
    # Fall back to config file
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from crossword import init_config
        config = init_config()
        dbfile = config.get("dbfile")
        if not dbfile:
            raise ValueError("config has no 'dbfile' key")
        return dbfile
    except Exception as e:
        print(f"error: could not determine source database: {e}", file=sys.stderr)
        print("Usage: python3 tools/migrate_wordlist.py [SRC_DB [DEST_DB]]", file=sys.stderr)
        sys.exit(1)


def resolve_dest_db(arg, src_db):
    if arg:
        return arg
    return os.path.join(os.path.dirname(os.path.abspath(src_db)), "words.db")


def migrate(src_db, dest_db):
    if not os.path.exists(src_db):
        print(f"error: source database not found: {src_db}", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(dest_db):
        print(f"error: destination already exists: {dest_db}", file=sys.stderr)
        print("Remove it first if you want to re-migrate.", file=sys.stderr)
        sys.exit(1)

    # Read words from source
    src_conn = sqlite3.connect(src_db)
    try:
        rows = src_conn.execute("SELECT word FROM words ORDER BY word").fetchall()
    except sqlite3.OperationalError as e:
        print(f"error: could not read words from {src_db}: {e}", file=sys.stderr)
        src_conn.close()
        sys.exit(1)
    src_conn.close()

    # Write to destination
    dest_conn = sqlite3.connect(dest_db)
    dest_conn.execute(WORDS_SCHEMA)
    dest_conn.executemany("INSERT INTO words (word) VALUES (?)", rows)
    dest_conn.commit()
    dest_conn.close()

    print(f"migrated {len(rows)} words")
    print(f"  from: {src_db}")
    print(f"  to:   {dest_db}")
    print()
    print("Next step: add 'word_dbfile' to ~/.config/crossword/config.yaml pointing to the new file.")


if __name__ == "__main__":
    args = sys.argv[1:]
    src  = resolve_src_db(args[0] if len(args) > 0 else None)
    dest = resolve_dest_db(args[1] if len(args) > 1 else None, src)
    migrate(src, dest)
