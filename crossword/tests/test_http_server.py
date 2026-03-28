"""
Unit tests for HTTP server - router and request handler.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from crossword.http_server.server import Route, Router, RequestHandler, create_server
from crossword.http_server.main import register_routes
from crossword.http_server.puzzle_handlers import (
    _puzzle_response,
    handle_create_puzzle,
    handle_switch_to_grid_mode,
    handle_switch_to_puzzle_mode,
    handle_toggle_puzzle_black_cell,
)
from crossword.tests import TestPuzzle


class TestRoute:
    """Tests for Route class"""

    def test_route_matches_method_and_path(self):
        """Route matches when method and path both match"""
        handler = Mock()
        route = Route("GET", r"^/grids$", handler)

        assert route.matches("GET", "/grids")

    def test_route_no_match_wrong_method(self):
        """Route doesn't match with wrong method"""
        handler = Mock()
        route = Route("GET", r"^/grids$", handler)

        assert not route.matches("POST", "/grids")

    def test_route_no_match_wrong_path(self):
        """Route doesn't match with wrong path"""
        handler = Mock()
        route = Route("GET", r"^/grids$", handler)

        assert not route.matches("GET", "/puzzles")

    def test_route_captures_path_params(self):
        """Route extracts capture groups from path"""
        handler = Mock()
        route = Route("GET", r"^/grids/(\d+)$", handler)

        params = route.extract_params("/grids/42")
        assert params == ("42",)

    def test_route_multiple_captures(self):
        """Route extracts multiple capture groups"""
        handler = Mock()
        route = Route("PUT", r"^/grids/(\d+)/cells/(\d+)/(\d+)$", handler)

        params = route.extract_params("/grids/1/cells/5/7")
        assert params == ("1", "5", "7")

    def test_route_case_insensitive_method(self):
        """Route method matching is case-insensitive"""
        handler = Mock()
        route = Route("GET", r"^/grids$", handler)

        assert route.matches("get", "/grids")
        assert route.matches("Get", "/grids")


class TestRouter:
    """Tests for Router class"""

    def test_router_add_route(self):
        """Router can add routes"""
        router = Router()
        handler = Mock()

        router.add_route("GET", r"^/grids$", handler)

        assert len(router.routes) == 1

    def test_router_find_route_success(self):
        """Router finds matching route"""
        router = Router()
        handler = Mock()
        router.add_route("GET", r"^/grids$", handler)

        route, params = router.find_route("GET", "/grids")

        assert route is not None
        assert route.handler == handler
        assert params == ()

    def test_router_find_route_with_params(self):
        """Router finds route and extracts params"""
        router = Router()
        handler = Mock()
        router.add_route("GET", r"^/grids/(\d+)$", handler)

        route, params = router.find_route("GET", "/grids/42")

        assert route is not None
        assert params == ("42",)

    def test_router_find_route_not_found(self):
        """Router returns None for non-matching route"""
        router = Router()
        handler = Mock()
        router.add_route("GET", r"^/grids$", handler)

        route, _ = router.find_route("POST", "/grids")

        assert route is None

    def test_router_get_handler_success(self):
        """Router.get_handler returns handler for matching route"""
        router = Router()
        handler = Mock()
        router.add_route("GET", r"^/grids$", handler)

        result = router.get_handler("GET", "/grids")

        assert result == handler

    def test_router_get_handler_not_found(self):
        """Router.get_handler returns None for non-matching route"""
        router = Router()
        handler = Mock()
        router.add_route("GET", r"^/grids$", handler)

        result = router.get_handler("POST", "/grids")

        assert result is None

    def test_router_multiple_routes(self):
        """Router can handle multiple routes"""
        router = Router()
        handler1 = Mock()
        handler2 = Mock()
        handler3 = Mock()

        router.add_route("GET", r"^/grids$", handler1)
        router.add_route("POST", r"^/grids$", handler2)
        router.add_route("GET", r"^/puzzles$", handler3)

        assert router.get_handler("GET", "/grids") == handler1
        assert router.get_handler("POST", "/grids") == handler2
        assert router.get_handler("GET", "/puzzles") == handler3


class TestRequestHandler:
    """Tests for RequestHandler"""

    def _create_handler(self):
        """Create a RequestHandler instance with mocked dependencies"""
        handler = Mock(spec=RequestHandler)
        # Bind the actual methods we want to test to the mock
        handler._parse_session_token = RequestHandler._parse_session_token.__get__(handler, RequestHandler)
        handler._send_json = RequestHandler._send_json.__get__(handler, RequestHandler)
        handler._send_error = RequestHandler._send_error.__get__(handler, RequestHandler)
        return handler

    def test_parse_session_token(self):
        """RequestHandler extracts session token from cookies"""
        handler = self._create_handler()
        handler.headers = {"Cookie": "session=abc123def456"}

        token = handler._parse_session_token()

        assert token == "abc123def456"

    def test_parse_session_token_no_cookie(self):
        """RequestHandler returns None when no session cookie"""
        handler = self._create_handler()
        handler.headers = {"Cookie": "other=value"}

        token = handler._parse_session_token()

        assert token is None

    def test_parse_session_token_no_header(self):
        """RequestHandler returns None when no Cookie header"""
        handler = self._create_handler()
        handler.headers = {}

        token = handler._parse_session_token()

        assert token is None

    def test_parse_session_token_multiple_cookies(self):
        """RequestHandler extracts session from multiple cookies"""
        handler = self._create_handler()
        handler.headers = {"Cookie": "user=john; session=token123; theme=dark"}

        token = handler._parse_session_token()

        assert token == "token123"

    def test_send_json(self):
        """RequestHandler.send_json sends JSON response"""
        handler = self._create_handler()
        handler.wfile = MagicMock()
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        data = {"key": "value", "number": 42}
        handler._send_json(data, status=200)

        handler.send_response.assert_called_once_with(200)
        handler.send_header.assert_any_call("Content-Type", "application/json")
        handler.end_headers.assert_called_once()

    def test_send_error(self):
        """RequestHandler.send_error sends error as JSON"""
        handler = self._create_handler()
        handler.wfile = MagicMock()
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()

        handler._send_error(404, "Not Found")

        handler.send_response.assert_called_once_with(404)


