import os
import sqlite3
from unittest import TestCase

from crossword import Puzzle
from crossword.solver import Solver

DBFILE = os.path.expanduser("~/crossword.db")
PUZZLENAME = "disney-9"


class TestSolver(TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        with sqlite3.connect(DBFILE) as con:
            c = con.cursor()
            sql = r'''SELECT jsonstr FROM puzzles WHERE puzzlename=?'''
            result = c.execute(sql, (PUZZLENAME,))
            row = result.fetchone()
            jsonstr = row[0]
            self.puzzle = Puzzle.from_json(jsonstr)
            pass

    def test_get_all_words(self):
        solver = Solver(self.puzzle)
        for word in solver.all_words:
            print(word)
