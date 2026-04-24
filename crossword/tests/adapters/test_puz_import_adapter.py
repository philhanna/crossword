# crossword.tests.adapters.test_puz_import_adapter
from pathlib import Path

import pytest

from crossword.adapters.puz_import_adapter import PuzImportAdapter
from crossword.ports.import_port import PuzzleImportError

DATA_DIR = Path(__file__).parent.parent / "data"
PUZ_FILE = DATA_DIR / "remedialchaostheory.puz"


@pytest.fixture(scope="module")
def puz_bytes():
    return PUZ_FILE.read_bytes()


@pytest.fixture(scope="module")
def adapter():
    return PuzImportAdapter()


@pytest.fixture(scope="module")
def imported(adapter, puz_bytes):
    return adapter.import_puzzle(puz_bytes)


class TestReturnShape:
    def test_returns_three_tuple(self, imported):
        assert isinstance(imported, tuple) and len(imported) == 3

    def test_title_is_str(self, imported):
        title, _, _ = imported
        assert isinstance(title, str)

    def test_author_is_str(self, imported):
        _, author, _ = imported
        assert isinstance(author, str)


class TestMetadata:
    def test_title(self, imported):
        title, _, _ = imported
        assert title == "PUZZLE #100: Remedial Chaos Theory"

    def test_author(self, imported):
        _, author, _ = imported
        assert author == "Paolo Pasco"

    def test_title_and_author_are_stripped(self, imported):
        title, author, _ = imported
        assert title == title.strip()
        assert author == author.strip()


class TestGridStructure:
    def test_puzzle_is_15x15(self, imported):
        _, _, puzzle = imported
        assert puzzle.n == 15

    def test_puzzle_is_in_puzzle_mode(self, imported):
        _, _, puzzle = imported
        assert puzzle.last_mode == "puzzle"

    def test_black_cell_count(self, imported):
        _, _, puzzle = imported
        count = sum(
            1
            for r in range(1, 16)
            for c in range(1, 16)
            if puzzle.grid.is_black_cell(r, c)
        )
        assert count == 43

    def test_known_black_cells(self, imported):
        _, _, puzzle = imported
        for r, c in [(1, 1), (1, 2), (1, 6), (7, 7), (15, 14), (15, 15)]:
            assert puzzle.grid.is_black_cell(r, c), f"Expected black cell at ({r}, {c})"

    def test_known_white_cells(self, imported):
        _, _, puzzle = imported
        for r, c in [(1, 3), (1, 8), (8, 1), (15, 1)]:
            assert not puzzle.grid.is_black_cell(r, c), f"Expected white cell at ({r}, {c})"


class TestCellLetters:
    def test_first_row_letters(self, imported):
        _, _, puzzle = imported
        assert puzzle.get_cell(1, 3) == "A"
        assert puzzle.get_cell(1, 8) == "Y"
        assert puzzle.get_cell(1, 15) == "B"

    def test_last_row_letters(self, imported):
        _, _, puzzle = imported
        assert puzzle.get_cell(15, 1) == "A"
        assert puzzle.get_cell(15, 2) == "D"
        assert puzzle.get_cell(15, 11) == "U"

    def test_letters_are_uppercase(self, imported):
        _, _, puzzle = imported
        for r in range(1, 16):
            for c in range(1, 16):
                if not puzzle.grid.is_black_cell(r, c):
                    letter = puzzle.get_cell(r, c)
                    assert letter == letter.upper(), f"Non-uppercase at ({r}, {c}): {letter!r}"


class TestWordCounts:
    def test_across_word_count(self, imported):
        _, _, puzzle = imported
        assert len(puzzle.across_words) == 42

    def test_down_word_count(self, imported):
        _, _, puzzle = imported
        assert len(puzzle.down_words) == 38


class TestClues:
    def test_first_across_clue(self, imported):
        _, _, puzzle = imported
        assert puzzle.get_clue(1, "A") == '"___, wirklich?" (German "Oh, really?")'

    def test_second_across_clue(self, imported):
        _, _, puzzle = imported
        assert puzzle.get_clue(4, "A") == "School for the Bulldogs"

    def test_third_across_clue(self, imported):
        _, _, puzzle = imported
        assert puzzle.get_clue(8, "A") == "Color picker option"

    def test_last_across_clue(self, imported):
        _, _, puzzle = imported
        assert puzzle.get_clue(73, "A") == "People for whom a U.S. state is named"

    def test_first_down_clue(self, imported):
        _, _, puzzle = imported
        assert puzzle.get_clue(1, "D") == "Make a nod (to)"

    def test_second_down_clue(self, imported):
        _, _, puzzle = imported
        assert puzzle.get_clue(2, "D") == "Cutting out"

    def test_last_down_clue(self, imported):
        _, _, puzzle = imported
        assert puzzle.get_clue(67, "D") == '"used to hate minions then i ___ up" (viral tweet)'

    def test_across_clues_all_nonempty(self, imported):
        _, _, puzzle = imported
        for seq, word in puzzle.across_words.items():
            assert word.get_clue(), f"Empty clue for {seq}A"

    def test_down_clues_all_nonempty(self, imported):
        _, _, puzzle = imported
        for seq, word in puzzle.down_words.items():
            assert word.get_clue(), f"Empty clue for {seq}D"


class TestParseErrors:
    def test_empty_bytes_raises(self, adapter):
        with pytest.raises(PuzzleImportError, match="Failed to parse"):
            adapter.import_puzzle(b"")

    def test_garbage_bytes_raises(self, adapter):
        with pytest.raises(PuzzleImportError, match="Failed to parse"):
            adapter.import_puzzle(b"not a puz file at all")
