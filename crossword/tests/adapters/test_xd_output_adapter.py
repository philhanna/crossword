# crossword.tests.adapters.test_xd_output_adapter
import re
import pytest

from crossword import Grid, Puzzle
from crossword.adapters.xd_output_adapter import XdOutputAdapter
from crossword.adapters.xd_import_adapter import XdImportAdapter
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
    return XdOutputAdapter(author_name="Test Author")


class TestXdOutputStructure:
    def test_returns_string(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        assert isinstance(result, str)

    def test_title_in_metadata(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        assert "Title: Sample Puzzle" in result

    def test_author_in_metadata(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        assert "Author: Test Author" in result

    def test_three_sections_separated_by_double_blank_lines(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        sections = re.split(r'\n{3,}', result.strip())
        assert len(sections) == 3

    def test_grid_section_has_correct_row_count(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        sections = re.split(r'\n{3,}', result.strip())
        grid_lines = [ln for ln in sections[1].splitlines() if ln.strip()]
        assert len(grid_lines) == 3

    def test_grid_rows_are_uppercase_letters(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        sections = re.split(r'\n{3,}', result.strip())
        for line in sections[1].splitlines():
            assert re.fullmatch(r'[A-Z#.]{3}', line.strip())

    def test_black_cell_rendered_as_hash(self, adapter):
        grid = Grid(3)
        grid.add_black_cell(2, 2)
        p = Puzzle(grid, title="Black")
        p.enter_puzzle_mode()
        result = XdOutputAdapter().export_puzzle_to_xd(p)
        sections = re.split(r'\n{3,}', result.strip())
        grid_lines = sections[1].splitlines()
        assert grid_lines[1][1] == '#'

    def test_across_clues_present(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        assert re.search(r'^A\d+\. ', result, re.MULTILINE)

    def test_down_clues_present(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        assert re.search(r'^D\d+\. ', result, re.MULTILINE)

    def test_clue_line_contains_tilde_separator(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        for line in result.splitlines():
            if re.match(r'^[AD]\d+\.', line):
                assert ' ~ ' in line

    def test_answer_is_uppercase(self, adapter, puzzle):
        result = adapter.export_puzzle_to_xd(puzzle)
        for line in result.splitlines():
            m = re.match(r'^[AD]\d+\. .+ ~ ([A-Z.]+)$', line)
            if m:
                assert m.group(1) == m.group(1).upper()

    def test_empty_title_and_author(self):
        grid = Grid(3)
        p = Puzzle(grid)
        result = XdOutputAdapter().export_puzzle_to_xd(p)
        assert "Title: \n" in result
        assert "Author: \n" in result

    def test_empty_cells_rendered_as_dot(self):
        grid = Grid(3)
        p = Puzzle(grid, title="Empty")
        result = XdOutputAdapter().export_puzzle_to_xd(p)
        sections = re.split(r'\n{3,}', result.strip())
        for line in sections[1].splitlines():
            assert '.' in line or re.fullmatch(r'[A-Z#.]+', line.strip())


class TestXdRoundTrip:
    def test_full_puzzle_round_trips(self, adapter, puzzle):
        xd_text = adapter.export_puzzle_to_xd(puzzle)
        title, author, imported = XdImportAdapter().import_puzzle(xd_text)
        assert title == puzzle.title
        assert author == "Test Author"
        assert imported.n == puzzle.n

    def test_cells_survive_round_trip(self, adapter, puzzle):
        xd_text = adapter.export_puzzle_to_xd(puzzle)
        _, _, imported = XdImportAdapter().import_puzzle(xd_text)
        for r in range(1, puzzle.n + 1):
            for c in range(1, puzzle.n + 1):
                if not puzzle.is_black_cell(r, c):
                    assert imported.get_cell(r, c) == puzzle.get_cell(r, c)

    def test_clues_survive_round_trip(self, adapter, puzzle):
        xd_text = adapter.export_puzzle_to_xd(puzzle)
        _, _, imported = XdImportAdapter().import_puzzle(xd_text)
        for seq in puzzle.across_words:
            assert imported.across_words[seq].get_clue() == puzzle.across_words[seq].get_clue()
        for seq in puzzle.down_words:
            assert imported.down_words[seq].get_clue() == puzzle.down_words[seq].get_clue()


class TestXdExportError:
    def test_raises_export_error_on_failure(self):
        adapter = XdOutputAdapter()
        with pytest.raises(ExportError):
            adapter.export_puzzle_to_xd(None)
