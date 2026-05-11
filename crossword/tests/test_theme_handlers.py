import http.client
import json
import threading
from http.server import HTTPServer

import pytest

from crossword.adapters.sqlite_theme_adapter import SQLiteThemeAdapter
from crossword.adapters.sqlite_grid_adapter import SQLiteGridAdapter
from crossword.use_cases.theme_use_cases import ThemeUseCases
from crossword.http_server.server import RequestHandler, Router
from crossword.http_server.theme_handlers import (
    handle_list_themes,
    handle_create_theme,
    handle_get_theme,
    handle_update_theme,
    handle_delete_theme,
    handle_add_words,
    handle_remove_word,
    handle_search_grids,
)


class FakeGridAdapter:
    def search(self, spec, size):
        return ["themed.txt"]


class _App:
    def __init__(self, theme_uc):
        self.theme_uc = theme_uc


@pytest.fixture
def client():
    repo = SQLiteThemeAdapter(":memory:")
    theme_uc = ThemeUseCases(repo, FakeGridAdapter())

    router = Router()
    router.add_route("GET",    r"^/api/themes$",                     handle_list_themes)
    router.add_route("POST",   r"^/api/themes$",                     handle_create_theme)
    router.add_route("GET",    r"^/api/themes/(\d+)/grids$",         handle_search_grids)
    router.add_route("GET",    r"^/api/themes/(\d+)$",               handle_get_theme)
    router.add_route("PUT",    r"^/api/themes/(\d+)$",               handle_update_theme)
    router.add_route("DELETE", r"^/api/themes/(\d+)$",               handle_delete_theme)
    router.add_route("POST",   r"^/api/themes/(\d+)/words$",         handle_add_words)
    router.add_route("DELETE", r"^/api/themes/(\d+)/words/([^/]+)$", handle_remove_word)

    class _Handler(RequestHandler):
        pass

    _Handler.router = router
    _Handler.app = _App(theme_uc)

    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    yield port
    httpd.shutdown()


def _req(port, method, path, body=None):
    conn = http.client.HTTPConnection("127.0.0.1", port)
    headers = {}
    payload = None
    if body is not None:
        payload = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(payload))
    conn.request(method, path, payload, headers)
    resp = conn.getresponse()
    raw = resp.read()
    data = json.loads(raw) if raw else {}
    conn.close()
    return resp.status, data


def test_post_themes_creates(client):
    status, data = _req(client, "POST", "/api/themes", {"title": "Birds", "word_lengths": [5, 7, 7, 5]})
    assert status == 201
    assert data["title"] == "Birds"
    assert data["word_lengths"] == [5, 7, 7, 5]
    assert "complete" in data


def test_post_themes_rejects_non_palindrome(client):
    status, data = _req(client, "POST", "/api/themes", {"title": "Bad", "word_lengths": [5, 7]})
    assert status == 400
    assert "error" in data


def test_get_themes_lists_all(client):
    _req(client, "POST", "/api/themes", {"title": "A", "word_lengths": [5, 5]})
    _req(client, "POST", "/api/themes", {"title": "B", "word_lengths": [7, 7]})
    status, data = _req(client, "GET", "/api/themes")
    assert status == 200
    assert len(data["themes"]) == 2


def test_get_theme_by_id(client):
    _req(client, "POST", "/api/themes", {"title": "Birds", "word_lengths": [5, 7, 7, 5]})
    status, data = _req(client, "GET", "/api/themes/1")
    assert status == 200
    assert data["title"] == "Birds"
    assert data["complete"] is False


def test_get_theme_not_found(client):
    status, _ = _req(client, "GET", "/api/themes/99")
    assert status == 404


def test_put_theme_updates_title(client):
    _req(client, "POST", "/api/themes", {"title": "Old", "word_lengths": [5, 5]})
    status, data = _req(client, "PUT", "/api/themes/1", {"title": "New"})
    assert status == 200
    assert data["title"] == "New"


def test_put_theme_rejects_non_palindrome(client):
    _req(client, "POST", "/api/themes", {"title": "T", "word_lengths": [5, 5]})
    status, _ = _req(client, "PUT", "/api/themes/1", {"word_lengths": [5, 7]})
    assert status == 400


def test_put_theme_not_found(client):
    status, _ = _req(client, "PUT", "/api/themes/99", {"title": "X"})
    assert status == 404


def test_delete_theme(client):
    _req(client, "POST", "/api/themes", {"title": "Gone", "word_lengths": [5, 5]})
    status, _ = _req(client, "DELETE", "/api/themes/1")
    assert status == 204
    assert _req(client, "GET", "/api/themes/1")[0] == 404


def test_delete_theme_not_found(client):
    status, _ = _req(client, "DELETE", "/api/themes/99")
    assert status == 404


def test_post_words(client):
    _req(client, "POST", "/api/themes", {"title": "T", "word_lengths": [5, 7, 5]})
    status, data = _req(client, "POST", "/api/themes/1/words", {"words": ["CRANE"]})
    assert status == 200
    assert "CRANE" in data["selected_words"]


def test_delete_word(client):
    _req(client, "POST", "/api/themes", {"title": "T", "word_lengths": [5, 7, 5]})
    _req(client, "POST", "/api/themes/1/words", {"words": ["CRANE"]})
    status, data = _req(client, "DELETE", "/api/themes/1/words/CRANE")
    assert status == 200
    assert "CRANE" not in data["selected_words"]


def test_complete_flag_true(client):
    _req(client, "POST", "/api/themes", {"title": "T", "word_lengths": [5, 7, 7, 5]})
    _req(client, "POST", "/api/themes/1/words", {"words": ["CRANE", "PELICAN", "SPARROW", "EGRET"]})
    _, data = _req(client, "GET", "/api/themes/1")
    assert data["complete"] is True


def test_get_theme_grids(client):
    _req(client, "POST", "/api/themes", {"title": "T", "word_lengths": [5, 7, 7, 5]})
    status, data = _req(client, "GET", "/api/themes/1/grids?size=15")
    assert status == 200
    assert data["grids"] == ["themed.txt"]


def test_get_theme_grids_not_found(client):
    status, _ = _req(client, "GET", "/api/themes/99/grids?size=15")
    assert status == 404


def test_get_theme_grids_missing_size(client):
    _req(client, "POST", "/api/themes", {"title": "T", "word_lengths": [5, 7, 7, 5]})
    status, _ = _req(client, "GET", "/api/themes/1/grids")
    assert status == 400
