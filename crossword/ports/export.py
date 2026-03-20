"""
Export Port - Exporting grids and puzzles to various formats

This port defines the contract for exporting puzzles to standard formats:
- PDF (printable grid)
- PNG (image)
- AcrossLite .puz (binary format)
- XML (structured text)
"""

from abc import ABC, abstractmethod
from crossword import Grid, Puzzle


class ExportError(Exception):
    """Base exception for export operations"""
    pass


class ExportPort(ABC):
    """
    Abstract interface for exporting grids and puzzles to various formats.
    """

    @abstractmethod
    def export_grid_to_pdf(self, grid: Grid) -> bytes:
        """
        Export a grid to PDF format.

        The PDF shows the grid layout with black and white cells.

        Args:
            grid: Grid object to export

        Returns:
            PDF file contents as bytes

        Raises:
            ExportError: If export fails
        """
        pass

    @abstractmethod
    def export_grid_to_png(self, grid: Grid) -> bytes:
        """
        Export a grid to PNG image format.

        The PNG shows the grid layout with black and white cells.

        Args:
            grid: Grid object to export

        Returns:
            PNG file contents as bytes

        Raises:
            ExportError: If export fails
        """
        pass

    @abstractmethod
    def export_puzzle_to_puz(self, puzzle: Puzzle) -> bytes:
        """
        Export a puzzle to AcrossLite .puz binary format.

        This format is the standard for distributing crossword puzzles
        and can be opened in most crossword software.

        Args:
            puzzle: Puzzle object to export

        Returns:
            .puz file contents as bytes

        Raises:
            ExportError: If export fails
        """
        pass

    @abstractmethod
    def export_puzzle_to_xml(self, puzzle: Puzzle) -> str:
        """
        Export a puzzle to XML text format.

        Args:
            puzzle: Puzzle object to export

        Returns:
            XML as a string

        Raises:
            ExportError: If export fails
        """
        pass
