# crossword.tests.adapters.test_ipuz_import_adapter
import json
import pytest

from crossword import Grid, Puzzle
from crossword.adapters.ipuz_export_adapter import IpuzExportAdapter
from crossword.adapters.ipuz_import_adapter import IpuzImportAdapter
from crossword.domain.word import Word
from crossword.ports.import_port import PuzzleImportError


@pytest.fixture
def adapter():
    return IpuzImportAdapter()


def _sample_doc(size=3, with_solution=True, with_clues=True):
    n = size
    puzzle_grid = []
    seq = 1
    # Open grid → every row-starting cell and every column-starting cell is numbered
    for r in range(n):
        row = []
        for c in range(n):
            is_word_start = (r == 0) or (c == 0)
            if is_word_start:
                row.append(seq)
                seq += 1
            else:
                row.append(0)
        puzzle_grid.append(row)

    doc = {
        "version": "http://ipuz.org/v2",
        "kind": ["http://ipuz.org/crossword#1"],
        "dimensions": {"width": n, "height": n},
        "title": "Sample Puzzle",
        "author": "Test Author",
        "block": "#",
        "empty": 0,
        "puzzle": puzzle_grid,
    }
    if with_solution:
        letters = [
            ["A", "B", "C"],
            ["D", "E", "F"],
            ["G", "H", "I"],
        ]
        doc["solution"] = letters
    if with_clues:
        doc["clues"] = {
            "Across": [[1, "Across clue 1"], [4, "Across clue 4"], [5, "Across clue 5"]],
            "Down": [[1, "Down clue 1"], [2, "Down clue 2"], [3, "Down clue 3"]],
        }
    return doc


class TestIpuzImportSuccess:
    def test_returns_tuple_of_three(self, adapter):
        result = adapter.import_puzzle(json.dumps(_sample_doc()))
        assert isinstance(result, tuple) and len(result) == 3

    def test_title_extracted(self, adapter):
        title, _, _ = adapter.import_puzzle(json.dumps(_sample_doc()))
        assert title == "Sample Puzzle"

    def test_author_extracted(self, adapter):
        _, author, _ = adapter.import_puzzle(json.dumps(_sample_doc()))
        assert author == "Test Author"

    def test_puzzle_size(self, adapter):
        _, _, puzzle = adapter.import_puzzle(json.dumps(_sample_doc(size=3)))
        assert puzzle.n == 3

    def test_solution_letters_filled(self, adapter):
        _, _, puzzle = adapter.import_puzzle(json.dumps(_sample_doc()))
        assert puzzle.get_cell(1, 1) == "A"
        assert puzzle.get_cell(2, 2) == "E"
        assert puzzle.get_cell(3, 3) == "I"

    def test_clues_applied(self, adapter):
        _, _, puzzle = adapter.import_puzzle(json.dumps(_sample_doc()))
        assert puzzle.get_clue(1, Word.ACROSS) == "Across clue 1"
        assert puzzle.get_clue(1, Word.DOWN) == "Down clue 1"

    def test_imported_puzzle_is_in_puzzle_mode(self, adapter):
        _, _, puzzle = adapter.import_puzzle(json.dumps(_sample_doc()))
        assert puzzle.last_mode == "puzzle"

    def test_empty_title_and_author_return_empty_string(self, adapter):
        doc = _sample_doc()
        doc["title"] = ""
        doc.pop("author")
        title, author, _ = adapter.import_puzzle(json.dumps(doc))
        assert title == ""
        assert author == ""

    def test_clues_optional(self, adapter):
        _, _, puzzle = adapter.import_puzzle(
            json.dumps(_sample_doc(with_clues=False))
        )
        for seq in puzzle.across_words:
            assert puzzle.get_clue(seq, Word.ACROSS) in (None, "")

    def test_solution_optional(self, adapter):
        _, _, puzzle = adapter.import_puzzle(
            json.dumps(_sample_doc(with_solution=False))
        )
        # No solution → cells unfilled (None, empty, or whitespace)
        cell = puzzle.get_cell(1, 1)
        assert cell is None or not cell.strip()

    def test_clue_object_form_supported(self, adapter):
        doc = _sample_doc()
        doc["clues"]["Across"] = [
            {"number": 1, "clue": "obj clue 1"},
            {"number": 4, "clue": "obj clue 4"},
            {"number": 5, "clue": "obj clue 5"},
        ]
        _, _, puzzle = adapter.import_puzzle(json.dumps(doc))
        assert puzzle.get_clue(1, Word.ACROSS) == "obj clue 1"

    def test_custom_block_marker(self, adapter):
        # 3x3 with center black cell using "B" as the block marker
        doc = {
            "version": "http://ipuz.org/v2",
            "kind": ["http://ipuz.org/crossword#1"],
            "dimensions": {"width": 3, "height": 3},
            "block": "B",
            "puzzle": [
                [1, 2, 3],
                [4, "B", 0],
                [5, 0, 0],
            ],
        }
        _, _, puzzle = adapter.import_puzzle(json.dumps(doc))
        assert puzzle.is_black_cell(2, 2)

    def test_html_entities_in_clues_unescaped(self, adapter):
        doc = _sample_doc()
        doc["clues"]["Across"] = [
            [1, "Say &quot;hi&quot; &mdash; quick"],
            [4, "AT&amp;T"],
            [5, "5 &lt; 6"],
        ]
        _, _, puzzle = adapter.import_puzzle(json.dumps(doc))
        assert puzzle.get_clue(1, Word.ACROSS) == 'Say "hi" — quick'
        assert puzzle.get_clue(4, Word.ACROSS) == "AT&T"
        assert puzzle.get_clue(5, Word.ACROSS) == "5 < 6"

    def test_html_tags_in_clues_stripped(self, adapter):
        doc = _sample_doc()
        doc["clues"]["Across"] = [
            [1, "see <i>this</i>"],
            [4, "a <b>bold</b> claim"],
            [5, "&lt;i&gt;escaped&lt;/i&gt; tag"],
        ]
        _, _, puzzle = adapter.import_puzzle(json.dumps(doc))
        assert puzzle.get_clue(1, Word.ACROSS) == "see this"
        assert puzzle.get_clue(4, Word.ACROSS) == "a bold claim"
        assert puzzle.get_clue(5, Word.ACROSS) == "escaped tag"

    def test_callback_wrapped_ipuz_accepted(self, adapter):
        content = "ipuz(" + json.dumps(_sample_doc()) + ")"
        title, _, _ = adapter.import_puzzle(content)
        assert title == "Sample Puzzle"


