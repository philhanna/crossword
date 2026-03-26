import zipfile
from io import BytesIO

from crossword.adapters.basic_export_adapter import BasicExportAdapter
from crossword.tests import TestPuzzle


class TestPuzzlePublishAcrossLite:

    def test_get_text(self):
        puzzle = TestPuzzle.create_nyt_daily()
        adapter = BasicExportAdapter()
        zip_bytes = adapter.export_puzzle_to_acrosslite(puzzle)
        with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
            text = zf.read("puzzle.txt").decode()
        assert "NINE.USUAL.IRON" in text
