from crossword.tests import TestPuzzle


class TestPuzzleGetNumberedCell:

    def setup_method(self):
        self.puzzle = TestPuzzle.create_solved_atlantic_puzzle()

    def test_get_across_only(self):
        # 8 across
        nc = self.puzzle.get_numbered_cell(2, 1)
        assert 8 == nc.seq
        assert nc.a > 0
        assert nc.d == 0

    def test_get_down_only(self):
        # 3 down
        nc = self.puzzle.get_numbered_cell(1, 3)
        assert 3 == nc.seq
        assert nc.a == 0
        assert nc.d > 0

    def test_get_both(self):
        # 15 across and down
        nc = self.puzzle.get_numbered_cell(6, 2)
        assert 15 == nc.seq
        assert nc.a > 0
        assert nc.d > 0

    def test_with_black_cell(self):
        nc = self.puzzle.get_numbered_cell(2, 5)
        assert nc is None

    def test_with_letter_cell(self):
        nc = self.puzzle.get_numbered_cell(2, 2)
        assert nc is None

    def test_off_grid(self):
        nc = self.puzzle.get_numbered_cell(19, 53)
        assert nc is None
