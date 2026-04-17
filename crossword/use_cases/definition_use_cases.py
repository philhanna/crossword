"""
Definition use cases - word definition lookup.

Public interface:
  lookup(word) -> dict
"""

from crossword.ports.definition_port import DefinitionNotFound, DefinitionProviderPort


class DefinitionUseCases:
    """
    Orchestrates word definition lookups via the definition provider port.

    Constructor injection: takes a DefinitionProviderPort instance.
    """

    def __init__(self, definition_port: DefinitionProviderPort):
        self.definition_port = definition_port

    def lookup(self, word: str) -> dict:
        """
        Look up definitions for a word.

        Args:
            word: The word to look up (case-insensitive).

        Returns:
            Dict with keys:
              - word: the looked-up word (lowercase)
              - entries: list of dicts, each with:
                  - part_of_speech: string (e.g. "noun", "verb")
                  - definitions: list of dicts with keys:
                      - text: definition text
                      - example: optional example sentence (str or None)

        Raises:
            DefinitionNotFound: If the word is not found in the provider.
        """
        result = self.definition_port.lookup(word)
        return {
            "word": result.word,
            "entries": [
                {
                    "part_of_speech": entry.part_of_speech.value,
                    "definitions": [
                        {"text": d.text, "example": d.example}
                        for d in entry.definitions
                    ],
                }
                for entry in result.entries
            ],
        }
