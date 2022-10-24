import os.path
import tempfile
from unittest import TestCase

from crossword.util import PuzzleToSVG
from tests import TestPuzzle


class TestPuzzleToSVG(TestCase):

    def test_write(self):
        puzzle = TestPuzzle.create_atlantic_puzzle_with_some_words()
        app = PuzzleToSVG(puzzle)
        xmlstr = app.generate_xml()
        filename = os.path.join(tempfile.gettempdir(), "atlantic.svg")
        with open(filename, "w") as fp:
            print(xmlstr, file=fp)

    def test_write_large(self):
        puzzle = TestPuzzle.create_nyt_puzzle()
        app = PuzzleToSVG(puzzle)
        xmlstr = app.generate_xml()
        filename = os.path.join(tempfile.gettempdir(), "nyt.svg")
        with open(filename, "w") as fp:
            print(xmlstr, file=fp)

    def test_write_scaled(self):
        puzzle = TestPuzzle.create_atlantic_puzzle_with_some_words()
        app = PuzzleToSVG(puzzle, scale=0.375)
        xmlstr = app.generate_xml()
        filename = os.path.join(tempfile.gettempdir(), "atlantic38.svg")
        with open(filename, "w") as fp:
            print(xmlstr, file=fp)
