"""
Unit tests for ExportUseCases
"""

import pytest
from unittest.mock import Mock
from crossword import Grid, Puzzle
from crossword.use_cases.export_use_cases import ExportUseCases
from crossword.ports.persistence import PersistenceError
from crossword.ports.export import ExportError


@pytest.fixture
def mock_persistence():
    """Create a mock persistence adapter"""
    return Mock()


@pytest.fixture
def mock_export():
    """Create a mock export adapter"""
    return Mock()


@pytest.fixture
def export_uc(mock_persistence, mock_export):
    """Create an ExportUseCases instance with mock adapters"""
    return ExportUseCases(mock_persistence, mock_export)


@pytest.fixture
def test_grid():
    """Create a test grid"""
    return Grid(15)


@pytest.fixture
def test_puzzle(test_grid):
    """Create a test puzzle"""
    return Puzzle(test_grid, title="Test Puzzle")


class TestExportUseCasesGridToPdf:
    """Tests for export_grid_to_pdf"""

    def test_export_grid_to_pdf_success(self, export_uc, mock_persistence, mock_export, test_grid):
        """Export grid to PDF successfully"""
        pdf_bytes = b"%PDF-1.4\n... PDF content ..."
        mock_persistence.load_grid.return_value = test_grid
        mock_export.export_grid_to_pdf.return_value = pdf_bytes

        result = export_uc.export_grid_to_pdf(1, "test_grid")

        assert result == pdf_bytes
        mock_persistence.load_grid.assert_called_once_with(1, "test_grid")
        mock_export.export_grid_to_pdf.assert_called_once_with(test_grid)

    def test_export_grid_to_pdf_grid_not_found(self, export_uc, mock_persistence, mock_export):
        """Export grid to PDF when grid not found"""
        mock_persistence.load_grid.side_effect = PersistenceError("Grid not found")

        with pytest.raises(PersistenceError, match="Grid not found"):
            export_uc.export_grid_to_pdf(1, "nonexistent")

    def test_export_grid_to_pdf_export_error(self, export_uc, mock_persistence, mock_export, test_grid):
        """Export grid to PDF when export fails"""
        mock_persistence.load_grid.return_value = test_grid
        mock_export.export_grid_to_pdf.side_effect = ExportError("Export failed")

        with pytest.raises(ExportError, match="Export failed"):
            export_uc.export_grid_to_pdf(1, "test_grid")


class TestExportUseCasesGridToPng:
    """Tests for export_grid_to_png"""

    def test_export_grid_to_png_success(self, export_uc, mock_persistence, mock_export, test_grid):
        """Export grid to PNG successfully"""
        png_bytes = b"\x89PNG\r\n\x1a\n... PNG content ..."
        mock_persistence.load_grid.return_value = test_grid
        mock_export.export_grid_to_png.return_value = png_bytes

        result = export_uc.export_grid_to_png(1, "test_grid")

        assert result == png_bytes
        mock_persistence.load_grid.assert_called_once_with(1, "test_grid")
        mock_export.export_grid_to_png.assert_called_once_with(test_grid)

    def test_export_grid_to_png_grid_not_found(self, export_uc, mock_persistence, mock_export):
        """Export grid to PNG when grid not found"""
        mock_persistence.load_grid.side_effect = PersistenceError("Grid not found")

        with pytest.raises(PersistenceError, match="Grid not found"):
            export_uc.export_grid_to_png(1, "nonexistent")

    def test_export_grid_to_png_export_error(self, export_uc, mock_persistence, mock_export, test_grid):
        """Export grid to PNG when export fails"""
        mock_persistence.load_grid.return_value = test_grid
        mock_export.export_grid_to_png.side_effect = ExportError("Export failed")

        with pytest.raises(ExportError, match="Export failed"):
            export_uc.export_grid_to_png(1, "test_grid")


class TestExportUseCasesPuzzleToPuz:
    """Tests for export_puzzle_to_puz"""

    def test_export_puzzle_to_puz_success(self, export_uc, mock_persistence, mock_export, test_puzzle):
        """Export puzzle to .puz successfully"""
        puz_bytes = b"ACROSS&DOWN\x00... .puz content ..."
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_export.export_puzzle_to_puz.return_value = puz_bytes

        result = export_uc.export_puzzle_to_puz(1, "test_puzzle")

        assert result == puz_bytes
        mock_persistence.load_puzzle.assert_called_once_with(1, "test_puzzle")
        mock_export.export_puzzle_to_puz.assert_called_once_with(test_puzzle)

    def test_export_puzzle_to_puz_puzzle_not_found(self, export_uc, mock_persistence, mock_export):
        """Export puzzle to .puz when puzzle not found"""
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            export_uc.export_puzzle_to_puz(1, "nonexistent")

    def test_export_puzzle_to_puz_export_error(self, export_uc, mock_persistence, mock_export, test_puzzle):
        """Export puzzle to .puz when export fails"""
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_export.export_puzzle_to_puz.side_effect = ExportError("Export failed")

        with pytest.raises(ExportError, match="Export failed"):
            export_uc.export_puzzle_to_puz(1, "test_puzzle")


class TestExportUseCasesPuzzleToXml:
    """Tests for export_puzzle_to_xml"""

    def test_export_puzzle_to_xml_success(self, export_uc, mock_persistence, mock_export, test_puzzle):
        """Export puzzle to XML successfully"""
        xml_str = '<?xml version="1.0"?><puzzle>...</puzzle>'
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_export.export_puzzle_to_xml.return_value = xml_str

        result = export_uc.export_puzzle_to_xml(1, "test_puzzle")

        assert result == xml_str
        mock_persistence.load_puzzle.assert_called_once_with(1, "test_puzzle")
        mock_export.export_puzzle_to_xml.assert_called_once_with(test_puzzle)

    def test_export_puzzle_to_xml_puzzle_not_found(self, export_uc, mock_persistence, mock_export):
        """Export puzzle to XML when puzzle not found"""
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            export_uc.export_puzzle_to_xml(1, "nonexistent")

    def test_export_puzzle_to_xml_export_error(self, export_uc, mock_persistence, mock_export, test_puzzle):
        """Export puzzle to XML when export fails"""
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_export.export_puzzle_to_xml.side_effect = ExportError("Export failed")

        with pytest.raises(ExportError, match="Export failed"):
            export_uc.export_puzzle_to_xml(1, "test_puzzle")
