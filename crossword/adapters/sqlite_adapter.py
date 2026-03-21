"""
SQLiteAdapter - SQLite implementation of the Persistence Port

Uses sqlite3 directly (no ORM). Assumes the database schema is already created.
"""

import sqlite3
from datetime import datetime
from crossword import Grid, Puzzle
from crossword.ports.persistence import PersistencePort, PersistenceError


class SQLiteAdapter(PersistencePort):
    """
    SQLite adapter for persistent storage of grids and puzzles.

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
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to connect to database {db_path}: {e}")

    def init_schema(self) -> None:
        """
        Initialize the database schema (for testing with :memory: databases).

        On production databases, the schema should already exist.

        Raises:
            PersistenceError: If schema creation fails
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS grids (
                    id              INTEGER PRIMARY KEY,
                    userid          INTEGER,
                    gridname        TEXT,
                    created         TEXT,
                    modified        TEXT,
                    jsonstr         TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS puzzles (
                    id              INTEGER PRIMARY KEY,
                    userid          INTEGER,
                    puzzlename      TEXT,
                    created         TEXT,
                    modified        TEXT,
                    jsonstr         TEXT
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to initialize schema: {e}")

    # ======================================================================
    # Grid Operations
    # ======================================================================

    def save_grid(self, user_id: int, name: str, grid: Grid) -> None:
        """Save a grid to the database."""
        try:
            jsonstr = grid.to_json()
            now = datetime.now().isoformat()
            cursor = self.conn.cursor()

            # Check if grid already exists
            cursor.execute(
                "SELECT id FROM grids WHERE userid = ? AND gridname = ?",
                (user_id, name)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing grid
                cursor.execute(
                    """UPDATE grids
                       SET jsonstr = ?, modified = ?
                       WHERE userid = ? AND gridname = ?""",
                    (jsonstr, now, user_id, name)
                )
            else:
                # Insert new grid
                cursor.execute(
                    """INSERT INTO grids (userid, gridname, created, modified, jsonstr)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, name, now, now, jsonstr)
                )

            self.conn.commit()
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to save grid: {e}")

    def load_grid(self, user_id: int, name: str) -> Grid:
        """Load a grid from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT jsonstr FROM grids WHERE userid = ? AND gridname = ?",
                (user_id, name)
            )
            row = cursor.fetchone()

            if not row:
                raise PersistenceError(f"Grid '{name}' not found for user {user_id}")

            return Grid.from_json(row['jsonstr'])
        except PersistenceError:
            raise
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to load grid: {e}")
        except Exception as e:
            raise PersistenceError(f"Failed to deserialize grid: {e}")

    def delete_grid(self, user_id: int, name: str) -> None:
        """Delete a grid from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "DELETE FROM grids WHERE userid = ? AND gridname = ?",
                (user_id, name)
            )

            if cursor.rowcount == 0:
                raise PersistenceError(f"Grid '{name}' not found for user {user_id}")

            self.conn.commit()
        except PersistenceError:
            raise
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to delete grid: {e}")

    def list_grids(self, user_id: int) -> list[str]:
        """Get list of grid names for a user, sorted by most recently modified."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT gridname FROM grids
                   WHERE userid = ?
                   ORDER BY modified DESC""",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [row['gridname'] for row in rows if row['gridname'] is not None]
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to list grids: {e}")

    # ======================================================================
    # Puzzle Operations
    # ======================================================================

    def save_puzzle(self, user_id: int, name: str, puzzle: Puzzle) -> None:
        """Save a puzzle to the database."""
        try:
            jsonstr = puzzle.to_json()
            now = datetime.now().isoformat()
            cursor = self.conn.cursor()

            # Check if puzzle already exists
            cursor.execute(
                "SELECT id FROM puzzles WHERE userid = ? AND puzzlename = ?",
                (user_id, name)
            )
            existing = cursor.fetchone()

            if existing:
                # Update existing puzzle
                cursor.execute(
                    """UPDATE puzzles
                       SET jsonstr = ?, modified = ?
                       WHERE userid = ? AND puzzlename = ?""",
                    (jsonstr, now, user_id, name)
                )
            else:
                # Insert new puzzle
                cursor.execute(
                    """INSERT INTO puzzles (userid, puzzlename, created, modified, jsonstr)
                       VALUES (?, ?, ?, ?, ?)""",
                    (user_id, name, now, now, jsonstr)
                )

            self.conn.commit()
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to save puzzle: {e}")

    def load_puzzle(self, user_id: int, name: str) -> Puzzle:
        """Load a puzzle from the database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT jsonstr FROM puzzles WHERE userid = ? AND puzzlename = ?",
                (user_id, name)
            )
            row = cursor.fetchone()

            if not row:
                raise PersistenceError(f"Puzzle '{name}' not found for user {user_id}")

            return Puzzle.from_json(row['jsonstr'])
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
                (user_id, name)
            )

            if cursor.rowcount == 0:
                raise PersistenceError(f"Puzzle '{name}' not found for user {user_id}")

            self.conn.commit()
        except PersistenceError:
            raise
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to delete puzzle: {e}")

    def list_puzzles(self, user_id: int) -> list[str]:
        """Get list of puzzle names for a user, sorted by most recently modified."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """SELECT puzzlename FROM puzzles
                   WHERE userid = ?
                   ORDER BY modified DESC""",
                (user_id,)
            )
            rows = cursor.fetchall()
            return [row['puzzlename'] for row in rows if row['puzzlename'] is not None]
        except sqlite3.Error as e:
            raise PersistenceError(f"Failed to list puzzles: {e}")

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def __del__(self):
        """Ensure connection is closed on deletion."""
        self.close()
