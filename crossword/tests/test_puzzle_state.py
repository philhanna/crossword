from crossword.domain import puzzle_state as ps
from crossword.tests import TestPuzzle


class TestPuzzleCompletionMethods:
    """Puzzle.is_filled() / Puzzle.all_clues_complete()."""

    def test_is_filled_false_when_empty(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        assert not puzzle.is_filled()

    def test_is_filled_false_when_partial(self):
        puzzle = TestPuzzle.create_atlantic_puzzle_with_some_words()
        assert not puzzle.is_filled()

    def test_is_filled_true_when_solved(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        assert puzzle.is_filled()

    def test_is_filled_false_when_no_words(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        puzzle.across_words = {}
        puzzle.down_words = {}
        assert not puzzle.is_filled()

    def test_all_clues_complete_false_when_empty(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        assert not puzzle.all_clues_complete()

    def test_all_clues_complete_false_when_filled_no_clues(self):
        puzzle = self.filled_no_clues_puzzle()
        assert puzzle.is_filled()
        assert not puzzle.all_clues_complete()

    def test_all_clues_complete_true_when_solved(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        assert puzzle.all_clues_complete()

    def test_all_clues_complete_false_with_whitespace_only_clue(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        puzzle.get_across_word(1).set_clue("   ")
        assert not puzzle.all_clues_complete()

    @staticmethod
    def filled_no_clues_puzzle():
        """A fully filled puzzle with every clue cleared."""
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        words = list(puzzle.across_words.values()) + list(puzzle.down_words.values())
        for word in words:
            word.set_clue(None)
        return puzzle


class TestDetectCompletionState:
    """puzzle_state.detect_completion_state() across the ladder."""

    def test_empty_is_draft(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        assert ps.DRAFT == ps.detect_completion_state(puzzle)

    def test_partial_is_draft(self):
        puzzle = TestPuzzle.create_atlantic_puzzle_with_some_words()
        assert ps.DRAFT == ps.detect_completion_state(puzzle)

    def test_filled_no_clues_is_filled(self):
        puzzle = TestPuzzleCompletionMethods.filled_no_clues_puzzle()
        assert ps.FILLED == ps.detect_completion_state(puzzle)

    def test_solved_is_finished(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        assert ps.FINISHED == ps.detect_completion_state(puzzle)


class TestStateConstants:
    """The module's state vocabulary."""

    def test_all_states(self):
        assert ps.ALL_STATES == [
            ps.DRAFT, ps.FILLED, ps.FINISHED,
            ps.SUBMITTED, ps.PUBLISHED, ps.ARCHIVED,
        ]

    def test_completion_ladder(self):
        assert ps.COMPLETION_LADDER == [ps.DRAFT, ps.FILLED, ps.FINISHED]

    def test_read_only(self):
        assert ps.READ_ONLY == {ps.SUBMITTED, ps.PUBLISHED, ps.ARCHIVED}
