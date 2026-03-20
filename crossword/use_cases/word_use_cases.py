"""
Word use cases - Word suggestions, validation, and lookup.

Public interface:
  get_suggestions(pattern) -> list[str]
  get_all_words() -> list[str]
  validate_word(word) -> bool
"""

import re
from crossword.ports.word_list import WordListPort


class WordUseCases:
    """
    Orchestrates word operations via the word list port.

    Constructor injection: takes a WordListPort instance.
    """

    def __init__(self, word_list: WordListPort):
        self.word_list = word_list

    def get_suggestions(self, pattern: str) -> list[str]:
        """
        Get word suggestions matching a pattern.

        Pattern is a regex with ? for unknown letters and . for exact position.
        Example: "?HALE" or ".H.LE" (5-letter words with H in position 2, E in position 5).

        Args:
            pattern: Pattern string with wildcards or regex

        Returns:
            List of matching words (lowercase), or empty list if no matches

        Raises:
            ValueError: If pattern is not a valid regex
        """
        # Convert simple pattern (with ?) to regex if needed
        regex_pattern = self._pattern_to_regex(pattern)
        try:
            return self.word_list.get_matches(regex_pattern)
        except ValueError as e:
            raise ValueError(f"Invalid pattern: {e}")

    def get_all_words(self) -> list[str]:
        """
        Get all words in the dictionary.

        Returns:
            List of all words (lowercase)
        """
        return self.word_list.get_all_words()

    def validate_word(self, word: str) -> bool:
        """
        Check if a word is in the dictionary.

        Args:
            word: Word to validate (case-insensitive)

        Returns:
            True if word is in dictionary, False otherwise
        """
        if not isinstance(word, str) or not word:
            return False

        word_lower = word.lower()
        all_words = self.word_list.get_all_words()
        return word_lower in all_words

    # Helper methods

    def _pattern_to_regex(self, pattern: str) -> str:
        """
        Convert a simple pattern with ? wildcards to a regex pattern.

        Example: "?HALE" -> "^.HALE$" (case-insensitive)
        If pattern already looks like regex, return as-is.

        Args:
            pattern: Pattern with ? for unknown or a regex

        Returns:
            Regex pattern string
        """
        # If already contains regex syntax, assume it's a full regex
        if any(c in pattern for c in "[]()*+^$.|"):
            return pattern

        # Convert ? to . (any character) and ^ . $ anchors
        escaped = pattern.replace("?", ".")
        return f"^{escaped}$"
