from crossword.tests import TestPuzzle


class TestPuzzleCrossing:

    def setup_method(self):
        self.puzzle = TestPuzzle.create_nyt_daily()

    def test_gets_across(self):
        actual = self.puzzle.get_numbered_cell_across(5, 9)
        assert 24 == actual.seq

    def test_gets_across_when_numbered(self):
        actual = self.puzzle.get_numbered_cell_across(2, 1)
        assert 14 == actual.seq

    def test_gets_nothing_across_for_black_cell(self):
        actual = self.puzzle.get_numbered_cell_across(2, 5)
        assert actual is None

    def test_gets_nothing_across_when_off_grid(self):
        actual = self.puzzle.get_numbered_cell_across(55, 66)
        assert actual is None

    def test_gets_down(self):
        actual = self.puzzle.get_numbered_cell_down(5, 9)
        assert 8 == actual.seq

    def test_gets_down_when_numbered(self):
        actual = self.puzzle.get_numbered_cell_down(5, 15)
        assert 27 == actual.seq

    def test_gets_nothing_down_for_black_cell(self):
        actual = self.puzzle.get_numbered_cell_down(3, 11)
        assert actual is None

    def test_gets_nothing_down_when_off_grid(self):
        actual = self.puzzle.get_numbered_cell_across(-1, 45)
        assert actual is None
