"""
Tests for circled squares: the domain, SVG, PDF exports, use case and route
"""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from crossword import Grid, Puzzle
from crossword.adapters.nytimes_export_adapter import NYTimesExportAdapter
from crossword.adapters.solved_pdf_export_adapter import SolvedPdfExportAdapter
from crossword.adapters.solver_pdf_export_adapter import SolverPdfExportAdapter
from crossword.domain.to_svg import GridToSVG, PuzzleToSVG
from crossword.http_server.main import create_app
from crossword.http_server.puzzle_routes import _puzzle_response
from crossword.use_cases.puzzle_use_cases import PuzzleUseCases


@pytest.fixture
def puzzle():
    """A 5x5 puzzle in Puzzle mode with black squares at (1, 1) and (5, 5)"""
    grid = Grid(5)
    grid.add_black_cell(1, 1, undo=False)
    puzzle = Puzzle(grid)
    puzzle.last_mode = "puzzle"
    return puzzle


class TestPuzzleCircles:

    def test_new_puzzle_has_no_circles(self, puzzle):
        assert puzzle.circled_cells == set()
        assert not puzzle.is_circled(2, 2)

    def test_toggle_on_and_off(self, puzzle):
        puzzle.toggle_circle(2, 2)
        assert puzzle.is_circled(2, 2)
        puzzle.toggle_circle(2, 2)
        assert not puzzle.is_circled(2, 2)

    def test_black_square_cannot_be_circled(self, puzzle):
        with pytest.raises(ValueError):
            puzzle.toggle_circle(1, 1)
        assert puzzle.circled_cells == set()

    @pytest.mark.parametrize("r, c", [(0, 1), (6, 1), (1, 0), (1, 6)])
    def test_square_outside_grid_cannot_be_circled(self, puzzle, r, c):
        with pytest.raises(ValueError):
            puzzle.toggle_circle(r, c)

    def test_toggle_pushes_undo_entry(self, puzzle):
        puzzle.toggle_circle(2, 3)
        assert puzzle.undo_stack == [['circle', 2, 3]]

    def test_toggle_without_undo(self, puzzle):
        puzzle.toggle_circle(2, 3, undo=False)
        assert puzzle.undo_stack == []

    def test_undo_and_redo(self, puzzle):
        puzzle.toggle_circle(2, 3)

        puzzle.undo()
        assert not puzzle.is_circled(2, 3)
        assert puzzle.undo_stack == []
        assert puzzle.redo_stack == [['circle', 2, 3]]

        puzzle.redo()
        assert puzzle.is_circled(2, 3)
        assert puzzle.undo_stack == [['circle', 2, 3]]
        assert puzzle.redo_stack == []

    def test_circle_in_locked_word_is_allowed(self, puzzle):
        puzzle.set_locked(5, "A", True)
        puzzle.toggle_circle(2, 2)
        assert puzzle.is_circled(2, 2)

    def test_clear_leaves_circles(self, puzzle):
        puzzle.toggle_circle(2, 2)
        puzzle.set_text(6, "A", "ABCDE")
        puzzle.clear_unlocked()
        assert puzzle.is_circled(2, 2)


class TestCirclesJson:

    def test_round_trip(self, puzzle):
        puzzle.toggle_circle(3, 4)
        puzzle.toggle_circle(2, 2)
        image = puzzle.to_json()
        assert '"circled_cells": [[2, 2], [3, 4]]' in image
        assert Puzzle.from_json(image).circled_cells == {(2, 2), (3, 4)}

    def test_json_without_key_loads_with_no_circles(self, puzzle):
        import json
        image = json.loads(puzzle.to_json())
        del image['circled_cells']
        assert Puzzle.from_json(json.dumps(image)).circled_cells == set()

    def test_puzzles_differing_only_in_circles_are_not_equal(self, puzzle):
        other = Puzzle.from_json(puzzle.to_json())
        assert other == puzzle
        other.toggle_circle(2, 2, undo=False)
        assert other != puzzle


class TestCirclesAndGridChanges:

    def test_square_turned_black_loses_its_circle(self, puzzle):
        puzzle.toggle_circle(2, 2)
        puzzle.toggle_circle(3, 3)
        puzzle.toggle_black_cell(2, 2)
        assert not puzzle.is_circled(2, 2)
        assert not puzzle.is_circled(4, 4)
        assert puzzle.is_circled(3, 3)

    def test_rotate_leaves_white_circles_in_place(self, puzzle):
        puzzle.toggle_circle(3, 3)
        puzzle.rotate_grid()
        assert puzzle.circled_cells == {(3, 3)}


