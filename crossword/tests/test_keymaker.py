from unittest import TestCase, skip

from crossword.dtable import DTable


class TestKeymaker(TestCase):

    def test_keymaker(self):
        pattern = "D.SH"
        actual = DTable.keymaker(pattern)
        expected = [
            'D...', '..S.', '...H'
        ]
        self.assertListEqual(expected, actual)

    def test_keymaker_with_all_blanks(self):
        pattern = "......"
        actual = DTable.keymaker(pattern)
        self.assertIsNone(actual)
