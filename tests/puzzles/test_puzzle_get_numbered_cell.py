from unittest import TestCase

from tests import load_test_puzzle


class TestPuzzleGetNumberedCell(TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.puzzle = load_test_puzzle("solved_atlantic_puzzle")

    def test_get_across_only(self):
        # 8 across
        nc = self.puzzle.get_numbered_cell(2, 1)
        self.assertEqual(8, nc.seq)
        self.assertTrue(nc.a > 0)
        self.assertTrue(nc.d == 0)

    def test_get_down_only(self):
        # 3 down
        nc = self.puzzle.get_numbered_cell(1, 3)
        self.assertEqual(3, nc.seq)
        self.assertTrue(nc.a == 0)
        self.assertTrue(nc.d > 0)

    def test_get_both(self):
        # 15 across and down
        nc = self.puzzle.get_numbered_cell(6, 2)
        self.assertEqual(15, nc.seq)
        self.assertTrue(nc.a > 0)
        self.assertTrue(nc.d > 0)

    def test_with_black_cell(self):
        nc = self.puzzle.get_numbered_cell(2, 5)
        self.assertIsNone(nc)

    def test_with_letter_cell(self):
        nc = self.puzzle.get_numbered_cell(2, 2)
        self.assertIsNone(nc)

    def test_off_grid(self):
        nc = self.puzzle.get_numbered_cell(19, 53)
        self.assertIsNone(nc)
