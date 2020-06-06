import json

from numbered_cell import NumberedCell


class Grid:
    """ An empty n x n cells with black cells and numbered cells """

    def __init__(self, n):
        """ Creates a new Grid object of the specified size """
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
        """ Marks cell (r, c) as black (also its symmetric cell) """
        self.black_cells.add((r, c))
        self.black_cells.add(self.symmetric_point(r, c))
        self.numbered_cells = None

    def remove_black_cell(self, r, c):
        """ Marks cell (r, c) as not black (also its symmetric cell) """
        self.black_cells.discard((r, c))
        self.black_cells.discard(self.symmetric_point(r, c))
        self.numbered_cells = None

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

        # If already calculated, return that (lazy instantiation)

        if self.numbered_cells:
            return self.numbered_cells

        # Otherwise calculate and store

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
        """ Returns the JSON string representation of the Grid """
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
        """ Creates a Grid object from its JSON string representation """
        image = json.loads(jsonstr)
        n = image['n']
        grid = Grid(n)
        for r, c in image['black_cells']:
            grid.add_black_cell(r, c)

        # Add the numbered cells

        grid.get_numbered_cells()
        return grid

    def validate(self):
        """ Validates the grid according to the NYTimes rules """

        # 1. Crosswords must have black square symmetry, which typically comes
        # in the form of 180-degree rotational symmetry
        # 2. Crosswords must have all-over interlock;
        # 3. Crosswords must not have unchecked squares 
        # (i.e., all letters must be found in both Across and Down answers);
        # 4. All answers must be at least 3 letters long;
        # 5. Black squares should be used in moderation.
        # (Source: NYTimes submissions guidelines)
        #
        # Item 1 is taken care of by virtue of the symmetric point
        # awareness of add_black_cell and remove_black_cell.
        #
        # Item 5 is subjective

        ok = True
        messages = ""

        for fun in (self.validate_interlock,
                    self.validate_unchecked_squares,
                    self.validate_minimum_word_length):
            errmsg = fun()
            if errmsg:
                ok = False
                messages += errmsg + "\n"

        return ok, messages

    def validate_interlock(self):
        """ No islands of white cells enclosed in black cells """

        # ==============================================================
        # Create a matrix corresponding to the grid,
        # with each cell having the value of its partition number
        # (which we will calculate).  Call the matrix "partition".
        #
        # The partition number is (r, c), where r and c
        # are the row and column of the first cell in the partition.
        # We'll initialize them all to (0, 0).
        # ==============================================================

        partition = {}
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                if self.is_black_cell(r, c):
                    continue
                partition[(r, c)] = (0, 0)

        # ==============================================================
        # Inner function which recursively marks its immediate neighbors
        # (up, down, left, right) as belonging to the same partition.
        # ==============================================================

        def mark_partition(r, c, pr, pc):

            if r < 1 or r > self.n or c < 1 or c > self.n:
                return      # Off the grid

            if self.is_black_cell(r, c):
                return      # Black cell

            if partition[(r, c)] != (0, 0):
                return      # Already marked

            # Otherwise, add this to the partition

            partition[(r, c)] = (pr, pc)
            mark_partition(r-1, c, pr, pc)  # Up
            mark_partition(r, c+1, pr, pc)  # Right
            mark_partition(r, c-1, pr, pc)  # Left
            mark_partition(r+1, c, pr, pc)  # Down

        # ==============================================================
        # Now go through the whole grid, left to right, top to bottom.
        # If a cell does not yet belong to a partition, call
        # mark_partition on it.
        # ==============================================================

        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                if self.is_black_cell(r, c):
                    continue
                if partition[(r, c)] == (0, 0):
                    mark_partition(r, c, r, c)

        # ==============================================================
        # Everything is now marked.  Create the set of all the distict
        # partitions.  We are expecting only one if the grid has
        # all-over interlock
        # ==============================================================

        partitions = set()
        for r in range(1, self.n + 1):
            for c in range(1, self.n + 1):
                if self.is_black_cell(r, c):
                    continue
                markr, markc = partition[(r, c)]
                partitions.add((markr, markc))

        # ==============================================================
        # If there are more than one partitions, format an appropriate
        # set of error messages
        # ==============================================================

        errmsg = ""
        if len(partitions) > 1:
            errmsg += "*** No all-over interlock: ***\n"
            np = 0
            for r, c in sorted(list(partitions)):
                np += 1
                errmsg += f"Cell at ({r}, {c}) starts partition {np}" + "\n"

        # ==============================================================
        # Done
        # ==============================================================

        return errmsg.strip()

    def validate_unchecked_squares(self):
        """ Crosswords must not have unchecked squares:
            All letters must be found in both Across and Down answers
        """
        errmsg = ""

        aset = set()  # All the (r, c) in across words
        dset = set()  # All the (r, c) in down words
        ncdict = {}
        for nc in self.get_numbered_cells():
            r = nc.r
            c = nc.c
            for i in range(nc.across_length):
                aset.add((r, c))
                ncdict[(r, c)] = nc
                c += 1
            r = nc.r
            c = nc.c
            for i in range(nc.down_length):
                dset.add((r, nc.c))
                ncdict[(r, c)] = nc
                r += 1
        across_but_not_down = aset - dset
        down_but_not_across = dset - aset
        all_checked = True
        if across_but_not_down:
            for r, c in across_but_not_down:
                all_checked = False
                nc = ncdict[(r, c)]
                errmsg += f"({r},{c}) is part of {nc.seq} across but no down word" + "\n"
        if down_but_not_across:
            for r, c in down_but_not_across:
                all_checked = False
                nc = ncdict[(r, c)]
                errmsg += f"({r},{c}) is part of {nc.seq} down but no across word" + "\n"

        if all_checked:
            return ""

        return "*** Some unchecked cells: ***\n" + errmsg.strip()

    def validate_minimum_word_length(self):
        """ All words must be at least three characters long """
        errmsg = ""
        all_long = True
        for nc in self.get_numbered_cells():
            if 0 < nc.across_length < 3:
                all_long = False
                errmsg += f"{nc.seq} across is only {nc.across_length} letters long\n"
            if 0 < nc.down_length < 3:
                all_long = False
                errmsg += f"{nc.seq} down is only {nc.down_length} letters long\n"

        if all_long:
            return ""

        return "*** Some words shorter than 3 letters: ***\n" + errmsg.strip()

    def __str__(self):
        """ Returns the string representation of the Grid """
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
