import re

from crossword import Configuration


class WordList:
    """ Given a regular expression, returns a list of all the words that match the pattern """

    def __init__(self, filename=None):
        if not filename:
            filename = Configuration.get_words_filename()
        self.filename = filename
        self.words = []
        with open(filename, "rt") as fp:
            for line in fp:
                line = line.strip()
                self.words.append(line)

    def lookup(self, pattern):
        pattern = "^" + pattern + "$"
        pattern = re.sub('[ ?]', '.', pattern)
        regexp = re.compile(pattern, re.IGNORECASE)
        result = []
        for line in self.words:
            m = regexp.match(line)
            if m:
                result.append(line)
        return result
