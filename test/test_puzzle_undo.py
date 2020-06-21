from unittest import TestCase

from crossword import Puzzle


class TestPuzzleUndo(TestCase):

    def test_remove_history(self):
        puzzle = self.create_test_puzzle()
        puzzle.set_text(10, 'A', 'ZOOM')
        puzzle.set_text(10, 'A', 'PLOT')
        puzzle.undo()
        puzzle.set_text(10, 'A', 'STEP')
        #print(f"undo={puzzle.undo_stack}, redo={puzzle.redo_stack}")
        self.assertListEqual([['text', 10, 'A', 'RIOT'], ['text', 10, 'A', 'ZOOM']], puzzle.undo_stack)
        self.assertListEqual([['text', 10, 'A', 'PLOT']], puzzle.redo_stack)
        puzzle.remove_history()
        self.assertListEqual([], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)


    def test_undo_text(self):
        puzzle = self.create_test_puzzle()
        self.assertEqual('RIOT', puzzle.get_text(10, 'A'))
        self.assertEqual('ERO ICA ', puzzle.get_text(4, 'D'))
        self.assertListEqual([], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)

        puzzle.set_text(10, 'A', 'ZOOM')
        self.assertEqual('ZOOM', puzzle.get_text(10, 'A'))
        self.assertEqual('EZO ICA ', puzzle.get_text(4, 'D'))
        self.assertListEqual([
            ['text', 10, 'A', 'RIOT']
        ], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)

        puzzle.set_text(10, 'A', 'PLUS')
        self.assertEqual('PLUS', puzzle.get_text(10, 'A'))
        self.assertEqual('EPO ICA ', puzzle.get_text(4, 'D'))
        self.assertListEqual([
            ['text', 10, 'A', 'RIOT'],
            ['text', 10, 'A', 'ZOOM']
        ], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)

        puzzle.undo()
        self.assertEqual('ZOOM', puzzle.get_text(10, 'A'))
        self.assertEqual('EZO ICA ', puzzle.get_text(4, 'D'))
        self.assertListEqual([
            ['text', 10, 'A', 'RIOT']
        ], puzzle.undo_stack)

    def test_redo_text(self):
        puzzle = self.create_test_puzzle()
        self.assertEqual('RIOT', puzzle.get_text(10, 'A'))
        self.assertEqual('ERO ICA ', puzzle.get_text(4, 'D'))
        self.assertListEqual([], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)

        puzzle.set_text(10, 'A', 'ZOOM')
        self.assertEqual('ZOOM', puzzle.get_text(10, 'A'))
        self.assertEqual('EZO ICA ', puzzle.get_text(4, 'D'))
        self.assertListEqual([
            ['text', 10, 'A', 'RIOT']
        ], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)

        puzzle.undo()
        self.assertEqual('RIOT', puzzle.get_text(10, 'A'))
        self.assertEqual('ERO ICA ', puzzle.get_text(4, 'D'))
        self.assertListEqual([], puzzle.undo_stack)
        self.assertListEqual([
            ['text', 10, 'A', 'ZOOM']
        ], puzzle.redo_stack)

        puzzle.redo()
        self.assertEqual('ZOOM', puzzle.get_text(10, 'A'))
        self.assertEqual('EZO ICA ', puzzle.get_text(4, 'D'))
        self.assertListEqual([
            ['text', 10, 'A', 'RIOT']
        ], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)

    def test_to_json(self):
        puzzle = self.create_test_puzzle()
        self.assertEqual(None, puzzle.get_title())
        self.assertEqual('RIOT', puzzle.get_text(10, 'A'))
        self.assertEqual(None, puzzle.get_clue(10, 'A'))
        self.assertListEqual([], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)

        puzzle.set_text(10, 'A', 'ZOOM')
        self.assertEqual(None, puzzle.get_title())
        self.assertEqual('ZOOM', puzzle.get_text(10, 'A'))
        self.assertEqual(None, puzzle.get_clue(10, 'A'))
        self.assertListEqual([
            ['text', 10, 'A', 'RIOT']
        ], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)

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
    { "seq": 1, "r": 1, "c": 1, "across_length": 3, "down_length": 4 },
    { "seq": 2, "r": 1, "c": 2, "across_length": 0, "down_length": 4 },
    { "seq": 3, "r": 1, "c": 3, "across_length": 0, "down_length": 9 },
    { "seq": 4, "r": 1, "c": 6, "across_length": 4, "down_length": 8 },
    { "seq": 5, "r": 1, "c": 7, "across_length": 0, "down_length": 9 },
    { "seq": 6, "r": 1, "c": 8, "across_length": 0, "down_length": 4 },
    { "seq": 7, "r": 1, "c": 9, "across_length": 0, "down_length": 3 },
    { "seq": 8, "r": 2, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 9, "r": 2, "c": 4, "across_length": 0, "down_length": 8 },
    { "seq": 10, "r": 2, "c": 6, "across_length": 4, "down_length": 0 },
    { "seq": 11, "r": 3, "c": 1, "across_length": 9, "down_length": 0 },
    { "seq": 12, "r": 3, "c": 5, "across_length": 0, "down_length": 5 },
    { "seq": 13, "r": 4, "c": 1, "across_length": 8, "down_length": 0 },
    { "seq": 14, "r": 5, "c": 3, "across_length": 5, "down_length": 0 },
    { "seq": 15, "r": 6, "c": 2, "across_length": 8, "down_length": 4 },
    { "seq": 16, "r": 6, "c": 8, "across_length": 0, "down_length": 4 },
    { "seq": 17, "r": 6, "c": 9, "across_length": 0, "down_length": 4 },
    { "seq": 18, "r": 7, "c": 1, "across_length": 9, "down_length": 3 },
    { "seq": 19, "r": 8, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 20, "r": 8, "c": 6, "across_length": 4, "down_length": 0 },
    { "seq": 21, "r": 9, "c": 1, "across_length": 4, "down_length": 0 },
    { "seq": 22, "r": 9, "c": 7, "across_length": 3, "down_length": 0 }
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
