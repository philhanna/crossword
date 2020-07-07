import logging
import re
import sqlite3

from crossword import dbfile


class WordList:
    """ Given a regular expression, returns a list of all the words that match the pattern """

    def __init__(self):
        words = []
        with sqlite3.connect(dbfile()) as con:
            c = con.cursor()
            try:
                c.execute('''
                    SELECT      *
                    FROM        WORDS
                ''')
                for row in c.fetchall():
                    word = row[0]
                    words.append(word)
            except sqlite3.Error as e:
                msg = (
                    f"Error loading words:"
                    f" {e}"
                )
                logging.warning(msg)
        self.words = words

    def lookup(self, pattern):
        pattern = "^" + pattern + "$"
        pattern = re.sub('[ ?]', '.', pattern)
        regexp = re.compile(pattern, re.IGNORECASE)
        result = [line for line in self.words if regexp.match(line)]
        return result
