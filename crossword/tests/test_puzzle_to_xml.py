import re
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from crossword.adapters.basic_export_adapter import BasicExportAdapter
from crossword.tests import TestPuzzle


class TestPuzzleToXML:

    def test_xml(self):
        puzzle = TestPuzzle.create_nyt_daily()
        adapter = BasicExportAdapter()
        xmlstr = adapter.export_puzzle_to_xml(puzzle)
        root = ET.fromstring(xmlstr)
        path = ".//{http://crossword.info/xml/rectangular-puzzle}clue[@number = '50'][@word = '67']"
        clue : Element = root.find(path)
        assert clue is not None
