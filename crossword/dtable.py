import os.path
import pickle
from collections import defaultdict

INFILE = os.path.expanduser("~/.local/share/crossword/words")
OUTFILE = os.path.expanduser("~/.local/share/crossword/dtable.bin")
FREQ = "ESIARNTOLCDUGMPHBYFKWVZXJQ"


class DTable:
    """ A pre-processed version of the dictionary

    The key to the table is (word length, position within word, letter)
    and the value in the table is a list of indices within the master
    word list of that length that have that letter at that position.

    This makes it easy to combine multiple constraints on a word by simply
    taking the set intersection of the word indices, which is generally
    a fast operation.
    """

    def __init__(self, infile=INFILE, outfile=OUTFILE):
        """ Constructor, with defauls for infile and outfile """
        self.table = None
        self.words = None
        self.infile = infile
        self.outfile = outfile

    def create(self):
        """ Precompiles word list into the table format """
        self.table = table = defaultdict(set)
        self.words = words = []
        with open(self.infile) as fp:
            for windex, line in enumerate(fp):
                word = line.strip()
                words.append(word)
                length = len(word)
                for pos in range(length):
                    letter = word[pos]
                    key = (length, pos, letter)
                    table[key].add(windex)
        with open(self.outfile, 'wb') as fp:
            pickle.dump((words, table), fp)

    def load(self):
        with open(self.outfile, "rb") as fp:
            self.words, self.table = pickle.load(fp)
