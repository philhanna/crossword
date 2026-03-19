from crossword import Grid


class TestGridUndoRedo:

    def test_undo_with_empty_stack(self):
        grid = Grid(5)
        grid.undo()
        assert [] == grid.undo_stack
        assert [] == grid.redo_stack
        pass

    def test_redo_with_empty_stack(self):
        grid = Grid(5)
        grid.redo()
        assert [] == grid.undo_stack
        assert [] == grid.redo_stack
        pass

    def test_add__remove_black_cell(self):
        grid = Grid(5)
        grid.add_black_cell(1, 2)
        assert True == grid.is_black_cell(1, 2)
        assert True == grid.is_black_cell(5, 4)
        assert [(1, 2)] == grid.undo_stack
        assert [] == grid.redo_stack
        grid.remove_black_cell(1, 2)
        assert False == grid.is_black_cell(1, 2)
        assert False == grid.is_black_cell(5, 4)
        assert [(1, 2), (1, 2)] == grid.undo_stack
        assert [] == grid.redo_stack

    def test_add_undo(self):
        grid = Grid(5)
        grid.add_black_cell(1, 2)
        assert True == grid.is_black_cell(1, 2)
        assert True == grid.is_black_cell(5, 4)
        assert [(1, 2)] == grid.undo_stack
        assert [] == grid.redo_stack
        grid.undo()
        assert False == grid.is_black_cell(1, 2)
        assert False == grid.is_black_cell(5, 4)
        assert [] == grid.undo_stack
        assert [(1, 2)] == grid.redo_stack

    def test_add__add_undo_redo(self):
        grid = Grid(5)
        grid.add_black_cell(1, 2)
        grid.add_black_cell(3, 4)
        assert True == grid.is_black_cell(1, 2)
        assert True == grid.is_black_cell(5, 4)
        assert True == grid.is_black_cell(3, 4)
        assert True == grid.is_black_cell(3, 2)
        assert [(1, 2), (3, 4)] == grid.undo_stack
        assert [] == grid.redo_stack

        grid.undo()
        assert True == grid.is_black_cell(1, 2)
        assert True == grid.is_black_cell(5, 4)
        assert False == grid.is_black_cell(3, 4)
        assert False == grid.is_black_cell(3, 2)
        assert [(1, 2)] == grid.undo_stack
        assert [(3, 4)] == grid.redo_stack

        grid.redo()
        assert True == grid.is_black_cell(1, 2)
        assert True == grid.is_black_cell(5, 4)
        assert True == grid.is_black_cell(3, 4)
        assert True == grid.is_black_cell(3, 2)
        assert [(1, 2), (3, 4)] == grid.undo_stack
        assert [] == grid.redo_stack

        grid.undo()
        assert True == grid.is_black_cell(1, 2)
        assert True == grid.is_black_cell(5, 4)
        assert False == grid.is_black_cell(3, 4)
        assert False == grid.is_black_cell(3, 2)
        assert [(1, 2)] == grid.undo_stack
        assert [(3, 4)] == grid.redo_stack

        grid.undo()
        assert False == grid.is_black_cell(1, 2)
        assert False == grid.is_black_cell(5, 4)
        assert False == grid.is_black_cell(3, 4)
        assert False == grid.is_black_cell(3, 2)
        assert [] == grid.undo_stack
        assert [(3, 4), (1, 2)] == grid.redo_stack
