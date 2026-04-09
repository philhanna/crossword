# crossword.ports.auth_port
from abc import ABC, abstractmethod
from crossword.domain.user import User


class AuthError(Exception):
    """Raised by auth use cases on bad credentials."""


class UserNotFound(Exception):
    """Raised by adapter when a user lookup finds nothing."""


class UserPort(ABC):

    @abstractmethod
    def create_user(self, username: str, email: str, password_hash: bytes, **profile) -> User:
        ...

    @abstractmethod
    def get_user_by_username(self, username: str) -> User:
        """Raises UserNotFound if not found."""
        ...

    @abstractmethod
    def get_user_by_id(self, user_id: int) -> User:
        """Raises UserNotFound if not found."""
        ...

    @abstractmethod
    def update_last_access(self, user_id: int, timestamp: str) -> None:
        ...
