from unittest import TestCase

from crossword.grids import Grid
from crossword.puzzles import Puzzle


class TestPuzzleTitle(TestCase):

    def test_title_not_set(self):
        grid = Grid(11)
        puzzle = Puzzle(grid)
        self.assertIsNone(puzzle.title)

    def test_title_is_set(self):
        grid = Grid(11)
        puzzle = Puzzle(grid, "My Title")
        self.assertEqual("My Title", puzzle.title)

    def test_title_set_later(self):
        grid = Grid(11)
        puzzle = Puzzle(grid)
        puzzle.title = "Later"
        self.assertEqual("Later", puzzle.title)

    def test_title_changed(self):
        grid = Grid(11)
        puzzle = Puzzle(grid, "First Title")
        self.assertEqual("First Title", puzzle.title)
        puzzle.title = "Second Title"
        self.assertEqual("Second Title", puzzle.title)

    def test_title_set_back_to_none(self):
        grid = Grid(11)
        puzzle = Puzzle(grid, "First Title")
        self.assertEqual("First Title", puzzle.title)
        puzzle.title = None
        self.assertIsNone(puzzle.title)
