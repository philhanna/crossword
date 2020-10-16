import os
import sqlite3
from unittest import TestCase

from crossword import Puzzle, Word
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
            self.jsonstr = row[0]

    def setUp(self):
        self.puzzle = Puzzle.from_json(self.jsonstr)
        self.solver = Solver(self.puzzle)

    def test_get_all_words(self):
        solver = self.solver
        self.assertEqual(140, len(solver.all_words))

    def test_most_constrained(self):
        solver = self.solver
        word = solver.most_constrained()
        self.assertIsNotNone(word)
        self.assertEqual("PR ", word.get_text())

    def test_get_crossing_words(self):
        puzzle = self.puzzle
        word = puzzle.get_word(4, Word.DOWN)
        for crosser in self.solver.get_crossing_words(word):
            print(crosser)
        pass
