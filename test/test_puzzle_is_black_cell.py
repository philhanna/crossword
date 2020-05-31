from unittest import TestCase

from test.test_puzzle import TestPuzzle


class TestPuzzleIsBlackCell(TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.puzzle = TestPuzzle.create_solved_atlantic_puzzle()

    def test_is_black_cell_true(self):
        self.assertTrue(self.puzzle.is_black_cell(2, 5))

    def test_is_black_cell_false(self):
        self.assertFalse(self.puzzle.is_black_cell(2, 6))

    def test_is_black_cell_false_numbered(self):
        self.assertFalse(self.puzzle.is_black_cell(1, 6))

    def test_is_black_cell_false_letter(self):
        self.assertFalse(self.puzzle.is_black_cell(3, 2))

    def test_is_black_cell_off_grid(self):
        self.assertFalse(self.puzzle.is_black_cell(15, 23))
