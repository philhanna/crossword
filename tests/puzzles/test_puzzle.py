import os
import tempfile
from unittest import TestCase

from crossword.grids import Grid
from crossword.puzzles import Puzzle
from tests import load_test_puzzle


class TestPuzzle(TestCase):

    def test_nyt_daily(self):
        import json
        puzzle = load_test_puzzle("nyt_daily")
        jsonstr = puzzle.to_json()
        obj = json.loads(jsonstr)
        jsonstr = json.dumps(obj, indent=2)
        with open("/tmp/nyt_daily.json", "w") as fp:
            fp.write(jsonstr)

    def test_equals(self):
        puzzle1 = load_test_puzzle("solved_atlantic_puzzle")
        puzzle2 = load_test_puzzle("solved_atlantic_puzzle")
        self.assertEqual(puzzle1, puzzle2)

    def test_hash(self):
        puzzle1 = load_test_puzzle("solved_atlantic_puzzle")
        puzzle2 = load_test_puzzle("solved_atlantic_puzzle")
        self.assertEqual(hash(puzzle1), hash(puzzle2))

    def test_cell_type(self):
        puzzle = load_test_puzzle("puzzle")
        cell = puzzle.get_cell(1, 1)
        self.assertEqual(type(cell), str)
        cell = puzzle.get_cell(1, 3)
        self.assertEqual(type(cell), str)
        puzzle.set_cell(1, 5, 'D')
        cell = puzzle.get_cell(1, 5)
        self.assertEqual(type(cell), str)

    def test_set_cell(self):
        n = 5
        puzzle = Puzzle(Grid(n))
        puzzle.set_cell(2, 3, 'D')
        cell = puzzle.get_cell(2, 3)
        self.assertEqual('D', cell)
        for r in range(1, n + 1):
            if r == 2:
                continue
            for c in range(1, n + 1):
                if c == 3:
                    continue
                cell = puzzle.get_cell(r, c)
                self.assertEqual(Puzzle.WHITE, cell, f'Mismatch at ({r}, {c})')

    def test_add_black(self):
        n = 5
        grid = Grid(n)
        black_cells = [
            (1, 1),
            (1, 3),
            (2, 3),
            (2, 4),
            (3, 1),
            (3, 2),
        ]
        for (r, c) in black_cells:
            grid.add_black_cell(r, c)

        puzzle = Puzzle(grid)

        expected_cells = [
            ["*", " ", "*", " ", " "],
            [" ", " ", "*", "*", " "],
            ["*", "*", " ", "*", "*"],
            [" ", "*", "*", " ", " "],
            [" ", " ", "*", " ", "*"],
        ]
        for r in range(1, n + 1):
            for c in range(1, n + 1):
                expected = expected_cells[r - 1][c - 1]
                actual = puzzle.get_cell(r, c)
                self.assertEqual(expected, actual, f'Mismatch at ({r},{c})')

    def test_set_across_word(self):
        puzzle = load_test_puzzle("atlantic_puzzle")
        seq = 10
        parm = "RIOT"
        puzzle.get_across_word(seq).set_text(parm)
        expected = parm
        actual = puzzle.get_across_word(seq).get_text()
        self.assertEqual(expected, actual)

    def test_set_down_word(self):
        puzzle = load_test_puzzle("atlantic_puzzle")
        seq = 22
        parm = "BUBBA"
        puzzle.get_across_word(seq).set_text(parm)
        expected = "BUB"
        actual = puzzle.get_across_word(seq).get_text()
        self.assertEqual(expected, actual)

    def test_save(self):
        puzzle = load_test_puzzle("solved_atlantic_puzzle")
        jsonstr = puzzle.to_json()
        filename = os.path.join(tempfile.gettempdir(), "test_puzzle.test_save.json")
        with open(filename, "wt") as fp:
            print(jsonstr, file=fp)

    def test_load_atlantic(self):

        # Make sure the saved file is there: create it in /tmp
        self.test_save()
        filename = os.path.join(tempfile.gettempdir(), "test_puzzle.test_save.json")

        # Load the file
        with open(filename, "rt") as fp:
            jsonstr = fp.read()
        puzzle = Puzzle.from_json(jsonstr)

        # Check some contents

        self.assertEqual(9, puzzle.n)

        word = puzzle.get_across_word(8)
        self.assertEqual("SLIM", word.get_text())
        self.assertEqual("Reed-like", word.get_clue())

        word = puzzle.get_down_word(17)
        self.assertEqual("EHRE", word.get_text())
        self.assertEqual("Honor, to Fritz", word.get_clue())

    def test_word_count(self):
        puzzle = load_test_puzzle("atlantic_puzzle")
        expected = 26
        actual = puzzle.get_word_count()
        self.assertEqual(expected, actual)

    def test_str(self):
        grid = Grid(3)
        puzzle = Puzzle(grid)
        puzzle_string = str(puzzle)
        self.assertTrue("+-----+" in puzzle_string)
        self.assertTrue("| | | |" in puzzle_string)
