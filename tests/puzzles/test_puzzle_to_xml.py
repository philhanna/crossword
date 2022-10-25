import xml.etree.ElementTree as ET
from unittest import TestCase
from xml.etree.ElementTree import Element

from crossword.ui.puzzle_to_xml import PuzzleToXML
from tests import MockUser, load_pickled_puzzle


class TestPuzzleToXML(TestCase):

    def test_xml(self):
        user = MockUser()
        puzzle = load_pickled_puzzle("nyt_daily")
        app = PuzzleToXML(user, puzzle)
        root = ET.fromstring(app.xmlstr)
        path = ".//{http://crossword.info/xml/rectangular-puzzle}clue[@number = '50'][@word = '67']"
        clue : Element = root.find(path)
        self.assertIsNotNone(clue, "Clue not found")
