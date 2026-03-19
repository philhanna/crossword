from crossword.tests import MockUser, TestPuzzle
from crossword.ui import PuzzlePublishAcrossLite


class TestPuzzlePublishAcrossLite:

    def test_get_text(self):
        user = MockUser()
        puzzle = TestPuzzle.create_nyt_daily()
        publisher = PuzzlePublishAcrossLite(user, puzzle, "nyt0920")
        text = publisher.get_txt()
        assert "NINE.USUAL.IRON" in text
