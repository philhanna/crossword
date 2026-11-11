import pytest

from crossword import Grid, Puzzle

A = "A"
D = "D"

ROWS = ["ABCDE", "FGHIJ", "KLMNO", "PQRST", "UVWXY"]

# Across words 1, 6, 7, 8 and 9 are rows 1 to 5 of an empty 5x5 grid;
# down words 1 to 5 are its columns.
ROW_SEQ = [1, 6, 7, 8, 9]


def make_puzzle(rows=ROWS, locked=(1, 6)):
    """ A filled 5x5 puzzle, every row clued, with the given rows locked """
    puzzle = Puzzle(Grid(5))
    for seq, row in zip(ROW_SEQ, rows):
        puzzle.set_text(seq, A, row, undo=False, check_duplicates=False)
        puzzle.set_clue(seq, A, f"clue for {row}")
    for seq in range(1, 6):
        puzzle.set_clue(seq, D, f"down {seq}")
    for seq in locked:
        puzzle.set_locked(seq, A, True)
    puzzle.undo_stack = []
    return puzzle


def state(puzzle):
    """ Everything a swap may touch, for comparing before and after """
    words = list(puzzle.across_words.values()) + list(puzzle.down_words.values())
    return {(w.seq, w.direction): (w.get_text(), w.get_clue(), w.is_locked())
            for w in words}


