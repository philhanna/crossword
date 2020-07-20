from unittest import TestCase

from crossword.tests import MockUser, TestPuzzle
from crossword.ui.puzzle_to_xml import PuzzleToXML


class TestPuzzleToXML(TestCase):

    def test_xml(self):
        user = MockUser()
        puzzle = TestPuzzle.create_nyt_daily()
        app = PuzzleToXML(user, puzzle)
        print(app.xmlstr)
        self.assertTrue('<clue number="50" word="67">Lollipop</clue>' in app.xmlstr, app.xmlstr)

    # Skip this unless writing a new version to Dropbox
    def notest_xml_temp_write(self):
        user = MockUser()
        puzzle = TestPuzzle.create_nyt_daily()
        app = PuzzleToXML(user, puzzle)
        with open("/home/saspeh/Dropbox/crossword/acts_mine.xml", "w") as fp:
            fp.write(app.xmlstr)
