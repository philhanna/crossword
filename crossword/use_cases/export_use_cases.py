"""
Export use cases - exporting puzzles to various formats.

Public interface:
  export_puzzle_to_acrosslite(user_id, name) -> bytes
  export_puzzle_to_xml(user_id, name) -> str
  export_puzzle_to_nytimes(user_id, name) -> bytes
  export_puzzle_to_json(user_id, name) -> str
"""

from crossword.ports.persistence_port import PersistencePort
from crossword.adapters.acrosslite_export_adapter import AcrossLiteExportAdapter
from crossword.adapters.ccxml_export_adapter import CcxmlExportAdapter
from crossword.adapters.nytimes_export_adapter import NYTimesExportAdapter
from crossword.adapters.json_export_adapter import JsonExportAdapter


class ExportUseCases:
    """
    Orchestrates export operations via persistence and format-specific adapters.

    Constructor injection: takes PersistencePort and the four export adapters.
    """

    def __init__(
        self,
        persistence: PersistencePort,
        acrosslite: AcrossLiteExportAdapter,
        xml: CcxmlExportAdapter,
        nytimes: NYTimesExportAdapter,
        json_adapter: JsonExportAdapter,
    ):
        self.persistence = persistence
        self._acrosslite = acrosslite
        self._xml = xml
        self._nytimes = nytimes
        self._json = json_adapter

    def export_puzzle_to_acrosslite(self, user_id: int, name: str) -> bytes:
        puzzle = self.persistence.load_puzzle(user_id, name)
        return self._acrosslite.export_puzzle_to_acrosslite(puzzle)

    def export_puzzle_to_xml(self, user_id: int, name: str) -> str:
        puzzle = self.persistence.load_puzzle(user_id, name)
        return self._xml.export_puzzle_to_xml(puzzle)

    def export_puzzle_to_nytimes(self, user_id: int, name: str) -> bytes:
        puzzle = self.persistence.load_puzzle(user_id, name)
        return self._nytimes.export_puzzle_to_nytimes(puzzle)

    def export_puzzle_to_json(self, user_id: int, name: str) -> str:
        puzzle = self.persistence.load_puzzle(user_id, name)
        return self._json.export_puzzle_to_json(puzzle)
