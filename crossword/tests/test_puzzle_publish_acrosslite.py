from crossword.adapters.acrosslite_export_adapter import AcrossLiteExportAdapter
from crossword.tests import TestPuzzle


class TestPuzzlePublishAcrossLite:

    def test_get_text(self):
        puzzle = TestPuzzle.create_nyt_daily()
        adapter = AcrossLiteExportAdapter()
        text = adapter.export_puzzle_to_acrosslite(puzzle)
        assert "NINE.USUAL.IRON" in text
