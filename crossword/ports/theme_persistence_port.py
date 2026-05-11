from abc import ABC, abstractmethod

from crossword.domain.theme import Theme


class ThemePersistencePort(ABC):
    """Abstract persistence interface for Theme objects, scoped by user_id."""

    @abstractmethod
    def create(self, user_id, title: str, word_lengths: list[int]) -> Theme: ...

    @abstractmethod
    def get(self, user_id, theme_id: int) -> Theme | None: ...

    @abstractmethod
    def list_all(self, user_id) -> list[Theme]: ...

    @abstractmethod
    def update(
        self,
        user_id,
        theme_id: int,
        *,
        title: str | None = None,
        word_lengths: list[int] | None = None,
    ) -> Theme | None: ...

    @abstractmethod
    def delete(self, user_id, theme_id: int) -> bool: ...

    @abstractmethod
    def add_word(self, user_id, theme_id: int, words: list[str]) -> Theme | None: ...

    @abstractmethod
    def remove_word(self, user_id, theme_id: int, word: str) -> Theme | None: ...
