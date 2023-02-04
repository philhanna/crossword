from unittest import TestCase

from crossword.util import LetterList


class TestLetterList(TestCase):

    def test_get_blocks(self):
        ilist = [3, 2, 3, 4, 5, 1, 1, 2, 3]
        #ilist = [1, 2, 3, 4, 5]
        for first, last in LetterList.get_blocks(ilist):
            print(f"({first=},{last=})")
