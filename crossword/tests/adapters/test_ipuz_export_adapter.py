# crossword.tests.adapters.test_ipuz_export_adapter
import json
import pytest

from crossword import Grid, Puzzle
from crossword.adapters.ipuz_export_adapter import IpuzExportAdapter
from crossword.ports.export_port import ExportError


@pytest.fixture
def puzzle():
    grid = Grid(3)
    p = Puzzle(grid, title="Sample Puzzle")
    p.enter_puzzle_mode()
    for seq in sorted(p.across_words):
        word = p.across_words[seq]
        word.set_text("ABC"[: word.length])
        word.set_clue(f"Across clue {seq}")
    for seq in sorted(p.down_words):
        word = p.down_words[seq]
        word.set_text("DEF"[: word.length])
        word.set_clue(f"Down clue {seq}")
    return p


@pytest.fixture
def adapter():
    return IpuzExportAdapter(author_name="Test Author")


class TestIpuzExportStructure:
    def test_returns_string(self, adapter, puzzle):
        result = adapter.export_puzzle_to_ipuz(puzzle)
        assert isinstance(result, str)

    def test_output_is_valid_json(self, adapter, puzzle):
        result = adapter.export_puzzle_to_ipuz(puzzle)
        json.loads(result)  # should not raise

    def test_required_top_level_fields(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_ipuz(puzzle))
        assert doc["version"] == "http://ipuz.org/v2"
        assert "http://ipuz.org/crossword#1" in doc["kind"]
        assert doc["dimensions"] == {"width": 3, "height": 3}
        assert doc["block"] == "#"
        assert doc["empty"] == 0

    def test_title_and_author(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_ipuz(puzzle))
        assert doc["title"] == "Sample Puzzle"
        assert doc["author"] == "Test Author"

    def test_puzzle_grid_dimensions(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_ipuz(puzzle))
        assert len(doc["puzzle"]) == 3
        for row in doc["puzzle"]:
            assert len(row) == 3

    def test_solution_grid_dimensions(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_ipuz(puzzle))
        assert len(doc["solution"]) == 3
        for row in doc["solution"]:
            assert len(row) == 3

    def test_clues_present(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_ipuz(puzzle))
        assert "Across" in doc["clues"]
        assert "Down" in doc["clues"]
        assert len(doc["clues"]["Across"]) == len(puzzle.across_words)
        assert len(doc["clues"]["Down"]) == len(puzzle.down_words)

    def test_clue_entries_are_seq_text_pairs(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_ipuz(puzzle))
        for entry in doc["clues"]["Across"]:
            assert isinstance(entry, list) and len(entry) == 2
            assert isinstance(entry[0], int)
            assert isinstance(entry[1], str)

    def test_black_cell_rendered_as_hash(self):
        grid = Grid(3)
        grid.add_black_cell(2, 2)
        p = Puzzle(grid, title="Black")
        p.enter_puzzle_mode()
        doc = json.loads(IpuzExportAdapter().export_puzzle_to_ipuz(p))
        assert doc["puzzle"][1][1] == "#"
        assert doc["solution"][1][1] == "#"

    def test_numbered_cells_carry_their_sequence(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_ipuz(puzzle))
        # Cell (1,1) of a 3x3 with no blacks is always numbered "1"
        assert doc["puzzle"][0][0] == 1

    def test_unnumbered_open_cell_is_empty_marker(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_ipuz(puzzle))
        # An interior cell of a fully open 3x3 that is not a word start should be 0
        # (cell at (2,2) is not numbered in a 3x3 with no blacks)
        assert doc["puzzle"][1][1] == 0

    def test_solution_letters_are_uppercase(self, adapter, puzzle):
        doc = json.loads(adapter.export_puzzle_to_ipuz(puzzle))
        for row in doc["solution"]:
            for cell in row:
                if cell and cell != "#":
                    assert cell == cell.upper()

    def test_empty_title_and_author(self):
        grid = Grid(3)
        p = Puzzle(grid)
        doc = json.loads(IpuzExportAdapter().export_puzzle_to_ipuz(p))
        assert doc["title"] == ""
        assert doc["author"] == ""


class TestIpuzExportError:
    def test_raises_export_error_on_failure(self):
        adapter = IpuzExportAdapter()
        with pytest.raises(ExportError):
            adapter.export_puzzle_to_ipuz(None)
