from unittest import TestCase

from test.test_puzzle import TestPuzzle
from word import *


class TestAcrossWord(TestCase):

    def test_get(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        DownWord(puzzle, 6).set_text("TOED")
        DownWord(puzzle, 7).set_text("STS")
        actual = AcrossWord(puzzle, 10).get_text()
        expected = "  OT"
        self.assertEqual(expected, actual)
