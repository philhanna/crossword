from unittest import TestCase

from crossword import LetterList


class TestLetterList(TestCase):

    def test_with_all(self):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.assertEqual(".", LetterList.regexp(letters))

    def test_with_small_straight(self):
        letters = "ABCD"
        self.assertEqual("[A-D]", LetterList.regexp(letters))

    def test_with_gaps(self):
        letters = "BCDKLMWXZ"
        self.assertEqual("[^AE-JN-VY]", LetterList.regexp(letters))

    def test_with_all_but_j_and_q(self):
        letters = "ABCDEFGHIKLMNOPRSTUVWXYZ"
        self.assertEqual("[^JQ]", LetterList.regexp(letters))

    def test_with_all_but_z(self):
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXY"
        self.assertEqual("[^Z]", LetterList.regexp(letters))

    def test_with_single_letter(self):
        letters = "S"
        self.assertEqual("S", LetterList.regexp(letters))

    def test_with_empty_pattern(self):
        letters = ""
        self.assertEqual("", LetterList.regexp(letters))
