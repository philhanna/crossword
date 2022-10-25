from unittest import TestCase

from crossword.words import Word, AcrossWord
from tests import load_test_object


class TestWord(TestCase):

    def test_is_complete(self):
        puzzle = load_test_object("atlantic_puzzle")
        word = AcrossWord(puzzle, 4)
        word.set_text("HEFT")
        self.assertTrue(word.is_complete())
        word.set_text("EFT")
        self.assertFalse(word.is_complete())
        word.set_text("HEFT")
        self.assertTrue(word.is_complete())

    def test_direction(self):
        self.assertEqual("A", Word.ACROSS)
        self.assertEqual("D", Word.DOWN)

    def test_get_crossing_words(self):
        puzzle = load_test_object("word_puzzle")
        word = puzzle.get_across_word(17)
        self.assertEqual("NINE", word.get_text())
        cw = word.get_crossing_words()
        self.assertEqual(4, len(cw))
