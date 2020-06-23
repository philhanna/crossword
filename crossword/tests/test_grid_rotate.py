from unittest import TestCase

from crossword import Grid


class TestGridRotate(TestCase):

    def test_rotate(self):
        grid = self.get_good_grid()
        grid.rotate()
        expected = {(1, 8), (1, 9),
            (4, 4),
            (5, 1), (5, 2), (5, 3), (5, 7), (5, 8), (5, 9),
            (6, 6),
            (9, 1), (9, 2),}
        actual = { (r, c) for (r, c) in grid.get_black_cells() }
        self.assertSetEqual(expected, actual)

    def test_rotate_twice(self):
        grid = self.get_good_grid()
        oldjson = grid.to_json()
        grid.rotate()
        grid.rotate()
        newjson = grid.to_json()
        self.assertEqual(oldjson, newjson)

    @staticmethod
    def get_good_grid():
        jsonstr = """
        {
  "n": 9,
  "cells": [
    "+-----------------+",
    "|*| | | |*| | | | |",
    "|*| | | |*| | | | |",
    "| | | | |*| | | | |",
    "| | | | | |*| | | |",
    "| | | | | | | | | |",
    "| | | |*| | | | | |",
    "| | | | |*| | | | |",
    "| | | | |*| | | |*|",
    "| | | | |*| | | |*|",
    "+-----------------+"
  ],
  "black_cells": [
    [ 1, 1 ],
    [ 1, 5 ],
    [ 2, 1 ],
    [ 2, 5 ],
    [ 3, 5 ],
    [ 4, 6 ],
    [ 6, 4 ],
    [ 7, 5 ],
    [ 8, 5 ],
    [ 8, 9 ],
    [ 9, 5 ],
    [ 9, 9 ]
  ],
  "numbered_cells": [
    { "seq": 1, "r": 1, "c": 2, "a": 3, "d": 9 },
    { "seq": 2, "r": 1, "c": 3, "a": 0, "d": 9 },
    { "seq": 3, "r": 1, "c": 4, "a": 0, "d": 5 },
    { "seq": 4, "r": 1, "c": 6, "a": 4, "d": 3 },
    { "seq": 5, "r": 1, "c": 7, "a": 0, "d": 9 },
    { "seq": 6, "r": 1, "c": 8, "a": 0, "d": 9 },
    { "seq": 7, "r": 1, "c": 9, "a": 0, "d": 7 },
    { "seq": 8, "r": 2, "c": 2, "a": 3, "d": 0 },
    { "seq": 9, "r": 2, "c": 6, "a": 4, "d": 0 },
    { "seq": 10, "r": 3, "c": 1, "a": 4, "d": 7 },
    { "seq": 11, "r": 3, "c": 6, "a": 4, "d": 0 },
    { "seq": 12, "r": 4, "c": 1, "a": 5, "d": 0 },
    { "seq": 13, "r": 4, "c": 5, "a": 0, "d": 3 },
    { "seq": 14, "r": 4, "c": 7, "a": 3, "d": 0 },
    { "seq": 15, "r": 5, "c": 1, "a": 9, "d": 0 },
    { "seq": 16, "r": 5, "c": 6, "a": 0, "d": 5 },
    { "seq": 17, "r": 6, "c": 1, "a": 3, "d": 0 },
    { "seq": 18, "r": 6, "c": 5, "a": 5, "d": 0 },
    { "seq": 19, "r": 7, "c": 1, "a": 4, "d": 0 },
    { "seq": 20, "r": 7, "c": 4, "a": 0, "d": 3 },
    { "seq": 21, "r": 7, "c": 6, "a": 4, "d": 0 },
    { "seq": 22, "r": 8, "c": 1, "a": 4, "d": 0 },
    { "seq": 23, "r": 8, "c": 6, "a": 3, "d": 0 },
    { "seq": 24, "r": 9, "c": 1, "a": 4, "d": 0 },
    { "seq": 25, "r": 9, "c": 6, "a": 3, "d": 0 }
  ]
}
"""
        grid = Grid.from_json(jsonstr)
        return grid
