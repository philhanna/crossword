from crossword import AcrossWord, DownWord


class Solver:
    """ Solves the puzzle, if possible """
    def __init__(self, puzzle):
        self.puzzle = puzzle

        acrosswords = [
            AcrossWord(puzzle, nc.seq) for nc in puzzle.numbered_cells if nc.a
        ]
        downwords = [
            DownWord(puzzle, nc.seq) for nc in puzzle.numbered_cells if nc.d
        ]
        self.all_words = acrosswords + downwords

    def most_constrained(self):
        """ Finds the non-complete word with the fewest blanks """
        pass
