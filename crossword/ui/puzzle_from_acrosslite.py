import struct

from crossword import Grid, Puzzle, Word


class PuzzleFromAcrossLite:
    """ Reads a .puz file and creates a JSON string for the crossword editor """

    OFFSET_WIDTH = 0x002c
    OFFSET_WORDS = 0x0034
    BLACK_CELL = '.'

    def __init__(self, data):

        self.data = data
        self.offset = 0

        # Get the size
        self.offset = self.OFFSET_WIDTH
        self.n = n = self.read_byte()
        self.grid = grid = Grid(n)

        # Read the solution to get the black cell locations
        self.offset = self.OFFSET_WORDS
        for r in range(1, n+1):
            line = self.read_chunk(n)
            for c in range(1, n+1):
                letter = chr(line[c-1])
                if letter == self.BLACK_CELL:
                    grid.add_black_cell(r, c)

        # Create the puzzle, then go back and read the words
        self.puzzle = puzzle = Puzzle(grid)

        self.offset = self.OFFSET_WORDS
        for r in range(1, n+1):
            line = self.read_chunk(n)
            for c in range(1, n + 1):
                letter = chr(line[c-1])
                if not grid.is_black_cell(r, c):
                    puzzle.set_cell(r, c, letter)

        # Skip over the solution work area
        self.offset += n*n

        # Read the title and set it in the puzzle

        title = self.read_string()
        if title != "":
            puzzle.title = title

        # Skip the author and copyright lines
        s = self.read_string()     # author
        s = self.read_string()     # copyright

        # Read the clues
        for nc in puzzle.numbered_cells:
            if nc.a:        # Across word
                clue = self.read_string()
                puzzle.set_clue(nc.seq, Word.ACROSS, clue)
            if nc.d:        # Down word
                clue = self.read_string()
                puzzle.set_clue(nc.seq, Word.DOWN, clue)

        # Done
        self.jsonstr = puzzle.to_json()

    def read_byte(self):
        from_offset = self.offset
        self.offset += 1
        to_offset = self.offset
        data = self.data[from_offset:to_offset]
        return struct.unpack("<B", data)[0]

    def read_short(self):
        from_offset = self.offset
        self.offset += 2
        to_offset = self.offset
        data = self.data[from_offset:to_offset]
        return struct.unpack("<H", data)[0]

    def read_string(self):
        from_offset = self.offset
        while self.data[self.offset] != 0:
            self.offset += 1
        to_offset = self.offset
        chunk = self.data[from_offset:to_offset]
        s = str(chunk, "ISO-8859-1")
        self.offset += 1            # Skip the trailing null
        return s

    def read_chunk(self, count):
        from_offset = self.offset
        to_offset = self.offset + count
        data = self.data[from_offset:to_offset]
        self.offset += count
        return data
