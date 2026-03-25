import zipfile
from io import BytesIO

from crossword.adapters.export_adapter import ExportAdapter
from crossword.tests import TestPuzzle


class TestPuzzlePublishAcrossLite:

    def test_get_text(self):
        puzzle = TestPuzzle.create_nyt_daily()
        adapter = ExportAdapter()
        zip_bytes = adapter.export_puzzle_to_acrosslite(puzzle)
        with zipfile.ZipFile(BytesIO(zip_bytes)) as zf:
            text = zf.read("puzzle.txt").decode()
        assert "NINE.USUAL.IRON" in text
