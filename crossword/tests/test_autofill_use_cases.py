"""
Unit tests for AutofillUseCases and the puzzle-level pieces it relies on
"""

import pytest
from unittest.mock import Mock

from crossword import Grid, Puzzle
from crossword.adapters.flat_file_word_list_adapter import FlatFileWordListAdapter
from crossword.use_cases import autofill_use_cases
from crossword.use_cases.autofill_use_cases import AutofillError, AutofillUseCases
from crossword.use_cases.puzzle_use_cases import PuzzleUseCases

THREE_LETTER_WORDS = """
    ace ale ant ape arc are ark art ash ate bad bag bar bat bed bee bet bit
    box bus buy cab can cap car cat cop cow cry cup cut dad day den dig dog
    dot dry due ear eat egg end eve eye fan far fat fed few fin fit fix fly
    fog for fun gap gas get god gum gun guy had ham has hat hen her hid him
    his hit hot how hub hug ice ill ink inn ion its jam jar jaw joy key kid
    kit lab lap law lay leg let lid lip log lot low mad man map mat may men
    met mix mud nap net new nod not now nut oak oar oat odd off oil old one
    our out owe owl pad pan pat paw pay pen pet pie pig pin pit pot put rad
    rag ram ran rat raw ray red rib rid rim rip rod row rub rug run sad sat
    saw say sea see set sew she shy sin sip sir sit six sky sly son sow soy
    spy sub sum sun tab tag tan tap tar tea ten the tie tin tip toe ton too
    top toy try tub two urn use van vat vet war was wax way web wed wet who
    why win wit won yes yet you zip zoo
""".split()


def make_word_list(words):
    word_list = FlatFileWordListAdapter()
    word_list._build_index({w.lower() for w in words})
    return word_list


def make_puzzle(rows=None, size=3, black=()):
    """An open size x size grid, optionally with letters from rows
    (strings, " " for blank) typed in"""
    grid = Grid(size)
    for r, c in black:
        grid.add_black_cell(r, c, undo=False)
    puzzle = Puzzle(grid)
    for r, row in enumerate(rows or [], start=1):
        for c, letter in enumerate(row, start=1):
            puzzle.set_cell(r, c, letter)
    return puzzle


def all_words(puzzle):
    return list(puzzle.across_words.values()) + list(puzzle.down_words.values())


@pytest.fixture
def autofill_uc():
    return AutofillUseCases(make_word_list(THREE_LETTER_WORDS))


class TestAutofill:

    def test_fills_every_word_with_a_list_word(self, autofill_uc):
        puzzle = make_puzzle()

        result = autofill_uc.autofill(puzzle, seed=1)

        assert result.success
        texts = [w.get_text() for w in all_words(puzzle)]
        assert len(texts) == 6
        assert all(t.lower() in THREE_LETTER_WORDS for t in texts)

    def test_no_repeated_words(self, autofill_uc):
        puzzle = make_puzzle()

        autofill_uc.autofill(puzzle, seed=2)

        texts = [w.get_text() for w in all_words(puzzle)]
        assert len(set(texts)) == len(texts)

    def test_keeps_letters_already_placed(self, autofill_uc):
        puzzle = make_puzzle(["C  ", "   ", "   "])

        result = autofill_uc.autofill(puzzle, seed=3)

        assert result.success
        assert puzzle.get_cell(1, 1) == "C"
        assert puzzle.get_text(1, "A").startswith("C")
        assert puzzle.get_text(1, "D").startswith("C")

    def test_leaves_complete_and_locked_words_alone(self, autofill_uc):
        puzzle = make_puzzle(["RAT", "   ", "   "])
        puzzle.set_locked(1, "A", True)

        result = autofill_uc.autofill(puzzle, seed=4)

        assert result.success
        assert puzzle.get_text(1, "A") == "RAT"
        assert puzzle.get_word(1, "A").is_locked()

    def test_complete_word_missing_from_list_is_kept(self, autofill_uc):
        puzzle = make_puzzle(["QZX", "   ", "   "])

        result = autofill_uc.autofill(puzzle, seed=5)

        # The crossing words must start with Q, Z and X, which no word does
        assert not result.success
        assert puzzle.get_text(1, "A") == "QZX"

    def test_already_full_puzzle_is_a_successful_no_op(self, autofill_uc):
        puzzle = make_puzzle(["RAT", "   ", "   "])
        autofill_uc.autofill(puzzle, seed=6)
        before = str(puzzle)
        undo_depth = len(puzzle.undo_stack)

        result = autofill_uc.autofill(puzzle, seed=7)

        assert result.success and result.fills == {}
        assert str(puzzle) == before
        assert len(puzzle.undo_stack) == undo_depth

    def test_same_seed_gives_same_fill(self, autofill_uc):
        first, second = make_puzzle(), make_puzzle()

        autofill_uc.autofill(first, seed=42)
        autofill_uc.autofill(second, seed=42)

        assert str(first) == str(second)

    def test_one_undo_removes_whole_fill_and_one_redo_restores_it(self, autofill_uc):
        puzzle = make_puzzle(["C  ", "   ", "   "])
        before = str(puzzle)
        autofill_uc.autofill(puzzle, seed=8)
        filled = str(puzzle)
        assert filled != before

        puzzle.undo()
        assert str(puzzle) == before

        puzzle.redo()
        assert str(puzzle) == filled

    def test_undo_stack_survives_json_round_trip(self, autofill_uc):
        puzzle = make_puzzle(["C  ", "   ", "   "])
        before = str(puzzle)
        autofill_uc.autofill(puzzle, seed=9)

        restored = Puzzle.from_json(puzzle.to_json())
        restored.undo()

        assert str(restored) == before


