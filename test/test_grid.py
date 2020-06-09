from unittest import TestCase

from grid import Grid
from test.test_puzzle import TestPuzzle


class TestGrid(TestCase):

    def test_symmetric_point(self):
        grid = Grid(9)
        expected = (8, 5)
        actual = grid.symmetric_point(2, 5)
        self.assertEqual(expected, actual)

    def test_symmetric_point_on_edge(self):
        grid = Grid(9)
        expected = (9, 1)
        actual = grid.symmetric_point(1, 9)
        self.assertEqual(expected, actual)

    def test_bad_symmetric_point(self):
        grid = Grid(9)
        actual = grid.symmetric_point(-3, 45)
        self.assertIsNone(actual)

    def test_add_black_cell(self):
        grid = Grid(9)
        grid.add_black_cell(1, 5)
        grid.add_black_cell(4, 9)
        expected = [(1, 5), (4, 9), (6, 1), (9, 5)]
        actual = grid.get_black_cells()
        self.assertEqual(expected, actual)

    def test_remove_black_cell(self):
        grid = Grid(9)
        grid.add_black_cell(1, 5)
        grid.add_black_cell(4, 9)
        grid.remove_black_cell(6, 1)
        expected = [(1, 5), (9, 5)]
        actual = grid.get_black_cells()
        self.assertEqual(expected, actual)

    def test_to_json(self):
        grid = Grid(9)
        grid.add_black_cell(1, 5)
        grid.add_black_cell(4, 9)
        jsonstr = grid.to_json()
        self.assertIsNotNone(jsonstr)

    def test_validate_minimum_word_length_bad(self):
        grid = TestGrid.get_bad_grid()
        errors = grid.validate_minimum_word_length()
        self.assertTrue(len(errors) > 0)

    def test_validate_minimum_word_length_good(self):
        grid = TestGrid.get_good_grid()
        errors = grid.validate_minimum_word_length()
        self.assertTrue(len(errors) == 0)

    def test_validate_unchecked_squares_bad(self):
        grid = TestGrid.get_bad_grid()
        errors = grid.validate_unchecked_squares()
        self.assertTrue(len(errors) > 0)

    def test_validate_unchecked_squares_good(self):
        grid = TestGrid.get_good_grid()
        errors = grid.validate_unchecked_squares()
        self.assertTrue(len(errors) == 0)

    def test_validate_interlock_bad(self):
        grid = TestGrid.get_bad_grid()
        errors = grid.validate_interlock()
        self.assertTrue(len(errors) > 0)

    def test_validate_interlock_good(self):
        grid = TestGrid.get_good_grid()
        errors = grid.validate_interlock()
        self.assertTrue(len(errors) == 0)

    def test_validate_bad(self):
        grid = TestGrid.get_bad_grid()
        ok, errors = grid.validate()
        self.assertFalse(ok)

    def test_validate_good(self):
        grid = TestGrid.get_good_grid()
        ok, errmsg = grid.validate()
        self.assertTrue(ok)

    def test_grid_from_puzzle(self):
        puzzle = TestPuzzle.create_nyt_daily()
        jsonstr = puzzle.to_json()
        grid = Grid.from_json(jsonstr)
        self.assertEqual(puzzle.n, grid.n)

    def test_word_count(self):
        grid = TestGrid.get_good_grid()
        expected = 76
        actual = grid.get_word_count()
        self.assertEqual(expected, actual)

    def test_statistics_good(self):
        grid = TestGrid.get_good_grid()
        stats = grid.get_statistics()
        self.assertTrue(stats['valid'])
        self.assertListEqual([1, 24, 53, 69], stats['wordlengths'][3]['alist'])
        print(stats)

    def test_statistics_bad(self):
        grid = TestGrid.get_bad_grid()
        stats = grid.get_statistics()
        self.assertEqual("7 x 7", stats['size'])
        self.assertEqual(23, stats['wordcount'])
        self.assertFalse(stats['valid'])
        print(stats)

    @staticmethod
    def get_good_grid():
        jsonstr = """
{
  "n": 15,
  "black_cells": [
    [ 1, 4 ],
    [ 1, 5 ],
    [ 1, 11 ],
    [ 2, 5 ],
    [ 2, 11 ],
    [ 3, 5 ],
    [ 3, 11 ],
    [ 4, 1 ],
    [ 4, 2 ],
    [ 4, 8 ],
    [ 4, 14 ],
    [ 4, 15 ],
    [ 5, 1 ],
    [ 5, 2 ],
    [ 5, 3 ],
    [ 5, 7 ],
    [ 5, 8 ],
    [ 5, 13 ],
    [ 5, 14 ],
    [ 5, 15 ],
    [ 6, 8 ],
    [ 6, 9 ],
    [ 6, 10 ],
    [ 7, 5 ],
    [ 7, 11 ],
    [ 8, 5 ],
    [ 8, 11 ],
    [ 9, 5 ],
    [ 9, 11 ],
    [ 10, 6 ],
    [ 10, 7 ],
    [ 10, 8 ],
    [ 11, 1 ],
    [ 11, 2 ],
    [ 11, 3 ],
    [ 11, 8 ],
    [ 11, 9 ],
    [ 11, 13 ],
    [ 11, 14 ],
    [ 11, 15 ],
    [ 12, 1 ],
    [ 12, 2 ],
    [ 12, 8 ],
    [ 12, 14 ],
    [ 12, 15 ],
    [ 13, 5 ],
    [ 13, 11 ],
    [ 14, 5 ],
    [ 14, 11 ],
    [ 15, 5 ],
    [ 15, 11 ],
    [ 15, 12 ]
  ],
  "numbered_cells": [
    { "seq": 1, "r": 1, "c": 1, "across_length": 3, "down_length": 3 },
    { "seq": 2, "r": 1, "c": 2, "across_length": 0, "down_length": 3 },
    { "seq": 3, "r": 1, "c": 3, "across_length": 0, "down_length": 4 },
    { "seq": 4, "r": 1, "c": 6, "across_length": 5, "down_length": 9 },
    { "seq": 5, "r": 1, "c": 7, "across_length": 0, "down_length": 4 },
    { "seq": 6, "r": 1, "c": 8, "across_length": 0, "down_length": 3 },
    { "seq": 7, "r": 1, "c": 9, "across_length": 0, "down_length": 5 },
    { "seq": 8, "r": 1, "c": 10, "across_length": 0, "down_length": 5 },
    { "seq": 9, "r": 1, "c": 12, "across_length": 4, "down_length": 14 },
    { "seq": 10, "r": 1, "c": 13, "across_length": 0, "down_length": 4 },
    { "seq": 11, "r": 1, "c": 14, "across_length": 0, "down_length": 3 },
    { "seq": 12, "r": 1, "c": 15, "across_length": 0, "down_length": 3 },
    { "seq": 13, "r": 2, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 14, "r": 2, "c": 4, "across_length": 0, "down_length": 14 },
    { "seq": 15, "r": 2, "c": 6, "across_length": 5, "down_length": 0 },
    { "seq": 16, "r": 2, "c": 12, "across_length": 4, "down_length": 0 },
    { "seq": 17, "r": 3, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 18, "r": 3, "c": 6, "across_length": 5, "down_length": 0 },
    { "seq": 19, "r": 3, "c": 12, "across_length": 4, "down_length": 0 },
    { "seq": 20, "r": 4, "c": 3, "across_length": 5, "down_length": 0 },
    { "seq": 21, "r": 4, "c": 5, "across_length": 0, "down_length": 3 },
    { "seq": 22, "r": 4, "c": 9, "across_length": 5, "down_length": 0 },
    { "seq": 23, "r": 4, "c": 11, "across_length": 0, "down_length": 3 },
    { "seq": 24, "r": 5, "c": 4, "across_length": 3, "down_length": 0 },
    { "seq": 25, "r": 5, "c": 9, "across_length": 4, "down_length": 0 },
    { "seq": 26, "r": 6, "c": 1, "across_length": 7, "down_length": 5 },
    { "seq": 27, "r": 6, "c": 2, "across_length": 0, "down_length": 5 },
    { "seq": 28, "r": 6, "c": 3, "across_length": 0, "down_length": 5 },
    { "seq": 29, "r": 6, "c": 7, "across_length": 0, "down_length": 4 },
    { "seq": 30, "r": 6, "c": 11, "across_length": 5, "down_length": 0 },
    { "seq": 31, "r": 6, "c": 13, "across_length": 0, "down_length": 5 },
    { "seq": 32, "r": 6, "c": 14, "across_length": 0, "down_length": 5 },
    { "seq": 33, "r": 6, "c": 15, "across_length": 0, "down_length": 5 },
    { "seq": 34, "r": 7, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 35, "r": 7, "c": 6, "across_length": 5, "down_length": 0 },
    { "seq": 36, "r": 7, "c": 8, "across_length": 0, "down_length": 3 },
    { "seq": 37, "r": 7, "c": 9, "across_length": 0, "down_length": 4 },
    { "seq": 38, "r": 7, "c": 10, "across_length": 0, "down_length": 9 },
    { "seq": 39, "r": 7, "c": 12, "across_length": 4, "down_length": 0 },
    { "seq": 40, "r": 8, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 41, "r": 8, "c": 6, "across_length": 5, "down_length": 0 },
    { "seq": 42, "r": 8, "c": 12, "across_length": 4, "down_length": 0 },
    { "seq": 43, "r": 9, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 44, "r": 9, "c": 6, "across_length": 5, "down_length": 0 },
    { "seq": 45, "r": 9, "c": 12, "across_length": 4, "down_length": 0 },
    { "seq": 46, "r": 10, "c": 1, "across_length": 5, "down_length": 0 },
    { "seq": 47, "r": 10, "c": 5, "across_length": 0, "down_length": 3 },
    { "seq": 48, "r": 10, "c": 9, "across_length": 7, "down_length": 0 },
    { "seq": 49, "r": 10, "c": 11, "across_length": 0, "down_length": 3 },
    { "seq": 50, "r": 11, "c": 4, "across_length": 4, "down_length": 0 },
    { "seq": 51, "r": 11, "c": 6, "across_length": 0, "down_length": 5 },
    { "seq": 52, "r": 11, "c": 7, "across_length": 0, "down_length": 5 },
    { "seq": 53, "r": 11, "c": 10, "across_length": 3, "down_length": 0 },
    { "seq": 54, "r": 12, "c": 3, "across_length": 5, "down_length": 4 },
    { "seq": 55, "r": 12, "c": 9, "across_length": 5, "down_length": 4 },
    { "seq": 56, "r": 12, "c": 13, "across_length": 0, "down_length": 4 },
    { "seq": 57, "r": 13, "c": 1, "across_length": 4, "down_length": 3 },
    { "seq": 58, "r": 13, "c": 2, "across_length": 0, "down_length": 3 },
    { "seq": 59, "r": 13, "c": 6, "across_length": 5, "down_length": 0 },
    { "seq": 60, "r": 13, "c": 8, "across_length": 0, "down_length": 3 },
    { "seq": 61, "r": 13, "c": 12, "across_length": 4, "down_length": 0 },
    { "seq": 62, "r": 13, "c": 14, "across_length": 0, "down_length": 3 },
    { "seq": 63, "r": 13, "c": 15, "across_length": 0, "down_length": 3 },
    { "seq": 64, "r": 14, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 65, "r": 14, "c": 6, "across_length": 5, "down_length": 0 },
    { "seq": 66, "r": 14, "c": 12, "across_length": 4, "down_length": 0 },
    { "seq": 67, "r": 15, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 68, "r": 15, "c": 6, "across_length": 5, "down_length": 0 },
    { "seq": 69, "r": 15, "c": 13, "across_length": 3, "down_length": 0 }
  ]
}

"""
        grid = Grid.from_json(jsonstr)
        return grid

    @staticmethod
    def get_bad_grid():
        jsonstr = """
    {
    "n": 7,
    "black_cells": [
    [ 1, 3 ], [ 2, 3 ], [ 3, 3 ], [ 3, 4 ], [ 3, 5 ], [ 4, 2 ],
    [ 4, 6 ], [ 5, 3 ], [ 5, 4 ], [ 5, 5 ], [ 6, 5 ], [ 7, 5 ]
    ],
    "numbered_cells": [
    { "seq": 1, "r": 1, "c": 1, "across_length": 2, "down_length": 7 },
    { "seq": 2, "r": 1, "c": 2, "across_length": 0, "down_length": 3 },
    { "seq": 3, "r": 1, "c": 4, "across_length": 4, "down_length": 2 },
    { "seq": 4, "r": 1, "c": 5, "across_length": 0, "down_length": 2 },
    { "seq": 5, "r": 1, "c": 6, "across_length": 0, "down_length": 3 },
    { "seq": 6, "r": 1, "c": 7, "across_length": 0, "down_length": 7 },
    { "seq": 7, "r": 2, "c": 1, "across_length": 2, "down_length": 0 },
    { "seq": 8, "r": 2, "c": 4, "across_length": 4, "down_length": 0 },
    { "seq": 9, "r": 3, "c": 1, "across_length": 2, "down_length": 0 },
    { "seq": 10, "r": 3, "c": 6, "across_length": 2, "down_length": 0 },
    { "seq": 11, "r": 4, "c": 3, "across_length": 3, "down_length": 0 },
    { "seq": 12, "r": 5, "c": 1, "across_length": 2, "down_length": 0 },
    { "seq": 13, "r": 5, "c": 2, "across_length": 0, "down_length": 3 },
    { "seq": 14, "r": 5, "c": 6, "across_length": 2, "down_length": 3 },
    { "seq": 15, "r": 6, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 16, "r": 6, "c": 3, "across_length": 0, "down_length": 2 },
    { "seq": 17, "r": 6, "c": 4, "across_length": 0, "down_length": 2 },
    { "seq": 18, "r": 6, "c": 6, "across_length": 2, "down_length": 0 },
    { "seq": 19, "r": 7, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 20, "r": 7, "c": 6, "across_length": 2, "down_length": 0 }
    ]
    }        
    """
        grid = Grid.from_json(jsonstr)
        return grid
