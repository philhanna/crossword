from unittest import TestCase

from crossword.puzzles import Puzzle
from crossword.words import Word


class TestPuzzleValidate(TestCase):

    def test_no_duplicate_words(self):
        puzzle = self.create_test_puzzle()
        errors = puzzle.validate_duplicate_words()
        self.assertEqual(0, len(errors))

    def test_duplicate_words(self):
        puzzle = self.create_test_puzzle()
        puzzle.get_word(7, Word.DOWN).set_text("DAB")
        errors = puzzle.validate_duplicate_words()
        self.assertEqual(1, len(errors))
        self.assertTrue("1 across" in errors[0])
        self.assertTrue("7 down" in errors[0])

    def test_ok_valid(self):
        puzzle = self.create_test_puzzle()
        ok, errors = puzzle.validate()
        self.assertTrue(ok)
        self.assertEqual(4, len(errors))
        self.assertTrue("interlock" in errors)
        self.assertTrue("unchecked" in errors)
        self.assertTrue("wordlength" in errors)
        self.assertTrue("dupwords" in errors)

    def test_ok_invalid(self):
        puzzle = self.create_test_puzzle()
        ok, errors = puzzle.validate()
        self.assertTrue(ok)
        self.assertEqual(4, len(errors))
        self.assertTrue("interlock" in errors)
        self.assertTrue("unchecked" in errors)
        self.assertTrue("wordlength" in errors)
        self.assertTrue("dupwords" in errors)

    @staticmethod
    def create_test_puzzle():
        jsonstr = """{
  "n": 9,
  "cells": [
    "+-----------------+",
    "|D|A|B|*|*|E|F|T|S|",
    "|S|L|I|M|*|R|I|O|T|",
    "|L|O|C|A|V|O|R|E|S|",
    "|R|E|U|N|I| |E|D|*|",
    "|*|*|R|A|P|I|D|*|*|",
    "|*|R|I|C|E|C|A|K|E|",
    "|C|O|O|L|R|A|N|C|H|",
    "|C|L|U|E|*| |C|A| |",
    "|R|O|S|S|*|*|E|R|E|",
    "+-----------------+"
  ],
  "black_cells": [
    [ 1, 4 ],
    [ 1, 5 ],
    [ 2, 5 ],
    [ 4, 9 ],
    [ 5, 1 ],
    [ 5, 2 ],
    [ 5, 8 ],
    [ 5, 9 ],
    [ 6, 1 ],
    [ 8, 5 ],
    [ 9, 5 ],
    [ 9, 6 ]
  ],
  "numbered_cells": [
    { "seq": 1, "r": 1, "c": 1, "a": 3, "d": 4 },
    { "seq": 2, "r": 1, "c": 2, "a": 0, "d": 4 },
    { "seq": 3, "r": 1, "c": 3, "a": 0, "d": 9 },
    { "seq": 4, "r": 1, "c": 6, "a": 4, "d": 8 },
    { "seq": 5, "r": 1, "c": 7, "a": 0, "d": 9 },
    { "seq": 6, "r": 1, "c": 8, "a": 0, "d": 4 },
    { "seq": 7, "r": 1, "c": 9, "a": 0, "d": 3 },
    { "seq": 8, "r": 2, "c": 1, "a": 4, "d": 0 },
    { "seq": 9, "r": 2, "c": 4, "a": 0, "d": 8 },
    { "seq": 10, "r": 2, "c": 6, "a": 4, "d": 0 },
    { "seq": 11, "r": 3, "c": 1, "a": 9, "d": 0 },
    { "seq": 12, "r": 3, "c": 5, "a": 0, "d": 5 },
    { "seq": 13, "r": 4, "c": 1, "a": 8, "d": 0 },
    { "seq": 14, "r": 5, "c": 3, "a": 5, "d": 0 },
    { "seq": 15, "r": 6, "c": 2, "a": 8, "d": 4 },
    { "seq": 16, "r": 6, "c": 8, "a": 0, "d": 4 },
    { "seq": 17, "r": 6, "c": 9, "a": 0, "d": 4 },
    { "seq": 18, "r": 7, "c": 1, "a": 9, "d": 3 },
    { "seq": 19, "r": 8, "c": 1, "a": 4, "d": 0 },
    { "seq": 20, "r": 8, "c": 6, "a": 4, "d": 0 },
    { "seq": 21, "r": 9, "c": 1, "a": 4, "d": 0 },
    { "seq": 22, "r": 9, "c": 7, "a": 3, "d": 0 }
  ],
  "across_words": [
    { "seq": 1, "text": "DAB", "clue": null },
    { "seq": 4, "text": "EFTS", "clue": null },
    { "seq": 8, "text": "SLIM", "clue": null },
    { "seq": 10, "text": "RIOT", "clue": null },
    { "seq": 11, "text": "LOCAVORES", "clue": null },
    { "seq": 13, "text": "REUNI ED", "clue": null },
    { "seq": 14, "text": "RAPID", "clue": null },
    { "seq": 15, "text": "RICECAKE", "clue": null },
    { "seq": 18, "text": "COOLRANCH", "clue": null },
    { "seq": 19, "text": "CLUE", "clue": null },
    { "seq": 20, "text": " CA ", "clue": null },
    { "seq": 21, "text": "ROSS", "clue": null },
    { "seq": 22, "text": "ERE", "clue": null }
  ],
  "down_words": [
    { "seq": 1, "text": "DSLR", "clue": null },
    { "seq": 2, "text": "ALOE", "clue": null },
    { "seq": 3, "text": "BICURIOUS", "clue": null },
    { "seq": 4, "text": "ERO ICA ", "clue": null },
    { "seq": 5, "text": "FIREDANCE", "clue": null },
    { "seq": 6, "text": "TOED", "clue": null },
    { "seq": 7, "text": "STS", "clue": null },
    { "seq": 9, "text": "MANACLES", "clue": null },
    { "seq": 12, "text": "VIPER", "clue": null },
    { "seq": 15, "text": "ROLO", "clue": null },
    { "seq": 16, "text": "KCAR", "clue": null },
    { "seq": 17, "text": "EH E", "clue": null },
    { "seq": 18, "text": "CCR", "clue": null }
  ],
  "undo_stack": [],
  "redo_stack": []
}
"""
        puzzle = Puzzle.from_json(jsonstr)
        return puzzle
