from unittest import TestCase

from crossword.puzzles import Puzzle
from tests import load_test_object


class TestPuzzleUndo(TestCase):

    def test_undo_with_empty_stack(self):
        puzzle = load_test_object("puzzle_undo")
        puzzle.undo_stack = []
        puzzle.undo()
        self.assertListEqual([], puzzle.undo_stack)

    def test_redo_with_empty_stack(self):
        puzzle = load_test_object("puzzle_undo")
        puzzle.redo_stack = []
        puzzle.redo()
        self.assertListEqual([], puzzle.redo_stack)

    def test_undo_text(self):
        puzzle = load_test_object("puzzle_undo")
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
        puzzle = load_test_object("puzzle_undo")
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
        puzzle = load_test_object("puzzle_undo")
        self.assertIsNone(puzzle.title)
        self.assertEqual('RIOT', puzzle.get_text(10, 'A'))
        self.assertEqual(None, puzzle.get_clue(10, 'A'))
        self.assertListEqual([], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)

        puzzle.set_text(10, 'A', 'ZOOM')
        self.assertIsNone(puzzle.title)
        self.assertEqual('ZOOM', puzzle.get_text(10, 'A'))
        self.assertEqual(None, puzzle.get_clue(10, 'A'))
        self.assertListEqual([
            ['text', 10, 'A', 'RIOT']
        ], puzzle.undo_stack)
        self.assertListEqual([], puzzle.redo_stack)
