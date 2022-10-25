from unittest import TestCase

from tests import load_test_object


class TestPuzzleCrossing(TestCase):

    def setUp(self):
        self.puzzle = load_test_object("nyt_daily")

    def test_gets_across(self):
        actual = self.puzzle.get_numbered_cell_across(5, 9)
        self.assertEqual(24, actual.seq)

    def test_gets_across_when_numbered(self):
        actual = self.puzzle.get_numbered_cell_across(2, 1)
        self.assertEqual(14, actual.seq)

    def test_gets_nothing_across_for_black_cell(self):
        actual = self.puzzle.get_numbered_cell_across(2, 5)
        self.assertIsNone(actual)

    def test_gets_nothing_across_when_off_grid(self):
        actual = self.puzzle.get_numbered_cell_across(55, 66)
        self.assertIsNone(actual)

    def test_gets_down(self):
        actual = self.puzzle.get_numbered_cell_down(5, 9)
        self.assertEqual(8, actual.seq)

    def test_gets_down_when_numbered(self):
        actual = self.puzzle.get_numbered_cell_down(5, 15)
        self.assertEqual(27, actual.seq)

    def test_gets_nothing_down_for_black_cell(self):
        actual = self.puzzle.get_numbered_cell_down(3, 11)
        self.assertIsNone(actual)

    def test_gets_nothing_down_when_off_grid(self):
        actual = self.puzzle.get_numbered_cell_across(-1, 45)
        self.assertIsNone(actual)
