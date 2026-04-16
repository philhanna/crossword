# crossword.tests.adapters.test_memory_session_store
import pytest
from crossword.adapters.memory_session_store import MemorySessionStore


@pytest.fixture
def store():
    return MemorySessionStore()


class TestMemorySessionStore:
    def test_create_session_returns_string(self, store):
        token = store.create_session({"user_id": 1})
        assert isinstance(token, str)

    def test_create_session_returns_unique_tokens(self, store):
        t1 = store.create_session({"user_id": 1})
        t2 = store.create_session({"user_id": 1})
        assert t1 != t2

    def test_get_session_returns_stored_info(self, store):
        info = {"user_id": 42, "username": "alice"}
        token = store.create_session(info)
        assert store.get_session(token) == info

    def test_get_session_unknown_token_returns_none(self, store):
        assert store.get_session("no-such-token") is None

    def test_delete_session_removes_it(self, store):
        token = store.create_session({"user_id": 1})
        store.delete_session(token)
        assert store.get_session(token) is None

    def test_delete_session_unknown_token_does_not_raise(self, store):
        store.delete_session("no-such-token")
