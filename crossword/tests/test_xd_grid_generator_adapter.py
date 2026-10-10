import sqlite3

import pytest

from crossword.adapters.xd_grid_generator_adapter import XdGridGeneratorAdapter
from crossword.domain.grid import Grid


@pytest.fixture
def empty_xdfile(tmp_path):
    path = tmp_path / "xd.db"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE grids (id INTEGER PRIMARY KEY, grid_text TEXT, size INTEGER)")
        conn.execute(
            "CREATE TABLE slot_counts (grid_id INTEGER, direction TEXT, length INTEGER, count INTEGER)"
        )
    return str(path)


class _StubRandom:
    def __init__(self):
        self.calls = []

    def generate(self, n, spec=None):
        self.calls.append((n, spec))
        return Grid(n)


def test_falls_back_to_random_when_no_grid_found(empty_xdfile):
    adapter = XdGridGeneratorAdapter(empty_xdfile)
    stub = _StubRandom()
    adapter._random = stub
    grid = adapter.generate(15)
    assert grid.n == 15
    assert stub.calls == [(15, None)]


def test_falls_back_to_random_when_no_grid_matches_spec(empty_xdfile):
    adapter = XdGridGeneratorAdapter(empty_xdfile)
    stub = _StubRandom()
    adapter._random = stub
    grid = adapter.generate(15, [11, 15, 11])
    assert grid.n == 15
    assert stub.calls == [(15, [11, 15, 11])]


def test_falls_back_to_random_for_non_xd_size(empty_xdfile):
    adapter = XdGridGeneratorAdapter(empty_xdfile)
    stub = _StubRandom()
    adapter._random = stub
    adapter.generate(9)
    assert stub.calls == [(9, None)]
