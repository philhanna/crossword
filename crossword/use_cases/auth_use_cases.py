# crossword.use_cases.auth_use_cases
from datetime import datetime

from crossword import sha256
from crossword.ports.auth_port import AuthError, UserNotFound, UserPort
from crossword.adapters.memory_session_store import MemorySessionStore


class AuthUseCases:

    def __init__(self, user_port: UserPort, session_store: MemorySessionStore):
        self._user_port = user_port
        self._session_store = session_store

    def login(self, username: str, password: str):
        """Verify credentials and return (User, token). Raises AuthError on failure."""
        try:
            user = self._user_port.get_user_by_username(username)
        except UserNotFound:
            raise AuthError("Invalid username or password")

        if sha256(password) != bytes(user.password):
            raise AuthError("Invalid username or password")

        self._user_port.update_last_access(user.id, datetime.now().isoformat())
        token = self._session_store.create_session({"id": user.id, "username": user.username})
        return user, token

    def logout(self, token: str) -> None:
        self._session_store.delete_session(token)

    def get_current_user(self, token: str) -> dict | None:
        return self._session_store.get_session(token)
