# crossword.adapters.sqlite_user_adapter
import sqlite3
from datetime import datetime

from crossword.domain.user import User
from crossword.ports.auth_port import UserPort, UserNotFound


class SQLiteUserAdapter(UserPort):
    """SQLite implementation of UserPort. Shares connection with SQLitePersistenceAdapter."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def _row_to_user(self, row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password=row["password"],
            email=row["email"],
            created=row["created"],
            last_access=row["last_access"],
            confirmed=row["confirmed"],
            author_name=row["author_name"],
            address_line_1=row["address_line_1"],
            address_line_2=row["address_line_2"],
            address_city=row["address_city"],
            address_state=row["address_state"],
            address_zip=row["address_zip"],
        )

    def create_user(self, username: str, email: str, password_hash: bytes, **profile) -> User:
        cursor = self._conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            raise ValueError("Username already taken")

        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            raise ValueError("Email already registered")

        now = datetime.now().isoformat()
        cursor.execute(
            """INSERT INTO users
               (username, email, password, created, last_access,
                confirmed, author_name, address_line_1, address_line_2,
                address_city, address_state, address_zip)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                username,
                email,
                password_hash,
                now,
                now,
                None,
                profile.get("author_name"),
                profile.get("address_line_1"),
                profile.get("address_line_2"),
                profile.get("address_city"),
                profile.get("address_state"),
                profile.get("address_zip"),
            ),
        )
        self._conn.commit()
        user_id = cursor.lastrowid
        return self.get_user_by_id(user_id)

    def get_user_by_username(self, username: str) -> User:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row is None:
            raise UserNotFound(f"User not found: {username}")
        return self._row_to_user(row)

    def get_user_by_id(self, user_id: int) -> User:
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            raise UserNotFound(f"User not found: id={user_id}")
        return self._row_to_user(row)

    def update_last_access(self, user_id: int, timestamp: str) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE users SET last_access = ? WHERE id = ?",
            (timestamp, user_id),
        )
        self._conn.commit()
