#!/usr/bin/env python3
"""
CLI tool for creating a crossword user account.

Usage:
    python tools/create_user.py --username <u> --email <e> --password <p>
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="Create a crossword user account")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--email", required=True, help="Email address")
    parser.add_argument("--password", required=True, help="Password (plain text)")
    args = parser.parse_args()

    from crossword import config
    import sqlite3

    dbfile = config.get("dbfile")
    if not dbfile:
        print("Error: dbfile not configured in ~/.config/crossword/config.yaml", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(dbfile)
    conn.row_factory = sqlite3.Row

    from crossword.adapters.sqlite_user_adapter import SQLiteUserAdapter
    from crossword.use_cases.user_use_cases import UserUseCases

    user_adapter = SQLiteUserAdapter(conn)
    user_uc = UserUseCases(user_adapter)

    try:
        user = user_uc.create_user(args.username, args.email, args.password)
        print(f"Created user id={user.id} username={user.username}")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
