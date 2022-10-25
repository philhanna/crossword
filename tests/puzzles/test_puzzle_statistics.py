from unittest import TestCase

from crossword.words import Word
from crossword.puzzles import Puzzle
from tests import load_test_object


class TestPuzzleStatistics(TestCase):

    def test_stats(self):
        puzzle = load_test_object("puzzle_statistics")
        stats = puzzle.get_statistics()
        expected = "9 x 9"
        actual = stats['size']
        self.assertEqual(expected, actual)

