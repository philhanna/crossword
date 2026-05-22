# crossword.tests.adapters.test_ccxml_import_adapter
import pytest

from crossword import Grid, Puzzle
from crossword.adapters.ccxml_export_adapter import CcxmlExportAdapter
from crossword.adapters.ccxml_import_adapter import CcxmlImportAdapter
from crossword.domain.word import Word
from crossword.ports.import_port import PuzzleImportError


@pytest.fixture
def adapter():
    return CcxmlImportAdapter()


def _build_sample_xml(
    title="Sample Puzzle",
    creator="Test Author",
    include_metadata=True,
    omit_grid=False,
):
    """3x3 open grid (no black cells), letters A..I, simple clues."""
    parts = ['<?xml version="1.0" encoding="UTF-8"?>']
    parts.append('<crossword-compiler xmlns="http://crossword.info/xml/crossword-compiler">')
    parts.append('<rectangular-puzzle xmlns="http://crossword.info/xml/rectangular-puzzle">')
    if include_metadata:
        parts.append('<metadata>')
        parts.append(f'<title>{title}</title>')
        parts.append(f'<creator>{creator}</creator>')
        parts.append('</metadata>')
    parts.append('<crossword>')
    if not omit_grid:
        parts.append('<grid width="3" height="3">')
        letters = [
            ["A", "B", "C"],
            ["D", "E", "F"],
            ["G", "H", "I"],
        ]
        # cells are 1-indexed; x=col, y=row
        seq_map = {(1, 1): 1, (1, 2): 2, (1, 3): 3, (2, 1): 4, (3, 1): 5}
        for c in range(1, 4):
            for r in range(1, 4):
                letter = letters[r - 1][c - 1]
                num = seq_map.get((r, c))
                num_attr = f' number="{num}"' if num else ''
                parts.append(f'<cell x="{c}" y="{r}" solution="{letter}"{num_attr}/>')
        parts.append('</grid>')
        # Across words: ids 1,2,3 → seq 1,2,3 (rows 1,2,3)
        parts.append('<word id="1" x="1-3" y="1"/>')
        parts.append('<word id="2" x="1-3" y="2"/>')
        parts.append('<word id="3" x="1-3" y="3"/>')
        # Down words: ids 4,5,6 → seq 1,4,5
        parts.append('<word id="4" x="1" y="1-3"/>')
        parts.append('<word id="5" x="2" y="1-3"/>')
        parts.append('<word id="6" x="3" y="1-3"/>')
        # Across clues — in an open 3x3, across starts are at seq 1, 4, 5
        parts.append('<clues ordering="normal">')
        parts.append('<title><b>Across</b></title>')
        parts.append('<clue word="1" number="1">Across clue 1</clue>')
        parts.append('<clue word="2" number="4">Across clue 4</clue>')
        parts.append('<clue word="3" number="5">Across clue 5</clue>')
        parts.append('</clues>')
        # Down clues — note seq numbers come from across numbering (1,4,5 not 4,5,6)
        parts.append('<clues ordering="normal">')
        parts.append('<title><b>Down</b></title>')
        parts.append('<clue word="4" number="1">Down clue 1</clue>')
        parts.append('<clue word="5" number="2">Down clue 2</clue>')
        parts.append('<clue word="6" number="3">Down clue 3</clue>')
        parts.append('</clues>')
    parts.append('</crossword>')
    parts.append('</rectangular-puzzle>')
    parts.append('</crossword-compiler>')
    return '\n'.join(parts)


