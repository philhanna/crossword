import json

from numbered_cell import NumberedCell


class Grid:
    """ An empty n x n cells with black cells and numbered cells """

    def __init__(self, n):
        self.n = n
        self.black_cells = set()
        self.numbered_cells = None  # Use lazy instantiation

    def symmetric_point(self, r, c):
        """ Returns the (r, c) of the cell at 180 degrees rotation """
        if not (1 <= r <= self.n) or not (1 <= c <= self.n):
            return None
        rprime = self.n + 1 - r
        cprime = self.n + 1 - c
        return rprime, cprime

    def add_black_cell(self, r, c):
        """ Mark cell (r, c) as black (also its symmetric cell) """
        self.black_cells.add((r, c))
        self.black_cells.add(self.symmetric_point(r, c))

    def remove_black_cell(self, r, c):
        """ Mark cell (r, c) as not black (also its symmetric cell) """
        self.black_cells.discard((r, c))
        self.black_cells.discard(self.symmetric_point(r, c))

    def is_black_cell(self, r, c):
        """ Returns True is there is a black cell at (r, c) """
        return (r, c) in self.black_cells

    def get_black_cells(self):
        """ Returns the list of (r, c) for each black cell """
        bclist = []
        n = self.n
        for r in range(1, n + 1):
            for c in range(1, n + 1):
                if self.is_black_cell(r, c):
                    bclist.append((r, c))
        return bclist

    def get_numbered_cells(self):
        """ Finds list of all cells that start a word """
        n = self.n
        nclist = []
        for r in range(1, n + 1):
            for c in range(1, n + 1):

                # Ignore black cells
                if self.is_black_cell(r, c):
                    continue

                # See if this is the start of an "across" word
                across_length = 0
                if c == 1 or self.is_black_cell(r, c - 1):
                    # This is the beginning of an "across" word
                    # Find the (r, c) of the stopping point, which is either
                    # the next black cell, or the edge of the puzzle
                    for cprime in range(c + 1, n + 1):
                        if self.is_black_cell(r, cprime):
                            across_length = cprime - c
                            break
                        if cprime == n:
                            across_length = cprime + 1 - c
                            break
                if across_length < 2:
                    across_length = 0

                # Same for "down" word
                down_length = 0
                if r == 1 or self.is_black_cell(r - 1, c):
                    # This is the beginning of a "down" word
                    # Find the (r, c) of the stopping point, which is either
                    # the next black cell, or the edge of the puzzle
                    for rprime in range(r + 1, n + 1):
                        if self.is_black_cell(rprime, c):
                            down_length = rprime - r
                            break
                        if rprime == n:
                            down_length = rprime + 1 - r
                            break
                if down_length < 2:
                    down_length = 0

                if across_length or down_length:
                    seq = 1 + len(nclist)
                    numbered_cell = NumberedCell(seq, r, c, a=across_length, d=down_length)
                    nclist.append(numbered_cell)
        self.numbered_cells = nclist
        return nclist

    def to_json(self):
        image = dict()
        image['n'] = self.n
        image['black_cells'] = self.get_black_cells()
        nclist = list()
        for numbered_cell in self.get_numbered_cells():
            ncdict = vars(numbered_cell)
            nclist.append(ncdict)
        image['numbered_cells'] = nclist

        jsonstr = json.dumps(image, indent=2)
        return jsonstr

    @staticmethod
    def from_json(jsonstr):
        image = json.loads(jsonstr)
        n = image['n']
        grid = Grid(n)
        for r, c in image['black_cells']:
            grid.add_black_cell(r, c)
        # Add the numbered cells
        grid.get_numbered_cells()
        return grid

    def __str__(self):
        sb = f'+{"-" * (self.n * 2 - 1)}+' + "\n"
        for r in range(1, self.n + 1):
            if r > 1:
                sb += '\n'
            row = "|"
            for c in range(1, self.n + 1):
                cell = "*" if self.is_black_cell(r, c) else " "
                if c > 1:
                    row += "|"
                row += cell
            row += "|"
            sb += row
        sb += "\n"
        sb += f'+{"-" * (self.n * 2 - 1)}+'
        return sb
