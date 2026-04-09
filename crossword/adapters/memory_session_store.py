# crossword.adapters.memory_session_store
import uuid


class MemorySessionStore:
    """In-memory session store. Sessions are lost on server restart."""

    def __init__(self):
        self._sessions: dict[str, dict] = {}

    def create_session(self, user_info: dict) -> str:
        token = str(uuid.uuid4())
        self._sessions[token] = user_info
        return token

    def get_session(self, token: str) -> dict | None:
        return self._sessions.get(token)

    def delete_session(self, token: str) -> None:
        self._sessions.pop(token, None)
