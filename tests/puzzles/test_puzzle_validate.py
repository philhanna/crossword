from unittest import TestCase

from crossword.puzzles import Puzzle
from crossword.words import Word
from tests import load_test_object


class TestPuzzleValidate(TestCase):

    def test_no_duplicate_words(self):
        puzzle = load_test_object("puzzle_validate")
        errors = puzzle.validate_duplicate_words()
        self.assertEqual(0, len(errors))

    def test_duplicate_words(self):
        puzzle = load_test_object("puzzle_validate")
        puzzle.get_word(7, Word.DOWN).set_text("DAB")
        errors = puzzle.validate_duplicate_words()
        self.assertEqual(1, len(errors))
        self.assertTrue("1 across" in errors[0])
        self.assertTrue("7 down" in errors[0])

    def test_ok_valid(self):
        puzzle = load_test_object("puzzle_validate")
        ok, errors = puzzle.validate()
        self.assertTrue(ok)
        self.assertEqual(4, len(errors))
        self.assertTrue("interlock" in errors)
        self.assertTrue("unchecked" in errors)
        self.assertTrue("wordlength" in errors)
        self.assertTrue("dupwords" in errors)

    def test_ok_invalid(self):
        puzzle = load_test_object("puzzle_validate")
        ok, errors = puzzle.validate()
        self.assertTrue(ok)
        self.assertEqual(4, len(errors))
        self.assertTrue("interlock" in errors)
        self.assertTrue("unchecked" in errors)
        self.assertTrue("wordlength" in errors)
        self.assertTrue("dupwords" in errors)
