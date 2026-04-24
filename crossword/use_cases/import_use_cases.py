# crossword.use_cases.import_use_cases
"""
Import use cases — create puzzles from external file formats.

Public interface:
  import_puzzle_from_acrosslite(user_id, name, content) -> None
  import_puzzle_from_xd(user_id, name, content) -> None
  import_puzzle_from_puz(user_id, name, content) -> None
"""

import logging

from crossword.adapters.acrosslite_import_adapter import AcrossLiteImportAdapter
from crossword.adapters.puz_import_adapter import PuzImportAdapter
from crossword.adapters.xd_import_adapter import XdImportAdapter
from crossword.ports.persistence_port import PersistencePort
from crossword.use_cases._name_validation import validate_new_public_name

logger = logging.getLogger(__name__)


class ImportUseCases:
    """
    Orchestrates puzzle import from external formats.

    Constructor injection: takes a PersistencePort and import adapters.
    """

    def __init__(self, persistence: PersistencePort, acrosslite_adapter: AcrossLiteImportAdapter,
                 xd_adapter: XdImportAdapter = None, puz_adapter: PuzImportAdapter = None):
        self.persistence = persistence
        self.acrosslite_adapter = acrosslite_adapter
        self.xd_adapter = xd_adapter or XdImportAdapter()
        self.puz_adapter = puz_adapter or PuzImportAdapter()

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

    def import_puzzle_from_xd(self, user_id: int, name: str, content: str) -> None:
        """
        Parse .xd format content, create a Puzzle, and save it.

        Args:
            user_id: The user who will own this puzzle
            name: Name/identifier for the new puzzle
            content: Full text content of an .xd file

        Raises:
            ValueError: If name is invalid or already exists
            PuzzleImportError: If the content cannot be parsed
            PersistenceError: If saving fails
        """
        validate_new_public_name("puzzle", name, self.persistence.list_puzzles(user_id))
        _title, _author, puzzle = self.xd_adapter.import_puzzle(content)
        self.persistence.save_puzzle(user_id, name, puzzle)
        logger.info("Imported puzzle %r from xd format for user %s", name, user_id)

    def import_puzzle_from_puz(self, user_id: int, name: str, content: bytes) -> None:
        """
        Parse AcrossLite binary (.puz) content, create a Puzzle, and save it.

        Args:
            user_id: The user who will own this puzzle
            name: Name/identifier for the new puzzle
            content: Raw bytes of a .puz file

        Raises:
            ValueError: If name is invalid or already exists
            PuzzleImportError: If the content cannot be parsed
            PersistenceError: If saving fails
        """
        validate_new_public_name("puzzle", name, self.persistence.list_puzzles(user_id))
        _title, _author, puzzle = self.puz_adapter.import_puzzle(content)
        self.persistence.save_puzzle(user_id, name, puzzle)
        logger.info("Imported puzzle %r from .puz format for user %s", name, user_id)
