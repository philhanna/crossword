from unittest import TestCase

from crossword.grids import Grid
from tests import load_test_object


class TestGrid(TestCase):

    def test_equals(self):
        grid1 = load_test_object("good_grid")
        grid2 = load_test_object("good_grid")
        self.assertEqual(grid1, grid2)

    def test_hash(self):
        grid1 = load_test_object("good_grid")
        grid2 = load_test_object("good_grid")
        self.assertEqual(hash(grid1), hash(grid2))

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
        grid = load_test_object("bad_grid")
        error_list = grid.validate_minimum_word_length()
        self.assertTrue(len(error_list) > 0)

    def test_validate_minimum_word_length_good(self):
        grid = load_test_object("good_grid")
        error_list = grid.validate_minimum_word_length()
        self.assertTrue(len(error_list) == 0)

    def test_validate_unchecked_squares_bad(self):
        grid = load_test_object("bad_grid")
        error_list = grid.validate_unchecked_squares()
        self.assertTrue(len(error_list) > 0)

    def test_validate_unchecked_squares_good(self):
        grid = load_test_object("good_grid")
        error_list = grid.validate_unchecked_squares()
        self.assertTrue(len(error_list) == 0)

    def test_validate_interlock_bad(self):
        grid = load_test_object("bad_grid")
        error_list = grid.validate_interlock()
        self.assertTrue(len(error_list) > 0)

    def test_validate_interlock_good(self):
        grid = load_test_object("good_grid")
        error_list = grid.validate_interlock()
        self.assertTrue(len(error_list) == 0)

    def test_validate_bad(self):
        grid = load_test_object("bad_grid")
        ok, errors = grid.validate()
        debug = False  # Toggle this to see more
        if debug:
            import json
            jsonstr = json.dumps(errors, indent=2)
            print(jsonstr)
        self.assertFalse(ok)

    def test_validate_good(self):
        grid = load_test_object("good_grid")
        ok, errors = grid.validate()
        debug = False  # Toggle this to see more
        if debug:
            import json
            jsonstr = json.dumps(errors, indent=2)
            print(jsonstr)
        self.assertTrue(ok)

    def test_grid_from_puzzle(self):
        puzzle = load_test_object("nyt_daily")
        jsonstr = puzzle.to_json()
        grid = Grid.from_json(jsonstr)
        self.assertEqual(puzzle.n, grid.n)

    def test_word_count(self):
        grid = load_test_object("good_grid")
        expected = 76
        actual = grid.get_word_count()
        self.assertEqual(expected, actual)

    def test_statistics_good(self):
        grid = load_test_object("good_grid")
        stats = grid.get_statistics()
        self.assertTrue(stats['valid'])
        self.assertListEqual([1, 24, 53, 69], stats['wordlengths'][3]['alist'])

    def test_statistics_bad(self):
        grid = load_test_object("bad_grid")
        stats = grid.get_statistics()
        self.assertEqual("7 x 7", stats['size'])
        self.assertEqual(23, stats['wordcount'])
        self.assertFalse(stats['valid'])

    def test_str(self):
        grid = Grid(3)
        grid_string = str(grid)
        self.assertTrue("+-----+" in grid_string)
        self.assertTrue("| | | |" in grid_string)
