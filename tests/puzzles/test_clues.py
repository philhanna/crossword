from unittest import TestCase

from tests import load_test_puzzle


class TestClues(TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.puzzle = load_test_puzzle("solved_atlantic_puzzle")

    def test_set_clue(self):
        word = self.puzzle.get_across_word(1)
        self.assertEqual("DAB", word.get_text())
        self.assertEqual("Dance move that's a hit?", word.get_clue())
