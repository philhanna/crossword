from unittest import TestCase

from puzzle import Puzzle
from test.test_grid import TestGrid
from test.test_puzzle import TestPuzzle
from test.test_word import TestWord
from word import *


class TestAcrossWord(TestCase):

    def test_get(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        DownWord(puzzle, 6).set_text("TOED")
        DownWord(puzzle, 7).set_text("STS")
        actual = AcrossWord(puzzle, 10).get_text()
        expected = "  OT"
        self.assertEqual(expected, actual)

    def test_get_crossing_words(self):
        grid = TestGrid.get_good_grid()
        puzzle = Puzzle(grid)
        # 20 across is crossed by:
        # 3 down, 14 down, 21 down, 4 down, and 5 down
        expected = [3, 14, 21, 4, 5]
        across_word = puzzle.get_across_word(20)
        actual = across_word.get_crossing_words()
        self.assertListEqual(expected, actual)

    def test_get_clear_word(self):
        puzzle = TestWord.create_puzzle()
        # 10 across is crossed by four down words
        # 10 down is complete
        # 11 down is not complete
        # 12 down is not complete
        # 13 down is not complete
        across_word = puzzle.get_across_word(10)
        expected = "E   "
        actual = across_word.get_clear_word()
        self.assertEqual(expected, actual)
