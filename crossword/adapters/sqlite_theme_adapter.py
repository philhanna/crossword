import json
import sqlite3

from crossword.domain.theme import Theme
from crossword.ports.theme_persistence_port import ThemePersistencePort


class SQLiteThemeAdapter(ThemePersistencePort):
    """ThemePersistencePort backed by the crossword SQLite database."""

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS themes (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        TEXT    NOT NULL,
                title          TEXT    NOT NULL,
                word_lengths   TEXT    NOT NULL,
                selected_words TEXT    NOT NULL
            )
        """)
        self._conn.commit()

    def _row_to_theme(self, row) -> Theme:
        return Theme(
            id=row["id"],
            title=row["title"],
            word_lengths=json.loads(row["word_lengths"]),
            selected_words=json.loads(row["selected_words"]),
        )

    def create(self, user_id, title: str, word_lengths: list[int]) -> Theme:
        cur = self._conn.execute(
            "INSERT INTO themes (user_id, title, word_lengths, selected_words)"
            " VALUES (?, ?, ?, ?)",
            (str(user_id), title, json.dumps(word_lengths), json.dumps([])),
        )
        self._conn.commit()
        return self.get(user_id, cur.lastrowid)

    def get(self, user_id, theme_id: int) -> Theme | None:
        row = self._conn.execute(
            "SELECT * FROM themes WHERE id = ? AND user_id = ?",
            (theme_id, str(user_id)),
        ).fetchone()
        return self._row_to_theme(row) if row else None

    def list_all(self, user_id) -> list[Theme]:
        rows = self._conn.execute(
            "SELECT * FROM themes WHERE user_id = ? ORDER BY id",
            (str(user_id),),
        ).fetchall()
        return [self._row_to_theme(r) for r in rows]

    def update(
        self,
        user_id,
        theme_id: int,
        *,
        title: str | None = None,
        word_lengths: list[int] | None = None,
    ) -> Theme | None:
        theme = self.get(user_id, theme_id)
        if theme is None:
            return None
        new_title = title if title is not None else theme.title
        new_lengths = word_lengths if word_lengths is not None else theme.word_lengths
        self._conn.execute(
            "UPDATE themes SET title = ?, word_lengths = ? WHERE id = ? AND user_id = ?",
            (new_title, json.dumps(new_lengths), theme_id, str(user_id)),
        )
        self._conn.commit()
        return self.get(user_id, theme_id)

    def delete(self, user_id, theme_id: int) -> bool:
        cur = self._conn.execute(
            "DELETE FROM themes WHERE id = ? AND user_id = ?",
            (theme_id, str(user_id)),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def add_word(self, user_id, theme_id: int, words: list[str]) -> Theme | None:
        theme = self.get(user_id, theme_id)
        if theme is None:
            return None
        existing = set(theme.selected_words)
        updated = theme.selected_words[:]
        for w in words:
            if w not in existing:
                updated.append(w)
                existing.add(w)
        self._conn.execute(
            "UPDATE themes SET selected_words = ? WHERE id = ? AND user_id = ?",
            (json.dumps(updated), theme_id, str(user_id)),
        )
        self._conn.commit()
        return self.get(user_id, theme_id)

    def remove_word(self, user_id, theme_id: int, word: str) -> Theme | None:
        theme = self.get(user_id, theme_id)
        if theme is None:
            return None
        updated = [w for w in theme.selected_words if w != word]
        self._conn.execute(
            "UPDATE themes SET selected_words = ? WHERE id = ? AND user_id = ?",
            (json.dumps(updated), theme_id, str(user_id)),
        )
        self._conn.commit()
        return self.get(user_id, theme_id)
