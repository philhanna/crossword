# crossword.tests.adapters.test_export_adapter
import json
import pytest
from unittest.mock import patch

from crossword import Grid, Puzzle, Word
from crossword.adapters.acrosslite_export_adapter import AcrossLiteExportAdapter
from crossword.adapters.ccxml_export_adapter import CcxmlExportAdapter
from crossword.adapters.nytimes_export_adapter import NYTimesExportAdapter
from crossword.adapters.json_export_adapter import JsonExportAdapter
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


class TestCcxmlExportAdapter:
    @pytest.fixture
    def adapter(self):
        return CcxmlExportAdapter()

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
        return NYTimesExportAdapter(
            author_name="Jane Smith",
            author_address="123 Main St, Springfield, IL 62701",
            author_email="jane@example.com",
        )

    def test_html_has_across_and_down(self, adapter, puzzle):
        html = adapter._build_html(puzzle)
        assert "ACROSS" in html
        assert "DOWN" in html

    def test_html_has_inline_svg(self, adapter, puzzle):
        html = adapter._build_html(puzzle)
        assert "<svg" in html

    def test_html_has_title(self, adapter, puzzle):
        html = adapter._build_html(puzzle)
        assert "Test Puzzle" in html

    def test_html_has_author_info(self, adapter, puzzle):
        html = adapter._build_html(puzzle)
        assert "Jane Smith" in html
        assert "123 Main St" in html
        assert "jane@example.com" in html

    def test_html_no_author_info_when_not_set(self, puzzle):
        adapter = NYTimesExportAdapter()
        html = adapter._build_html(puzzle)
        # The author info block should not be rendered when fields are empty
        assert "<strong>Name:</strong>" not in html
        assert "<strong>Address:</strong>" not in html
        assert "<strong>Email:</strong>" not in html

    def test_down_clues_have_no_page_break(self, adapter, puzzle):
        html = adapter._build_html(puzzle)
        # No page-break should appear between the ACROSS and DOWN headings
        body_start = html.index("</style>")
        across_pos = html.index("ACROSS", body_start)
        down_pos = html.index("DOWN", across_pos)
        assert "page-break" not in html[across_pos:down_pos]

    def test_export_returns_pdf_bytes(self, adapter, puzzle):
        _fake_pdf = b"%PDF-1.4 fake"
        with patch.object(adapter, "_html_to_pdf", return_value=_fake_pdf):
            result = adapter.export_puzzle_to_nytimes(puzzle)
        assert result == _fake_pdf


class TestJsonExportAdapter:
    @pytest.fixture
    def adapter(self):
        return JsonExportAdapter()

    def test_returns_string(self, adapter, puzzle):
        result = adapter.export_puzzle_to_json(puzzle)
        assert isinstance(result, str)

    def test_valid_json(self, adapter, puzzle):
        result = adapter.export_puzzle_to_json(puzzle)
        doc = json.loads(result)
        assert isinstance(doc, dict)

    def test_has_required_keys(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_json(puzzle))
        for key in ("title", "size", "grid", "across", "down"):
            assert key in doc, f"Missing key: {key}"

    def test_title(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_json(puzzle))
        assert doc["title"] == "Test Puzzle"

    def test_size(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_json(puzzle))
        assert doc["size"] == puzzle.n

    def test_grid_row_count(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_json(puzzle))
        assert len(doc["grid"]) == puzzle.n

    def test_grid_black_cell(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_json(puzzle))
        # (2,2) is black → row index 1, col index 1 should be '.'
        assert doc["grid"][1][1] == "."

    def test_across_words_present(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_json(puzzle))
        assert len(doc["across"]) == len(puzzle.across_words)

    def test_down_words_present(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_json(puzzle))
        assert len(doc["down"]) == len(puzzle.down_words)

    def test_word_has_seq_text_clue(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_json(puzzle))
        for word in doc["across"] + doc["down"]:
            assert "seq" in word
            assert "text" in word
            assert "clue" in word
