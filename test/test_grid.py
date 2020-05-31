from unittest import TestCase

from grid import Grid


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