class TestCirclesSvg:

    def test_puzzle_svg_draws_one_circle_per_circled_square(self, puzzle):
        puzzle.toggle_circle(2, 2)
        puzzle.toggle_circle(3, 4)
        assert PuzzleToSVG(puzzle).generate_xml().count("<circle") == 2

    def test_puzzle_svg_without_circles(self, puzzle):
        assert "<circle" not in PuzzleToSVG(puzzle).generate_xml()

    def test_grid_svg_with_circled_cells(self, puzzle):
        svg = GridToSVG(puzzle.grid, circled_cells={(2, 2)}).generate_xml()
        assert svg.count("<circle") == 1

    def test_grid_svg_without_circled_cells(self, puzzle):
        assert "<circle" not in GridToSVG(puzzle.grid).generate_xml()

    def test_circle_comes_before_its_letter(self, puzzle):
        puzzle.set_text(6, "A", "ABCDE")
        puzzle.toggle_circle(2, 1)
        svg = PuzzleToSVG(puzzle).generate_xml()
        assert svg.index("<circle") < svg.index(">A</text>")


class TestCirclesPdf:

    @pytest.mark.parametrize("adapter", [
        SolverPdfExportAdapter(),
        SolvedPdfExportAdapter(),
        NYTimesExportAdapter(),
    ], ids=["solver", "solved", "nytimes"])
    def test_html_contains_circle(self, adapter, puzzle):
        puzzle.toggle_circle(2, 2)
        html = adapter._build_html(puzzle)
        assert "<circle" in html


class TestToggleCircleUseCase:

    @pytest.fixture
    def persistence(self, puzzle):
        persistence = Mock()
        persistence.load_puzzle.return_value = puzzle
        return persistence

    def test_toggles_and_saves_in_puzzle_mode(self, persistence, puzzle):
        uc = PuzzleUseCases(persistence)
        result = uc.toggle_circle(1, "demo", 2, 2)
        assert result.is_circled(2, 2)
        persistence.save_puzzle.assert_called_once_with(1, "demo", puzzle)

    def test_refused_in_grid_mode(self, persistence, puzzle):
        puzzle.last_mode = "grid"
        uc = PuzzleUseCases(persistence)
        with pytest.raises(ValueError, match="Puzzle mode"):
            uc.toggle_circle(1, "demo", 2, 2)
        assert not puzzle.is_circled(2, 2)
        persistence.save_puzzle.assert_not_called()

    def test_black_square_is_refused(self, persistence):
        uc = PuzzleUseCases(persistence)
        with pytest.raises(ValueError):
            uc.toggle_circle(1, "demo", 1, 1)
        persistence.save_puzzle.assert_not_called()


class TestToggleCircleRoute:

    @pytest.fixture
    def container(self):
        container = Mock()
        container.config = {"message_line_timeout_ms": 1000, "theme_color": ""}
        return container

    @pytest.fixture
    def client(self, container):
        return TestClient(create_app(container=container), raise_server_exceptions=False)

    def test_puzzle_response_marks_circled_squares(self, puzzle):
        puzzle.toggle_circle(2, 3)
        cells = _puzzle_response(puzzle)["puzzle"]["cells"]
        assert cells[(2 - 1) * 5 + (3 - 1)]["circled"] is True
        assert "circled" not in cells[(2 - 1) * 5 + (2 - 1)]

    def test_route_converts_to_one_based(self, client, container, puzzle):
        puzzle.toggle_circle(2, 3)
        container.puzzle_uc.toggle_circle.return_value = puzzle

        response = client.put("/api/puzzles/demo/cells/1/2/circle")

        container.puzzle_uc.toggle_circle.assert_called_once_with(1, "demo", 2, 3)
        assert response.status_code == 200
        assert response.json()["puzzle"]["cells"]["7"]["circled"] is True

    def test_value_error_is_an_error_envelope(self, client, container):
        container.puzzle_uc.toggle_circle.side_effect = ValueError(
            "Circles can only be changed in Puzzle mode")

        response = client.put("/api/puzzles/demo/cells/0/0/circle")

        assert 400 <= response.status_code < 500
        assert response.json() == {"error": "Circles can only be changed in Puzzle mode"}
