# crossword.tests.adapters.test_sqlite_user_adapter
import sqlite3
import pytest

from crossword.adapters.sqlite_user_adapter import SQLiteUserAdapter
from crossword.ports.auth_port import UserNotFound
from crossword import sha256

USERS_DDL = """
CREATE TABLE users (
    id              INTEGER PRIMARY KEY,
    username        TEXT,
    password        BLOB,
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
"""


@pytest.fixture
def adapter():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(USERS_DDL)
    conn.commit()
    return SQLiteUserAdapter(conn)


class TestSQLiteUserAdapter:

    def test_create_user_returns_user_with_id(self, adapter):
        user = adapter.create_user("alice", "alice@example.com", sha256("secret"))
        assert user.id is not None
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    def test_create_user_duplicate_username_raises_value_error(self, adapter):
        adapter.create_user("alice", "alice@example.com", sha256("secret"))
        with pytest.raises(ValueError, match="Username already taken"):
            adapter.create_user("alice", "other@example.com", sha256("secret"))

    def test_create_user_duplicate_email_raises_value_error(self, adapter):
        adapter.create_user("alice", "alice@example.com", sha256("secret"))
        with pytest.raises(ValueError, match="Email already registered"):
            adapter.create_user("bob", "alice@example.com", sha256("secret"))

    def test_get_user_by_username_success(self, adapter):
        adapter.create_user("alice", "alice@example.com", sha256("secret"))
        user = adapter.get_user_by_username("alice")
        assert user.username == "alice"

    def test_get_user_by_username_not_found_raises(self, adapter):
        with pytest.raises(UserNotFound):
            adapter.get_user_by_username("nobody")

    def test_get_user_by_id_success(self, adapter):
        created = adapter.create_user("alice", "alice@example.com", sha256("secret"))
        user = adapter.get_user_by_id(created.id)
        assert user.id == created.id
        assert user.username == "alice"

    def test_update_last_access(self, adapter):
        user = adapter.create_user("alice", "alice@example.com", sha256("secret"))
        adapter.update_last_access(user.id, "2026-01-01T00:00:00")
        updated = adapter.get_user_by_id(user.id)
        assert updated.last_access == "2026-01-01T00:00:00"
