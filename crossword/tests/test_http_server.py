"""
Tests for the FastAPI web layer.

Every test drives the app through a TestClient, so what is checked is the
contract the frontend sees: paths, status codes, and response bodies.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from crossword.http_server.main import create_app, iter_routes, run_http_server
from crossword.http_server.puzzle_routes import _puzzle_response
from crossword.ports.definition_port import DefinitionNotFound
from crossword.ports.persistence_port import PersistenceError
from crossword.tests import TestPuzzle


@pytest.fixture
def container():
    """A stand-in for the wired application container."""
    container = Mock()
    container.config = {"message_line_timeout_ms": 1000, "theme_color": ""}
    return container


@pytest.fixture
def client(container):
    """A test client whose 500 responses come back instead of being raised."""
    app = create_app(container=container)
    return TestClient(app, raise_server_exceptions=False)


class TestRouteTable:
    """The registered paths the frontend depends on."""

    def test_every_expected_route_is_registered(self, client):
        registered = {
            (method, route.path)
            for route in iter_routes(client.app)
            for method in route.methods
        }

        for method, path in [
            ("GET", "/"),
            ("GET", "/static/css/theme.css"),
            ("GET", "/api/config"),
            ("GET", "/api/settings"),
            ("PUT", "/api/settings"),
            ("GET", "/api/dashboard"),
            ("GET", "/api/puzzles"),
            ("POST", "/api/puzzles"),
            ("GET", "/api/puzzles/{name}"),
            ("DELETE", "/api/puzzles/{name}"),
            ("POST", "/api/puzzles/{name}/mode/grid"),
            ("POST", "/api/puzzles/{name}/mode/puzzle"),
            ("PUT", "/api/puzzles/{name}/grid/cells/{r}/{c}"),
            ("POST", "/api/puzzles/{name}/grid/rotate"),
            ("POST", "/api/puzzles/{name}/grid/undo"),
            ("POST", "/api/puzzles/{name}/grid/redo"),
            ("GET", "/api/puzzles/{name}/state"),
            ("PUT", "/api/puzzles/{name}/state"),
            ("GET", "/api/export/puzzles/{name}/solved-pdf"),
            ("POST", "/api/import/puz"),
        ]:
            assert (method, path) in registered

    def test_static_assets_are_mounted(self, client):
        assert any(getattr(route, "name", None) == "static"
                   for route in client.app.routes)

    def test_unknown_path_returns_the_error_envelope(self, client):
        response = client.get("/api/nothing-here")

        assert response.status_code == 404
        assert "error" in response.json()


class TestErrorEnvelope:
    """Every failure reaches the frontend as {"error": ...}."""

    def test_use_case_value_error_becomes_400(self, client, container):
        container.puzzle_uc.list_puzzles.side_effect = ValueError("Invalid state: 'bogus'")

        response = client.get("/api/puzzles", params={"state": "bogus"})

        assert response.status_code == 400
        assert response.json() == {"error": "Invalid state: 'bogus'"}

    def test_missing_puzzle_becomes_404(self, client, container):
        container.puzzle_uc.load_puzzle.side_effect = PersistenceError("gone")

        response = client.get("/api/puzzles/nope")

        assert response.status_code == 404
        assert response.json() == {"error": "Puzzle not found: nope"}

    def test_unexpected_error_becomes_500(self, client, container):
        container.puzzle_uc.get_dashboard.side_effect = RuntimeError("disk on fire")

        response = client.get("/api/dashboard")

        assert response.status_code == 500
        assert response.json() == {"error": "disk on fire"}

    def test_missing_body_field_becomes_400(self, client, container):
        response = client.put("/api/puzzles/demo/state", json={})

        assert response.status_code == 400
        assert response.json() == {"error": "Missing 'state'"}
        container.puzzle_uc.set_puzzle_state.assert_not_called()

    def test_non_numeric_path_parameter_becomes_400(self, client, container):
        response = client.post("/api/puzzles/demo/state/history/not-a-number/restore")

        assert response.status_code == 400
        container.puzzle_uc.restore_puzzle_from_history.assert_not_called()


class TestPuzzleRoutes:
    """Puzzle CRUD and editing."""

    def test_puzzle_response_includes_mode_metadata(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        puzzle.enter_grid_mode()
        puzzle.grid_undo_stack = ["old"]

        response = _puzzle_response(puzzle)

        assert response["mode"] == "grid"
        assert response["grid_can_undo"] is True
        assert response["grid_can_redo"] is False
        assert response["puzzle_can_undo"] is False
        assert response["puzzle_can_redo"] is False
        assert response["can_undo"] is True

    def test_create_puzzle_accepts_size(self, client, container):
        puzzle = TestPuzzle.create_puzzle()
        container.puzzle_uc.load_puzzle.return_value = puzzle

        response = client.post("/api/puzzles", json={"name": "demo", "size": 15})

        container.puzzle_uc.create_puzzle.assert_called_once_with(1, "demo", size=15)
        assert response.status_code == 200
        assert response.json()["grid"]["size"] == puzzle.n

    def test_create_puzzle_write_failure_is_a_500(self, client, container):
        container.puzzle_uc.create_puzzle.side_effect = PersistenceError("read-only database")

        response = client.post("/api/puzzles", json={"name": "demo", "size": 15})

        assert response.status_code == 500
        assert response.json() == {"error": "read-only database"}

    def test_list_puzzles_hides_internal_new_entries(self, client, container):
        container.puzzle_uc.list_puzzles.return_value = ["alpha", "__new__abcd1234", "beta"]

        response = client.get("/api/puzzles")

        container.puzzle_uc.list_puzzles.assert_called_once_with(1, state=None)
        assert response.json() == {"puzzles": ["alpha", "beta"]}

    def test_list_puzzles_passes_state_query_param(self, client, container):
        container.puzzle_uc.list_puzzles.return_value = ["alpha"]

        response = client.get("/api/puzzles", params={"state": "draft"})

        container.puzzle_uc.list_puzzles.assert_called_once_with(1, state="draft")
        assert response.json() == {"puzzles": ["alpha"]}

    def test_dashboard_returns_puzzles(self, client, container):
        container.puzzle_uc.get_dashboard.return_value = {
            "puzzles": [{"name": "alpha", "state": "draft"}]
        }

        response = client.get("/api/dashboard")

        container.puzzle_uc.get_dashboard.assert_called_once_with(1)
        assert response.json() == {"puzzles": [{"name": "alpha", "state": "draft"}]}

    def test_delete_puzzle(self, client, container):
        response = client.delete("/api/puzzles/demo")

        container.puzzle_uc.delete_puzzle.assert_called_once_with(1, "demo")
        assert response.json() == {"status": "deleted", "name": "demo"}

    def test_open_puzzle_for_editing(self, client, container):
        container.puzzle_uc.open_puzzle_for_editing.return_value = "__wc__demo__a1b2c3d4"

        response = client.post("/api/puzzles/demo/open")

        assert response.json() == {
            "original_name": "demo", "working_name": "__wc__demo__a1b2c3d4"}

    def test_switch_to_grid_mode(self, client, container):
        puzzle = TestPuzzle.create_puzzle()
        puzzle.enter_grid_mode()
        container.puzzle_uc.switch_to_grid_mode.return_value = puzzle

        response = client.post("/api/puzzles/demo/mode/grid")

        container.puzzle_uc.switch_to_grid_mode.assert_called_once_with(1, "demo")
        assert response.json()["mode"] == "grid"

    def test_switch_to_puzzle_mode(self, client, container):
        puzzle = TestPuzzle.create_puzzle()
        puzzle.enter_puzzle_mode()
        container.puzzle_uc.switch_to_puzzle_mode.return_value = puzzle

        response = client.post("/api/puzzles/demo/mode/puzzle")

        container.puzzle_uc.switch_to_puzzle_mode.assert_called_once_with(1, "demo")
        assert response.json()["mode"] == "puzzle"

    def test_toggle_black_cell_converts_to_one_based_coordinates(self, client, container):
        puzzle = TestPuzzle.create_puzzle()
        puzzle.toggle_black_cell(1, 1)
        container.puzzle_uc.toggle_black_cell.return_value = puzzle

        response = client.put("/api/puzzles/demo/grid/cells/0/0")

        container.puzzle_uc.toggle_black_cell.assert_called_once_with(1, "demo", 1, 1)
        assert response.json()["grid"]["cells"][0] is True

    def test_set_cell_letter_converts_to_one_based_coordinates(self, client, container):
        response = client.put("/api/puzzles/demo/cells/2/3", json={"letter": "a"})

        container.puzzle_uc.set_cell_letter.assert_called_once_with(1, "demo", 3, 4, "a")
        assert response.json() == {"name": "demo", "r": 3, "c": 4, "letter": "A"}

    def test_generate_grid_reports_a_notice_instead_of_failing(self, client, container):
        container.puzzle_uc.generate_grid.side_effect = RuntimeError("no grid of that shape")

        response = client.post("/api/puzzles/demo/grid/generate")

        assert response.status_code == 200
        assert response.json() == {"notice": "no grid of that shape"}

    def test_generate_grid_passes_the_parsed_spec(self, client, container):
        container.puzzle_uc.generate_grid.return_value = TestPuzzle.create_puzzle()

        client.post("/api/puzzles/demo/grid/generate", params={"spec": "3,4,5"})

        container.puzzle_uc.generate_grid.assert_called_once_with(1, "demo", [3, 4, 5])

    def test_set_puzzle_title(self, client, container):
        response = client.put("/api/puzzles/demo/title", json={"title": "My Puzzle"})

        container.puzzle_uc.set_puzzle_title.assert_called_once_with(1, "demo", "My Puzzle")
        assert response.json() == {"name": "demo", "title": "My Puzzle"}

    def test_get_word_at(self, client, container):
        word = Mock()
        word.cell_iterator.return_value = iter([(1, 1), (1, 2)])
        word.get_text.return_value = "AT"
        word.get_clue.return_value = None
        container.puzzle_uc.get_word_at.return_value = word

        response = client.get("/api/puzzles/demo/words/5/across")

        container.puzzle_uc.get_word_at.assert_called_once_with(1, "demo", 5, "across")
        assert response.json() == {
            "seq": 5, "direction": "across",
            "cells": [[1, 1], [1, 2]], "answer": "AT", "clue": "",
        }


class TestWordRoutes:
    """Suggestions, constraints and definitions."""

    def test_set_word_clue_surfaces_duplicate_error(self, client, container):
        container.puzzle_uc.set_word_clue.side_effect = ValueError(
            "GARDEN duplicates GARDENS, already used at 12 across")

        response = client.put("/api/puzzles/demo/words/5/across",
                              json={"text": "GARDEN", "clue": ""})

        assert response.status_code == 400
        assert response.json() == {
            "error": "GARDEN duplicates GARDENS, already used at 12 across"}

    def test_suggestions_filter_using_puzzle_context(self, client, container):
        word = Mock()
        word.length = 3
        container.puzzle_uc.get_word_at.return_value = word
        container.word_uc.get_other_complete_words.return_value = ["CAT"]
        container.word_uc.get_suggestions.return_value = ["cot"]

        response = client.get("/api/words/suggestions", params={
            "pattern": "???", "puzzle": "demo", "seq": 5, "direction": "across"})

        container.puzzle_uc.get_word_at.assert_called_once_with(1, "demo", 5, "across")
        container.word_uc.get_other_complete_words.assert_called_once_with(word)
        container.word_uc.get_suggestions.assert_called_once_with("???", ["CAT"], length=3)
        assert response.json() == {"pattern": "???", "suggestions": ["cot"], "count": 1}

    def test_suggestions_without_puzzle_context_are_unfiltered(self, client, container):
        container.word_uc.get_suggestions.return_value = ["cat", "cats"]

        response = client.get("/api/words/suggestions", params={"pattern": "???"})

        container.puzzle_uc.get_word_at.assert_not_called()
        container.word_uc.get_suggestions.assert_called_once_with("???", None, length=None)
        assert response.json() == {
            "pattern": "???", "suggestions": ["cat", "cats"], "count": 2}

    def test_suggestions_accept_a_standalone_length(self, client, container):
        container.word_uc.get_suggestions.return_value = ["cat", "cot"]

        response = client.get("/api/words/suggestions",
                              params={"pattern": "C.*T", "length": 3})

        container.puzzle_uc.get_word_at.assert_not_called()
        container.word_uc.get_suggestions.assert_called_once_with("C.*T", None, length=3)
        assert response.json()["count"] == 2

    def test_suggestions_reject_a_pattern_that_is_too_long(self, client, container):
        container.word_uc.get_suggestions.side_effect = ValueError(
            "pattern too long (max 200 characters)")

        response = client.get("/api/words/suggestions", params={"pattern": "A" * 201})

        assert response.status_code == 400
        assert response.json() == {
            "error": "Invalid pattern: pattern too long (max 200 characters)"}

    def test_suggestions_require_a_pattern(self, client):
        response = client.get("/api/words/suggestions")

        assert response.status_code == 400
        assert response.json() == {"error": "Missing 'pattern'"}

    def test_word_constraints(self, client, container):
        word = Mock()
        container.puzzle_uc.get_word_at.return_value = word
        container.word_uc.get_word_constraints.return_value = {"cells": []}

        response = client.get("/api/puzzles/demo/words/5/across/constraints")

        container.word_uc.get_word_constraints.assert_called_once_with(word)
        assert response.json() == {"cells": []}

    def test_ranked_suggestions(self, client, container):
        word = Mock()
        container.puzzle_uc.get_word_at.return_value = word
        container.word_uc.get_ranked_suggestions.return_value = ["CAT"]

        response = client.get("/api/puzzles/demo/words/5/across/suggestions",
                              params={"pattern": "C??"})

        container.word_uc.get_ranked_suggestions.assert_called_once_with(word, "C??")
        assert response.json() == {"suggestions": ["CAT"], "count": 1}

    def test_definitions_not_found(self, client, container):
        container.definition_uc.lookup.side_effect = DefinitionNotFound("nope")

        response = client.get("/api/words/zzzz/definitions")

        assert response.status_code == 404
        assert response.json() == {"error": "No definitions found for 'zzzz'"}


class TestExportRoutes:
    """Downloads carry the right filename and content type."""

    @pytest.fixture
    def client(self, container):
        container.export_uc.export_puzzle_to_solver_pdf.return_value = b"solver"
        container.export_uc.export_puzzle_to_solved_pdf.return_value = b"solved"
        container.export_uc.export_puzzle_to_acrosslite.return_value = "grid text"
        return TestClient(create_app(container=container), raise_server_exceptions=False)

    def test_solver_pdf_uses_plain_pdf_suffix(self, client):
        response = client.get("/api/export/puzzles/demo/solver-pdf")

        assert response.headers["content-disposition"] == 'attachment; filename="demo.pdf"'
        assert response.headers["content-type"] == "application/pdf"
        assert response.content == b"solver"

    def test_solved_pdf_uses_solution_suffix(self, client):
        response = client.get("/api/export/puzzles/demo/solved-pdf")

        assert response.headers["content-disposition"] == \
            'attachment; filename="demo-solution.pdf"'

    def test_text_export_is_encoded(self, client):
        response = client.get("/api/export/puzzles/demo/acrosslite")

        assert response.content == b"grid text"
        assert response.headers["content-disposition"] == 'attachment; filename="demo.txt"'

    def test_missing_puzzle_is_a_404(self, client, container):
        container.export_uc.export_puzzle_to_solver_pdf.side_effect = PersistenceError("gone")

        response = client.get("/api/export/puzzles/nope/solver-pdf")

        assert response.status_code == 404
        assert response.json() == {"error": "Puzzle not found: nope"}


class TestImportRoutes:
    """Uploads are validated before the importer sees them."""

    def test_acrosslite_import(self, client, container):
        response = client.post("/api/import/acrosslite",
                               json={"name": " demo ", "content": "grid text"})

        container.import_uc.import_puzzle_from_acrosslite.assert_called_once_with(
            1, "demo", "grid text")
        assert response.json() == {"name": "demo"}

    def test_missing_name_is_rejected(self, client, container):
        response = client.post("/api/import/xd", json={"content": "text"})

        assert response.status_code == 400
        assert response.json() == {"error": "Missing puzzle name"}
        container.import_uc.import_puzzle_from_xd.assert_not_called()

    def test_missing_content_is_rejected(self, client, container):
        response = client.post("/api/import/ipuz", json={"name": "demo"})

        assert response.status_code == 400
        assert response.json() == {"error": "Missing file content"}

    def test_unusable_file_is_a_400(self, client, container):
        from crossword.ports.import_port import PuzzleImportError
        container.import_uc.import_puzzle_from_ccxml.side_effect = PuzzleImportError("bad xml")

        response = client.post("/api/import/ccxml",
                               json={"name": "demo", "content": "<nope/>"})

        assert response.status_code == 400
        assert response.json() == {"error": "bad xml"}

    def test_puz_import_decodes_base64(self, client, container):
        response = client.post("/api/import/puz",
                               json={"name": "demo", "content_b64": "aGVsbG8="})

        container.import_uc.import_puzzle_from_puz.assert_called_once_with(1, "demo", b"hello")
        assert response.json() == {"name": "demo"}

    def test_puz_import_rejects_bad_base64(self, client, container):
        response = client.post("/api/import/puz",
                               json={"name": "demo", "content_b64": "!!!not base64!!!"})

        assert response.status_code == 500
        assert response.json() == {"error": "Invalid base64 encoding"}


class TestSaveRoutes:
    """Save and Save As, which copy a working copy back to a real puzzle."""

    def test_missing_comment_is_rejected(self, client, container):
        response = client.post("/api/puzzles/demo/copy", json={"new_name": "demo-copy"})

        assert response.status_code == 400
        assert response.json() == {"error": "Missing or invalid 'comment'"}
        container.puzzle_uc.copy_puzzle.assert_not_called()

    def test_blank_comment_is_rejected(self, client, container):
        response = client.post("/api/puzzles/demo/copy",
                               json={"new_name": "demo-copy", "comment": "   "})

        assert response.status_code == 400
        assert response.json() == {"error": "Missing or invalid 'comment'"}
        container.puzzle_uc.copy_puzzle.assert_not_called()

    def test_missing_new_name_is_rejected(self, client, container):
        response = client.post("/api/puzzles/demo/copy", json={"comment": "why not"})

        assert response.status_code == 400
        assert response.json() == {"error": "Missing or invalid 'new_name'"}

    def test_valid_comment_is_passed_through(self, client, container):
        container.puzzle_uc.copy_puzzle.return_value = TestPuzzle.create_puzzle()

        response = client.post("/api/puzzles/demo/copy", json={
            "new_name": "demo-copy", "comment": "Fixed the theme entries"})

        container.puzzle_uc.copy_puzzle.assert_called_once_with(
            1, "demo", "demo-copy", "Fixed the theme entries")
        assert response.json()["name"] == "demo-copy"

    def test_use_case_rejection_surfaces_as_400(self, client, container):
        container.puzzle_uc.copy_puzzle.side_effect = ValueError("comment must not be empty")

        response = client.post("/api/puzzles/demo/copy",
                               json={"new_name": "demo-copy", "comment": "x"})

        assert response.status_code == 400
        assert response.json() == {"error": "comment must not be empty"}

    def test_rename_puzzle(self, client, container):
        response = client.post("/api/puzzles/demo/rename", json={"new_name": "demo2"})

        container.puzzle_uc.rename_puzzle.assert_called_once_with(1, "demo", "demo2")
        assert response.json() == {"name": "demo2"}


class TestPuzzleStateRoutes:
    """The lifecycle state of a puzzle and its history."""

    def test_get_puzzle_state(self, client, container):
        container.puzzle_uc.get_puzzle_state.return_value = {
            "state": "submitted", "publisher": "NYT",
            "date_submitted": "2026-06-06", "date_published": None,
        }

        response = client.get("/api/puzzles/demo/state")

        container.puzzle_uc.get_puzzle_state.assert_called_once_with(1, "demo")
        assert response.json() == {
            "name": "demo", "state": "submitted", "publisher": "NYT",
            "date_submitted": "2026-06-06", "date_published": None,
        }

    def test_set_puzzle_state(self, client, container):
        container.puzzle_uc.set_puzzle_state.return_value = {
            "state": "submitted", "publisher": "NYT",
            "date_submitted": "2026-06-06", "date_published": None,
        }

        response = client.put("/api/puzzles/demo/state", json={
            "state": "submitted", "publisher": "NYT", "date_submitted": "2026-06-06"})

        container.puzzle_uc.set_puzzle_state.assert_called_once_with(
            1, "demo", "submitted",
            publisher="NYT", date_submitted="2026-06-06", date_published=None,
        )
        assert response.json()["state"] == "submitted"

    def test_set_puzzle_state_validation_error_is_a_400(self, client, container):
        container.puzzle_uc.set_puzzle_state.side_effect = ValueError("publisher is required")

        response = client.put("/api/puzzles/demo/state", json={"state": "submitted"})

        assert response.status_code == 400
        assert response.json() == {"error": "publisher is required"}

    def test_get_puzzle_state_history(self, client, container):
        container.puzzle_uc.get_puzzle_state_history.return_value = [
            {"state": "draft", "changed_at": "2026-01-01T00:00:00"},
            {"state": "submitted", "changed_at": "2026-06-06T00:00:00"},
        ]

        response = client.get("/api/puzzles/demo/state/history")

        container.puzzle_uc.get_puzzle_state_history.assert_called_once_with(1, "demo")
        body = response.json()
        assert body["name"] == "demo"
        assert [row["state"] for row in body["history"]] == ["draft", "submitted"]

    def test_get_puzzle_state_history_not_found(self, client, container):
        container.puzzle_uc.get_puzzle_state_history.side_effect = PersistenceError("not found")

        response = client.get("/api/puzzles/nope/state/history")

        assert response.status_code == 404

    def test_restore_from_history(self, client, container):
        container.puzzle_uc.restore_puzzle_from_history.return_value = "__wc__demo__a1b2c3d4"

        response = client.post("/api/puzzles/demo/state/history/31/restore")

        container.puzzle_uc.restore_puzzle_from_history.assert_called_once_with(1, "demo", 31)
        assert response.json() == {
            "original_name": "demo", "working_name": "__wc__demo__a1b2c3d4"}

    def test_restore_from_history_without_content(self, client, container):
        container.puzzle_uc.restore_puzzle_from_history.side_effect = PersistenceError(
            "No restorable content for history row 31 of puzzle 'demo'")

        response = client.post("/api/puzzles/demo/state/history/31/restore")

        assert response.status_code == 404
        assert "No restorable content" in response.json()["error"]


class TestFrontendRoutes:
    """The page itself, its theme, and the settings screen."""

    def test_index_is_served(self, client):
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    def test_config_comes_from_the_wired_config(self, client):
        response = client.get("/api/config")

        assert response.json() == {"message_line_timeout_ms": 1000}

    def test_theme_css_is_empty_without_a_theme_color(self, client):
        response = client.get("/static/css/theme.css")

        assert response.headers["content-type"].startswith("text/css")
        assert response.text == ""

    def test_theme_css_derives_a_palette(self, container):
        container.config["theme_color"] = "#154d71"
        client = TestClient(create_app(container=container))

        response = client.get("/static/css/theme.css")

        assert "--c-primary: #154d71;" in response.text
        assert "--c-appbar-bg:" in response.text

    def test_settings_are_read_and_written(self, client):
        with patch("crossword.http_server.static_routes.get_settings",
                   return_value={"author_name": "Phil"}) as read, \
             patch("crossword.http_server.static_routes.put_settings",
                   return_value=True) as write:
            assert client.get("/api/settings").json() == {"author_name": "Phil"}
            response = client.put("/api/settings", json={"author_name": "Someone"})

        read.assert_called_once_with()
        write.assert_called_once_with({"author_name": "Someone"})
        assert response.json() == {"restart_required": True}


class TestServerStartup:
    """Starting the server."""

    def test_run_http_server_hands_uvicorn_the_configured_address(self):
        container = Mock()
        container.config = {"host": "127.0.0.1", "port": 5000}

        with patch("crossword.http_server.main.make_app", return_value=container), \
             patch("crossword.http_server.main.uvicorn.run") as run, \
             patch("builtins.print") as printed:
            run_http_server({"host": "127.0.0.1", "port": 5000})

        printed.assert_not_called()
        assert run.call_args.kwargs["host"] == "127.0.0.1"
        assert run.call_args.kwargs["port"] == 5000

    def test_create_app_wires_the_container_onto_the_app(self):
        container = Mock()
        container.config = {}

        app = create_app(container=container)

        assert app.state.container is container
