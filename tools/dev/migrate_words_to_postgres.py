#!/usr/bin/env python3
"""Migrate words from a SQLite database or text file into PostgreSQL."""
import argparse
import os
import sqlite3
import sys


def main():
    parser = argparse.ArgumentParser(description="Migrate words to PostgreSQL")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sqlite", metavar="PATH", help="SQLite database with a 'words' table")
    source.add_argument("--file", metavar="PATH", help="Text file with one word per line (ASCII)")
    parser.add_argument("--url", help="PostgreSQL connection URL (defaults to DATABASE_URL env var)")
    args = parser.parse_args()

    pg_url = args.url or os.environ.get("DATABASE_URL")
    if not pg_url:
        print("Error: provide --url or set DATABASE_URL", file=sys.stderr)
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("Error: psycopg2 not installed. Run: pip install psycopg2-binary", file=sys.stderr)
        sys.exit(1)

    # Load words from source
    if args.sqlite:
        try:
            conn_sq = sqlite3.connect(args.sqlite)
            words = {row[0].lower() for row in conn_sq.execute("SELECT word FROM words")}
            conn_sq.close()
        except sqlite3.Error as e:
            print(f"Error reading SQLite: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            with open(args.file, "r", encoding="ascii") as f:
                words = {line.strip().lower() for line in f if line.strip()}
        except (OSError, UnicodeDecodeError) as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        pg_conn = psycopg2.connect(pg_url)
    except psycopg2.Error as e:
        print(f"Error: cannot connect to PostgreSQL: {e}", file=sys.stderr)
        sys.exit(1)

    cur = pg_conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS words (
            word TEXT UNIQUE NOT NULL
        )
    """)

    count = 0
    for word in words:
        cur.execute(
            "INSERT INTO words (word) VALUES (%s) ON CONFLICT (word) DO NOTHING",
            (word,),
        )
        count += cur.rowcount

    pg_conn.commit()
    pg_conn.close()
    print(f"Migrated {count} words ({len(words)} total in source).")


if __name__ == "__main__":
    main()
