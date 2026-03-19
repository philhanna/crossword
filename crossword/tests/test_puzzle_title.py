from crossword import Grid, Puzzle


class TestPuzzleTitle:

    def test_title_not_set(self):
        grid = Grid(11)
        puzzle = Puzzle(grid)
        assert puzzle.title is None

    def test_title_is_set(self):
        grid = Grid(11)
        puzzle = Puzzle(grid, "My Title")
        assert "My Title" == puzzle.title

    def test_title_set_later(self):
        grid = Grid(11)
        puzzle = Puzzle(grid)
        puzzle.title = "Later"
        assert "Later" == puzzle.title

    def test_title_changed(self):
        grid = Grid(11)
        puzzle = Puzzle(grid, "First Title")
        assert "First Title" == puzzle.title
        puzzle.title = "Second Title"
        assert "Second Title" == puzzle.title

    def test_title_set_back_to_none(self):
        grid = Grid(11)
        puzzle = Puzzle(grid, "First Title")
        assert "First Title" == puzzle.title
        puzzle.title = None
        assert puzzle.title is None
