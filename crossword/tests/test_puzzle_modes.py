from crossword import Grid, Puzzle, Word
from crossword.tests import TestPuzzle


class TestPuzzleModes:

    def test_new_puzzle_starts_in_grid_mode(self):
        puzzle = TestPuzzle.create_puzzle()
        assert "grid" == puzzle.last_mode
        assert [] == puzzle.grid_undo_stack
        assert [] == puzzle.grid_redo_stack

    def test_old_json_defaults_to_puzzle_mode(self):
        puzzle = TestPuzzle.create_puzzle()
        jsonstr = puzzle.to_json()
        import json
        image = json.loads(jsonstr)
        del image["last_mode"]
        old_json = json.dumps(image)

        loaded = Puzzle.from_json(old_json)
        assert "puzzle" == loaded.last_mode

    def test_mode_switch_resets_mode_local_history(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        puzzle.set_text(10, Word.ACROSS, "ZOOM")
        assert len(puzzle.undo_stack) == 1

        puzzle.enter_grid_mode()
        puzzle.grid_undo_stack = ["dummy"]
        puzzle.grid_redo_stack = ["dummy"]
        puzzle.enter_grid_mode()
        assert "grid" == puzzle.last_mode
        assert [] == puzzle.grid_undo_stack
        assert [] == puzzle.grid_redo_stack

        puzzle.enter_puzzle_mode()
        assert "puzzle" == puzzle.last_mode
        assert [] == puzzle.undo_stack
        assert [] == puzzle.redo_stack

    def test_toggle_black_cell_tracks_grid_history(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        assert not puzzle.is_black_cell(4, 4)

        puzzle.toggle_black_cell(4, 4)

        assert puzzle.is_black_cell(4, 4)
        assert puzzle.is_black_cell(6, 6)
        assert len(puzzle.grid_undo_stack) == 1
        assert [] == puzzle.grid_redo_stack

        puzzle.undo_grid_change()
        assert not puzzle.is_black_cell(4, 4)
        assert not puzzle.is_black_cell(6, 6)
        assert [] == puzzle.grid_undo_stack
        assert len(puzzle.grid_redo_stack) == 1

        puzzle.redo_grid_change()
        assert puzzle.is_black_cell(4, 4)
        assert puzzle.is_black_cell(6, 6)
        assert len(puzzle.grid_undo_stack) == 1
        assert [] == puzzle.grid_redo_stack

    def test_replace_grid_preserves_clue_only_for_exact_same_word_identity(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        old_clue = puzzle.get_clue(10, Word.ACROSS)
        assert old_clue is not None

        newgrid = Grid.from_json(puzzle.grid.to_json())
        newgrid.add_black_cell(4, 4)
        puzzle.replace_grid(newgrid)

        assert puzzle.get_clue(10, Word.ACROSS) == old_clue

        affected_across = puzzle.get_across_word(13)
        assert affected_across is not None
        assert affected_across.get_clue() is None

    def test_replace_grid_uses_spaces_for_removed_black_cells(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        merged_before = puzzle.get_text(13, Word.ACROSS)
        assert "REUNITED" == merged_before

        newgrid = Grid.from_json(puzzle.grid.to_json())
        newgrid.remove_black_cell(4, 9)
        puzzle.replace_grid(newgrid)

        assert "REUNITED " == puzzle.get_text(13, Word.ACROSS)