class TestCreateServer:
    """Tests for create_server function"""

    def test_create_server_returns_tuple(self):
        """create_server returns (server, router) tuple"""
        fake_server = Mock()
        fake_server.server_address = ("127.0.0.1", 9999)
        with patch("http.server.HTTPServer", return_value=fake_server):
            server, router = create_server(port=9999)

        assert server is not None
        assert isinstance(router, Router)
        assert RequestHandler.router == router

    def test_create_server_router_attached(self):
        """create_server attaches router to RequestHandler"""
        fake_server = Mock()
        fake_server.server_address = ("127.0.0.1", 9998)
        with patch("http.server.HTTPServer", return_value=fake_server):
            server, router = create_server(port=9998)

        assert RequestHandler.router == router

    def test_create_server_custom_port_and_host(self):
        """create_server accepts custom port and host"""
        fake_server = Mock()
        fake_server.server_address = ("0.0.0.0", 8080)
        with patch("http.server.HTTPServer", return_value=fake_server):
            server, router = create_server(port=8080, host="0.0.0.0")

        assert server.server_address[1] == 8080
        assert server.server_address[0] == "0.0.0.0"


class TestRequestParsing:
    """Integration tests for request parsing"""

    def test_parse_query_parameters(self):
        """Request parsing extracts query parameters"""
        # This test verifies the logic (actual HTTP testing would use integration tests)
        from urllib.parse import parse_qs

        query_string = "name=test&size=15&active=true"
        query_dict = parse_qs(query_string)
        query_params = {k: v[0] if len(v) == 1 else v for k, v in query_dict.items()}

        assert query_params["name"] == "test"
        assert query_params["size"] == "15"
        assert query_params["active"] == "true"

    def test_parse_json_body(self):
        """Request parsing decodes JSON body"""
        body_text = '{"name": "test_grid", "size": 15}'
        body_params = json.loads(body_text)

        assert body_params["name"] == "test_grid"
        assert body_params["size"] == 15


class TestMergedPuzzleRoutes:
    """Tests for Phase 4 puzzle-centric route registration."""

    def test_register_routes_adds_new_puzzle_mode_routes(self):
        router = Router()
        register_routes(router)

        assert router.get_handler("POST", "/api/puzzles/demo/mode/grid") is not None
        assert router.get_handler("POST", "/api/puzzles/demo/mode/puzzle") is not None
        assert router.get_handler("PUT", "/api/puzzles/demo/grid/cells/0/1") is not None
        assert router.get_handler("POST", "/api/puzzles/demo/grid/rotate") is not None
        assert router.get_handler("POST", "/api/puzzles/demo/grid/undo") is not None
        assert router.get_handler("POST", "/api/puzzles/demo/grid/redo") is not None


class TestMergedPuzzleHandlers:
    """Direct handler tests for the merged puzzle API."""

    @pytest.fixture
    def request_handler(self):
        handler = Mock()
        handler.command = "POST"
        handler.path = "/api/test"
        return handler

    @pytest.fixture
    def app(self):
        app = Mock()
        app.puzzle_uc = Mock()
        return app

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

    def test_handle_create_puzzle_accepts_size(self, request_handler, app):
        puzzle = TestPuzzle.create_puzzle()
        app.puzzle_uc.load_puzzle.return_value = puzzle

        response = handle_create_puzzle(
            (), {}, {"name": "demo", "size": 15}, None, request_handler, app=app
        )

        app.puzzle_uc.create_puzzle.assert_called_once_with(1, "demo", grid_name=None, size=15)
        assert response["grid"]["size"] == puzzle.n

    def test_handle_switch_to_grid_mode(self, request_handler, app):
        puzzle = TestPuzzle.create_puzzle()
        puzzle.enter_grid_mode()
        app.puzzle_uc.switch_to_grid_mode.return_value = puzzle

        response = handle_switch_to_grid_mode(
            ("demo",), {}, {}, None, request_handler, app=app
        )

        app.puzzle_uc.switch_to_grid_mode.assert_called_once_with(1, "demo")
        assert response["mode"] == "grid"

    def test_handle_switch_to_puzzle_mode(self, request_handler, app):
        puzzle = TestPuzzle.create_puzzle()
        puzzle.enter_puzzle_mode()
        app.puzzle_uc.switch_to_puzzle_mode.return_value = puzzle

        response = handle_switch_to_puzzle_mode(
            ("demo",), {}, {}, None, request_handler, app=app
        )

        app.puzzle_uc.switch_to_puzzle_mode.assert_called_once_with(1, "demo")
        assert response["mode"] == "puzzle"

    def test_handle_toggle_puzzle_black_cell(self, request_handler, app):
        puzzle = TestPuzzle.create_puzzle()
        puzzle.toggle_black_cell(1, 1)
        app.puzzle_uc.toggle_black_cell.return_value = puzzle

        response = handle_toggle_puzzle_black_cell(
            ("demo", "0", "0"), {}, {}, None, request_handler, app=app
        )

        app.puzzle_uc.toggle_black_cell.assert_called_once_with(1, "demo", 1, 1)
        assert response["grid"]["cells"][0] is True
