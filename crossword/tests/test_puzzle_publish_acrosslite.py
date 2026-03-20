import pytest

# Skip these tests - they test the old Flask-based UI which is being replaced
# in Phase 2 with a Flask-free HTTP server architecture
pytestmark = pytest.mark.skip(reason="Legacy Flask UI - being replaced in Phase 2")


class TestPuzzlePublishAcrossLite:

    def test_get_text(self):
        from crossword.tests import MockUser, TestPuzzle
        from crossword.ui import PuzzlePublishAcrossLite

        user = MockUser()
        puzzle = TestPuzzle.create_nyt_daily()
        publisher = PuzzlePublishAcrossLite(user, puzzle, "nyt0920")
        text = publisher.get_txt()
        assert "NINE.USUAL.IRON" in text
