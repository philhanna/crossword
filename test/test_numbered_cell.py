from unittest import TestCase

from crossword.numbered_cell import NumberedCell


class TestNumberedCell(TestCase):

    def test_just_r_and_c(self):
        numbered_cell = NumberedCell(1, 3, 2)
        expected = "NumberedCell(seq=1,r=3,c=2)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(0, numbered_cell.across_length)
        self.assertEqual(0, numbered_cell.down_length)

    def test_with_across_length(self):
        numbered_cell = NumberedCell(1, 3, 2, a=4)
        expected = "NumberedCell(seq=1,r=3,c=2,a=4)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(4, numbered_cell.across_length)
        self.assertEqual(0, numbered_cell.down_length)

    def test_with_down_length(self):
        numbered_cell = NumberedCell(45, 3, 2, d=46)
        expected = "NumberedCell(seq=45,r=3,c=2,d=46)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(0, numbered_cell.across_length)
        self.assertEqual(46, numbered_cell.down_length)

    def test_with_both(self):
        numbered_cell = NumberedCell(22, 3, 2, d=46, a=12)
        expected = "NumberedCell(seq=22,r=3,c=2,a=12,d=46)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(12, numbered_cell.across_length)
        self.assertEqual(46, numbered_cell.down_length)

    def test_with_both_as_positional(self):
        numbered_cell = NumberedCell(4, 3, 2, 12, 46)
        expected = "NumberedCell(seq=4,r=3,c=2,a=12,d=46)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(12, numbered_cell.across_length)
        self.assertEqual(46, numbered_cell.down_length)

    def test_equals_when_equal(self):
        nca = NumberedCell(17, 3, 2, 4, 5)
        ncb = NumberedCell(17, 3, 2, 3 + 1, 4 + 1)
        self.assertEqual(nca, ncb)

    def test_hash(self):
        nc1 = NumberedCell(4, 3, 2, 12, 46)
        self.assertIsNotNone(hash(nc1))
