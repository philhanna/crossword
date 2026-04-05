"""
FlatFileWordListAdapter - flat ASCII file implementation of the Word List Port.

Loads newline-delimited words from a plain text file into memory and provides
regex-based lookup over the normalized word list.
"""

import re

from crossword.ports.word_list_port import WordListPort


class FlatFileWordListAdapter(WordListPort):
    """
    In-memory word list adapter backed by a plain text file.

    The source file is expected to contain one word per line. Words are
    normalized to lowercase and blank lines are ignored.
    """

    def __init__(self, file_path: str | None = None):
        self._words = set()
        if file_path:
            self.load_from_file(file_path)

    def load_from_file(self, file_path: str) -> None:
        """
        Load words from a text file.

        Args:
            file_path: Path to a newline-delimited text file

        Raises:
            Exception: If the file cannot be read
        """
        try:
            with open(file_path, "r", encoding="ascii") as f:
                self._words = {line.strip().lower() for line in f if line.strip()}
        except (OSError, UnicodeDecodeError) as e:
            raise Exception(f"Failed to load words from file: {e}")

    def get_matches(self, pattern: str) -> list[str]:
        """
        Find all words matching a regex pattern.

        Pattern matching is case-insensitive. The regex syntax is Python's
        standard `re` module syntax.
        """
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        return sorted(word for word in self._words if regex.fullmatch(word))

    def get_all_words(self) -> list[str]:
        """Return all words in sorted lowercase form."""
        return sorted(self._words)
