# crossword.use_cases.import_use_cases
"""
Import use cases — create puzzles from external file formats.

Public interface:
  import_puzzle_from_acrosslite(user_id, name, content) -> None
"""

import logging

from crossword.adapters.acrosslite_import_adapter import AcrossLiteImportAdapter
from crossword.ports.persistence_port import PersistencePort
from crossword.use_cases._name_validation import validate_new_public_name

logger = logging.getLogger(__name__)


class ImportUseCases:
    """
    Orchestrates puzzle import from external formats.

    Constructor injection: takes a PersistencePort and an import adapter.
    """

    def __init__(self, persistence: PersistencePort, acrosslite_adapter: AcrossLiteImportAdapter):
        self.persistence = persistence
        self.acrosslite_adapter = acrosslite_adapter

    def import_puzzle_from_acrosslite(self, user_id: int, name: str, content: str) -> None:
        """
        Parse AcrossLite text content, create a Puzzle, and save it.

        Args:
            user_id: The user who will own this puzzle
            name: Name/identifier for the new puzzle
            content: Full text content of an AcrossLite .txt file

        Raises:
            ValueError: If name is invalid or already exists
            ImportError: If the content cannot be parsed
            PersistenceError: If saving fails
        """
        validate_new_public_name("puzzle", name, self.persistence.list_puzzles(user_id))
        _title, _author, puzzle = self.acrosslite_adapter.import_puzzle(content)
        self.persistence.save_puzzle(user_id, name, puzzle)
        logger.info("Imported puzzle %r from AcrossLite format for user %s", name, user_id)
