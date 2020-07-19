from unittest import TestCase

from crossword.tests import MockUser, TestPuzzle
from crossword.ui.puzzle_to_xml import PuzzleToXML


class TestPuzzleToXML(TestCase):

    def test_xml(self):
        user = MockUser()
        puzzle = TestPuzzle.create_nyt_daily()
        app = PuzzleToXML(user, puzzle)
        self.assertTrue('<clue number="50" word="67">Lollipop</clue>' in app.xmlstr, app.xmlstr)
