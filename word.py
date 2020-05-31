from numbered_cell import NumberedCell


class Word:
    """ Abstract base class for Across and Down words """
    def __init__(self, puzzle, seq):
        self.puzzle = puzzle
        self.numbered_cell = self.lookup(seq)
        self.seq = seq
        self.length = 0
        self.clue = None

    def lookup(self, seq: int) -> NumberedCell:
        """ Given a sequence number, returns the numbered cell """
        nc = None
        for nc in self.puzzle.numbered_cells:
            if nc.seq == seq:
                return nc
        return nc

    def cell_iterator(self):
        """ Never called - overriden by subclasses """
        yield 0, 0

    def get_clue(self):
        """ Returns the word's clue """
        return self.clue

    def set_clue(self, clue):
        """ Sets the word's clue """
        self.clue = clue

    def get_text(self):
        """ Gets the word's text from the puzzle """
        text = ""
        for r, c in self.cell_iterator():
            letter = self.puzzle.get_cell(r, c)
            text += letter
        return text

    def set_text(self, text):
        """ Sets the word's text in the puzzle """
        text = text[:self.length]
        i = 0
        for r, c in self.cell_iterator():
            letter = text[i]
            self.puzzle.set_cell(r, c, letter)
            i += 1


class AcrossWord(Word):
    """ An across word """

    def __init__(self, puzzle, seq):
        super().__init__(puzzle, seq)
        self.length = self.numbered_cell.across_length

    def cell_iterator(self):
        r = self.numbered_cell.r
        c = self.numbered_cell.c
        for i in range(self.length):
            yield r, c
            c += 1


class DownWord(Word):
    """ A down word """

    def __init__(self, puzzle, seq):
        super().__init__(puzzle, seq)
        self.length = self.numbered_cell.down_length

    def cell_iterator(self):
        r = self.numbered_cell.r
        c = self.numbered_cell.c
        for i in range(self.length):
            yield r, c
            r += 1
