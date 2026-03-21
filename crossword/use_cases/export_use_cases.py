"""
Export use cases - Exporting grids and puzzles to various formats.

Public interface:
  export_grid_to_pdf(user_id, name) -> bytes
  export_grid_to_png(user_id, name) -> bytes
  export_puzzle_to_acrosslite(user_id, name) -> bytes
  export_puzzle_to_xml(user_id, name) -> str
  export_puzzle_to_nytimes(user_id, name) -> bytes
"""

from crossword.ports.persistence import PersistencePort, PersistenceError
from crossword.ports.export import ExportPort, ExportError


class ExportUseCases:
    """
    Orchestrates export operations via persistence and export ports.

    Constructor injection: takes PersistencePort and ExportPort instances.
    """

    def __init__(self, persistence: PersistencePort, export: ExportPort):
        self.persistence = persistence
        self.export = export

    def export_grid_to_pdf(self, user_id: int, name: str) -> bytes:
        """
        Export a grid to PDF format.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Returns:
            PDF file contents as bytes

        Raises:
            PersistenceError: If grid not found
            ExportError: If export fails
        """
        grid = self.persistence.load_grid(user_id, name)
        return self.export.export_grid_to_pdf(grid)

    def export_grid_to_png(self, user_id: int, name: str) -> bytes:
        """
        Export a grid to PNG image format.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Returns:
            PNG file contents as bytes

        Raises:
            PersistenceError: If grid not found
            ExportError: If export fails
        """
        grid = self.persistence.load_grid(user_id, name)
        return self.export.export_grid_to_png(grid)

    def export_puzzle_to_acrosslite(self, user_id: int, name: str) -> bytes:
        """
        Export a puzzle to AcrossLite text format.

        Returns a ZIP archive containing the .txt file and a .json backup.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            ZIP archive as bytes

        Raises:
            PersistenceError: If puzzle not found
            ExportError: If export fails
        """
        puzzle = self.persistence.load_puzzle(user_id, name)
        return self.export.export_puzzle_to_acrosslite(puzzle)

    def export_puzzle_to_xml(self, user_id: int, name: str) -> str:
        """
        Export a puzzle to Crossword Compiler XML format.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            XML as a string

        Raises:
            PersistenceError: If puzzle not found
            ExportError: If export fails
        """
        puzzle = self.persistence.load_puzzle(user_id, name)
        return self.export.export_puzzle_to_xml(puzzle)

    def export_puzzle_to_nytimes(self, user_id: int, name: str) -> bytes:
        """
        Export a puzzle in NYTimes submission format.

        Returns a ZIP archive containing an HTML clue sheet and SVG grid image.

        Args:
            user_id: The user who owns this puzzle
            name: Name/identifier for the puzzle

        Returns:
            ZIP archive as bytes

        Raises:
            PersistenceError: If puzzle not found
            ExportError: If export fails
        """
        puzzle = self.persistence.load_puzzle(user_id, name)
        return self.export.export_puzzle_to_nytimes(puzzle)
