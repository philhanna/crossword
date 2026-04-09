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
    normalized to lowercase and blank lines are ignored. Words are bucketed
    by length so that callers who know the target length avoid scanning the
    full dictionary.
    """

    def __init__(self, file_path: str | None = None):
        self._words_by_length: dict[int, list[str]] = {}
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
                words = {line.strip().lower() for line in f if line.strip()}
        except (OSError, UnicodeDecodeError) as e:
            raise Exception(f"Failed to load words from file: {e}")
        self._words_by_length = {}
        for w in words:
            self._words_by_length.setdefault(len(w), []).append(w)

    def get_matches(self, pattern: str, length: int = None) -> list[str]:
        """
        Find all words matching a regex pattern.

        Pattern matching is case-insensitive. The regex syntax is Python's
        standard `re` module syntax.

        Args:
            pattern: Python regex pattern
            length:  If provided, only words of this exact length are considered.
        """
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

        if length is not None:
            candidates = self._words_by_length.get(length, [])
        else:
            candidates = (w for bucket in self._words_by_length.values() for w in bucket)
        return sorted(word for word in candidates if regex.fullmatch(word))

    def get_all_words(self) -> list[str]:
        """Return all words in sorted lowercase form."""
        return sorted(w for bucket in self._words_by_length.values() for w in bucket)
