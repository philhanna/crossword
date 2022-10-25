from unittest import TestCase

from crossword.ui import PuzzlePublishAcrossLite
from tests import MockUser, load_test_object


class TestPuzzlePublishAcrossLite(TestCase):

    def test_get_text(self):
        user = MockUser()
        puzzle = load_test_object("nyt_daily")
        publisher = PuzzlePublishAcrossLite(user, puzzle, "nyt0920")
        text = publisher.get_txt()
        self.assertTrue("NINE.USUAL.IRON" in text, text)
