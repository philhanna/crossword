import json
from unittest import TestCase

from crossword.cells import NumberedCell
from crossword.util import CrosswordJSONEncoder, CrosswordJSONDecoder


class TestNumberedCellJSON(TestCase):

    def test_just_r_and_c(self):
        numbered_cell = NumberedCell(1, 3, 2)
        jsonstr = json.dumps(numbered_cell, cls=CrosswordJSONEncoder)
        actual = json.loads(jsonstr, cls=CrosswordJSONDecoder)
        self.assertEqual(numbered_cell, actual)
        self.assertEqual(0, actual.a)
        self.assertEqual(0, actual.d)

    def test_with_a(self):
        numbered_cell = NumberedCell(1, 3, 2, a=4)
        jsonstr = json.dumps(numbered_cell, cls=CrosswordJSONEncoder)
        actual = json.loads(jsonstr, cls=CrosswordJSONDecoder)
        self.assertEqual(numbered_cell, actual)
        self.assertEqual(4, actual.a)
        self.assertEqual(0, actual.d)

    def test_with_d(self):
        numbered_cell = NumberedCell(45, 3, 2, d=46)
        jsonstr = json.dumps(numbered_cell, cls=CrosswordJSONEncoder)
        actual = json.loads(jsonstr, cls=CrosswordJSONDecoder)
        self.assertEqual(numbered_cell, actual)
        self.assertEqual(0, actual.a)
        self.assertEqual(46, actual.d)

    def test_with_both(self):
        numbered_cell = NumberedCell(22, 3, 2, d=46, a=12)
        jsonstr = json.dumps(numbered_cell, cls=CrosswordJSONEncoder)
        actual = json.loads(jsonstr, cls=CrosswordJSONDecoder)
        self.assertEqual(numbered_cell, actual)
        self.assertEqual(12, actual.a)
        self.assertEqual(46, actual.d)

    def test_with_both_as_positional(self):
        numbered_cell = NumberedCell(4, 3, 2, 12, 46)
        jsonstr = json.dumps(numbered_cell, cls=CrosswordJSONEncoder)
        actual = json.loads(jsonstr, cls=CrosswordJSONDecoder)
        self.assertEqual(numbered_cell, actual)
        self.assertEqual(12, actual.a)
        self.assertEqual(46, actual.d)

    def test_equals_when_equal(self):
        nca = NumberedCell(17, 3, 2, 4, 5)
        jsonstra = json.dumps(nca, cls=CrosswordJSONEncoder)
        ncb = NumberedCell(17, 3, 2, 3 + 1, 4 + 1)
        jsonstrb = json.dumps(ncb, cls=CrosswordJSONEncoder)
        self.assertEqual(jsonstra, jsonstrb)
