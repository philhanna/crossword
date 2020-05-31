from unittest import TestCase

from test.test_puzzle import TestPuzzle
from word import *


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
