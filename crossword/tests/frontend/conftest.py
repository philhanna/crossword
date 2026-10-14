"""
Fixtures for the end-to-end frontend tests.

Each test gets its own server, started in a background thread on a free port
with a throwaway SQLite file and a throwaway settings file, and a Playwright
page already showing the dashboard. The `api` fixture talks to the same
server directly, so a test can set up puzzles without clicking for them.
"""

import base64
import socket
import threading
import time
from pathlib import Path

import pytest
import requests
import uvicorn
import yaml

from crossword.adapters import settings_adapter
from crossword.http_server.main import create_app

DATA_DIR = Path(__file__).parent.parent / "data"
SAMPLE_PUZ = DATA_DIR / "remedialchaostheory.puz"


@pytest.fixture
def server(tmp_path, monkeypatch):
    """Start the app on a free port and yield its base URL."""
    port = _free_port()
    config = {
        "host": "127.0.0.1",
        "port": port,
        "dbfile": str(tmp_path / "crossword.db"),
        "word_file": str(DATA_DIR / "words.txt"),
        "log_level": "WARNING",
        "message_line_timeout_ms": 3000,
        "theme_color": "",
        "definition_provider": "wiktionary",
    }

    # PUT /api/settings writes the user's config file; point it somewhere safe.
    settings_file = tmp_path / "config.yaml"
    settings_file.write_text(yaml.safe_dump(config))
    monkeypatch.setattr(settings_adapter, "_config_path", lambda: str(settings_file))

    app = create_app(config)
    uv_server = uvicorn.Server(uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="warning", log_config=None))
    thread = threading.Thread(target=uv_server.run, daemon=True)
    thread.start()
    deadline = time.time() + 10
    while not uv_server.started:
        if time.time() > deadline:
            raise RuntimeError("Test server did not start")
        time.sleep(0.02)

    yield f"http://127.0.0.1:{port}"

    uv_server.should_exit = True
    thread.join(timeout=10)


@pytest.fixture
def api(server):
    """A small client for setting up and checking server-side state."""
    return Api(server)


@pytest.fixture
def app_page(page, server):
    """A browser page showing the app's dashboard, with errors collected."""
    errors = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.goto(server)
    page.locator(".dash").wait_for()
    page.js_errors = errors
    yield page
    assert errors == [], f"JavaScript errors on the page: {errors}"


class Api:
    """Direct calls to the test server's REST API."""

    def __init__(self, base_url):
        self.base_url = base_url

    def call(self, method, path, body=None):
        resp = requests.request(method, self.base_url + path, json=body, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def create_puzzle(self, name, size=5):
        """Create an empty puzzle, switch it to Puzzle mode and save it."""
        self.call("POST", "/api/puzzles", {"name": name, "size": size})
        self.call("POST", f"/api/puzzles/{name}/mode/puzzle")
        return name

    def import_sample(self, name):
        """Import the bundled .puz file, which is fully filled and clued."""
        content_b64 = base64.b64encode(SAMPLE_PUZ.read_bytes()).decode()
        self.call("POST", "/api/import/puz", {"name": name, "content_b64": content_b64})
        return name

    def set_state(self, name, state, **fields):
        return self.call("PUT", f"/api/puzzles/{name}/state", {"state": state, **fields})

    def puzzle_names(self):
        return [p for p in self.call("GET", "/api/puzzles")["puzzles"]
                if not p.startswith("__")]

    def export_text(self, name, endpoint):
        resp = requests.get(f"{self.base_url}/api/export/puzzles/{name}/{endpoint}", timeout=10)
        resp.raise_for_status()
        return resp.content


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
