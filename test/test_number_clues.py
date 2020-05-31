from unittest import TestCase

from numbered_cell import NumberedCell
from test.test_puzzle import TestPuzzle


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
