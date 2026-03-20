import re
import xml.etree.ElementTree as ET
import pytest
from xml.etree.ElementTree import Element

# Skip these tests - they test the old Flask-based UI which is being replaced
# in Phase 2 with a Flask-free HTTP server architecture
pytestmark = pytest.mark.skip(reason="Legacy Flask UI - being replaced in Phase 2")


class TestPuzzleToXML:

    def test_xml(self):
        from crossword.tests import MockUser, TestPuzzle
        from crossword.ui.puzzle_to_xml import PuzzleToXML

        user = MockUser()
        puzzle = TestPuzzle.create_nyt_daily()
        app = PuzzleToXML(user, puzzle)
        root = ET.fromstring(app.xmlstr)
        path = ".//{http://crossword.info/xml/rectangular-puzzle}clue[@number = '50'][@word = '67']"
        clue : Element = root.find(path)
        assert clue is not None
