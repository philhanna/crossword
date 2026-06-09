"""
SQLitePersistenceAdapter - SQLite implementation of the Persistence Port.

Uses sqlite3 directly (no ORM). The persisted construction unit is a puzzle.
"""

import sqlite3
from datetime import datetime
from crossword import Puzzle
from crossword.ports.persistence_port import PersistencePort, PersistenceError


class SQLitePersistenceAdapter(PersistencePort):
    """
    SQLite adapter for persistent storage of unified puzzles.

    Connects to a SQLite database and implements CRUD operations.
    All operations are synchronous and single-threaded.
    """

    def __init__(self, db_path: str):
        """
        Initialize the adapter with a database path.

        Args:
            db_path: Path to SQLite database file (or ":memory:" for in-memory DB)

        Raises:
            PersistenceError: If database connection fails
        """
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            self._ensure_schema_compatibility()
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to connect to database {db_path}: {e}")

    def _table_exists(self, table_name: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table_name,),
        )
        return cursor.fetchone() is not None

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        rows = cursor.fetchall()
        return any(row["name"] == column_name for row in rows)

    def _ensure_schema_compatibility(self) -> None:
        """
        Bring the SQLite schema forward to the puzzle-centric layout expected
        by the merged editor work.
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS puzzles (
                    id              INTEGER PRIMARY KEY,
                    userid          INTEGER NOT NULL,
                    puzzlename      TEXT NOT NULL,
                    created         TEXT NOT NULL,
                    modified        TEXT NOT NULL,
                    last_mode       TEXT NOT NULL DEFAULT 'puzzle'
                                        CHECK (last_mode IN ('grid', 'puzzle')),
                    state           TEXT NOT NULL DEFAULT 'draft'
                                        CHECK (state IN (
                                            'draft','filled','finished',
                                            'submitted','published','archived')),
                    jsonstr         TEXT NOT NULL,
                    publisher       TEXT,
                    date_submitted  TEXT,
                    date_published  TEXT
                )
            """)

            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_puzzles_userid_puzzlename
                ON puzzles(userid, puzzlename)
            """)

            self.conn.commit()
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to ensure schema compatibility: {e}")

    def init_schema(self) -> None:
        """
        Initialize the database schema (for testing with :memory: databases).

        On production databases, the schema should already exist.

        Raises:
            PersistenceError: If schema creation fails
        """
        try:
            self._ensure_schema_compatibility()
        except PersistenceError:
            raise
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to initialize schema: {e}")

    # ======================================================================
    # Puzzle Operations
    # ======================================================================

    def save_puzzle(self, user_id: int, name: str, puzzle: Puzzle) -> None:
        """Save a puzzle to the database."""
        try:
            jsonstr = puzzle.to_json()
            now = datetime.now().isoformat()
            last_mode = getattr(puzzle, "last_mode", "puzzle")
            cursor = self.conn.cursor()

            # Check if puzzle already exists
            cursor.execute(
                "SELECT id FROM puzzles WHERE userid = ? AND puzzlename = ?",
                (user_id, name),
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing puzzle
                cursor.execute(
                    """UPDATE puzzles
                       SET jsonstr = ?, modified = ?, last_mode = ?
                       WHERE userid = ? AND puzzlename = ?""",
                    (jsonstr, now, last_mode, user_id, name),
                )
            else:
                # Insert new puzzle
                cursor.execute(
                    """INSERT INTO puzzles (userid, puzzlename, created, modified, last_mode, jsonstr)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, name, now, now, last_mode, jsonstr),
                )

            self.conn.commit()
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to save puzzle: {e}")

    def load_puzzle(self, user_id: int, name: str) -> Puzzle:
        """Load a puzzle from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT jsonstr, last_mode FROM puzzles WHERE userid = ? AND puzzlename = ?",
                (user_id, name),
            )
            row = cursor.fetchone()

            if not row:
                raise PersistenceError(f"Puzzle '{name}' not found for user {user_id}")

            puzzle = Puzzle.from_json(row["jsonstr"])
            row_last_mode = row["last_mode"] if "last_mode" in row.keys() else None
            if row_last_mode:
                puzzle.last_mode = row_last_mode
            return puzzle
        except PersistenceError:
            raise
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to load puzzle: {e}")
        except Exception as e:
            raise PersistenceError(f"Failed to deserialize puzzle: {e}")

    def delete_puzzle(self, user_id: int, name: str) -> None:
        """Delete a puzzle from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM puzzles WHERE userid = ? AND puzzlename = ?",
                (user_id, name),
            )

            if cursor.rowcount == 0:
                raise PersistenceError(f"Puzzle '{name}' not found for user {user_id}")

            self.conn.commit()
        except PersistenceError:
            raise
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to delete puzzle: {e}")

    def set_puzzle_state(self, user_id: int, name: str, state: str, *,
                         publisher: str | None = None,
                         date_submitted: str | None = None,
                         date_published: str | None = None) -> None:
        """Overwrite the puzzle's state columns in place."""
        try:
            now = datetime.now().isoformat()
            cursor = self.conn.cursor()
            cursor.execute(
                """UPDATE puzzles
                   SET state = ?, publisher = ?, date_submitted = ?,
                       date_published = ?, modified = ?
                   WHERE userid = ? AND puzzlename = ?""",
                (state, publisher, date_submitted, date_published, now, user_id, name),
            )

            if cursor.rowcount == 0:
                raise PersistenceError(f"Puzzle '{name}' not found for user {user_id}")

            self.conn.commit()
        except PersistenceError:
            raise
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to set puzzle state: {e}")

    def get_puzzle_state(self, user_id: int, name: str) -> dict | None:
        """Return the puzzle's current state columns as a dict, or None if absent."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT state, publisher, date_submitted, date_published
                   FROM puzzles WHERE userid = ? AND puzzlename = ?""",
                (user_id, name),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return {
                "state": row["state"],
                "publisher": row["publisher"],
                "date_submitted": row["date_submitted"],
                "date_published": row["date_published"],
            }
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to get puzzle state: {e}")

    def rename_puzzle(self, user_id: int, old_name: str, new_name: str) -> None:
        """Rename in place, preserving id and all columns (state included)."""
        try:
            now = datetime.now().isoformat()
            cursor = self.conn.cursor()
            cursor.execute(
                """UPDATE puzzles SET puzzlename = ?, modified = ?
                   WHERE userid = ? AND puzzlename = ?""",
                (new_name, now, user_id, old_name),
            )

            if cursor.rowcount == 0:
                raise PersistenceError(f"Puzzle '{old_name}' not found for user {user_id}")

            self.conn.commit()
        except PersistenceError:
            raise
        except sqlite3.IntegrityError:
            raise PersistenceError(f"Puzzle '{new_name}' already exists for user {user_id}")
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to rename puzzle: {e}")

    def list_puzzles(self, user_id: int, state: str | None = None) -> list[str]:
        """Get list of puzzle names for a user, sorted by most recently modified."""
        try:
            cursor = self.conn.cursor()
            if state is None:
                cursor.execute(
                    """SELECT puzzlename FROM puzzles
                       WHERE userid = ?
                       ORDER BY modified DESC""",
                    (user_id,),
                )
            else:
                cursor.execute(
                    """SELECT puzzlename FROM puzzles
                       WHERE userid = ? AND state = ?
                       ORDER BY modified DESC""",
                    (user_id, state),
                )
            rows = cursor.fetchall()
            return [row["puzzlename"] for row in rows if row["puzzlename"] is not None]
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to list puzzles: {e}")

    def list_puzzle_summaries(self, user_id: int) -> list[dict]:
        """Return summary rows for the user's real puzzles, most recent first."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT puzzlename, modified, state, publisher,
                          date_submitted, date_published
                   FROM puzzles
                   WHERE userid = ?
                     AND puzzlename IS NOT NULL
                     AND puzzlename NOT LIKE '@_@_wc@_@_%' ESCAPE '@'
                     AND puzzlename NOT LIKE '@_@_new@_@_%' ESCAPE '@'
                   ORDER BY modified DESC""",
                (user_id,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "name": row["puzzlename"],
                    "modified": row["modified"],
                    "state": row["state"],
                    "publisher": row["publisher"],
                    "date_submitted": row["date_submitted"],
                    "date_published": row["date_published"],
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to list puzzle summaries: {e}")

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self, "conn") and self.conn:
            self.conn.close()

    def __del__(self):
        """Ensure connection is closed on deletion."""
        self.close()
