from io import StringIO
from unittest import TestCase

from crossword.clue_import_visitor import ClueImportVisitor
from test.test_puzzle import TestPuzzle


class TestImportClues(TestCase):

    def test_changed_clue(self):
        with StringIO() as fp:
            fp.write("seq,direction,word,clue" + "\n")
            fp.write("13,across,REUNITED,...and it feels so nice" + "\n")
            csvstr = fp.getvalue()

        visitor = ClueImportVisitor(csvstr)
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        puzzle.accept(visitor)

        expected = "...and it feels so nice"
        actual = puzzle.get_across_word(13).get_clue()
        self.assertEqual(expected, actual)

    def test_incompatible_puzzle(self):
        with StringIO() as fp:
            fp.write("seq,direction,word,clue" + "\n")
            fp.write("44,across,REUNITED,...and it feels so nice" + "\n")
            csvstr = fp.getvalue()

        visitor = ClueImportVisitor(csvstr)
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        try:
            puzzle.accept(visitor)
            expected = "...and it feels so nice"
            actual = puzzle.get_across_word(44).get_clue()
            self.assertEqual(expected, actual)
        except RuntimeError:
            pass # This was expected
