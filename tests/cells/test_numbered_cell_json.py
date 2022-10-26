import json
from unittest import TestCase

from crossword.cells import NumberedCell
from crossword.util import CrosswordJSONEncoder, CrosswordJSONDecoder


class TestNumberedCellJSON(TestCase):

    def test_just_r_and_c(self):
        nc = NumberedCell(1, 3, 2)
        jsonstr = nc.to_json()
        actual = NumberedCell.from_json(jsonstr)
        self.assertEqual(nc, actual)

    def test_with_a(self):
        nc = NumberedCell(1, 3, 2, a=4)
        jsonstr = nc.to_json()
        actual = NumberedCell.from_json(jsonstr)
        self.assertEqual(nc, actual)
        self.assertEqual(4, actual.a)
        self.assertEqual(0, actual.d)

    def test_with_d(self):
        nc = NumberedCell(45, 3, 2, d=46)
        jsonstr = nc.to_json()
        actual = NumberedCell.from_json(jsonstr)
        self.assertEqual(nc, actual)
        self.assertEqual(0, actual.a)
        self.assertEqual(46, actual.d)

    def test_with_both(self):
        nc = NumberedCell(22, 3, 2, d=46, a=12)
        jsonstr = nc.to_json()
        actual = NumberedCell.from_json(jsonstr)
        self.assertEqual(nc, actual)
        self.assertEqual(12, actual.a)
        self.assertEqual(46, actual.d)

    def test_with_both_as_positional(self):
        nc = NumberedCell(4, 3, 2, 12, 46)
        jsonstr = nc.to_json()
        actual = NumberedCell.from_json(jsonstr)
        self.assertEqual(nc, actual)
        self.assertEqual(12, actual.a)
        self.assertEqual(46, actual.d)

    def test_equals_when_equal(self):
        nca = NumberedCell(17, 3, 2, 4, 5)
        jsonstra = nca.to_json()
        ncb = NumberedCell(17, 3, 2, 3 + 1, 4 + 1)
        jsonstrb = ncb.to_json()
        self.assertEqual(jsonstra, jsonstrb)
