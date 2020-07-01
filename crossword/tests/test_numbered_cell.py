import unittest
from unittest import TestCase

from crossword import NumberedCell


class TestNumberedCell(TestCase):

    def test_just_r_and_c(self):
        numbered_cell = NumberedCell(1, 3, 2)
        expected = "NumberedCell(seq=1,r=3,c=2)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(0, numbered_cell.a)
        self.assertEqual(0, numbered_cell.d)

    def test_with_a(self):
        numbered_cell = NumberedCell(1, 3, 2, a=4)
        expected = "NumberedCell(seq=1,r=3,c=2,a=4)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(4, numbered_cell.a)
        self.assertEqual(0, numbered_cell.d)

    def test_with_d(self):
        numbered_cell = NumberedCell(45, 3, 2, d=46)
        expected = "NumberedCell(seq=45,r=3,c=2,d=46)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(0, numbered_cell.a)
        self.assertEqual(46, numbered_cell.d)

    def test_with_both(self):
        numbered_cell = NumberedCell(22, 3, 2, d=46, a=12)
        expected = "NumberedCell(seq=22,r=3,c=2,a=12,d=46)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(12, numbered_cell.a)
        self.assertEqual(46, numbered_cell.d)

    def test_with_both_as_positional(self):
        numbered_cell = NumberedCell(4, 3, 2, 12, 46)
        expected = "NumberedCell(seq=4,r=3,c=2,a=12,d=46)"
        actual = str(numbered_cell)
        self.assertEqual(expected, actual)
        self.assertEqual(12, numbered_cell.a)
        self.assertEqual(46, numbered_cell.d)

    def test_equals_when_equal(self):
        nca = NumberedCell(17, 3, 2, 4, 5)
        ncb = NumberedCell(17, 3, 2, 3 + 1, 4 + 1)
        self.assertEqual(nca, ncb)

    def test_hash(self):
        nc1 = NumberedCell(4, 3, 2, 12, 46)
        self.assertIsNotNone(hash(nc1))

    def test_to_json(self):
        nc = NumberedCell(17, 3, 2, 4, 5)
        expected = '{"seq": 17, "r": 3, "c": 2, "a": 4, "d": 5}'
        actual = nc.to_json()
        self.assertEqual(expected, actual)

    def test_from_json(self):
        jsonstr = '{"seq": 17, "r": 3, "c": 2, "a": 4}'
        nc = NumberedCell.from_json(jsonstr)
        self.assertEqual(17, nc.seq)
        self.assertEqual(3, nc.r)
        self.assertEqual(2, nc.c)
        self.assertEqual(4, nc.a)
        self.assertEqual(0, nc.d)

    def test_json_round_trip(self):
        nc1 = NumberedCell(17, 3, 2, 4, 5)
        jsonstr = nc1.to_json()
        nc2 = NumberedCell.from_json(jsonstr)
        self.assertEqual(nc1, nc2)

    @unittest.skip("Only while debugging")
    def test_print_json(self):
        nc = NumberedCell(17, 3, 2, 4, 5)
        print(f"DEBUG: json={nc.to_json()}")
