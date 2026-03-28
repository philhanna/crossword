# crossword.tests.adapters.test_export_adapter
import zipfile
from io import BytesIO

import pytest

from crossword import Grid, Puzzle, Word
from crossword.adapters.acrosslite_export_adapter import AcrossLiteExportAdapter
from crossword.adapters.xml_export_adapter import XmlExportAdapter
from crossword.adapters.nytimes_export_adapter import NYTimesExportAdapter
from crossword.ports.export_port import ExportError


@pytest.fixture
def puzzle():
    """Small 5x5 puzzle with a couple of black cells and some filled words."""
    grid = Grid(5)
    grid.add_black_cell(2, 2)   # also marks (4, 4) symmetric
    p = Puzzle(grid, title="Test Puzzle")
    # Fill in a couple of words so output is non-trivial
    for seq in sorted(p.across_words):
        p.across_words[seq].set_text("ABCDE"[:p.across_words[seq].length])
        p.across_words[seq].set_clue(f"Across clue {seq}")
    for seq in sorted(p.down_words):
        p.down_words[seq].set_text("ABCDE"[:p.down_words[seq].length])
        p.down_words[seq].set_clue(f"Down clue {seq}")
    return p


class TestAcrossLiteExportAdapter:
    @pytest.fixture
    def adapter(self):
        return AcrossLiteExportAdapter()

    def test_returns_string(self, adapter, puzzle):
        result = adapter.export_puzzle_to_acrosslite(puzzle)
        assert isinstance(result, str)

    def test_has_required_sections(self, adapter, puzzle):
        result = adapter.export_puzzle_to_acrosslite(puzzle)
        for tag in ("<ACROSS PUZZLE>", "<TITLE>", "<SIZE>", "<GRID>", "<ACROSS>", "<DOWN>"):
            assert tag in result, f"Missing section: {tag}"

    def test_grid_has_correct_row_count(self, adapter, puzzle):
        result = adapter.export_puzzle_to_acrosslite(puzzle)
        grid_section = result.split("<GRID>")[1].split("<ACROSS>")[0]
        rows = [line.strip() for line in grid_section.splitlines() if line.strip()]
        assert len(rows) == puzzle.n

    def test_black_cells_are_dots(self, adapter, puzzle):
        result = adapter.export_puzzle_to_acrosslite(puzzle)
        grid_section = result.split("<GRID>")[1].split("<ACROSS>")[0]
        rows = [line.strip() for line in grid_section.splitlines() if line.strip()]
        # (2,2) is black → row index 1, col index 1 should be '.'
        assert rows[1][1] == "."

    def test_title_present(self, adapter, puzzle):
        result = adapter.export_puzzle_to_acrosslite(puzzle)
        assert "Test Puzzle" in result


class TestXmlExportAdapter:
    @pytest.fixture
    def adapter(self):
        return XmlExportAdapter()

    def test_returns_string(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xml(puzzle)
        assert isinstance(result, str)

    def test_xml_declaration(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xml(puzzle)
        assert result.startswith('<?xml version="1.0"')

    def test_has_crossword_compiler_root(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xml(puzzle)
        assert "<crossword-compiler" in result

    def test_has_grid_element(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xml(puzzle)
        assert "<grid " in result

    def test_has_across_and_down_clues(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xml(puzzle)
        assert "Across" in result
        assert "Down" in result

    def test_title_in_metadata(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xml(puzzle)
        assert "Test Puzzle" in result

    def test_black_cells_are_type_block(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xml(puzzle)
        assert 'type="block"' in result


class TestNYTimesExportAdapter:
    @pytest.fixture
    def adapter(self):
        return NYTimesExportAdapter()

    def test_returns_bytes(self, adapter, puzzle):
        result = adapter.export_puzzle_to_nytimes(puzzle)
        assert isinstance(result, bytes)

    def test_is_zip(self, adapter, puzzle):
        result = adapter.export_puzzle_to_nytimes(puzzle)
        assert result[:2] == b"PK"

    def test_zip_contains_html_and_svg(self, adapter, puzzle):
        result = adapter.export_puzzle_to_nytimes(puzzle)
        with zipfile.ZipFile(BytesIO(result)) as zf:
            names = zf.namelist()
        assert "puzzle.html" in names
        assert "puzzle.svg" in names

    def test_html_has_across_and_down(self, adapter, puzzle):
        result = adapter.export_puzzle_to_nytimes(puzzle)
        with zipfile.ZipFile(BytesIO(result)) as zf:
            html = zf.read("puzzle.html").decode()
        assert "ACROSS" in html
        assert "DOWN" in html

    def test_svg_has_svg_element(self, adapter, puzzle):
        result = adapter.export_puzzle_to_nytimes(puzzle)
        with zipfile.ZipFile(BytesIO(result)) as zf:
            svg = zf.read("puzzle.svg").decode()
        assert "<svg" in svg
