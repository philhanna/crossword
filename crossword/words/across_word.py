from crossword.words import Word


class AcrossWord(Word):
    """ An across word """

    def __init__(self, puzzle, seq):
        super().__init__(puzzle, seq)
        self.length = self.numbered_cell.a
        self.direction = Word.ACROSS
        self.location = f"{seq} across"

    def cell_iterator(self):
        """ Generator for iterating through the cells of an across word """
        r = self.numbered_cell.r
        c = self.numbered_cell.c
        for i in range(self.length):
            yield r, c
            c += 1

    def get_crossing_word(self, r, c):
        x = 0
        for rprime in range(r, 0, -1):
            if self.puzzle.is_black_cell(rprime, c):
                x = rprime
                break
        x += 1
        nc = self.puzzle.get_numbered_cell(x, c)
        return self.puzzle.get_down_word(nc.seq)