class TestSwapWords:

    def test_swaps_letters_and_clues(self):
        puzzle = make_puzzle()
        assert puzzle.swap_words(1, 6, A) is True
        assert "FGHIJ" == puzzle.get_text(1, A)
        assert "ABCDE" == puzzle.get_text(6, A)
        assert "clue for FGHIJ" == puzzle.get_clue(1, A)
        assert "clue for ABCDE" == puzzle.get_clue(6, A)

    def test_both_words_stay_locked(self):
        puzzle = make_puzzle()
        puzzle.swap_words(1, 6, A)
        assert puzzle.get_word(1, A).is_locked()
        assert puzzle.get_word(6, A).is_locked()

    def test_swapping_twice_restores_the_original(self):
        puzzle = make_puzzle()
        before = state(puzzle)
        puzzle.swap_words(1, 6, A)
        puzzle.swap_words(1, 6, A)
        # Crossing clues were cleared by the first swap and stay cleared
        after = state(puzzle)
        for key in before:
            assert before[key][0] == after[key][0]
            assert before[key][2] == after[key][2]

    def test_crossing_clues_cleared_only_where_letters_changed(self):
        puzzle = make_puzzle(rows=["ABCDE", "ABXDE", "KLMNO", "PQRST", "UVWXY"])
        puzzle.swap_words(1, 6, A)
        # Only column 3 differs between the two rows
        assert "down 3" != puzzle.get_clue(3, D)
        assert puzzle.get_clue(3, D) is None
        for seq in (1, 2, 4, 5):
            assert f"down {seq}" == puzzle.get_clue(seq, D)

    def test_swap_works_for_down_words(self):
        puzzle = make_puzzle(locked=())
        puzzle.set_locked(1, D, True)
        puzzle.set_locked(2, D, True)
        puzzle.swap_words(1, 2, D)
        assert "BGLQV" == puzzle.get_text(1, D)
        assert "AFKPU" == puzzle.get_text(2, D)

    def test_unlocked_word_is_refused(self):
        puzzle = make_puzzle(locked=(1,))
        before = state(puzzle)
        with pytest.raises(ValueError, match="locked"):
            puzzle.swap_words(1, 6, A)
        assert before == state(puzzle)

    def test_different_lengths_are_refused(self):
        grid = Grid(5)
        grid.add_black_cell(1, 5, undo=False)
        puzzle = Puzzle(grid)
        short = next(w for w in puzzle.across_words.values() if w.length == 4)
        full = next(w for w in puzzle.across_words.values() if w.length == 5)
        puzzle.set_locked(short.seq, A, True)
        puzzle.set_locked(full.seq, A, True)
        with pytest.raises(ValueError, match="different lengths"):
            puzzle.swap_words(short.seq, full.seq, A)

    def test_unknown_word_is_refused(self):
        puzzle = make_puzzle()
        with pytest.raises(ValueError):
            puzzle.swap_words(1, 99, A)

    def test_same_word_does_nothing(self):
        puzzle = make_puzzle()
        before = state(puzzle)
        assert puzzle.swap_words(1, 1, A) is False
        assert before == state(puzzle)
        assert [] == puzzle.undo_stack

    def test_identical_letters_do_nothing(self):
        puzzle = make_puzzle(rows=["ABCDE", "ABCDE", "KLMNO", "PQRST", "UVWXY"])
        before = state(puzzle)
        assert puzzle.swap_words(1, 6, A) is False
        assert before == state(puzzle)
        assert [] == puzzle.undo_stack

    def test_locked_crossing_word_is_refused(self):
        puzzle = make_puzzle()
        puzzle.set_locked(3, D, True)
        before = state(puzzle)
        with pytest.raises(ValueError, match="3 down"):
            puzzle.swap_words(1, 6, A)
        assert before == state(puzzle)

    def test_locked_crossing_word_is_fine_if_its_letter_is_unchanged(self):
        puzzle = make_puzzle(rows=["ABCDE", "ABXDE", "KLMNO", "PQRST", "UVWXY"])
        puzzle.set_locked(1, D, True)
        assert puzzle.swap_words(1, 6, A) is True

    def test_duplicate_is_refused_and_puzzle_unchanged(self):
        # Swapping rows 1 and 2 turns column 1 (AFKPF) into FAKPF, which is row 5
        puzzle = make_puzzle(rows=["ABCDE", "FGHIJ", "KLMNO", "PQRST", "FAKPF"])
        before = state(puzzle)
        with pytest.raises(ValueError, match="duplicates"):
            puzzle.swap_words(1, 6, A)
        assert before == state(puzzle)
        assert [] == puzzle.undo_stack
        assert puzzle.get_word(1, A).is_locked()
        assert puzzle.get_word(6, A).is_locked()

    def test_incomplete_words_swap_without_clues(self):
        puzzle = make_puzzle()
        puzzle.set_locked(1, A, False)
        puzzle.set_locked(6, A, False)
        puzzle.set_text(1, A, "AB DE", undo=False, check_duplicates=False)
        puzzle.get_word(1, A).set_clue(None)
        puzzle.set_locked(1, A, True)
        puzzle.set_locked(6, A, True)
        puzzle.swap_words(1, 6, A)
        assert "FGHIJ" == puzzle.get_text(1, A)
        assert "AB DE" == puzzle.get_text(6, A)
        assert puzzle.get_clue(6, A) is None
        assert "clue for FGHIJ" == puzzle.get_clue(1, A)


class TestSwapUndoRedo:

    def test_one_undo_restores_everything(self):
        puzzle = make_puzzle()
        before = state(puzzle)
        puzzle.swap_words(1, 6, A)
        assert 1 == len(puzzle.undo_stack)
        puzzle.undo()
        assert before == state(puzzle)
        assert [] == puzzle.undo_stack

    def test_redo_repeats_the_swap(self):
        puzzle = make_puzzle()
        puzzle.swap_words(1, 6, A)
        after = state(puzzle)
        puzzle.undo()
        puzzle.redo()
        assert after == state(puzzle)
        assert 1 == len(puzzle.undo_stack)

    def test_undo_and_redo_keep_both_words_locked(self):
        puzzle = make_puzzle()
        puzzle.swap_words(1, 6, A)
        puzzle.undo()
        assert puzzle.get_word(1, A).is_locked()
        assert puzzle.get_word(6, A).is_locked()
        puzzle.redo()
        assert puzzle.get_word(1, A).is_locked()
        assert puzzle.get_word(6, A).is_locked()
