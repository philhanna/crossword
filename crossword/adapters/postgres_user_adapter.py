# crossword.adapters.postgres_user_adapter
from datetime import datetime

import psycopg2
import psycopg2.extras

from crossword.domain.user import User
from crossword.ports.auth_port import UserPort, UserNotFound


class PostgresUserAdapter(UserPort):

    def __init__(self, conn):
        self._conn = conn
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id              SERIAL PRIMARY KEY,
                    username        TEXT,
                    password        BYTEA,
                    created         TEXT,
                    last_access     TEXT,
                    email           TEXT,
                    confirmed       TEXT,
                    author_name     TEXT,
                    address_line_1  TEXT,
                    address_line_2  TEXT,
                    address_city    TEXT,
                    address_state   TEXT,
                    address_zip     TEXT
                )
            """)
        self._conn.commit()

    def _cursor(self):
        return self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _row_to_user(self, row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            password=bytes(row["password"]) if row["password"] is not None else None,
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
        with self._cursor() as cur:
            cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                raise ValueError("Username already taken")

            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                raise ValueError("Email already registered")

            now = datetime.now().isoformat()
            cur.execute(
                """INSERT INTO users
                   (username, email, password, created, last_access,
                    confirmed, author_name, address_line_1, address_line_2,
                    address_city, address_state, address_zip)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (
                    username, email, psycopg2.Binary(password_hash),
                    now, now, None,
                    profile.get("author_name"),
                    profile.get("address_line_1"),
                    profile.get("address_line_2"),
                    profile.get("address_city"),
                    profile.get("address_state"),
                    profile.get("address_zip"),
                ),
            )
            new_id = cur.fetchone()['id']
        self._conn.commit()
        return self.get_user_by_id(new_id)

    def get_user_by_username(self, username: str) -> User:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
        if row is None:
            raise UserNotFound(f"User not found: {username}")
        return self._row_to_user(row)

    def get_user_by_id(self, user_id: int) -> User:
        with self._cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
        if row is None:
            raise UserNotFound(f"User not found: id={user_id}")
        return self._row_to_user(row)

    def update_last_access(self, user_id: int, timestamp: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                "UPDATE users SET last_access = %s WHERE id = %s",
                (timestamp, user_id),
            )
        self._conn.commit()
