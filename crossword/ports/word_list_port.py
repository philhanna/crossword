"""
Word List Port - Word dictionary lookup

This port defines the contract for word list operations.
Implementations may load the word list into memory, query a database, or fetch from an API.
"""

from abc import ABC, abstractmethod


class WordListPort(ABC):
    """
    Abstract interface for word list operations (dictionary lookup, word suggestions).
    """

    @abstractmethod
    def get_matches(self, pattern: str, length: int = None) -> list[str]:
        """
        Find all words matching a regex pattern.

        Pattern matching is case-insensitive. The regex syntax is Python's
        standard `re` module syntax.

        Args:
            pattern: Python regex pattern (e.g., "^[A-Z]{5}$" for 5-letter words)
            length:  If provided, only words of this exact length are considered.
                     Callers should supply this whenever the target length is known,
                     as it avoids scanning irrelevant words.

        Returns:
            List of matching words (lowercase), or empty list if no matches

        Raises:
            ValueError: If pattern is not a valid regex
        """
        pass

    @abstractmethod
    def get_all_words(self) -> list[str]:
        """
        Get all words in the dictionary.

        Returns:
            List of all words in the dictionary (lowercase)
        """
        pass
