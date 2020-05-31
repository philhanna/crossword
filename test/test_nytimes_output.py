import os
import tempfile
from unittest import TestCase

from nytimes_output import NYTimesOutput
from test.test_puzzle import TestPuzzle


class TestNYTimesOutput(TestCase):

    def test_write_big_nyt(self):
        puzzle = TestPuzzle.create_nyt_puzzle()
        filename = os.path.join(tempfile.gettempdir(), "nyt.html")
        app = NYTimesOutput(filename, puzzle)
        app.generate_svg()
        app.generate_html()

    def test_write_daily_nyt(self):
        puzzle = TestPuzzle.create_nyt_daily()
        filename = os.path.join(tempfile.gettempdir(), "nyt_daily.html")
        app = NYTimesOutput(filename, puzzle)
        app.generate_svg()
        app.generate_html()

    def test_write_atlantic(self):
        puzzle = TestPuzzle.create_atlantic_puzzle_with_some_words()
        filename = os.path.join(tempfile.gettempdir(), "atlantic.html")
        app = NYTimesOutput(filename, puzzle)
        app.generate_svg()
        app.generate_html()
