from unittest import TestCase

from crossword.cells import NumberedCell
from crossword.grids import Grid
from crossword.puzzles import Puzzle
from tests import TestPuzzle


class TestPuzzleReplaceGrid(TestCase):

    def test_wrong_size(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        grid = Grid(5)
        with self.assertRaises(ValueError):
            puzzle.replace_grid(grid)

    def test_same_grid(self):
        oldpuzzle = TestPuzzle.create_solved_atlantic_puzzle()
        grid = Grid.from_json(oldpuzzle.to_json())
        newpuzzle = Puzzle.from_json(oldpuzzle.to_json())
        newpuzzle.replace_grid(grid)
        self.assertEqual(oldpuzzle, newpuzzle)

    def test_new_grid(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        oldjson = puzzle.to_json()
        grid = Grid.from_json(puzzle.to_json())
        grid.add_black_cell(4, 4)
        puzzle.replace_grid(grid)
        newjson = puzzle.to_json()

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
            NumberedCell(seq=1, r=1, c=1, a=3, d=4),
            NumberedCell(seq=2, r=1, c=2, a=0, d=4),
            NumberedCell(seq=3, r=1, c=3, a=0, d=9),
            NumberedCell(seq=4, r=1, c=6, a=4, d=5),
            NumberedCell(seq=5, r=1, c=7, a=0, d=9),
            NumberedCell(seq=6, r=1, c=8, a=0, d=4),
            NumberedCell(seq=7, r=1, c=9, a=0, d=3),
            NumberedCell(seq=8, r=2, c=1, a=4, d=0),
            NumberedCell(seq=9, r=2, c=4, a=0, d=2),
            NumberedCell(seq=10, r=2, c=6, a=4, d=0),
            NumberedCell(seq=11, r=3, c=1, a=9, d=0),
            NumberedCell(seq=12, r=3, c=5, a=0, d=5),
            NumberedCell(seq=13, r=4, c=1, a=3, d=0),
            NumberedCell(seq=14, r=4, c=5, a=4, d=0),
            NumberedCell(seq=15, r=5, c=3, a=5, d=0),
            NumberedCell(seq=16, r=5, c=4, a=0, d=5),
            NumberedCell(seq=17, r=6, c=2, a=4, d=4),
            NumberedCell(seq=18, r=6, c=7, a=3, d=0),
            NumberedCell(seq=19, r=6, c=8, a=0, d=4),
            NumberedCell(seq=20, r=6, c=9, a=0, d=4),
            NumberedCell(seq=21, r=7, c=1, a=9, d=3),
            NumberedCell(seq=22, r=7, c=6, a=0, d=2),
            NumberedCell(seq=23, r=8, c=1, a=4, d=0),
            NumberedCell(seq=24, r=8, c=6, a=4, d=0),
            NumberedCell(seq=25, r=9, c=1, a=4, d=0),
            NumberedCell(seq=26, r=9, c=7, a=3, d=0),
        ]
        actual = []
        for x in new['numbered_cells']:
            jsonstr = json.dumps(x)
            nc = NumberedCell.from_json(jsonstr)
            actual.append(nc)
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
