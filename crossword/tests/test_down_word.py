from unittest import TestCase

from crossword import Puzzle, AcrossWord, DownWord
from crossword.tests import TestGrid, TestPuzzle, TestWord


class TestDownWord(TestCase):

    def test_get(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        AcrossWord(puzzle, 4).set_text("EFTS")
        AcrossWord(puzzle, 10).set_text("RIOT")
        AcrossWord(puzzle, 11).set_text("LOCAVORES")
        word = DownWord(puzzle, 7)
        actual = word.get_text()
        expected = "STS"
        self.assertEqual(expected, actual)

    def test_get_crossing_words(self):
        grid = TestGrid.get_good_grid()
        puzzle = Puzzle(grid)
        # 47 down is crossed by:
        # 46 across, 50 across, 54 across
        expected = [46, 50, 54]
        down_word = puzzle.get_down_word(47)
        actual = down_word.get_crossing_words()
        self.assertListEqual(expected, actual)

    def test_get_clear_word(self):
        puzzle = TestWord.create_puzzle()
        # 4 down is crossed by six across words
        # 1 across is complete
        # 14 across is complete
        # 17 across is complete
        # 20 across is complete
        # 23 across is complete
        # 28 across is NOT complete
        down_word = puzzle.get_down_word(4)
        expected = "SMEEC "
        actual = down_word.get_clear_word()
        self.assertEqual(expected, actual)
