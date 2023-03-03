from crossword.words import Word


class DownWord(Word):
    """ A down word """

    def __init__(self, puzzle, seq):
        super().__init__(puzzle, seq)
        self.length = self.numbered_cell.d
        self.direction = Word.DOWN
        self.location = f"{seq} down"

    def cell_iterator(self) -> (int, int):
        """ Generator for iterating through the cells of a down word """
        r = self.numbered_cell.r
        c = self.numbered_cell.c
        for i in range(self.length):
            yield r, c
            r += 1

    def get_crossing_word(self, r: int, c: int) -> Word:
        x = 0
        for cprime in range(c, 0, -1):
            if self.puzzle.is_black_cell(r, cprime):
                x = cprime
                break
        x += 1
        nc = self.puzzle.get_numbered_cell(r, x)
        return self.puzzle.get_across_word(nc.seq)
