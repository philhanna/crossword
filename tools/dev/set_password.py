#!/usr/bin/env python3
"""
Dev tool: set a user's password directly in the database.

Usage:
    python tools/dev/set_password.py --id <user_id> --password <plain_text>
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def main():
    parser = argparse.ArgumentParser(description="Set a user's password")
    parser.add_argument("--id", required=True, type=int, help="User ID")
    parser.add_argument("--password", required=True, help="New password (plain text)")
    args = parser.parse_args()

    from crossword import config, sha256
    import sqlite3

    dbfile = config.get("dbfile")
    if not dbfile:
        print("Error: dbfile not configured in ~/.config/crossword/config.yaml", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(dbfile)
    cursor = conn.cursor()

    cursor.execute("SELECT id, username FROM users WHERE id = ?", (args.id,))
    row = cursor.fetchone()
    if row is None:
        print(f"Error: no user with id={args.id}", file=sys.stderr)
        conn.close()
        sys.exit(1)

    cursor.execute("UPDATE users SET password = ? WHERE id = ?", (sha256(args.password), args.id))
    conn.commit()
    conn.close()

    print(f"Password updated for user id={row[0]} username={row[1]}")


if __name__ == "__main__":
    main()
