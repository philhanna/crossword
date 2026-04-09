# crossword.tests.test_user_use_cases
import pytest
from unittest.mock import MagicMock

from crossword import sha256
from crossword.use_cases.user_use_cases import UserUseCases


@pytest.fixture
def user_port():
    return MagicMock()


@pytest.fixture
def user_uc(user_port):
    return UserUseCases(user_port)


class TestUserUseCases:

    def test_create_user_hashes_password(self, user_uc, user_port):
        user_port.create_user.return_value = MagicMock()
        user_uc.create_user("alice", "alice@example.com", "secret")
        args = user_port.create_user.call_args[0]
        assert args[2] == sha256("secret")

    def test_create_user_propagates_duplicate_username_error(self, user_uc, user_port):
        user_port.create_user.side_effect = ValueError("Username already taken")
        with pytest.raises(ValueError, match="Username already taken"):
            user_uc.create_user("alice", "alice@example.com", "secret")

    def test_create_user_propagates_duplicate_email_error(self, user_uc, user_port):
        user_port.create_user.side_effect = ValueError("Email already registered")
        with pytest.raises(ValueError, match="Email already registered"):
            user_uc.create_user("alice", "alice@example.com", "secret")
