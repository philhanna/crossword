"""
Definition Provider Port — dictionary/thesaurus lookup.

Implementations may query a local database, a third-party API (e.g. Merriam-Webster),
or any other source. The port is technology-agnostic.
"""

from abc import ABC, abstractmethod

from crossword.domain.definition import WordResult


class DefinitionNotFound(Exception):
    pass


class DefinitionProviderPort(ABC):

    @abstractmethod
    def lookup(self, word: str) -> WordResult:
        """
        Return definitions for *word*, grouped by part of speech.

        Args:
            word: The word to look up (case-insensitive).

        Returns:
            WordResult with one LexicalEntry per part of speech found.

        Raises:
            DefinitionNotFound: If the word is not in the provider's vocabulary.
        """
        pass
