#!/usr/bin/env python3
"""Copy all rows from a SQLite database into a PostgreSQL database."""
import argparse
import os
import sqlite3
import sys


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite data to PostgreSQL")
    parser.add_argument("--sqlite", required=True, help="Path to SQLite database file")
    parser.add_argument("--url", help="PostgreSQL connection URL (defaults to DATABASE_URL env var)")
    args = parser.parse_args()

    pg_url = args.url or os.environ.get("DATABASE_URL")
    if not pg_url:
        print("Error: provide --url or set DATABASE_URL", file=sys.stderr)
        sys.exit(1)

    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        print("Error: psycopg2 not installed. Run: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    sqlite_conn = sqlite3.connect(args.sqlite)
    sqlite_conn.row_factory = sqlite3.Row

    try:
        pg_conn = psycopg2.connect(pg_url)
    except psycopg2.Error as e:
        print(f"Error: cannot connect to PostgreSQL: {e}", file=sys.stderr)
        sys.exit(1)

    from crossword.adapters.postgres_persistence_adapter import PostgresPersistenceAdapter
    from crossword.adapters.postgres_user_adapter import PostgresUserAdapter

    _p = PostgresPersistenceAdapter(pg_conn)
    _u = PostgresUserAdapter(pg_conn)

    pg_cur = pg_conn.cursor()

    # Migrate users
    sqlite_cur = sqlite_conn.execute("SELECT * FROM users")
    user_rows = sqlite_cur.fetchall()
    user_count = 0
    for row in user_rows:
        password = bytes(row["password"]) if row["password"] is not None else None
        pg_cur.execute(
            """INSERT INTO users
               (id, username, password, created, last_access, email, confirmed,
                author_name, address_line_1, address_line_2,
                address_city, address_state, address_zip)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (id) DO NOTHING""",
            (
                row["id"], row["username"],
                psycopg2.Binary(password) if password is not None else None,
                row["created"], row["last_access"], row["email"], row["confirmed"],
                row["author_name"], row["address_line_1"], row["address_line_2"],
                row["address_city"], row["address_state"], row["address_zip"],
            ),
        )
        user_count += pg_cur.rowcount

    # Migrate puzzles
    sqlite_cur = sqlite_conn.execute("SELECT * FROM puzzles")
    puzzle_rows = sqlite_cur.fetchall()
    puzzle_count = 0
    for row in puzzle_rows:
        last_mode = row["last_mode"] if "last_mode" in row.keys() else "puzzle"
        pg_cur.execute(
            """INSERT INTO puzzles
               (userid, puzzlename, created, modified, last_mode, jsonstr)
               VALUES (%s, %s, %s, %s, %s, %s)
               ON CONFLICT (userid, puzzlename) DO NOTHING""",
            (row["userid"], row["puzzlename"], row["created"],
             row["modified"], last_mode, row["jsonstr"]),
        )
        puzzle_count += pg_cur.rowcount

    pg_conn.commit()
    pg_conn.close()
    sqlite_conn.close()

    print(f"Migrated {user_count} users and {puzzle_count} puzzles.")


if __name__ == "__main__":
    main()
