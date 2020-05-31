import os.path
import tempfile
from unittest import TestCase

from clue_export_visitor import ClueExportVisitor
from test.test_puzzle import TestPuzzle


class TestExportClues(TestCase):

    def test_export_clues(self):
        visitor = ClueExportVisitor()
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        puzzle.accept(visitor)
        filename = os.path.join(tempfile.gettempdir(), 'test_export_clues') + ".csv"
        csvstr = visitor.csvstr
        with open(filename, "w") as fp:
            print(csvstr, file=fp)
