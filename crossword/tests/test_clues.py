from crossword.tests import TestPuzzle


class TestClues:

    def setup_method(self):
        self.puzzle = TestPuzzle.create_solved_atlantic_puzzle()

    def test_set_clue(self):
        word = self.puzzle.get_across_word(1)
        assert "DAB" == word.get_text()
        assert "Dance move that's a hit?" == word.get_clue()
