from crossword.grids import Grid
from crossword.util import ToSVG


class GridToSVG(ToSVG):
    """ Generates SVG with an image of the puzzle """

    def __init__(self, grid: Grid, *args, **kwargs):
        super().__init__(grid.n, *args, **kwargs)
        self.grid = grid
        self.black_cells = grid.get_black_cells()
        self.numbered_cells = grid.get_numbered_cells()
