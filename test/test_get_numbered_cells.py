from unittest import TestCase

from crossword.grid import Grid
from crossword.numbered_cell import NumberedCell


class TestGetNumberedCells(TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        grid = Grid(9)
        for r, c in [
            (1, 4),
            (1, 5),
            (2, 5),
            (5, 1),
            (5, 2),
            (6, 1)
        ]:
            grid.add_black_cell(r, c)
        self.nclist = grid.get_numbered_cells()

    def test_across_only(self):
        self.assertIn(NumberedCell(8, 2, 1, 4, 0), self.nclist)
        self.assertIn(NumberedCell(22, 9, 7, 3, 0), self.nclist)

    def test_down_only(self):
        self.assertIn(NumberedCell(5, 1, 7, 0, 9), self.nclist)

    def test_both(self):
        self.assertIn(NumberedCell(15, 6, 2, 8, 4), self.nclist)
