"""
SQLiteDictionaryAdapter - Word list implementation of the Word List Port

Loads a dictionary into memory and provides word matching via regex patterns.
Words are bucketed by length so that callers who know the target length avoid
scanning the full dictionary.
"""

import re
import sqlite3
from crossword.ports.word_list_port import WordListPort


class SQLiteDictionaryAdapter(WordListPort):
    """
    In-memory word dictionary adapter.

    Loads all words from a source (database or file) into memory for fast regex matching.
    Suitable for moderate dictionary sizes (up to ~100k words).
    """

    def __init__(self):
        """Initialize with empty word list."""
        self._words_by_length: dict[int, list[str]] = {}
        self._match_cache: dict[tuple[str, int | None], list[str]] = {}

    def _build_index(self, words: set[str]) -> None:
        self._words_by_length = {}
        self._match_cache = {}
        for w in words:
            self._words_by_length.setdefault(len(w), []).append(w)

    def load_from_database(self, db_path: str) -> None:
        """
        Load words from a SQLite database.

        Args:
            db_path: Path to SQLite database containing a 'words' table

        Raises:
            Exception: If database connection fails
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM words")
            words = {row[0].lower() for row in cursor.fetchall()}
            conn.close()
        except sqlite3.Error as e:
            raise Exception(f"Failed to load words from database: {e}")
        self._build_index(words)

    def load_from_file(self, file_path: str) -> None:
        """
        Load words from a text file (one word per line).

        Args:
            file_path: Path to text file containing words

        Raises:
            Exception: If file reading fails
        """
        try:
            with open(file_path, "r", encoding="ascii") as f:
                words = {line.strip().lower() for line in f if line.strip()}
        except (OSError, UnicodeDecodeError) as e:
            raise Exception(f"Failed to load words from file: {e}")
        self._build_index(words)

    def get_matches(self, pattern: str, length: int = None) -> list[str]:
        """
        Find all words matching a regex pattern.

        Pattern matching is case-insensitive. The regex syntax is Python's
        standard `re` module syntax.

        Args:
            pattern: Python regex pattern (e.g., "^[A-Z]{5}$" for 5-letter words)
            length:  If provided, only words of this exact length are considered.

        Returns:
            List of matching words (lowercase), or empty list if no matches

        Raises:
            ValueError: If pattern is not a valid regex
        """
        cache_key = (pattern, length)
        if cache_key in self._match_cache:
            return self._match_cache[cache_key]

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        if length is not None:
            candidates = self._words_by_length.get(length, [])
        else:
            candidates = (w for bucket in self._words_by_length.values() for w in bucket)
        result = sorted(word for word in candidates if regex.fullmatch(word))
        self._match_cache[cache_key] = result
        return result

    def get_all_words(self) -> list[str]:
        """
        Get all words in the dictionary.

        Returns:
            List of all words in the dictionary (lowercase, sorted)
        """
        return sorted(w for bucket in self._words_by_length.values() for w in bucket)
