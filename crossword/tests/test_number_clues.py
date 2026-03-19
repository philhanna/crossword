from crossword import NumberedCell
from crossword.tests import TestPuzzle


class TestNumberClues:

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
        assert expected == actual

    def test_nyt(self):
        puzzle = TestPuzzle.create_nyt_puzzle()
        nclist = puzzle.numbered_cells
        assert 124 == len(nclist)

    def test_contains_across(self):
        # Construct 42 across
        data = """
        {
            "seq": 42,
            "r": 9,
            "c": 12,
            "a": 4,
            "d": 0
        }
        """
        nc = NumberedCell.from_json(data)
        assert nc.contains_across(9, 13)
        assert nc.contains_across(9, 15)
        assert not nc.contains_across(10, 1)
        assert not nc.contains_across(9, 45)

    def test_contains_down(self):
        # Construct 1 down
        data = """
        {
            "seq": 1,
            "r": 1,
            "c": 1,
            "a": 4,
            "d": 4
        }
        """
        nc = NumberedCell.from_json(data)
        assert nc.contains_down(2, 1)
        assert nc.contains_down(4, 1)
        assert not nc.contains_down(10, 1)
        assert not nc.contains_down(9, 45)
