"""
DictionaryAdapter - Word list implementation of the Word List Port

Loads a dictionary into memory and provides word matching via regex patterns.
"""

import re
import sqlite3
from crossword.ports.word_list import WordListPort


class DictionaryAdapter(WordListPort):
    """
    In-memory word dictionary adapter.

    Loads all words from a source (database or file) into memory for fast regex matching.
    Suitable for moderate dictionary sizes (up to ~100k words).
    """

    def __init__(self):
        """Initialize with empty word list."""
        self._words = set()

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
            self._words = {row[0].lower() for row in cursor.fetchall()}
            conn.close()
        except sqlite3.Error as e:
            raise Exception(f"Failed to load words from database: {e}")

    def load_from_file(self, file_path: str) -> None:
        """
        Load words from a text file (one word per line).

        Args:
            file_path: Path to text file containing words

        Raises:
            Exception: If file reading fails
        """
        try:
            with open(file_path, 'r') as f:
                self._words = {line.strip().lower() for line in f if line.strip()}
        except IOError as e:
            raise Exception(f"Failed to load words from file: {e}")

    def get_matches(self, pattern: str) -> list[str]:
        """
        Find all words matching a regex pattern.

        Pattern matching is case-insensitive. The regex syntax is Python's
        standard `re` module syntax.

        Args:
            pattern: Python regex pattern (e.g., "^[A-Z]{5}$" for 5-letter words)

        Returns:
            List of matching words (lowercase), or empty list if no matches

        Raises:
            ValueError: If pattern is not a valid regex
        """
        try:
            # Compile the pattern (case-insensitive)
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        # Find all matching words (use search to match anywhere, not just start)
        return sorted([word for word in self._words if regex.search(word)])

    def get_all_words(self) -> list[str]:
        """
        Get all words in the dictionary.

        Returns:
            List of all words in the dictionary (lowercase, sorted)
        """
        return sorted(self._words)
