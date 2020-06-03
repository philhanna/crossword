from unittest import TestCase

from test.test_puzzle import TestPuzzle
from word import AcrossWord


class TestWord(TestCase):

    def test_too_short(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        AcrossWord(puzzle, 4).set_text("EFT")
