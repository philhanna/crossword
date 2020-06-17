from unittest import TestCase

from crossword import Grid
from test.test_puzzle import TestPuzzle


class TestPuzzleReplaceGrid(TestCase):

    def test_replace_grid(self):
        puzzle = TestPuzzle.create_atlantic_puzzle_with_some_words()
        grid = Grid.from_json(puzzle.to_json())
        grid.add_black_cell(1, 1)
        grid.remove_black_cell(1, 5)
        puzzle.replace_grid(grid)
        #print(puzzle)
        self.assertEqual(" EFTS", puzzle.get_across_word(3).get_text())
        self.assertTrue(puzzle.is_black_cell(1, 1))
        self.assertFalse(puzzle.is_black_cell(1, 5))
        self.assertTrue(puzzle.is_black_cell(9, 9))
        self.assertFalse(puzzle.is_black_cell(9, 5))

    def test_replace_grid_bad(self):
        puzzle = TestPuzzle.create_puzzle()
        grid = Grid.from_json(puzzle.to_json())
        grid.add_black_cell(1, 1)
        grid.remove_black_cell(1, 5)

        bigger_puzzle = TestPuzzle.create_atlantic_puzzle_with_some_words()
        new_grid = Grid.from_json(bigger_puzzle.to_json())
        try:
            puzzle.replace_grid(new_grid)
            self.fail("Should have thrown exception because of incompatible sizes")
        except ValueError as e:
            # This is the expected result
            pass
