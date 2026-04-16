"""
Unit tests for dependency wiring - verify make_app() assembles and injected correctly.
"""

import pytest
import sqlite3
import tempfile
import os
from crossword.wiring import make_app, AppContainer
from crossword.ports.persistence_port import PersistenceError
from crossword.tests import TestPuzzle


@pytest.fixture
def temp_word_db():
    """Create a temporary word-list database with a handful of words."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE words (word TEXT UNIQUE NOT NULL)")
    conn.executemany("INSERT INTO words (word) VALUES (?)", [
        ("apple",), ("banana",), ("cherry",),
    ])
    conn.commit()
    conn.close()
    yield path
    try:
        os.remove(path)
    except Exception:
        pass


@pytest.fixture
def temp_word_file():
    """Create a temporary word-list text file with a handful of words."""
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.write(fd, b"delta\necho\nfoxtrot\n")
    os.close(fd)
    yield path
    try:
        os.remove(path)
    except Exception:
        pass


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database with schema."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    # Initialize schema
    from crossword.adapters.sqlite_persistence_adapter import SQLitePersistenceAdapter
    adapter = SQLitePersistenceAdapter(path)
    adapter.init_schema()

    yield path

    # Cleanup
    try:
        os.remove(path)
    except:
        pass


@pytest.fixture
def base_config(temp_db):
    """Minimal valid config with all required keys."""
    return {"dbfile": temp_db, "host": "localhost", "port": 5000}


class TestMakeApp:
    """Tests for make_app() wiring function"""

    def test_make_app_creates_container(self, base_config):
        """make_app() returns AppContainer with all use cases"""
        app = make_app(base_config)

        assert isinstance(app, AppContainer)
        assert app.puzzle_uc is not None
        assert app.word_uc is not None

    def test_make_app_initializes_puzzle_use_case(self, base_config):
        """Puzzle use case is wired correctly"""
        app = make_app(base_config)

        # Puzzle use case should have a persistence port
        assert app.puzzle_uc.persistence is not None

    def test_make_app_initializes_word_use_case(self, base_config):
        """Word use case is wired correctly"""
        app = make_app(base_config)

        # Word use case should have a word list port
        assert app.word_uc.word_list is not None

    def test_make_app_missing_dbfile(self):
        """make_app() raises error if dbfile not in config"""
        config = {}
        with pytest.raises(ValueError, match="dbfile.*required"):
            make_app(config)

    def test_make_app_invalid_dbfile(self):
        """make_app() raises error if database connection fails"""
        config = {"dbfile": "/nonexistent/path/to/database.db"}
        with pytest.raises(Exception):  # PersistenceError
            make_app(config)


class TestWordListWiring:
    """Tests for word list loading priority in make_app()"""

    def test_loads_word_dbfile(self, base_config, temp_word_db):
        """word_dbfile present → adapter populated from dedicated word DB"""
        app = make_app({**base_config, "word_dbfile": temp_word_db})
        words = app.word_uc.get_all_words()
        assert set(words) == {"apple", "banana", "cherry"}

    def test_word_dbfile_takes_priority_over_dbfile(self, base_config, temp_word_db):
        """word_dbfile wins over dbfile even when dbfile has a words table"""
        # base_config's dbfile (puzzle DB) has no words — word_dbfile should still be used
        app = make_app({**base_config, "word_dbfile": temp_word_db})
        assert set(app.word_uc.get_all_words()) == {"apple", "banana", "cherry"}

    def test_falls_back_to_word_file(self, base_config, temp_word_file):
        """No word_dbfile, word_file present → SQLite adapter loads from text file"""
        app = make_app({**base_config, "word_file": temp_word_file})
        assert set(app.word_uc.get_all_words()) == {"delta", "echo", "foxtrot"}

    def test_falls_back_to_dbfile(self, base_config):
        """No word_dbfile or word_file → adapter falls back to puzzle DB"""
        # Insert a word directly into the puzzle DB's words table
        conn = sqlite3.connect(base_config["dbfile"])
        conn.execute("CREATE TABLE IF NOT EXISTS words (word TEXT UNIQUE NOT NULL)")
        conn.execute("INSERT INTO words (word) VALUES ('golf')")
        conn.commit()
        conn.close()

        app = make_app(base_config)
        assert "golf" in app.word_uc.get_all_words()

    def test_empty_adapter_when_no_word_sources(self, base_config):
        """No word sources configured → adapter is empty, no exception raised"""
        app = make_app(base_config)
        assert app.word_uc.get_all_words() == []


class TestEndToEndWiring:
    """End-to-end tests with wired app"""

    def test_puzzle_crud_end_to_end(self, base_config):
        """Can create, load, delete puzzles via wired app"""
        app = make_app(base_config)

        # Create puzzle directly
        app.puzzle_uc.create_puzzle(1, "puzzle1", size=15)

        # Load puzzle
        puzzle = app.puzzle_uc.load_puzzle(1, "puzzle1")
        assert puzzle.n == 15

        # List puzzles
        puzzles = app.puzzle_uc.list_puzzles(1)
        assert "puzzle1" in puzzles

        # Delete puzzle
        app.puzzle_uc.delete_puzzle(1, "puzzle1")
        puzzles = app.puzzle_uc.list_puzzles(1)
        assert "puzzle1" not in puzzles

    def test_puzzle_set_cell_letter_end_to_end(self, base_config):
        """Can set cell letters in puzzle via wired app"""
        app = make_app(base_config)

        # Create puzzle
        app.puzzle_uc.create_puzzle(1, "puzzle1", size=15)

        # Set cell letter
        puzzle = app.puzzle_uc.set_cell_letter(1, "puzzle1", 2, 2, "A")
        assert puzzle.get_cell(2, 2) == "A"

        # Load again to verify persistence
        puzzle = app.puzzle_uc.load_puzzle(1, "puzzle1")
        assert puzzle.get_cell(2, 2) == "A"

    def test_merged_editor_flow_end_to_end(self, base_config):
        """A new puzzle can move through Grid and Puzzle modes and persist last mode."""
        app = make_app(base_config)

        app.puzzle_uc.create_puzzle(1, "merged", size=9)
        original = app.puzzle_uc.load_puzzle(1, "merged")
        assert original.last_mode == "grid"

        working_name = app.puzzle_uc.open_puzzle_for_editing(1, "merged")
        working = app.puzzle_uc.load_puzzle(1, working_name)
        assert working.last_mode == "grid"

        working = app.puzzle_uc.switch_to_puzzle_mode(1, working_name)
        assert working.last_mode == "puzzle"

        working = app.puzzle_uc.set_word_clue(
            1, working_name, 1, "across", "Computer science topic", text="ALGORITHM"
        )
        assert working.get_across_word(1).get_text() == "ALGORITHM"
        assert working.get_across_word(1).get_clue() == "Computer science topic"

        undone = app.puzzle_uc.undo_puzzle(1, working_name)
        assert undone.get_across_word(1).get_text().strip() == ""

        redone = app.puzzle_uc.redo_puzzle(1, working_name)
        assert redone.get_across_word(1).get_text() == "ALGORITHM"

        grid_changed = app.puzzle_uc.switch_to_grid_mode(1, working_name)
        assert grid_changed.last_mode == "grid"

        grid_changed = app.puzzle_uc.toggle_black_cell(1, working_name, 2, 2)
        assert grid_changed.is_black_cell(2, 2)

        grid_undone = app.puzzle_uc.undo_grid(1, working_name)
        assert not grid_undone.is_black_cell(2, 2)

        grid_redone = app.puzzle_uc.redo_grid(1, working_name)
        assert grid_redone.is_black_cell(2, 2)

        final_working = app.puzzle_uc.switch_to_puzzle_mode(1, working_name)
        assert final_working.last_mode == "puzzle"

        app.puzzle_uc.copy_puzzle(1, working_name, "merged")
        reopened = app.puzzle_uc.load_puzzle(1, "merged")
        assert reopened.last_mode == "puzzle"
        assert reopened.get_across_word(1).get_text() == "ALGORITHM"
        assert reopened.get_across_word(1).get_clue() == "Computer science topic"

    def test_late_grid_edit_recomputes_entries_end_to_end(self, base_config):
        """Late grid edits preserve letters, clear affected clues, and keep unaffected clues."""
        app = make_app(base_config)

        seeded = TestPuzzle.create_solved_atlantic_puzzle()
        seeded.enter_puzzle_mode()
        app.puzzle_uc.persistence.save_puzzle(1, "atlantic", seeded)

        working_name = app.puzzle_uc.open_puzzle_for_editing(1, "atlantic")
        app.puzzle_uc.switch_to_grid_mode(1, working_name)

        changed = app.puzzle_uc.toggle_black_cell(1, working_name, 4, 9)
        merged_word = changed.get_across_word(13)
        assert merged_word.get_text() == "REUNITED "
        assert merged_word.get_clue() is None
        assert changed.get_across_word(10).get_clue() == "Hit at the Comedy Cellar, say"

        puzzle_mode = app.puzzle_uc.switch_to_puzzle_mode(1, working_name)
        assert puzzle_mode.get_across_word(13).get_text() == "REUNITED "
        assert puzzle_mode.get_across_word(13).get_clue() is None
        assert puzzle_mode.last_mode == "puzzle"

        app.puzzle_uc.copy_puzzle(1, working_name, "atlantic")
        reloaded = app.puzzle_uc.load_puzzle(1, "atlantic")
        assert reloaded.last_mode == "puzzle"
        assert reloaded.get_across_word(13).get_text() == "REUNITED "

    def test_working_copy_discard_does_not_modify_saved_puzzle(self, base_config):
        """Deleting a working copy discards unsaved edits to the original puzzle."""
        app = make_app(base_config)

        app.puzzle_uc.create_puzzle(1, "discardme", size=9)
        original = app.puzzle_uc.load_puzzle(1, "discardme")
        assert original.title is None

        working_name = app.puzzle_uc.open_puzzle_for_editing(1, "discardme")
        app.puzzle_uc.set_puzzle_title(1, working_name, "Unsaved title")
        app.puzzle_uc.delete_puzzle(1, working_name)

        reloaded = app.puzzle_uc.load_puzzle(1, "discardme")
        assert reloaded.title is None

    def test_word_validation_end_to_end(self, base_config):
        """Can validate words via wired app"""
        app = make_app(base_config)

        # Validation works (with empty dictionary)
        result = app.word_uc.validate_word("HELLO")
        # Result depends on whether words are in DB, but should not raise
        assert isinstance(result, bool)

        # Get all words (should be empty or have words from DB)
        words = app.word_uc.get_all_words()
        assert isinstance(words, list)
