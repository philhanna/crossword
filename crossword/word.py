from crossword.numbered_cell import NumberedCell


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
        if len(text) < self.length:
            text += " " * self.length
            text = text[:self.length]
        i = 0
        for r, c in self.cell_iterator():
            letter = text[i]
            self.puzzle.set_cell(r, c, letter)
            i += 1

    def is_complete(self):
        """ Returns True if this word has no blanks """
        for (r, c) in self.cell_iterator():
            letter = self.puzzle.get_cell(r, c)
            if letter == ' ':
                return False
        return True


class AcrossWord(Word):
    """ An across word """

    def __init__(self, puzzle, seq):
        super().__init__(puzzle, seq)
        self.length = self.numbered_cell.across_length

    def cell_iterator(self):
        """ Generator for iterating through the cells of an across word """
        r = self.numbered_cell.r
        c = self.numbered_cell.c
        for i in range(self.length):
            yield r, c
            c += 1

    def get_crossing_words(self):
        """ Finds the list of down words that cross this one

        Algorithm:
            - Get the row and column of this word
            - Loop through its cells left to right
            - For each (r, c) in the word, find the down word
            that contains it by looking up to the border of
            a black cell or the edge of the puzzle
            - Add the seq of the down word to the output list
        """
        crossing_words = []
        for r, c in self.cell_iterator():
            x = 0
            for rprime in range(r, 0, -1):
                if self.puzzle.is_black_cell(rprime, c):
                    x = rprime
                    break
            x += 1
            nc = self.puzzle.get_numbered_cell(x, c)
            if nc:
                crossing_words.append(nc.seq)
        return crossing_words

    def get_clear_word(self):
        """ Sets to blank all letters of this word
        that are not intersected with completed
        crossing words.

        Algorithm:
            - Get the list of crossing words
            - If the length of the list is the same as
            the length of this word:
            - Loop through the cells left to right
            - If the crossing word is complete (no blanks),
            then set the corresponding letter in this word to blank
        """
        before = self.get_text()
        after = ""
        crossing_words = self.get_crossing_words()
        if len(crossing_words) != self.length:
            # TODO: This is really an error if the puzzle is fully checked
            return before
        for i in range(self.length):
            seq = crossing_words[i]
            down_word = self.puzzle.get_down_word(seq)
            if down_word.is_complete():
                text = self.get_text()
                letter = text[i]
                after += letter
            else:
                after += " "
        return after


class DownWord(Word):
    """ A down word """

    def __init__(self, puzzle, seq):
        super().__init__(puzzle, seq)
        self.length = self.numbered_cell.down_length

    def cell_iterator(self):
        """ Generator for iterating through the cells of a down word """
        r = self.numbered_cell.r
        c = self.numbered_cell.c
        for i in range(self.length):
            yield r, c
            r += 1

    def get_crossing_words(self):
        """ Finds the list of across words that cross this one

        Algorithm:
            - Get the row and column of this word
            - Loop through its cells top to bottom
            - For each (r, c) in the word, find the across word
            that contains it by looking up to the border of
            a black cell or the edge of the puzzle
            - Add the seq of the across word to the output list
        """
        crossing_words = []
        for r, c in self.cell_iterator():
            x = 0
            for cprime in range(c, 0, -1):
                if self.puzzle.is_black_cell(r, cprime):
                    x = cprime
                    break
            x += 1
            nc = self.puzzle.get_numbered_cell(r, x)
            if nc:
                crossing_words.append(nc.seq)
        return crossing_words

    def get_clear_word(self):
        """ Sets to blank all letters of this word
        that are not intersected with completed
        crossing words.

        Algorithm:
            - Get the list of crossing words
            - If the length of the list is the same as
            the length of this word:
            - Loop through the cells top to bottom
            - If the crossing word is complete (no blanks),
            then set the corresponding letter in this word to blank
        """
        before = self.get_text()
        after = ""
        crossing_words = self.get_crossing_words()
        if len(crossing_words) != self.length:
            # TODO: This is really an error if the puzzle is fully checked
            return before
        for i in range(self.length):
            seq = crossing_words[i]
            across_word = self.puzzle.get_across_word(seq)
            if across_word.is_complete():
                text = self.get_text()
                letter = text[i]
                after += letter
            else:
                after += " "
        return after
