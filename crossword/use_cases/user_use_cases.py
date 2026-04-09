# crossword.use_cases.user_use_cases
from crossword import sha256
from crossword.ports.auth_port import UserPort
from crossword.domain.user import User


class UserUseCases:

    def __init__(self, user_port: UserPort):
        self._user_port = user_port

    def create_user(self, username: str, email: str, password: str, **profile) -> User:
        """Hash password and create user. Propagates ValueError on duplicate username/email."""
        password_hash = sha256(password)
        return self._user_port.create_user(username, email, password_hash, **profile)
