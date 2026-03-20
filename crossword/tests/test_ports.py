"""
Tests for Port Interfaces

Verification that ports are properly defined and can be imported.
"""

import pytest
from abc import ABC
from crossword import Grid, Puzzle
from crossword.ports import (
    PersistencePort,
    PersistenceError,
    WordListPort,
    ExportPort,
    ExportError,
)


class TestPortsImport:
    """Verify all ports can be imported without error"""

    def test_persistence_port_is_abc(self):
        """PersistencePort should be an ABC"""
        assert issubclass(PersistencePort, ABC)

    def test_word_list_port_is_abc(self):
        """WordListPort should be an ABC"""
        assert issubclass(WordListPort, ABC)

    def test_export_port_is_abc(self):
        """ExportPort should be an ABC"""
        assert issubclass(ExportPort, ABC)

    def test_persistence_error_is_exception(self):
        """PersistenceError should be an Exception"""
        assert issubclass(PersistenceError, Exception)

    def test_export_error_is_exception(self):
        """ExportError should be an Exception"""
        assert issubclass(ExportError, Exception)


class TestPortSignatures:
    """Verify port method signatures"""

    def test_persistence_port_has_required_methods(self):
        """PersistencePort should have all required methods"""
        required_methods = [
            "save_grid",
            "load_grid",
            "delete_grid",
            "list_grids",
            "save_puzzle",
            "load_puzzle",
            "delete_puzzle",
            "list_puzzles",
        ]
        for method_name in required_methods:
            assert hasattr(PersistencePort, method_name), f"Missing {method_name}"

    def test_word_list_port_has_required_methods(self):
        """WordListPort should have all required methods"""
        required_methods = [
            "get_matches",
            "get_all_words",
        ]
        for method_name in required_methods:
            assert hasattr(WordListPort, method_name), f"Missing {method_name}"

    def test_export_port_has_required_methods(self):
        """ExportPort should have all required methods"""
        required_methods = [
            "export_grid_to_pdf",
            "export_grid_to_png",
            "export_puzzle_to_puz",
            "export_puzzle_to_xml",
        ]
        for method_name in required_methods:
            assert hasattr(ExportPort, method_name), f"Missing {method_name}"
