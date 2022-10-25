from unittest import TestCase

from crossword.cells import NumberedCell
from crossword.grids import Grid
from crossword.puzzles import Puzzle
from tests import load_test_object


class TestPuzzleReplaceGrid(TestCase):

    def test_wrong_size(self):
        puzzle = load_test_object("solved_atlantic_puzzle")
        grid = Grid(5)
        with self.assertRaises(ValueError):
            puzzle.replace_grid(grid)

    def test_same_grid(self):
        oldpuzzle = load_test_object("solved_atlantic_puzzle")
        grid = Grid.from_json(oldpuzzle.to_json())
        newpuzzle = Puzzle.from_json(oldpuzzle.to_json())
        newpuzzle.replace_grid(grid)
        self.assertEqual(oldpuzzle, newpuzzle)

    def test_new_grid(self):
        puzzle = load_test_object("solved_atlantic_puzzle")
        oldjson = puzzle.to_json()
        grid = Grid.from_json(puzzle.to_json())
        grid.add_black_cell(4, 4)
        puzzle.replace_grid(grid)
        newjson = puzzle.to_json()
        newpuzzle = Puzzle.from_json(newjson)

        import json
        old = json.loads(oldjson)
        new = json.loads(newjson)

        # Compare black cells
        self.assertIn([4, 4], new['black_cells'])
        self.assertIn([6, 6], new['black_cells'])
        new['black_cells'].remove([4, 4])
        new['black_cells'].remove([6, 6])
        self.assertListEqual(old['black_cells'], new['black_cells'])

        # Compare numbered cells
        expected = [
            NumberedCell(1, 1, 1, 3, 4),
            NumberedCell(2, 1, 2, 0, 4),
            NumberedCell(3, 1, 3, 0, 9),
            NumberedCell(4, 1, 6, 4, 5),
            NumberedCell(5, 1, 7, 0, 9),
            NumberedCell(6, 1, 8, 0, 4),
            NumberedCell(7, 1, 9, 0, 3),
            NumberedCell(8, 2, 1, 4, 0),
            NumberedCell(9, 2, 4, 0, 2),
            NumberedCell(10, 2, 6, 4, 0),
            NumberedCell(11, 3, 1, 9, 0),
            NumberedCell(12, 3, 5, 0, 5),
            NumberedCell(13, 4, 1, 3, 0),
            NumberedCell(14, 4, 5, 4, 0),
            NumberedCell(15, 5, 3, 5, 0),
            NumberedCell(16, 5, 4, 0, 5),
            NumberedCell(17, 6, 2, 4, 4),
            NumberedCell(18, 6, 7, 3, 0),
            NumberedCell(19, 6, 8, 0, 4),
            NumberedCell(20, 6, 9, 0, 4),
            NumberedCell(21, 7, 1, 9, 3),
            NumberedCell(22, 7, 6, 0, 2),
            NumberedCell(23, 8, 1, 4, 0),
            NumberedCell(24, 8, 6, 4, 0),
            NumberedCell(25, 9, 1, 4, 0),
            NumberedCell(26, 9, 7, 3, 0),
        ]
        actual = [nc for nc in newpuzzle.numbered_cells]

        self.assertListEqual(expected, actual)

        # Compare clues

        oldclues = {x['text']: x['clue']
                    for x in old['across_words'] + old['down_words']}
        newclues = {x['text']: x['clue']
                    for x in new['across_words'] + new['down_words']}
        for k, v in newclues.items():
            if k in oldclues:
                oldclue = oldclues[k]
                self.assertEqual(oldclue, newclues[k])
