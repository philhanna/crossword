# crossword.tests.adapters.test_xd_import_adapter
import pytest
from crossword.adapters.xd_import_adapter import XdImportAdapter
from crossword.ports.import_port import PuzzleImportError

# 3x3 all-white grid:
#   numbered cells: 1=(1,1), 2=(1,2), 3=(1,3), 4=(2,1), 5=(3,1)
#   across words: 1, 4, 5   down words: 1, 2, 3
VALID_3X3 = """\
Title: Sample Puzzle
Author: Test Author


ABC
DEF
GHI


A1. Row one ~ ABC
A4. Row two ~ DEF
A5. Row three ~ GHI

D1. Col one ~ ADG
D2. Col two ~ BEH
D3. Col three ~ CFI
"""

# 3x3 with black cell at (2,2):
#   across words: 1, 3   down words: 1, 2
WITH_BLACK = """\
Title: Black Cell Puzzle
Author:


ABC
D#F
GHI


A1. Row one ~ ABC
A3. Row three ~ GHI

D1. Col one ~ ADG
D2. Col three ~ CFI
"""

# No title or author
NO_META = """\
Title:
Author:


ABC
DEF
GHI


A1. Row one ~ ABC
A4. Row two ~ DEF
A5. Row three ~ GHI

D1. Col one ~ ADG
D2. Col two ~ BEH
D3. Col three ~ CFI
"""


@pytest.fixture
def adapter():
    return XdImportAdapter()


class TestImportPuzzleSuccess:
    def test_returns_tuple_of_three(self, adapter):
        result = adapter.import_puzzle(VALID_3X3)
        assert isinstance(result, tuple) and len(result) == 3

    def test_title_extracted(self, adapter):
        title, _, _ = adapter.import_puzzle(VALID_3X3)
        assert title == "Sample Puzzle"

    def test_author_extracted(self, adapter):
        _, author, _ = adapter.import_puzzle(VALID_3X3)
        assert author == "Test Author"

    def test_puzzle_size(self, adapter):
        _, _, puzzle = adapter.import_puzzle(VALID_3X3)
        assert puzzle.n == 3

    def test_cells_filled_from_grid(self, adapter):
        _, _, puzzle = adapter.import_puzzle(VALID_3X3)
        assert puzzle.get_cell(1, 1) == 'A'
        assert puzzle.get_cell(2, 3) == 'F'
        assert puzzle.get_cell(3, 3) == 'I'

    def test_across_clues_set(self, adapter):
        _, _, puzzle = adapter.import_puzzle(VALID_3X3)
        clues = [w.get_clue() for w in puzzle.across_words.values()]
        assert "Row one" in clues
        assert "Row two" in clues
        assert "Row three" in clues

    def test_down_clues_set(self, adapter):
        _, _, puzzle = adapter.import_puzzle(VALID_3X3)
        clues = [w.get_clue() for w in puzzle.down_words.values()]
        assert "Col one" in clues
        assert "Col two" in clues
        assert "Col three" in clues

    def test_empty_title_and_author_return_empty_string(self, adapter):
        title, author, _ = adapter.import_puzzle(NO_META)
        assert title == ""
        assert author == ""

    def test_black_cells_imported(self, adapter):
        _, _, puzzle = adapter.import_puzzle(WITH_BLACK)
        assert puzzle.grid.is_black_cell(2, 2)
        assert not puzzle.grid.is_black_cell(1, 1)

    def test_underscore_treated_as_black(self, adapter):
        # D_F grid: black at (2,2). Renumbered seqs: 1=(1,1), 2=(1,3), 3=(3,1)
        content = """\
Title: Underscore Test
Author:


ABC
D_F
GHI


A1. Row one ~ ABC
A3. Row three ~ GHI

D1. Col one ~ ADG
D2. Col three ~ CFI
"""
        _, _, puzzle = adapter.import_puzzle(content)
        assert puzzle.grid.is_black_cell(2, 2)

    def test_imported_puzzle_is_in_puzzle_mode(self, adapter):
        _, _, puzzle = adapter.import_puzzle(VALID_3X3)
        assert puzzle.last_mode == "puzzle"

    def test_crlf_line_endings_accepted(self, adapter):
        crlf_content = VALID_3X3.replace('\n', '\r\n')
        title, _, _ = adapter.import_puzzle(crlf_content)
        assert title == "Sample Puzzle"

    def test_clue_answer_stripped(self, adapter):
        _, _, puzzle = adapter.import_puzzle(VALID_3X3)
        assert puzzle.get_clue(1, "A") == "Row one"

    def test_clue_markup_stripped(self, adapter):
        content = VALID_3X3.replace("Row one ~ ABC", "Row {/one/} ~ ABC")
        _, _, puzzle = adapter.import_puzzle(content)
        assert puzzle.get_clue(1, "A") == "Row one"


class TestParseErrors:
    def test_fewer_than_three_sections_raises(self, adapter):
        with pytest.raises(PuzzleImportError, match="at least 3 sections"):
            adapter.import_puzzle("Title: X\n\n\nABC\nDEF\nGHI\n")

    def test_empty_grid_raises(self, adapter):
        # Three sections, but grid section contains only whitespace
        with pytest.raises(PuzzleImportError, match="Empty grid"):
            adapter.import_puzzle("Title: X\n\n\n   \n   \n\n\nA1. clue ~ ABC\n")

    def test_non_square_grid_raises(self, adapter):
        content = "Title: X\n\n\nABCD\nDEF\nGHI\n\n\nA1. ~ ABCD\n"
        with pytest.raises(PuzzleImportError, match="has 4 characters"):
            adapter.import_puzzle(content)

    def test_invalid_grid_character_raises(self, adapter):
        content = VALID_3X3.replace("ABC\nDEF\nGHI", "A1C\nDEF\nGHI")
        with pytest.raises(PuzzleImportError, match="Invalid character"):
            adapter.import_puzzle(content)

    def test_missing_across_clue_raises(self, adapter):
        content = VALID_3X3.replace("A4. Row two ~ DEF\n", "")
        with pytest.raises(PuzzleImportError, match="Missing across clues"):
            adapter.import_puzzle(content)

    def test_missing_down_clue_raises(self, adapter):
        content = VALID_3X3.replace("D2. Col two ~ BEH\n", "")
        with pytest.raises(PuzzleImportError, match="Missing down clues"):
            adapter.import_puzzle(content)
