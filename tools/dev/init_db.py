#!/usr/bin/env python3
"""Initialize the PostgreSQL database schema."""
import argparse
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Initialize PostgreSQL schema")
    parser.add_argument("--url", help="PostgreSQL connection URL (defaults to DATABASE_URL env var)")
    args = parser.parse_args()

    url = args.url or os.environ.get("DATABASE_URL")
    if not url:
        print("Error: provide --url or set DATABASE_URL", file=sys.stderr)
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("Error: psycopg2 not installed. Run: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    try:
        conn = psycopg2.connect(url)
    except psycopg2.Error as e:
        print(f"Error: cannot connect to database: {e}", file=sys.stderr)
        sys.exit(1)

    from crossword.adapters.postgres_persistence_adapter import PostgresPersistenceAdapter
    from crossword.adapters.postgres_user_adapter import PostgresUserAdapter

    persistence = PostgresPersistenceAdapter(conn)
    user = PostgresUserAdapter(conn)
    _ = persistence, user  # keep references so __del__ doesn't close conn early

    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS words (
            word TEXT UNIQUE NOT NULL
        )
    """)
    conn.commit()

    conn.close()
    print("Schema initialized successfully.")


if __name__ == "__main__":
    main()
