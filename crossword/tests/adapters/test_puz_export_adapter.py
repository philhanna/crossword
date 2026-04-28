# crossword.tests.adapters.test_puz_export_adapter
import puz
import pytest

from crossword.adapters.puz_export_adapter import PuzExportAdapter
from crossword.ports.export_port import ExportError
from crossword.tests import TestPuzzle


@pytest.fixture
def adapter():
    return PuzExportAdapter(author_name="Test Author")


@pytest.fixture
def puzzle():
    return TestPuzzle.create_solved_atlantic_puzzle()


@pytest.fixture
def exported(adapter, puzzle):
    return adapter.export_puzzle_to_puz(puzzle)


@pytest.fixture
def puz_doc(exported):
    doc = puz.Puzzle()
    doc.load(exported)
    return doc


class TestPuzExportAdapter:
    def test_returns_bytes(self, exported):
        assert isinstance(exported, bytes)

    def test_sets_title(self, puz_doc, puzzle):
        assert puz_doc.title == puzzle.title

    def test_sets_author(self, puz_doc):
        assert puz_doc.author == "Test Author"

    def test_sets_square_dimensions(self, puz_doc, puzzle):
        assert puz_doc.width == puzzle.n
        assert puz_doc.height == puzzle.n

    def test_exports_black_cells_as_dots(self, puz_doc):
        assert puz_doc.solution[3] == "."
        assert puz_doc.solution[4] == "."

    def test_exports_solution_letters(self, puz_doc):
        assert puz_doc.solution[:9] == "DAB..EFTS"

    def test_fill_is_dashes_for_white_cells_and_dots_for_black_cells(self, puz_doc):
        assert puz_doc.fill[:9] == "---..----"

    def test_clues_are_exported_in_puz_order(self, puz_doc):
        assert puz_doc.clues[0] == "Dance move that's a hit?"
        assert puz_doc.clues[1] == "Gift for a shutterbug, briefly"
        assert puz_doc.clues[2] == "Healing succulent"
        assert puz_doc.clues[3] == "Open to expanding one's sense of identity"

    def test_missing_clues_export_as_empty_strings(self, adapter):
        puzzle = TestPuzzle.create_puzzle()
        doc = puz.Puzzle()
        doc.load(adapter.export_puzzle_to_puz(puzzle))
        assert all(clue == "" for clue in doc.clues)

    def test_wraps_build_errors(self, adapter, puzzle, monkeypatch):
        def boom(_puzzle):
            raise RuntimeError("boom")

        monkeypatch.setattr(adapter, "_build_puz", boom)
        with pytest.raises(ExportError, match=r"\.puz export failed: boom"):
            adapter.export_puzzle_to_puz(puzzle)
