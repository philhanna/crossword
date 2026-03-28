import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

from crossword import Grid, Puzzle
from crossword.domain.word import Word


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "dev" / "migrate196.py"
SPEC = importlib.util.spec_from_file_location("migrate196_tool", MODULE_PATH)
migrate196 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = migrate196
SPEC.loader.exec_module(migrate196)


def create_legacy_source_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE puzzles (
            id          INTEGER PRIMARY KEY,
            userid      INTEGER NOT NULL,
            puzzlename  TEXT NOT NULL,
            created     TEXT NOT NULL,
            modified    TEXT NOT NULL,
            jsonstr     TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE grids (
            id          INTEGER PRIMARY KEY,
            userid      INTEGER NOT NULL,
            gridname    TEXT NOT NULL,
            created     TEXT NOT NULL,
            modified    TEXT NOT NULL,
            jsonstr     TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE TABLE words (word TEXT UNIQUE NOT NULL)")
    conn.commit()
    conn.close()


def load_puzzle_json(conn: sqlite3.Connection, name: str) -> dict:
    row = conn.execute(
        "SELECT jsonstr FROM puzzles WHERE puzzlename = ?",
        (name,),
    ).fetchone()
    return json.loads(row[0])


class TestMigrate196Tool:
    def test_migrates_legacy_puzzle_rows_missing_last_mode(self, tmp_path):
        source = tmp_path / "legacy.db"
        dest = tmp_path / "migrated.db"
        create_legacy_source_db(source)

        grid = Grid(5)
        puzzle = Puzzle(grid)
        puzzle.title = "Legacy Puzzle"
        first_across = min(puzzle.across_words)
        puzzle.set_clue(first_across, Word.ACROSS, "Starts here")

        legacy_image = json.loads(puzzle.to_json())
        legacy_image.pop("last_mode", None)
        legacy_image.pop("grid_undo_stack", None)
        legacy_image.pop("grid_redo_stack", None)

        conn = sqlite3.connect(source)
        conn.execute(
            """
            INSERT INTO puzzles (userid, puzzlename, created, modified, jsonstr)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, "legacy", "2026-01-01T00:00:00", "2026-01-01T00:00:00", json.dumps(legacy_image)),
        )
        conn.execute("INSERT INTO words (word) VALUES ('legacyword')")
        conn.commit()
        conn.close()

        report = migrate196.migrate_database(str(source), str(dest))

        assert report.migrated_puzzles == 1
        assert report.dropped_grids_table is True

        migrated_conn = sqlite3.connect(dest)
        migrated_conn.row_factory = sqlite3.Row

        columns = {
            row["name"]
            for row in migrated_conn.execute("PRAGMA table_info(puzzles)").fetchall()
        }
        assert "last_mode" in columns

        loaded = migrated_conn.execute(
            "SELECT last_mode, jsonstr FROM puzzles WHERE puzzlename = ?",
            ("legacy",),
        ).fetchone()
        assert loaded["last_mode"] == "puzzle"

        image = json.loads(loaded["jsonstr"])
        assert image["last_mode"] == "puzzle"
        assert "grid_undo_stack" in image
        assert "grid_redo_stack" in image

        words = migrated_conn.execute("SELECT word FROM words").fetchall()
        assert [row["word"] for row in words] == ["legacyword"]

        assert migrated_conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'grids'"
        ).fetchone() is None
        migrated_conn.close()

        source_conn = sqlite3.connect(source)
        source_columns = {
            row[1] for row in source_conn.execute("PRAGMA table_info(puzzles)").fetchall()
        }
        assert "last_mode" not in source_columns
        assert source_conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'grids'"
        ).fetchone() is not None
        source_conn.close()

    def test_resolves_grid_from_legacy_grids_table(self, tmp_path):
        source = tmp_path / "legacy-grid.db"
        dest = tmp_path / "migrated-grid.db"
        create_legacy_source_db(source)

        grid = Grid(5)
        grid.add_black_cell(2, 2, undo=False)
        puzzle = Puzzle(grid)
        puzzle.title = "Separated Grid"
        first_across = min(puzzle.across_words)
        puzzle.set_text(first_across, Word.ACROSS, "APPLE", undo=False)
        puzzle.set_clue(first_across, Word.ACROSS, "Fruit")

        image = json.loads(puzzle.to_json())
        legacy_image = {
            "title": image["title"],
            "grid_name": "base-grid",
            "across_words": image["across_words"],
            "down_words": image["down_words"],
            "undo_stack": image["undo_stack"],
            "redo_stack": image["redo_stack"],
        }

        conn = sqlite3.connect(source)
        conn.execute(
            """
            INSERT INTO grids (userid, gridname, created, modified, jsonstr)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, "base-grid", "2026-01-01T00:00:00", "2026-01-01T00:00:00", grid.to_json()),
        )
        conn.execute(
            """
            INSERT INTO puzzles (userid, puzzlename, created, modified, jsonstr)
            VALUES (?, ?, ?, ?, ?)
            """,
            (1, "legacy-grid", "2026-01-01T00:00:00", "2026-01-01T00:00:00", json.dumps(legacy_image)),
        )
        conn.commit()
        conn.close()

        migrate196.migrate_database(str(source), str(dest))

        migrated_conn = sqlite3.connect(dest)
        migrated_conn.row_factory = sqlite3.Row
        loaded = migrated_conn.execute(
            "SELECT last_mode, jsonstr FROM puzzles WHERE puzzlename = ?",
            ("legacy-grid",),
        ).fetchone()
        assert loaded["last_mode"] == "puzzle"

        migrated_image = json.loads(loaded["jsonstr"])
        assert migrated_image["n"] == 5
        assert [2, 2] in migrated_image["black_cells"]
        assert migrated_image["last_mode"] == "puzzle"

        migrated_puzzle = Puzzle.from_json(loaded["jsonstr"])
        migrated_first_across = min(migrated_puzzle.across_words)
        assert migrated_puzzle.get_across_word(migrated_first_across).get_text() == "APPLE"
        assert migrated_puzzle.get_across_word(migrated_first_across).get_clue() == "Fruit"

        migrated_conn.close()

    def test_fails_and_removes_destination_on_unresolved_grid_reference(self, tmp_path):
        source = tmp_path / "broken.db"
        dest = tmp_path / "broken-migrated.db"
        create_legacy_source_db(source)

        conn = sqlite3.connect(source)
        conn.execute(
            """
            INSERT INTO puzzles (userid, puzzlename, created, modified, jsonstr)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                1,
                "broken",
                "2026-01-01T00:00:00",
                "2026-01-01T00:00:00",
                json.dumps({"title": "Broken", "grid_name": "missing-grid"}),
            ),
        )
        conn.commit()
        conn.close()

        with pytest.raises(migrate196.MigrationError):
            migrate196.migrate_database(str(source), str(dest))

        assert not dest.exists()
