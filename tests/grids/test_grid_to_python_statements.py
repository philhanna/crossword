from io import StringIO
from pathlib import Path
from unittest import TestCase

from crossword.cells import NumberedCell
from crossword.grids import Grid
from tests import testdata

# Do not delete this line! It is necessary so that the import
# of NumberedCell is never optimized away by the IDE
dummy_numbered_cell = NumberedCell(1, 1, 1, 1, 1)


class TestGridToPythonStatements(TestCase):

    def test_to_python_statements(self):
        filename = Path(testdata).joinpath("sample_grid.json")
        with open(filename) as fp:
            jsonstr = fp.read()
        oldgrid = Grid.from_json(jsonstr)

        with StringIO() as fp:
            oldgrid.to_python(fp)
            stmts = fp.getvalue()

        newgrid = Grid.from_python(stmts)

        self.assertEqual(oldgrid, newgrid)
