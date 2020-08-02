from unittest import TestCase

from crossword import Grid


class TestGridUndoRedo(TestCase):

    def test_undo_with_empty_stack(self):
        grid = Grid(5)
        grid.undo()
        self.assertListEqual([], grid.undo_stack)
        self.assertListEqual([], grid.redo_stack)
        pass

    def test_redo_with_empty_stack(self):
        grid = Grid(5)
        grid.redo()
        self.assertListEqual([], grid.undo_stack)
        self.assertListEqual([], grid.redo_stack)
        pass

    def test_add__remove_black_cell(self):
        grid = Grid(5)
        grid.add_black_cell(1, 2)
        self.assertEqual(True, grid.is_black_cell(1, 2))
        self.assertEqual(True, grid.is_black_cell(5, 4))
        self.assertEqual([(1, 2)], grid.undo_stack)
        self.assertEqual([], grid.redo_stack)
        grid.remove_black_cell(1, 2)
        self.assertEqual(False, grid.is_black_cell(1, 2))
        self.assertEqual(False, grid.is_black_cell(5, 4))
        self.assertEqual([(1, 2), (1, 2)], grid.undo_stack)
        self.assertEqual([], grid.redo_stack)

    def test_add_undo(self):
        grid = Grid(5)
        grid.add_black_cell(1, 2)
        self.assertEqual(True, grid.is_black_cell(1, 2))
        self.assertEqual(True, grid.is_black_cell(5, 4))
        self.assertEqual([(1, 2)], grid.undo_stack)
        self.assertEqual([], grid.redo_stack)
        grid.undo()
        self.assertEqual(False, grid.is_black_cell(1, 2))
        self.assertEqual(False, grid.is_black_cell(5, 4))
        self.assertEqual([], grid.undo_stack)
        self.assertEqual([(1, 2)], grid.redo_stack)

    def test_add__add_undo_redo(self):
        grid = Grid(5)
        grid.add_black_cell(1, 2)
        grid.add_black_cell(3, 4)
        self.assertEqual(True, grid.is_black_cell(1, 2))
        self.assertEqual(True, grid.is_black_cell(5, 4))
        self.assertEqual(True, grid.is_black_cell(3, 4))
        self.assertEqual(True, grid.is_black_cell(3, 2))
        self.assertEqual([(1, 2), (3, 4)], grid.undo_stack)
        self.assertEqual([], grid.redo_stack)

        grid.undo()
        self.assertEqual(True, grid.is_black_cell(1, 2))
        self.assertEqual(True, grid.is_black_cell(5, 4))
        self.assertEqual(False, grid.is_black_cell(3, 4))
        self.assertEqual(False, grid.is_black_cell(3, 2))
        self.assertEqual([(1, 2)], grid.undo_stack)
        self.assertEqual([(3, 4)], grid.redo_stack)

        grid.redo()
        self.assertEqual(True, grid.is_black_cell(1, 2))
        self.assertEqual(True, grid.is_black_cell(5, 4))
        self.assertEqual(True, grid.is_black_cell(3, 4))
        self.assertEqual(True, grid.is_black_cell(3, 2))
        self.assertEqual([(1, 2), (3, 4)], grid.undo_stack)
        self.assertEqual([], grid.redo_stack)

        grid.undo()
        self.assertEqual(True, grid.is_black_cell(1, 2))
        self.assertEqual(True, grid.is_black_cell(5, 4))
        self.assertEqual(False, grid.is_black_cell(3, 4))
        self.assertEqual(False, grid.is_black_cell(3, 2))
        self.assertEqual([(1, 2)], grid.undo_stack)
        self.assertEqual([(3, 4)], grid.redo_stack)

        grid.undo()
        self.assertEqual(False, grid.is_black_cell(1, 2))
        self.assertEqual(False, grid.is_black_cell(5, 4))
        self.assertEqual(False, grid.is_black_cell(3, 4))
        self.assertEqual(False, grid.is_black_cell(3, 2))
        self.assertEqual([], grid.undo_stack)
        self.assertEqual([(3, 4), (1, 2)], grid.redo_stack)
