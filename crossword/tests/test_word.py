from unittest import TestCase

from crossword import AcrossWord, Puzzle, Word
from crossword.tests import TestPuzzle


class TestWord(TestCase):

    def test_is_complete(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
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
        puzzle = self.create_puzzle()
        word = puzzle.get_across_word(17)
        self.assertEqual("NINE", word.get_text())
        cw = word.get_crossing_words()
        self.assertEqual(4, len(cw))
        #self.assertEqual(puzzle.get_down_word(1).get_text(), cw[0])
        #self.assertEqual(puzzle.get_down_word(2).get_text(), cw[1])
        #self.assertEqual(puzzle.get_down_word(3).get_text(), cw[2])
        #self.assertEqual(puzzle.get_down_word(4).get_text(), cw[3])

    @staticmethod
    def create_puzzle():
        jsonstr = r'''{
  "n": 15,
  "black_cells": [
[1,5],[1,11],[2,5],[2,11],[3,5],[3,11],[4,14],
[4,15],[5,7],[5,12],[6,1],[6,2],[6,3],
[6,8],[6,9],[7,4],[8,5],[8,6],[8,10],
[8,11],[9,12],[10,7],[10,8],[10,13],[10,14],
[10,15],[11,4],[11,9],[12,1],[12,2],[13,5],
[13,11],[14,5],[14,11],[15,5],[15,11]],
  "numbered_cells": [
    { "seq": 1, "r": 1, "c": 1, "a": 4, "d": 5 },
    { "seq": 2, "r": 1, "c": 2, "a": 0, "d": 5 },
    { "seq": 3, "r": 1, "c": 3, "a": 0, "d": 5 },
    { "seq": 4, "r": 1, "c": 4, "a": 0, "d": 6 },
    { "seq": 5, "r": 1, "c": 6, "a": 5, "d": 7 },
    { "seq": 6, "r": 1, "c": 7, "a": 0, "d": 4 },
    { "seq": 7, "r": 1, "c": 8, "a": 0, "d": 5 },
    { "seq": 8, "r": 1, "c": 9, "a": 0, "d": 5 },
    { "seq": 9, "r": 1, "c": 10, "a": 0, "d": 7 },
    { "seq": 10, "r": 1, "c": 12, "a": 4, "d": 4 },
    { "seq": 11, "r": 1, "c": 13, "a": 0, "d": 9 },
    { "seq": 12, "r": 1, "c": 14, "a": 0, "d": 3 },
    { "seq": 13, "r": 1, "c": 15, "a": 0, "d": 3 },
    { "seq": 14, "r": 2, "c": 1, "a": 4, "d": 0 },
    { "seq": 15, "r": 2, "c": 6, "a": 5, "d": 0 },
    { "seq": 16, "r": 2, "c": 12, "a": 4, "d": 0 },
    { "seq": 17, "r": 3, "c": 1, "a": 4, "d": 0 },
    { "seq": 18, "r": 3, "c": 6, "a": 5, "d": 0 },
    { "seq": 19, "r": 3, "c": 12, "a": 4, "d": 0 },
    { "seq": 20, "r": 4, "c": 1, "a": 13, "d": 0 },
    { "seq": 21, "r": 4, "c": 5, "a": 0, "d": 4 },
    { "seq": 22, "r": 4, "c": 11, "a": 0, "d": 4 },
    { "seq": 23, "r": 5, "c": 1, "a": 6, "d": 0 },
    { "seq": 24, "r": 5, "c": 8, "a": 4, "d": 0 },
    { "seq": 25, "r": 5, "c": 13, "a": 3, "d": 0 },
    { "seq": 26, "r": 5, "c": 14, "a": 0, "d": 5 },
    { "seq": 27, "r": 5, "c": 15, "a": 0, "d": 5 },
    { "seq": 28, "r": 6, "c": 4, "a": 4, "d": 0 },
    { "seq": 29, "r": 6, "c": 7, "a": 0, "d": 4 },
    { "seq": 30, "r": 6, "c": 10, "a": 6, "d": 0 },
    { "seq": 31, "r": 6, "c": 12, "a": 0, "d": 3 },
    { "seq": 32, "r": 7, "c": 1, "a": 3, "d": 5 },
    { "seq": 33, "r": 7, "c": 2, "a": 0, "d": 5 },
    { "seq": 34, "r": 7, "c": 3, "a": 0, "d": 9 },
    { "seq": 35, "r": 7, "c": 5, "a": 11, "d": 0 },
    { "seq": 36, "r": 7, "c": 8, "a": 0, "d": 3 },
    { "seq": 37, "r": 7, "c": 9, "a": 0, "d": 4 },
    { "seq": 38, "r": 8, "c": 1, "a": 4, "d": 0 },
    { "seq": 39, "r": 8, "c": 4, "a": 0, "d": 3 },
    { "seq": 40, "r": 8, "c": 7, "a": 3, "d": 0 },
    { "seq": 41, "r": 8, "c": 12, "a": 4, "d": 0 },
    { "seq": 42, "r": 9, "c": 1, "a": 11, "d": 0 },
    { "seq": 43, "r": 9, "c": 5, "a": 0, "d": 4 },
    { "seq": 44, "r": 9, "c": 6, "a": 0, "d": 7 },
    { "seq": 45, "r": 9, "c": 10, "a": 0, "d": 7 },
    { "seq": 46, "r": 9, "c": 11, "a": 0, "d": 4 },
    { "seq": 47, "r": 9, "c": 13, "a": 3, "d": 0 },
    { "seq": 48, "r": 10, "c": 1, "a": 6, "d": 0 },
    { "seq": 49, "r": 10, "c": 9, "a": 4, "d": 0 },
    { "seq": 50, "r": 10, "c": 12, "a": 0, "d": 6 },
    { "seq": 51, "r": 11, "c": 1, "a": 3, "d": 0 },
    { "seq": 52, "r": 11, "c": 5, "a": 4, "d": 0 },
    { "seq": 53, "r": 11, "c": 7, "a": 0, "d": 5 },
    { "seq": 54, "r": 11, "c": 8, "a": 0, "d": 5 },
    { "seq": 55, "r": 11, "c": 10, "a": 6, "d": 0 },
    { "seq": 56, "r": 11, "c": 13, "a": 0, "d": 5 },
    { "seq": 57, "r": 11, "c": 14, "a": 0, "d": 5 },
    { "seq": 58, "r": 11, "c": 15, "a": 0, "d": 5 },
    { "seq": 59, "r": 12, "c": 3, "a": 13, "d": 0 },
    { "seq": 60, "r": 12, "c": 4, "a": 0, "d": 4 },
    { "seq": 61, "r": 12, "c": 9, "a": 0, "d": 4 },
    { "seq": 62, "r": 13, "c": 1, "a": 4, "d": 3 },
    { "seq": 63, "r": 13, "c": 2, "a": 0, "d": 3 },
    { "seq": 64, "r": 13, "c": 6, "a": 5, "d": 0 },
    { "seq": 65, "r": 13, "c": 12, "a": 4, "d": 0 },
    { "seq": 66, "r": 14, "c": 1, "a": 4, "d": 0 },
    { "seq": 67, "r": 14, "c": 6, "a": 5, "d": 0 },
    { "seq": 68, "r": 14, "c": 12, "a": 4, "d": 0 },
    { "seq": 69, "r": 15, "c": 1, "a": 4, "d": 0 },
    { "seq": 70, "r": 15, "c": 6, "a": 5, "d": 0 },
    { "seq": 71, "r": 15, "c": 12, "a": 4, "d": 0 }
  ],
  "across_words": [
    { "seq": 1, "text": "ACTS", "clue": "____ of the Apostles" },
    { "seq": 5, "text": "PLASM", "clue": "Suffix with ecto- or proto-" },
    { "seq": 10, "text": "ENVY", "clue": "" },
    { "seq": 14, "text": "SHIM", "clue": "Blade in the pen" },
    { "seq": 15, "text": "     ", "clue": null },
    { "seq": 16, "text": "V   ", "clue": null },
    { "seq": 17, "text": "NINE", "clue": "The Nazgul sum" },
    { "seq": 18, "text": "     ", "clue": null },
    { "seq": 19, "text": "I   ", "clue": null },
    { "seq": 20, "text": "ENTERTAINMENT", "clue": "" },
    { "seq": 23, "text": "RASCAL", "clue": "" },
    { "seq": 24, "text": "    ", "clue": null },
    { "seq": 25, "text": "   ", "clue": null },
    { "seq": 28, "text": "H   ", "clue": "" },
    { "seq": 30, "text": "      ", "clue": null },
    { "seq": 32, "text": "   ", "clue": null },
    { "seq": 35, "text": "           ", "clue": null },
    { "seq": 38, "text": "    ", "clue": null },
    { "seq": 40, "text": "   ", "clue": null },
    { "seq": 41, "text": "    ", "clue": null },
    { "seq": 42, "text": "           ", "clue": null },
    { "seq": 47, "text": "   ", "clue": null },
    { "seq": 48, "text": "      ", "clue": null },
    { "seq": 49, "text": "    ", "clue": null },
    { "seq": 51, "text": "   ", "clue": null },
    { "seq": 52, "text": "    ", "clue": null },
    { "seq": 55, "text": "      ", "clue": null },
    { "seq": 59, "text": "             ", "clue": null },
    { "seq": 62, "text": "    ", "clue": null },
    { "seq": 64, "text": "     ", "clue": null },
    { "seq": 65, "text": "    ", "clue": null },
    { "seq": 66, "text": "    ", "clue": null },
    { "seq": 67, "text": "     ", "clue": null },
    { "seq": 68, "text": "    ", "clue": null },
    { "seq": 69, "text": "    ", "clue": null },
    { "seq": 70, "text": "     ", "clue": null },
    { "seq": 71, "text": "    ", "clue": null }
  ],
  "down_words": [
    { "seq": 1, "text": "ASNER", "clue": "Ed of \"Up\"" },
    { "seq": 2, "text": "CHINA", "clue": "" },
    { "seq": 3, "text": "TINTS", "clue": null },
    { "seq": 4, "text": "SMEECH", "clue": null },
    { "seq": 5, "text": "P  TL  ", "clue": null },
    { "seq": 6, "text": "L  A", "clue": null },
    { "seq": 7, "text": "A  I ", "clue": null },
    { "seq": 8, "text": "S  N ", "clue": null },
    { "seq": 9, "text": "M  M   ", "clue": null },
    { "seq": 10, "text": "EVIN", "clue": "" },
    { "seq": 11, "text": "N  T     ", "clue": null },
    { "seq": 12, "text": "V  ", "clue": null },
    { "seq": 13, "text": "Y  ", "clue": null },
    { "seq": 21, "text": "RA  ", "clue": null },
    { "seq": 22, "text": "E   ", "clue": null },
    { "seq": 26, "text": "     ", "clue": null },
    { "seq": 27, "text": "     ", "clue": null },
    { "seq": 29, "text": "    ", "clue": null },
    { "seq": 31, "text": "   ", "clue": null },
    { "seq": 32, "text": "     ", "clue": null },
    { "seq": 33, "text": "     ", "clue": null },
    { "seq": 34, "text": "         ", "clue": null },
    { "seq": 36, "text": "   ", "clue": null },
    { "seq": 37, "text": "    ", "clue": null },
    { "seq": 39, "text": "   ", "clue": null },
    { "seq": 43, "text": "    ", "clue": null },
    { "seq": 44, "text": "       ", "clue": null },
    { "seq": 45, "text": "       ", "clue": null },
    { "seq": 46, "text": "    ", "clue": null },
    { "seq": 50, "text": "      ", "clue": null },
    { "seq": 53, "text": "     ", "clue": null },
    { "seq": 54, "text": "     ", "clue": null },
    { "seq": 56, "text": "     ", "clue": null },
    { "seq": 57, "text": "     ", "clue": null },
    { "seq": 58, "text": "     ", "clue": null },
    { "seq": 60, "text": "    ", "clue": null },
    { "seq": 61, "text": "    ", "clue": null },
    { "seq": 62, "text": "   ", "clue": null },
    { "seq": 63, "text": "   ", "clue": null }
  ]
}'''
        puzzle = Puzzle.from_json(jsonstr)
        return puzzle