class TestIpuzImportRoundTrip:
    def test_export_then_import_preserves_letters(self):
        grid = Grid(3)
        p = Puzzle(grid, title="RT")
        p.enter_puzzle_mode()
        for seq in sorted(p.across_words):
            w = p.across_words[seq]
            w.set_text("ABC"[: w.length])
            w.set_clue(f"A{seq}")
        for seq in sorted(p.down_words):
            w = p.down_words[seq]
            w.set_text("DEF"[: w.length])
            w.set_clue(f"D{seq}")

        ipuz_text = IpuzExportAdapter(author_name="Tester").export_puzzle_to_ipuz(p)
        title, author, imported = IpuzImportAdapter().import_puzzle(ipuz_text)

        assert title == "RT"
        assert author == "Tester"
        assert imported.n == p.n
        for r in range(1, p.n + 1):
            for c in range(1, p.n + 1):
                if not p.is_black_cell(r, c):
                    assert imported.get_cell(r, c) == p.get_cell(r, c)

    def test_round_trip_with_black_cells(self):
        grid = Grid(5)
        grid.add_black_cell(3, 3)
        p = Puzzle(grid, title="BlackRT")
        p.enter_puzzle_mode()
        ipuz_text = IpuzExportAdapter().export_puzzle_to_ipuz(p)
        _, _, imported = IpuzImportAdapter().import_puzzle(ipuz_text)
        assert imported.is_black_cell(3, 3)

    def test_clues_survive_round_trip(self):
        grid = Grid(3)
        p = Puzzle(grid, title="CluesRT")
        p.enter_puzzle_mode()
        for seq in sorted(p.across_words):
            p.set_clue(seq, Word.ACROSS, f"Across {seq}")
        for seq in sorted(p.down_words):
            p.set_clue(seq, Word.DOWN, f"Down {seq}")
        ipuz_text = IpuzExportAdapter().export_puzzle_to_ipuz(p)
        _, _, imported = IpuzImportAdapter().import_puzzle(ipuz_text)
        for seq in p.across_words:
            assert imported.get_clue(seq, Word.ACROSS) == f"Across {seq}"
        for seq in p.down_words:
            assert imported.get_clue(seq, Word.DOWN) == f"Down {seq}"


class TestIpuzImportErrors:
    def test_invalid_json_raises(self, adapter):
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle("not json at all")

    def test_missing_kind_raises(self, adapter):
        doc = _sample_doc()
        doc.pop("kind")
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle(json.dumps(doc))

    def test_unsupported_kind_raises(self, adapter):
        doc = _sample_doc()
        doc["kind"] = ["http://ipuz.org/sudoku#1"]
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle(json.dumps(doc))

    def test_missing_puzzle_grid_raises(self, adapter):
        doc = _sample_doc()
        doc.pop("puzzle")
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle(json.dumps(doc))

    def test_non_square_grid_raises(self, adapter):
        doc = _sample_doc()
        doc["dimensions"] = {"width": 4, "height": 3}
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle(json.dumps(doc))

    def test_asymmetric_grid_raises(self, adapter):
        doc = _sample_doc(size=5, with_solution=False, with_clues=False)
        # Single black at (1,1) only — no mirror → asymmetric
        doc["puzzle"][0][0] = "#"
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle(json.dumps(doc))

    def test_root_must_be_object(self, adapter):
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle("[1, 2, 3]")
