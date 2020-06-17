import csv
from io import StringIO

from crossword import Visitor


class ClueImportVisitor(Visitor):

    def __init__(self, csvstr):
        super().__init__()
        self.csvstr = csvstr

    def visit_puzzle(self, puzzle):
        """ Reads the words and clues from a string in CSV format """
        with StringIO(self.csvstr) as fp:
            cfp = csv.reader(fp)
            next(cfp)  # Skip column headings
            for row in cfp:
                seq = int(row[0])
                direction = row[1]
                text = row[2]
                clue_text = row[3]
                if direction == 'across':
                    word = puzzle.get_across_word(seq)
                    if not word:
                        errmsg = f'{seq} across is not defined'
                        raise RuntimeError(errmsg)
                    previous_text = word.get_text()
                    if text != previous_text:
                        errmsg = f'Word at {seq} across should be "{previous_text}", not "{text}"'
                        raise RuntimeError(errmsg)
                    word.set_clue(clue_text)
                elif direction == 'down':
                    word = puzzle.get_down_word(seq)
                    if not word:
                        errmsg = f'{seq} down is not defined'
                        raise RuntimeError(errmsg)
                    previous_text = word.get_text()
                    if text != previous_text:
                        errmsg = f'Word at {seq} down should be "{previous_text}", not "{text}"'
                        raise RuntimeError(errmsg)
                    word.set_clue(clue_text)
                else:
                    errmsg = f'Direction is "{direction}", not "across" or "down"'
                    raise RuntimeError(errmsg)

    @property
    def csvstr(self):
        return self._csvstr

    @csvstr.setter
    def csvstr(self, value):
        self._csvstr = value
