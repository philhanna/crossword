from unittest import TestCase
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from tests import MockUser, TestPuzzle
from crossword.ui.puzzle_to_xml import PuzzleToXML


class TestPuzzleToXML(TestCase):

    def test_xml(self):
        user = MockUser()
        puzzle = TestPuzzle.create_nyt_daily()
        app = PuzzleToXML(user, puzzle)
        root = ET.fromstring(app.xmlstr)
        path = ".//{http://crossword.info/xml/rectangular-puzzle}clue[@number = '50'][@word = '67']"
        clue : Element = root.find(path)
        self.assertIsNotNone(clue, "Clue not found")
