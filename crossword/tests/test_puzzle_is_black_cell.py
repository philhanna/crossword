from crossword.tests import TestPuzzle


class TestPuzzleIsBlackCell:

    def setup_method(self):
        self.puzzle = TestPuzzle.create_solved_atlantic_puzzle()

    def test_is_black_cell_true(self):
        assert self.puzzle.is_black_cell(2, 5)

    def test_is_black_cell_false(self):
        assert not self.puzzle.is_black_cell(2, 6)

    def test_is_black_cell_false_numbered(self):
        assert not self.puzzle.is_black_cell(1, 6)

    def test_is_black_cell_false_letter(self):
        assert not self.puzzle.is_black_cell(3, 2)

    def test_is_black_cell_off_grid(self):
        assert not self.puzzle.is_black_cell(15, 23)