class TestAutofillFailure:

    def test_impossible_grid_fails_and_changes_nothing(self):
        # Every across word would start with a vowel-less pair that no
        # down word can continue
        uc = AutofillUseCases(make_word_list(["cat", "dog", "pig"]))
        puzzle = make_puzzle()
        before = str(puzzle)

        result = uc.autofill(puzzle, seed=1)

        assert not result.success
        assert "No fill is possible" in result.message
        assert str(puzzle) == before
        assert puzzle.undo_stack == []

    def test_slot_with_no_candidates_is_named(self, autofill_uc):
        puzzle = make_puzzle(["QQ ", "   ", "   "])

        result = autofill_uc.autofill(puzzle, seed=1)

        assert not result.success
        assert "No words fit 1-Across" in result.message
        assert "QQ." in result.message

    def test_empty_word_list_fails_cleanly(self):
        uc = AutofillUseCases(make_word_list([]))
        puzzle = make_puzzle()

        result = uc.autofill(puzzle, seed=1)

        assert not result.success
        assert puzzle.undo_stack == []

    def test_locked_incomplete_word_is_reported(self, autofill_uc):
        puzzle = make_puzzle(["CA ", "   ", "   "])
        puzzle.set_locked(1, "A", True)

        result = autofill_uc.autofill(puzzle, seed=1)

        assert not result.success
        assert "1-Across is locked but not filled in" in result.message

    def test_gives_up_when_time_runs_out(self, autofill_uc, monkeypatch):
        clock = iter(range(0, 1000))
        monkeypatch.setattr(autofill_use_cases.time, "monotonic", lambda: next(clock))
        monkeypatch.setattr(autofill_use_cases, "FIRST_ATTEMPT_BUDGET", 0)
        puzzle = make_puzzle()
        before = str(puzzle)

        result = autofill_uc.autofill(puzzle, time_limit=0, seed=1)

        assert not result.success
        assert "No fill found in 0 seconds" in result.message
        assert str(puzzle) == before


class TestPuzzleUseCasesAutofill:

    def test_saves_the_filled_puzzle(self, autofill_uc):
        persistence = Mock()
        puzzle = make_puzzle()
        persistence.load_puzzle.return_value = puzzle
        puzzle_uc = PuzzleUseCases(persistence, autofill_uc=autofill_uc)

        result = puzzle_uc.autofill(1, "p", seed=1)

        assert result.is_filled()
        persistence.save_puzzle.assert_called_once_with(1, "p", puzzle)

    def test_failure_raises_and_saves_nothing(self):
        persistence = Mock()
        persistence.load_puzzle.return_value = make_puzzle()
        uc = AutofillUseCases(make_word_list(["cat", "dog", "pig"]))
        puzzle_uc = PuzzleUseCases(persistence, autofill_uc=uc)

        with pytest.raises(AutofillError, match="No fill is possible"):
            puzzle_uc.autofill(1, "p", seed=1)

        persistence.save_puzzle.assert_not_called()

    def test_without_a_word_list_raises(self):
        puzzle_uc = PuzzleUseCases(Mock())

        with pytest.raises(AutofillError, match="not available"):
            puzzle_uc.autofill(1, "p")
