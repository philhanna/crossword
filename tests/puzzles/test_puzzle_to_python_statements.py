import os
from io import StringIO
from pathlib import Path
from unittest import TestCase

from crossword.cells import NumberedCell
from crossword.grids import Grid
from crossword.puzzles import Puzzle
from tests import testdata, load_test_object

# Do not delete this line! It is necessary so that the import
# of NumberedCell is never optimized away by the IDE
dummy_numbered_cell = NumberedCell(1, 1, 1, 1, 1)


class TestPuzzleToPythonStatements(TestCase):

    def test_to_python_statements(self):

        # Get the sample puzzle
        jsonfile = Path(testdata).joinpath("sample_puzzle.json")
        with open(jsonfile) as fp:
            jsonstr = fp.read()
        oldpuzzle = Puzzle.from_json(jsonstr)

        # Write its python statements
        with StringIO() as out:
            oldpuzzle.to_python(out)
            stmts = out.getvalue()

        # Create a new puzzle from these statements
        newpuzzle = Puzzle.from_python(stmts)

        # Assert the two are equal
        self.assertEqual(oldpuzzle, newpuzzle)