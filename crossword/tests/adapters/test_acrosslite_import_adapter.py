# crossword.tests.adapters.test_acrosslite_import_adapter
import pytest
from crossword.adapters.acrosslite_import_adapter import AcrossLiteImportAdapter, ImportError

# 3x3 all-white grid:
#   numbered cells: 1=(1,1), 2=(1,2), 3=(1,3), 4=(2,1), 5=(3,1)
#   across words: 1, 4, 5   down words: 1, 2, 3
VALID_3X3 = """\
<ACROSS PUZZLE>
<TITLE>
Sample Puzzle
<AUTHOR>
Test Author
<SIZE>
3x3
<GRID>
ABC
DEF
GHI
<ACROSS>
Row one
Row two
Row three
<DOWN>
Col one
Col two
Col three
"""

# 3x3 with empty cells ('X' → not filled)
EMPTY_CELLS_3X3 = """\
<ACROSS PUZZLE>
<TITLE>
<AUTHOR>
<SIZE>
3x3
<GRID>
XXX
XXX
XXX
<ACROSS>
Row one
Row two
Row three
<DOWN>
Col one
Col two
Col three
"""


@pytest.fixture
def adapter():
    return AcrossLiteImportAdapter()


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
        title, author, _ = adapter.import_puzzle(EMPTY_CELLS_3X3)
        assert title == ""
        assert author == ""

    def test_x_cells_not_filled(self, adapter):
        _, _, puzzle = adapter.import_puzzle(EMPTY_CELLS_3X3)
        assert puzzle.get_cell(1, 1) == ' '

    def test_blank_lines_before_header_are_ignored(self, adapter):
        content = "\n\n" + VALID_3X3
        title, _, _ = adapter.import_puzzle(content)
        assert title == "Sample Puzzle"

    def test_lowercase_size_accepted(self, adapter):
        content = VALID_3X3.replace("3x3", "3X3")
        _, _, puzzle = adapter.import_puzzle(content)
        assert puzzle.n == 3

    def test_black_cells_imported(self, adapter):
        # 3x3 with black at (2,2): 2 across words (seqs 1,3), 2 down words (seqs 1,2)
        content = """\
<ACROSS PUZZLE>
<TITLE>
With Black
<AUTHOR>
<SIZE>
3x3
<GRID>
ABC
D.F
GHI
<ACROSS>
Row one
Row three
<DOWN>
Col one
Col three
"""
        _, _, puzzle = adapter.import_puzzle(content)
        assert puzzle.grid.is_black_cell(2, 2)
        assert not puzzle.grid.is_black_cell(1, 1)


class TestParseErrors:
    def test_empty_content_raises(self, adapter):
        with pytest.raises(ImportError, match="missing '<ACROSS PUZZLE>'"):
            adapter.import_puzzle("")

    def test_non_blank_before_header_raises(self, adapter):
        with pytest.raises(ImportError, match="Not an AcrossLite"):
            adapter.import_puzzle("junk\n<ACROSS PUZZLE>\n")

    def test_missing_size_section_raises(self, adapter):
        content = "<ACROSS PUZZLE>\n<GRID>\nXXX\nXXX\nXXX\n<ACROSS>\na\nb\nc\n<DOWN>\na\nb\nc\n"
        with pytest.raises(ImportError, match="Missing required section <SIZE>"):
            adapter.import_puzzle(content)

    def test_missing_grid_section_raises(self, adapter):
        content = "<ACROSS PUZZLE>\n<SIZE>\n3x3\n<ACROSS>\na\nb\nc\n<DOWN>\na\nb\nc\n"
        with pytest.raises(ImportError, match="Missing required section <GRID>"):
            adapter.import_puzzle(content)

    def test_missing_across_section_raises(self, adapter):
        content = "<ACROSS PUZZLE>\n<SIZE>\n3x3\n<GRID>\nXXX\nXXX\nXXX\n<DOWN>\na\nb\nc\n"
        with pytest.raises(ImportError, match="Missing required section <ACROSS>"):
            adapter.import_puzzle(content)

    def test_missing_down_section_raises(self, adapter):
        content = "<ACROSS PUZZLE>\n<SIZE>\n3x3\n<GRID>\nXXX\nXXX\nXXX\n<ACROSS>\na\nb\nc\n"
        with pytest.raises(ImportError, match="Missing required section <DOWN>"):
            adapter.import_puzzle(content)


class TestParseSizeErrors:
    def test_no_x_separator_raises(self, adapter):
        with pytest.raises(ImportError, match="Invalid <SIZE> format"):
            adapter._parse_size("55")

    def test_non_numeric_raises(self, adapter):
        with pytest.raises(ImportError, match="Non-numeric <SIZE>"):
            adapter._parse_size("axb")

    def test_non_square_raises(self, adapter):
        with pytest.raises(ImportError, match="Non-square"):
            adapter._parse_size("3x5")

    def test_zero_size_raises(self, adapter):
        with pytest.raises(ImportError, match="Invalid grid size"):
            adapter._parse_size("0x0")


class TestValidateGridErrors:
    def test_wrong_row_count_raises(self, adapter):
        content = VALID_3X3.replace("ABC\nDEF\nGHI", "ABC\nDEF")
        with pytest.raises(ImportError, match="Expected 3 grid rows"):
            adapter.import_puzzle(content)

    def test_wrong_row_length_raises(self, adapter):
        content = VALID_3X3.replace("ABC\nDEF\nGHI", "ABCD\nDEF\nGHI")
        with pytest.raises(ImportError, match="has 4 characters"):
            adapter.import_puzzle(content)

    def test_invalid_character_raises(self, adapter):
        content = VALID_3X3.replace("ABC\nDEF\nGHI", "A1C\nDEF\nGHI")
        with pytest.raises(ImportError, match="Invalid character"):
            adapter.import_puzzle(content)


class TestClueMismatchErrors:
    def test_across_clue_count_mismatch_raises(self, adapter):
        content = VALID_3X3.replace("Row one\nRow two\nRow three", "Row one\nRow two")
        with pytest.raises(ImportError, match="Across clue count mismatch"):
            adapter.import_puzzle(content)

    def test_down_clue_count_mismatch_raises(self, adapter):
        content = VALID_3X3.replace("Col one\nCol two\nCol three", "Col one")
        with pytest.raises(ImportError, match="Down clue count mismatch"):
            adapter.import_puzzle(content)
