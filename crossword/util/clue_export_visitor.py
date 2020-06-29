import csv
from io import StringIO

from crossword import Visitor


class ClueExportVisitor(Visitor):

    def __init__(self):
        super().__init__()
        self.csvstr = None

    def visit_puzzle(self, puzzle):
        """ Writes the words and clues to a string in CSV format """
        with StringIO(newline=None) as fp:
            cfp = csv.writer(fp)

            # Column headings
            cfp.writerow(['seq', 'direction', 'word', 'clue'])

            # Across
            for seq in sorted(puzzle.across_words):
                across_word = puzzle.across_words[seq]
                direction = 'across'
                text = across_word.get_text()
                clue = across_word.get_clue()
                cfp.writerow([seq, direction, text, clue])

            # Down
            for seq in sorted(puzzle.down_words):
                down_word = puzzle.down_words[seq]
                direction = 'down'
                text = down_word.get_text()
                clue = down_word.get_clue()
                cfp.writerow([seq, direction, text, clue])

            value = fp.getvalue().strip() # Hack to work around final extra \n CSVWriter adds
            self.csvstr = value

    @property
    def csvstr(self):
        return self._csvstr

    @csvstr.setter
    def csvstr(self, value):
        self._csvstr = value
