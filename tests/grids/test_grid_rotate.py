from unittest import TestCase

from tests import load_test_grid


class TestGridRotate(TestCase):

    def test_rotate(self):
        grid = load_test_grid("good_grid")
        grid.rotate()
        expected = {(1, 8), (1, 9),
            (4, 4),
            (5, 1), (5, 2), (5, 3), (5, 7), (5, 8), (5, 9),
            (6, 6),
            (9, 1), (9, 2),}
        actual = { (r, c) for (r, c) in grid.get_black_cells() }
        self.assertSetEqual(expected, actual)

    def test_rotate_twice(self):
        grid = load_test_grid("good_grid")
        grid.undo_stack = []
        grid.redo_stack = []
        oldjson = grid.to_json()
        grid.rotate()
        grid.rotate()
        grid.undo_stack = []
        grid.redo_stack = []
        newjson = grid.to_json()
        self.assertEqual(oldjson, newjson)

