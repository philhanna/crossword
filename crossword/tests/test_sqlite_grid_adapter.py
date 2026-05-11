import sqlite3

import pytest

from crossword.adapters.sqlite_grid_adapter import SQLiteGridAdapter

_SCHEMA = """
CREATE TABLE grids (
    id        INTEGER PRIMARY KEY,
    filename  TEXT    NOT NULL UNIQUE,
    size      INTEGER NOT NULL,
    grid_text TEXT    NOT NULL UNIQUE
);
CREATE TABLE slot_counts (
    grid_id   INTEGER NOT NULL REFERENCES grids(id),
    direction TEXT    NOT NULL CHECK (direction IN ('A', 'D')),
    length    INTEGER NOT NULL,
    count     INTEGER NOT NULL,
    PRIMARY KEY (grid_id, direction, length)
);
"""


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "grids.db"
    con = sqlite3.connect(path)
    con.executescript(_SCHEMA)

    # gridA: size=15, 2×5A 2×7A, benign Down slots — should match [5,7,7,5]
    con.execute("INSERT INTO grids VALUES (1, 'gridA.txt', 15, 'textA')")
    con.executemany(
        "INSERT INTO slot_counts VALUES (1, ?, ?, ?)",
        [("A", 5, 2), ("A", 7, 2), ("D", 3, 4), ("D", 4, 4)],
    )

    # gridB: size=15, has gap slot (6A) — excluded by gap constraint
    con.execute("INSERT INTO grids VALUES (2, 'gridB.txt', 15, 'textB')")
    con.executemany(
        "INSERT INTO slot_counts VALUES (2, ?, ?, ?)",
        [("A", 5, 2), ("A", 7, 2), ("A", 6, 1)],
    )

    # gridC: size=15, has oversized slot (8A) — excluded by max constraint
    con.execute("INSERT INTO grids VALUES (3, 'gridC.txt', 15, 'textC')")
    con.executemany(
        "INSERT INTO slot_counts VALUES (3, ?, ?, ?)",
        [("A", 5, 2), ("A", 7, 2), ("A", 8, 1)],
    )

    # gridD: size=15, has 5D slot — excluded by spec-length-in-Down constraint
    con.execute("INSERT INTO grids VALUES (4, 'gridD.txt', 15, 'textD')")
    con.executemany(
        "INSERT INTO slot_counts VALUES (4, ?, ?, ?)",
        [("A", 5, 2), ("A", 7, 2), ("D", 5, 1)],
    )

    # gridE: size=21 — excluded by size filter
    con.execute("INSERT INTO grids VALUES (5, 'gridE.txt', 21, 'textE')")
    con.executemany(
        "INSERT INTO slot_counts VALUES (5, ?, ?, ?)",
        [("A", 5, 2), ("A", 7, 2)],
    )

    # gridF: size=15, wrong 5A count (3 instead of 2) — excluded by count constraint
    con.execute("INSERT INTO grids VALUES (6, 'gridF.txt', 15, 'textF')")
    con.executemany(
        "INSERT INTO slot_counts VALUES (6, ?, ?, ?)",
        [("A", 5, 3), ("A", 7, 2)],
    )

    con.commit()
    con.close()
    return path


@pytest.fixture
def adapter(db_path):
    return SQLiteGridAdapter(str(db_path))


def test_search_returns_only_matching_grid(adapter):
    result = adapter.search([5, 7, 7, 5], 15)
    assert result == ["gridA.txt"]


def test_search_excludes_gap_slot(adapter):
    assert "gridB.txt" not in adapter.search([5, 7, 7, 5], 15)


def test_search_excludes_oversized_slot(adapter):
    assert "gridC.txt" not in adapter.search([5, 7, 7, 5], 15)


def test_search_excludes_down_spec_length(adapter):
    assert "gridD.txt" not in adapter.search([5, 7, 7, 5], 15)


def test_search_excludes_wrong_size(adapter):
    assert "gridE.txt" not in adapter.search([5, 7, 7, 5], 15)


def test_search_excludes_wrong_count(adapter):
    assert "gridF.txt" not in adapter.search([5, 7, 7, 5], 15)


def test_search_results_alphabetical(adapter):
    result = adapter.search([5, 7, 7, 5], 15)
    assert result == sorted(result)


def test_search_empty_when_no_match(adapter):
    assert adapter.search([5, 7, 7, 5], 99) == []


def test_search_returns_empty_when_no_db_configured():
    adapter = SQLiteGridAdapter(None)
    assert adapter.search([5, 7, 7, 5], 15) == []
