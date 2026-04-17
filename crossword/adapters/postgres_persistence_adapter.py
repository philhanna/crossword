# crossword.adapters.postgres_persistence_adapter
from datetime import datetime

import psycopg2
import psycopg2.extras

from crossword import Puzzle
from crossword.ports.persistence_port import PersistencePort, PersistenceError


class PostgresPersistenceAdapter(PersistencePort):

    def __init__(self, conn):
        self.conn = conn
        self.init_schema()

    def init_schema(self) -> None:
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS puzzles (
                        id          SERIAL PRIMARY KEY,
                        userid      INTEGER NOT NULL,
                        puzzlename  TEXT NOT NULL,
                        created     TEXT NOT NULL,
                        modified    TEXT NOT NULL,
                        last_mode   TEXT NOT NULL DEFAULT 'puzzle'
                                        CHECK (last_mode IN ('grid', 'puzzle')),
                        jsonstr     TEXT NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE UNIQUE INDEX IF NOT EXISTS idx_puzzles_userid_puzzlename
                    ON puzzles (userid, puzzlename)
                """)
            self.conn.commit()
        except psycopg2.Error as e:
            raise PersistenceError(f"Failed to initialize schema: {e}")

    def _cursor(self):
        return self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def save_puzzle(self, user_id: int, name: str, puzzle: Puzzle) -> None:
        try:
            jsonstr = puzzle.to_json()
            now = datetime.now().isoformat()
            last_mode = getattr(puzzle, "last_mode", "puzzle")
            with self._cursor() as cur:
                cur.execute(
                    "SELECT id FROM puzzles WHERE userid = %s AND puzzlename = %s",
                    (user_id, name)
                )
                existing = cur.fetchone()
                if existing:
                    cur.execute(
                        """UPDATE puzzles
                           SET jsonstr = %s, modified = %s, last_mode = %s
                           WHERE userid = %s AND puzzlename = %s""",
                        (jsonstr, now, last_mode, user_id, name)
                    )
                else:
                    cur.execute(
                        """INSERT INTO puzzles (userid, puzzlename, created, modified, last_mode, jsonstr)
                           VALUES (%s, %s, %s, %s, %s, %s)""",
                        (user_id, name, now, now, last_mode, jsonstr)
                    )
            self.conn.commit()
        except psycopg2.Error as e:
            raise PersistenceError(f"Failed to save puzzle: {e}")

    def load_puzzle(self, user_id: int, name: str) -> Puzzle:
        try:
            with self._cursor() as cur:
                cur.execute(
                    "SELECT jsonstr, last_mode FROM puzzles WHERE userid = %s AND puzzlename = %s",
                    (user_id, name)
                )
                row = cur.fetchone()
            if not row:
                raise PersistenceError(f"Puzzle '{name}' not found for user {user_id}")
            puzzle = Puzzle.from_json(row['jsonstr'])
            if row['last_mode']:
                puzzle.last_mode = row['last_mode']
            return puzzle
        except PersistenceError:
            raise
        except psycopg2.Error as e:
            raise PersistenceError(f"Failed to load puzzle: {e}")
        except Exception as e:
            raise PersistenceError(f"Failed to deserialize puzzle: {e}")

    def delete_puzzle(self, user_id: int, name: str) -> None:
        try:
            with self._cursor() as cur:
                cur.execute(
                    "DELETE FROM puzzles WHERE userid = %s AND puzzlename = %s",
                    (user_id, name)
                )
                if cur.rowcount == 0:
                    raise PersistenceError(f"Puzzle '{name}' not found for user {user_id}")
            self.conn.commit()
        except PersistenceError:
            raise
        except psycopg2.Error as e:
            raise PersistenceError(f"Failed to delete puzzle: {e}")

    def list_puzzles(self, user_id: int) -> list[str]:
        try:
            with self._cursor() as cur:
                cur.execute(
                    """SELECT puzzlename FROM puzzles
                       WHERE userid = %s
                       ORDER BY modified DESC""",
                    (user_id,)
                )
                rows = cur.fetchall()
            return [row['puzzlename'] for row in rows if row['puzzlename'] is not None]
        except psycopg2.Error as e:
            raise PersistenceError(f"Failed to list puzzles: {e}")

    def close(self) -> None:
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

    def __del__(self):
        self.close()
