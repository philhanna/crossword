from crossword import AcrossWord, DownWord


class Solver:
    """ Solves the puzzle, if possible """
    def __init__(self, puzzle):
        """ Constructor """
        self.puzzle = puzzle
        acrosswords = [
            AcrossWord(puzzle, nc.seq) for nc in puzzle.numbered_cells if nc.a
        ]
        downwords = [
            DownWord(puzzle, nc.seq) for nc in puzzle.numbered_cells if nc.d
        ]
        self.all_words = acrosswords + downwords

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
