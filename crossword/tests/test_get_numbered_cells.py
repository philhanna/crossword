from crossword import Grid, NumberedCell


class TestGetNumberedCells:

    def setup_method(self):
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
        assert NumberedCell(8, 2, 1, 4, 0) in self.nclist
        assert NumberedCell(22, 9, 7, 3, 0) in self.nclist

    def test_down_only(self):
        assert NumberedCell(5, 1, 7, 0, 9) in self.nclist

    def test_both(self):
        assert NumberedCell(15, 6, 2, 8, 4) in self.nclist
