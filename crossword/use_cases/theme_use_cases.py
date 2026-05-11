from crossword.domain.theme import Theme
from crossword.ports.theme_persistence_port import ThemePersistencePort
from crossword.adapters.sqlite_grid_adapter import SQLiteGridAdapter


def _require_palindrome(word_lengths: list[int]) -> None:
    if word_lengths != word_lengths[::-1]:
        raise ValueError("word_lengths must be palindromic")


class ThemeUseCases:

    def __init__(
        self,
        theme_repo: ThemePersistencePort,
        grid_adapter: SQLiteGridAdapter,
    ) -> None:
        self.theme_repo = theme_repo
        self.grid_adapter = grid_adapter

    def create_theme(
        self,
        user_id,
        title: str,
        word_lengths: list[int],
        selected_words: list[str] | None = None,
    ) -> Theme:
        _require_palindrome(word_lengths)
        theme = self.theme_repo.create(user_id, title, word_lengths)
        if selected_words:
            theme = self.theme_repo.add_word(user_id, theme.id, selected_words)
        return theme

    def get_theme(self, user_id, theme_id: int) -> Theme | None:
        return self.theme_repo.get(user_id, theme_id)

    def list_themes(self, user_id) -> list[Theme]:
        return self.theme_repo.list_all(user_id)

    def update_theme(
        self,
        user_id,
        theme_id: int,
        *,
        title: str | None = None,
        word_lengths: list[int] | None = None,
    ) -> Theme | None:
        if word_lengths is not None:
            _require_palindrome(word_lengths)
        return self.theme_repo.update(user_id, theme_id, title=title, word_lengths=word_lengths)

    def delete_theme(self, user_id, theme_id: int) -> bool:
        return self.theme_repo.delete(user_id, theme_id)

    def add_words(self, user_id, theme_id: int, words: list[str]) -> Theme | None:
        return self.theme_repo.add_word(user_id, theme_id, words)

    def remove_word(self, user_id, theme_id: int, word: str) -> Theme | None:
        return self.theme_repo.remove_word(user_id, theme_id, word)

    def search_grids(self, user_id, theme_id: int, size: int) -> list[str] | None:
        """Return matching grid filenames, or None if the theme does not exist."""
        theme = self.theme_repo.get(user_id, theme_id)
        if theme is None:
            return None
        return self.grid_adapter.search(theme.word_lengths, size)