class TestCcxmlImportSuccess:
    def test_returns_tuple_of_three(self, adapter):
        result = adapter.import_puzzle(_build_sample_xml())
        assert isinstance(result, tuple) and len(result) == 3

    def test_title_extracted(self, adapter):
        title, _, _ = adapter.import_puzzle(_build_sample_xml())
        assert title == "Sample Puzzle"

    def test_author_extracted(self, adapter):
        _, author, _ = adapter.import_puzzle(_build_sample_xml())
        assert author == "Test Author"

    def test_puzzle_size(self, adapter):
        _, _, puzzle = adapter.import_puzzle(_build_sample_xml())
        assert puzzle.n == 3

    def test_solution_letters_filled(self, adapter):
        _, _, puzzle = adapter.import_puzzle(_build_sample_xml())
        assert puzzle.get_cell(1, 1) == "A"
        assert puzzle.get_cell(2, 2) == "E"
        assert puzzle.get_cell(3, 3) == "I"

    def test_across_clues_applied(self, adapter):
        _, _, puzzle = adapter.import_puzzle(_build_sample_xml())
        assert puzzle.get_clue(1, Word.ACROSS) == "Across clue 1"
        assert puzzle.get_clue(4, Word.ACROSS) == "Across clue 4"
        assert puzzle.get_clue(5, Word.ACROSS) == "Across clue 5"

    def test_down_clues_applied(self, adapter):
        _, _, puzzle = adapter.import_puzzle(_build_sample_xml())
        # Down seq numbers for an open 3x3 are 1, 2, 3 (every top-row cell starts a down)
        assert puzzle.get_clue(1, Word.DOWN) == "Down clue 1"
        assert puzzle.get_clue(2, Word.DOWN) == "Down clue 2"
        assert puzzle.get_clue(3, Word.DOWN) == "Down clue 3"

    def test_imported_puzzle_is_in_puzzle_mode(self, adapter):
        _, _, puzzle = adapter.import_puzzle(_build_sample_xml())
        assert puzzle.last_mode == "puzzle"

    def test_missing_metadata_returns_empty_strings(self, adapter):
        xml = _build_sample_xml(include_metadata=False)
        title, author, _ = adapter.import_puzzle(xml)
        assert title == ""
        assert author == ""

    def test_clue_direction_inferred_from_word_when_title_missing(self, adapter):
        """If <title> text is absent, direction is taken from the referenced <word>."""
        xml = _build_sample_xml()
        # Strip out the <b>Across</b>/<b>Down</b> text — leave bare <title/>
        xml = xml.replace("<title><b>Across</b></title>", "<title/>")
        xml = xml.replace("<title><b>Down</b></title>", "<title/>")
        _, _, puzzle = adapter.import_puzzle(xml)
        assert puzzle.get_clue(1, Word.ACROSS) == "Across clue 1"
        assert puzzle.get_clue(1, Word.DOWN) == "Down clue 1"

    def test_black_cell_imported(self, adapter):
        """5x5 with a center black cell — verify it lands in the right spot."""
        parts = [
            '<?xml version="1.0"?>',
            '<crossword-compiler>',
            '<rectangular-puzzle>',
            '<metadata><title>Blk</title><creator></creator></metadata>',
            '<crossword>',
            '<grid width="5" height="5">',
        ]
        for c in range(1, 6):
            for r in range(1, 6):
                if (r, c) == (3, 3):
                    parts.append(f'<cell x="{c}" y="{r}" type="block"/>')
                else:
                    parts.append(f'<cell x="{c}" y="{r}" solution="X"/>')
        parts += ['</grid>', '</crossword>', '</rectangular-puzzle>', '</crossword-compiler>']
        _, _, puzzle = adapter.import_puzzle('\n'.join(parts))
        assert puzzle.is_black_cell(3, 3)

    def test_html_entities_in_clues_unescaped(self, adapter):
        xml = _build_sample_xml().replace(
            "Across clue 1",
            "Say &amp;quot;hi&amp;quot; &amp;mdash; quick",
        )
        _, _, puzzle = adapter.import_puzzle(xml)
        assert puzzle.get_clue(1, Word.ACROSS) == 'Say "hi" — quick'

    def test_html_tags_in_clues_stripped(self, adapter):
        xml = _build_sample_xml().replace(
            "Across clue 1",
            "see &lt;i&gt;this&lt;/i&gt;",
        )
        _, _, puzzle = adapter.import_puzzle(xml)
        assert puzzle.get_clue(1, Word.ACROSS) == "see this"

    def test_no_namespace_accepted(self, adapter):
        """Files lacking the xmlns declarations should still parse."""
        xml = """<?xml version="1.0"?>
<crossword-compiler>
  <rectangular-puzzle>
    <metadata><title>NoNS</title><creator>Tester</creator></metadata>
    <crossword>
      <grid width="2" height="2">
        <cell x="1" y="1" solution="A" number="1"/>
        <cell x="2" y="1" solution="B" number="2"/>
        <cell x="1" y="2" solution="C" number="3"/>
        <cell x="2" y="2" solution="D"/>
      </grid>
    </crossword>
  </rectangular-puzzle>
</crossword-compiler>"""
        title, author, puzzle = adapter.import_puzzle(xml)
        assert title == "NoNS"
        assert author == "Tester"
        assert puzzle.get_cell(2, 2) == "D"


