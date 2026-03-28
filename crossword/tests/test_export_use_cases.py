"""
Unit tests for ExportUseCases
"""

import pytest
from unittest.mock import Mock
from crossword import Grid, Puzzle
from crossword.use_cases.export_use_cases import ExportUseCases
from crossword.ports.persistence_port import PersistenceError
from crossword.ports.export_port import ExportError


@pytest.fixture
def mock_persistence():
    return Mock()


@pytest.fixture
def mock_acrosslite():
    return Mock()


@pytest.fixture
def mock_xml():
    return Mock()


@pytest.fixture
def mock_nytimes():
    return Mock()


@pytest.fixture
def export_uc(mock_persistence, mock_acrosslite, mock_xml, mock_nytimes):
    return ExportUseCases(mock_persistence, mock_acrosslite, mock_xml, mock_nytimes)


@pytest.fixture
def test_grid():
    """Create a test grid"""
    return Grid(15)


@pytest.fixture
def test_puzzle(test_grid):
    """Create a test puzzle"""
    return Puzzle(test_grid, title="Test Puzzle")


class TestExportUseCasesPuzzleToAcrosslite:
    """Tests for export_puzzle_to_acrosslite"""

    def test_export_puzzle_to_acrosslite_success(self, export_uc, mock_persistence, mock_acrosslite, test_puzzle):
        zip_bytes = b"PK\x03\x04... zip content ..."
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_acrosslite.export_puzzle_to_acrosslite.return_value = zip_bytes

        result = export_uc.export_puzzle_to_acrosslite(1, "test_puzzle")

        assert result == zip_bytes
        mock_persistence.load_puzzle.assert_called_once_with(1, "test_puzzle")
        mock_acrosslite.export_puzzle_to_acrosslite.assert_called_once_with(test_puzzle)

    def test_export_puzzle_to_acrosslite_puzzle_not_found(self, export_uc, mock_persistence):
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            export_uc.export_puzzle_to_acrosslite(1, "nonexistent")

    def test_export_puzzle_to_acrosslite_export_error(self, export_uc, mock_persistence, mock_acrosslite, test_puzzle):
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_acrosslite.export_puzzle_to_acrosslite.side_effect = ExportError("Export failed")

        with pytest.raises(ExportError, match="Export failed"):
            export_uc.export_puzzle_to_acrosslite(1, "test_puzzle")


class TestExportUseCasesPuzzleToXml:
    """Tests for export_puzzle_to_xml"""

    def test_export_puzzle_to_xml_success(self, export_uc, mock_persistence, mock_xml, test_puzzle):
        xml_str = '<?xml version="1.0"?><puzzle>...</puzzle>'
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_xml.export_puzzle_to_xml.return_value = xml_str

        result = export_uc.export_puzzle_to_xml(1, "test_puzzle")

        assert result == xml_str
        mock_persistence.load_puzzle.assert_called_once_with(1, "test_puzzle")
        mock_xml.export_puzzle_to_xml.assert_called_once_with(test_puzzle)

    def test_export_puzzle_to_xml_puzzle_not_found(self, export_uc, mock_persistence):
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            export_uc.export_puzzle_to_xml(1, "nonexistent")

    def test_export_puzzle_to_xml_export_error(self, export_uc, mock_persistence, mock_xml, test_puzzle):
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_xml.export_puzzle_to_xml.side_effect = ExportError("Export failed")

        with pytest.raises(ExportError, match="Export failed"):
            export_uc.export_puzzle_to_xml(1, "test_puzzle")


class TestExportUseCasesPuzzleToNytimes:
    """Tests for export_puzzle_to_nytimes"""

    def test_export_puzzle_to_nytimes_success(self, export_uc, mock_persistence, mock_nytimes, test_puzzle):
        zip_bytes = b"PK\x03\x04... zip content ..."
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_nytimes.export_puzzle_to_nytimes.return_value = zip_bytes

        result = export_uc.export_puzzle_to_nytimes(1, "test_puzzle")

        assert result == zip_bytes
        mock_persistence.load_puzzle.assert_called_once_with(1, "test_puzzle")
        mock_nytimes.export_puzzle_to_nytimes.assert_called_once_with(test_puzzle)

    def test_export_puzzle_to_nytimes_puzzle_not_found(self, export_uc, mock_persistence):
        mock_persistence.load_puzzle.side_effect = PersistenceError("Puzzle not found")

        with pytest.raises(PersistenceError, match="Puzzle not found"):
            export_uc.export_puzzle_to_nytimes(1, "nonexistent")

    def test_export_puzzle_to_nytimes_export_error(self, export_uc, mock_persistence, mock_nytimes, test_puzzle):
        mock_persistence.load_puzzle.return_value = test_puzzle
        mock_nytimes.export_puzzle_to_nytimes.side_effect = ExportError("Export failed")

        with pytest.raises(ExportError, match="Export failed"):
            export_uc.export_puzzle_to_nytimes(1, "test_puzzle")
