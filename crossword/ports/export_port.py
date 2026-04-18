"""
Export Port - Exporting grids and puzzles to various formats

This port defines the contract for exporting puzzles to standard formats:
- PDF (printable grid)
- PNG (image)
- AcrossLite text format (.txt)
- Crossword Compiler XML format (.xml)
- NYTimes submission format (.html + .svg)
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
    def export_puzzle_to_acrosslite(self, puzzle: Puzzle) -> bytes:
        """
        Export a puzzle to AcrossLite text format (.txt).

        Produces a ZIP archive containing the .txt file and a .json backup.
        The AcrossLite text format is documented at:
        https://www.litsoft.com/across/docs/AcrossTextFormat.pdf

        Args:
            puzzle: Puzzle object to export

        Returns:
            ZIP archive as bytes

        Raises:
            ExportError: If export fails
        """
        pass

    @abstractmethod
    def export_puzzle_to_xml(self, puzzle: Puzzle) -> str:
        """
        Export a puzzle to Crossword Compiler XML format.

        Args:
            puzzle: Puzzle object to export

        Returns:
            XML as a string

        Raises:
            ExportError: If export fails
        """
        pass

    @abstractmethod
    def export_puzzle_to_json(self, puzzle: Puzzle) -> str:
        """
        Export a puzzle to JSON format.

        Produces a clean JSON document with title, grid size, cell layout,
        and all across/down words with text and clues.

        Args:
            puzzle: Puzzle object to export

        Returns:
            JSON as a string

        Raises:
            ExportError: If export fails
        """
        pass

    @abstractmethod
    def export_puzzle_to_solver_pdf(self, puzzle: Puzzle) -> bytes:
        """
        Export a puzzle to a compact solver PDF.

        Produces a single Letter-size page with an empty numbered grid on the
        left and ACROSS / DOWN clue lists side-by-side on the right.

        Args:
            puzzle: Puzzle object to export

        Returns:
            PDF file contents as bytes

        Raises:
            ExportError: If export fails
        """
        pass

    @abstractmethod
    def export_puzzle_to_nytimes(self, puzzle: Puzzle) -> bytes:
        """
        Export a puzzle in NYTimes submission format (PDF).

        Produces a PDF with:
          - Page 1: filled-in answer grid with numbers and author contact info
          - Page 2+: clue sheet with ACROSS then DOWN, double-spaced,
            answer words in a column at far right

        Args:
            puzzle: Puzzle object to export

        Returns:
            PDF file contents as bytes

        Raises:
            ExportError: If export fails
        """
        pass
