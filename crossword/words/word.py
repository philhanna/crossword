from crossword.cells import NumberedCell


class Word:
    """ Abstract base class for Across and Down words """

    # Enumerated values of word direction.
    # Safer to use these, like Word.ACROSS and Word.DOWN, instead of string values

    ACROSS = "A"
    DOWN = "D"

    def __init__(self, puzzle, seq):
        self.puzzle = puzzle
        self.numbered_cell = self.lookup(seq)
        self.seq = seq
        self.direction = None
        self.length = 0
        self.clue = None
        self.location = None

    def lookup(self, seq: int) -> NumberedCell:
        """ Given a sequence number, returns the numbered cell """
        for nc in self.puzzle.numbered_cells:
            if nc.seq == seq:
                return nc
        return None

    def cell_iterator(self):
        """ Never called - overriden by subclasses """
        raise RuntimeError("cell_iterator must be implemented by subclasses")

    def get_crossing_word(self, r, c):
        """ Never called - overridden by subclasses """
        raise RuntimeError("get_crossing_word must be implemented by subclasses")

    def get_crossing_words(self):
        """ Finds the list of words that cross this one

        Algorithm:
            - Get the row and column of this word
            - Loop through its cells left to right (top to bottom)
            - For each (r, c) in the word, find the down word (across word)
            that contains it by looking for to the border of
            a black cell or the edge of the puzzle
            - Add the crossing word to the output list
        """
        crossing_words = []
        for r, c in self.cell_iterator():
            crossing_word = self.get_crossing_word(r, c)
            crossing_words.append(crossing_word)
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
            crossing_word = crossing_words[i]
            if crossing_word.is_complete():
                text = self.get_text()
                letter = text[i]
                after += letter
            else:
                after += " "
        return after

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
            if not letter:
                letter = " "
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

    def __str__(self):
        text = self.get_text().replace(' ', '.')
        sb = f"{self.location} {self.length} letters '{text}'"
        return sb




