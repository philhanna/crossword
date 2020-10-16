import os.path
import pickle
from collections import defaultdict

INFILE = os.path.expanduser("~/.local/share/crossword/words")
OUTFILE = os.path.expanduser("~/.local/share/crossword/dtable.bin")
FREQ = "ESIARNTOLCDUGMPHBYFKWVZXJQ"


class DTable:
    """ A pre-processed version of the dictionary

    For an n-letter word, there will be n entries in the table,
    one for each letter per position with '.' in all the other
    positions.  For example, the word "DASH" would create entries
    for the keys "D...", ".A..", "..S.", and "...H".
    and the value in the table is a list of indices within the master
    word list of that length that have that letter at that position.

    So in the list of indices for "D...", there would be the indices
    corresponding to "DATA", "DAMP", "DOZE", etc.

    Looking up possible matches for a word with multiple filled-in
    letters like "D.SH" would amount to looking up the lists for
    "D...", "..S.", and "...H" and taking the intersection.  It also
    makes it possible to do this only once in solving a puzzle and
    then adding an entry to the table with the key "D.SH" pointing
    to the intersection thus obtained.
    """

    def __init__(self, infile=INFILE, outfile=OUTFILE):
        """ Constructor, with defauls for infile and outfile """
        self.table = None
        self.words = None
        self.infile = infile
        self.outfile = outfile

    @staticmethod
    def keymaker(pattern):
        """ Given a pattern, returns the list of keys
        that can be derived from it.  As described in the comments
        at the head of this class, this would be, for a
        pattern like "D.SH" a list of three keys:
        [ 'D...', '..S.', '...H']
        If the pattern is all blanks (i.e., dots), returns None
        """
        keylist = []
        length = len(pattern)
        for i in range(length):
            letter = pattern[i]
            if letter not in [' ', '.']:
                prefix = "." * i
                suffix = "." * (length - i - 1)
                key = prefix + letter + suffix
                keylist.append(key)
        return keylist if keylist else None

    def create(self):
        """ Precompiles word list into the table format """
        self.table = table = defaultdict(set)
        self.words = words = []
        with open(self.infile) as fp:
            for windex, line in enumerate(fp):
                word = line.strip()
                words.append(word)
                length = len(word)
                for i in range(length):
                    key = ""
                    for j in range(length):
                        key += "." if i == j else word[i]
                    table[key].add(windex)

    def load(self):
        with open(self.outfile, "rb") as fp:
            self.words, self.table = pickle.load(fp)

    def save(self):
        with open(self.outfile, "wb") as fp:
            pickle.dump((self.words, self.table), fp)

    def lookup(self, pattern):
        """ Returns all the words that match this key """

        table = self.table

        # If there is an exact match, return the set of indices it points to
        if pattern in table:
            return table[pattern]

        # Otherwise, break down the pattern into
