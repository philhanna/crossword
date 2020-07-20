from unittest import TestCase

from crossword.tests import MockUser, TestPuzzle
from crossword.ui import PuzzlePublishAcrossLite


class TestPuzzlePublishAcrossLite(TestCase):

    def test_get_text(self):
        user = MockUser()
        puzzle = TestPuzzle.create_nyt_daily()
        publisher = PuzzlePublishAcrossLite(user, puzzle, "nyt0920")
        text = publisher.get_txt()
        self.assertTrue("NINE.USUAL.IRON" in text, text)
