from crossword import AcrossWord, DownWord


class Solver:
    """ Solves the puzzle, if possible """

    def __init__(self, puzzle):
        """ Constructor """
        self.puzzle = puzzle
        self.all_words = all_words = []
        for nc in puzzle.numbered_cells:
            if nc.a:
                all_words.append(AcrossWord(puzzle, nc.seq))
            if nc.d:
                all_words.append(DownWord(puzzle, nc.seq))

    def most_constrained(self):
        """ Returns the non-complete word with the fewest blanks """
        max_word = None
        max_blanks = 1000000
        for word in self.all_words:
            text = word.get_text()
            nblanks = text.count(' ')
            if 0 < nblanks < max_blanks:
                max_word = word
                max_blanks = nblanks
        return max_word

    def get_crossing_words(self, word):
        return [crosser
                for crosser in word.get_crossing_words()
                if not crosser.is_complete()]
