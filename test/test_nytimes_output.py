import os
import tempfile
from unittest import TestCase

from crossword.nytimes_output import NYTimesOutput
from test.test_puzzle import TestPuzzle


class TestNYTimesOutput(TestCase):

    ############################################################
    # Unit tests
    ############################################################

    def test_write_big_nyt(self):
        puzzle = TestPuzzle.create_nyt_puzzle()
        basename = "nyt"
        self.runtest(puzzle, basename)

    def test_write_daily_nyt(self):
        puzzle = TestPuzzle.create_nyt_daily()
        basename = "nyt_daily"
        self.runtest(puzzle, basename)

    def test_write_atlantic(self):
        puzzle = TestPuzzle.create_atlantic_puzzle_with_some_words()
        basename = "atlantic"
        self.runtest(puzzle, basename)

    ############################################################
    # Internal methods
    ############################################################

    def runtest(self, puzzle, basename):
        app = NYTimesOutput(puzzle, basename)
        tempdir = tempfile.gettempdir()

        filename = os.path.join(tempdir, basename + ".html")
        content = app.get_html()
        with open(filename, "wt") as fp:
            fp.write(content)

        filename = os.path.join(tempdir, basename + ".svg")
        content = app.get_svg()
        with open(filename, "wt") as fp:
            fp.write(content)
