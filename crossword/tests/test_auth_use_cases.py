# crossword.tests.test_auth_use_cases
import pytest
from unittest.mock import MagicMock

from crossword import sha256
from crossword.domain.user import User
from crossword.ports.auth_port import AuthError, UserNotFound
from crossword.adapters.memory_session_store import MemorySessionStore
from crossword.use_cases.auth_use_cases import AuthUseCases


def _make_user(username="alice", password="secret"):
    return User(id=1, username=username, password=sha256(password))


@pytest.fixture
def user_port():
    return MagicMock()


@pytest.fixture
def session_store():
    return MemorySessionStore()


@pytest.fixture
def auth_uc(user_port, session_store):
    return AuthUseCases(user_port, session_store)


class TestAuthUseCases:

    def test_login_success(self, auth_uc, user_port):
        user_port.get_user_by_username.return_value = _make_user()
        user, token = auth_uc.login("alice", "secret")
        assert user.username == "alice"
        assert token is not None

    def test_login_wrong_password(self, auth_uc, user_port):
        user_port.get_user_by_username.return_value = _make_user()
        with pytest.raises(AuthError):
            auth_uc.login("alice", "wrong")

    def test_login_unknown_user(self, auth_uc, user_port):
        user_port.get_user_by_username.side_effect = UserNotFound("alice")
        with pytest.raises(AuthError):
            auth_uc.login("alice", "secret")

    def test_logout_removes_session(self, auth_uc, user_port):
        user_port.get_user_by_username.return_value = _make_user()
        _, token = auth_uc.login("alice", "secret")
        auth_uc.logout(token)
        assert auth_uc.get_current_user(token) is None

    def test_get_current_user_valid_token(self, auth_uc, user_port):
        user_port.get_user_by_username.return_value = _make_user()
        _, token = auth_uc.login("alice", "secret")
        session = auth_uc.get_current_user(token)
        assert session["username"] == "alice"

    def test_get_current_user_invalid_token_returns_none(self, auth_uc):
        assert auth_uc.get_current_user("bogus-token") is None
