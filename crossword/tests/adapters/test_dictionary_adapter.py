"""
Tests for SQLiteDictionaryAdapter - Word list adapter tests
"""

import pytest
from pathlib import Path
from crossword.adapters.sqlite_dictionary_adapter import SQLiteDictionaryAdapter

FIXTURE_WORDS = [
    'hello', 'world', 'python', 'test', 'apple', 'application',
    'cat', 'dog', 'bird', 'bear', 'books', 'book',
]


def make_adapter(words=None):
    adapter = SQLiteDictionaryAdapter()
    for w in (words or FIXTURE_WORDS):
        adapter._words_by_length.setdefault(len(w), []).append(w)
    return adapter


class TestSQLiteDictionaryAdapter:
    """Test suite for SQLiteDictionaryAdapter"""

    @pytest.fixture
    def adapter(self):
        return make_adapter()

    def test_get_all_words(self, adapter):
        words = adapter.get_all_words()
        assert len(words) == 12
        assert 'hello' in words
        assert words == sorted(words)

    def test_get_matches_exact_length(self, adapter):
        matches = adapter.get_matches("^.{4}$")
        assert 'test' in matches
        assert 'book' in matches
        assert 'hello' not in matches

    def test_get_matches_starting_letter(self, adapter):
        matches = adapter.get_matches("^a.*$")
        assert 'apple' in matches
        assert 'application' in matches
        assert 'hello' not in matches

    def test_get_matches_ending_letter(self, adapter):
        matches = adapter.get_matches("^.*e$")
        assert 'apple' in matches
        assert 'hello' not in matches

    def test_get_matches_contains_pattern(self, adapter):
        matches = adapter.get_matches("^.*app.*$")
        assert 'apple' in matches
        assert 'application' in matches
        assert 'hello' not in matches

    def test_get_matches_case_insensitive(self, adapter):
        adapter._words_by_length.setdefault(5, []).append('HELLO')
        matches = adapter.get_matches("^hello$")
        assert any(m.lower() == 'hello' for m in matches)

    def test_get_matches_no_results(self, adapter):
        matches = adapter.get_matches("^xyz$")
        assert matches == []

    def test_get_matches_invalid_pattern(self, adapter):
        with pytest.raises(ValueError):
            adapter.get_matches("[invalid(regex")

    def test_get_matches_with_length(self, adapter):
        matches = adapter.get_matches("^.*$", length=4)
        assert all(len(w) == 4 for w in matches)
        assert 'test' in matches
        assert 'book' in matches
        assert 'hello' not in matches

    def test_get_matches_with_length_no_results(self, adapter):
        assert adapter.get_matches("^.*$", length=99) == []

    def test_get_matches_with_length_and_pattern(self, adapter):
        matches = adapter.get_matches("^b.*$", length=4)
        assert 'bear' in matches   # 4 letters, starts with b
        assert 'book' in matches   # 4 letters, starts with b
        assert 'bird' in matches   # 4 letters, starts with b
        assert 'books' not in matches  # 5 letters, filtered by length

    def test_load_from_database(self):
        db_path = Path(__file__).resolve().parents[3] / "examples" / "words.db"
        if not db_path.exists():
            pytest.skip(f"words.db not found at {db_path}")

        adapter = SQLiteDictionaryAdapter()
        adapter.load_from_database(str(db_path))

        words = adapter.get_all_words()
        assert len(words) > 70000

    def test_word_pattern_search_crossword(self):
        db_path = Path(__file__).resolve().parents[3] / "examples" / "words.db"
        if not db_path.exists():
            pytest.skip(f"words.db not found at {db_path}")

        adapter = SQLiteDictionaryAdapter()
        adapter.load_from_database(str(db_path))

        matches = adapter.get_matches("^a.{4}$")
        assert len(matches) > 0
        assert all(len(w) == 5 for w in matches)
        assert all(w.startswith('a') for w in matches)

        matches = adapter.get_matches("^[aeiou].[aeiou].$")
        assert len(matches) > 0

    def test_load_from_ascii_file(self, tmp_path):
        word_file = tmp_path / "words.txt"
        word_file.write_text("Delta\necho\n\necho\nFoxtrot\n", encoding="ascii")

        adapter = SQLiteDictionaryAdapter()
        adapter.load_from_file(str(word_file))

        assert adapter.get_all_words() == ["delta", "echo", "foxtrot"]

    def test_load_from_non_ascii_file_raises(self, tmp_path):
        word_file = tmp_path / "words.txt"
        word_file.write_text("cafe\ncaf\u00e9\n", encoding="utf-8")

        adapter = SQLiteDictionaryAdapter()
        with pytest.raises(Exception, match="Failed to load words from file"):
            adapter.load_from_file(str(word_file))
