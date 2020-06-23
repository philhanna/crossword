from unittest import TestCase

from crossword import NumberedCell
from crossword.tests import TestPuzzle


class TestNumberClues(TestCase):

    def test_number_clues(self):
        puzzle = TestPuzzle.create_puzzle()
        expected = [
            NumberedCell(1,1,1,a=2,d=2),
            NumberedCell(2,1,2,d=2),
            NumberedCell(3,1,4,a=2),
            NumberedCell(4,1,5,d=2),
            NumberedCell(5,2,1,a=2),
            NumberedCell(6,4,1,d=2),
            NumberedCell(7,4,4,a=2,d=2),
            NumberedCell(8,4,5,d=2),
            NumberedCell(9,5,1,a=2),
            NumberedCell(10,5,4,a=2)
        ]
        actual = puzzle.numbered_cells
        self.assertEqual(expected, actual)

    def test_nyt(self):
        puzzle = TestPuzzle.create_nyt_puzzle()
        nclist = puzzle.numbered_cells
        self.assertEqual(124, len(nclist))

    def test_contains_across(self):
        # Construct 42 across
        data = """
        {
            "seq": 42,
            "r": 9,
            "c": 12,
            "across_length": 4,
            "down_length": 0
        }
        """
        nc = NumberedCell.from_json(data)
        self.assertTrue(nc.contains_across(9, 13))
        self.assertTrue(nc.contains_across(9, 15))
        self.assertFalse(nc.contains_across(10, 1))
        self.assertFalse(nc.contains_across(9, 45))

    def test_contains_down(self):
        # Construct 1 down
        data = """
        {
            "seq": 1,
            "r": 1,
            "c": 1,
            "across_length": 4,
            "down_length": 4
        }
        """
        nc = NumberedCell.from_json(data)
        self.assertTrue(nc.contains_down(2, 1))
        self.assertTrue(nc.contains_down(4, 1))
        self.assertFalse(nc.contains_down(10, 1))
        self.assertFalse(nc.contains_down(9, 45))