class TestCcxmlImportRoundTrip:
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

        xml = CcxmlExportAdapter(author_name="Tester").export_puzzle_to_xml(p)
        title, author, imported = CcxmlImportAdapter().import_puzzle(xml)

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
        xml = CcxmlExportAdapter().export_puzzle_to_xml(p)
        _, _, imported = CcxmlImportAdapter().import_puzzle(xml)
        assert imported.is_black_cell(3, 3)

    def test_clues_survive_round_trip(self):
        grid = Grid(3)
        p = Puzzle(grid, title="CluesRT")
        p.enter_puzzle_mode()
        for seq in sorted(p.across_words):
            p.set_clue(seq, Word.ACROSS, f"Across {seq}")
        for seq in sorted(p.down_words):
            p.set_clue(seq, Word.DOWN, f"Down {seq}")
        xml = CcxmlExportAdapter().export_puzzle_to_xml(p)
        _, _, imported = CcxmlImportAdapter().import_puzzle(xml)
        for seq in p.across_words:
            assert imported.get_clue(seq, Word.ACROSS) == f"Across {seq}"
        for seq in p.down_words:
            assert imported.get_clue(seq, Word.DOWN) == f"Down {seq}"


class TestCcxmlImportErrors:
    def test_invalid_xml_raises(self, adapter):
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle("not xml at all <<<")

    def test_missing_rectangular_puzzle_raises(self, adapter):
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle('<?xml version="1.0"?><something-else/>')

    def test_missing_grid_raises(self, adapter):
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle(_build_sample_xml(omit_grid=True))

    def test_non_square_grid_raises(self, adapter):
        xml = """<?xml version="1.0"?>
<crossword-compiler><rectangular-puzzle><crossword>
<grid width="4" height="3"></grid>
</crossword></rectangular-puzzle></crossword-compiler>"""
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle(xml)

    def test_missing_cell_raises(self, adapter):
        xml = """<?xml version="1.0"?>
<crossword-compiler><rectangular-puzzle><crossword>
<grid width="2" height="2">
<cell x="1" y="1" solution="A"/>
<cell x="2" y="1" solution="B"/>
<cell x="1" y="2" solution="C"/>
</grid>
</crossword></rectangular-puzzle></crossword-compiler>"""
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle(xml)

    def test_asymmetric_grid_raises(self, adapter):
        parts = [
            '<?xml version="1.0"?>',
            '<crossword-compiler><rectangular-puzzle><crossword>',
            '<grid width="5" height="5">',
        ]
        for c in range(1, 6):
            for r in range(1, 6):
                if (r, c) == (1, 1):
                    parts.append(f'<cell x="{c}" y="{r}" type="block"/>')
                else:
                    parts.append(f'<cell x="{c}" y="{r}" solution="X"/>')
        parts += ['</grid>', '</crossword></rectangular-puzzle></crossword-compiler>']
        with pytest.raises(PuzzleImportError):
            adapter.import_puzzle('\n'.join(parts))
