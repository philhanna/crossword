"""
Tests for FlatFileWordListAdapter - flat-file word list adapter tests.
"""

import pytest

from crossword.adapters.flat_file_word_list_adapter import FlatFileWordListAdapter

FIXTURE_WORDS = [
    "hello", "world", "python", "test", "apple", "application",
    "cat", "dog", "bird", "bear", "books", "book",
]


def make_adapter(words=None):
    adapter = FlatFileWordListAdapter()
    for w in (words or FIXTURE_WORDS):
        adapter._words_by_length.setdefault(len(w), []).append(w)
    return adapter


class TestFlatFileWordListAdapter:
    """Test suite for FlatFileWordListAdapter."""

    @pytest.fixture
    def adapter(self):
        return make_adapter()

    def test_get_all_words(self, adapter):
        words = adapter.get_all_words()
        assert len(words) == 12
        assert "hello" in words
        assert words == sorted(words)

    def test_get_matches_exact_length(self, adapter):
        matches = adapter.get_matches("^.{4}$")
        assert "test" in matches
        assert "book" in matches
        assert "hello" not in matches

    def test_get_matches_starting_letter(self, adapter):
        matches = adapter.get_matches("^a.*$")
        assert "apple" in matches
        assert "application" in matches
        assert "hello" not in matches

    def test_get_matches_case_insensitive(self, adapter):
        adapter._words_by_length.setdefault(5, []).append("HELLO")
        matches = adapter.get_matches("^hello$")
        assert any(m.lower() == "hello" for m in matches)

    def test_get_matches_invalid_pattern(self, adapter):
        with pytest.raises(ValueError):
            adapter.get_matches("[invalid(regex")

    def test_get_matches_with_length(self, adapter):
        matches = adapter.get_matches("^.*$", length=4)
        assert all(len(w) == 4 for w in matches)
        assert "test" in matches
        assert "book" in matches
        assert "hello" not in matches

    def test_get_matches_with_length_no_results(self, adapter):
        assert adapter.get_matches("^.*$", length=99) == []

    def test_get_matches_with_length_and_pattern(self, adapter):
        matches = adapter.get_matches("^b.*$", length=4)
        assert "bear" in matches   # 4 letters, starts with b
        assert "book" in matches   # 4 letters, starts with b
        assert "bird" in matches   # 4 letters, starts with b
        assert "books" not in matches  # 5 letters, filtered by length

    def test_load_from_ascii_file(self, tmp_path):
        word_file = tmp_path / "words.txt"
        word_file.write_text("Delta\necho\n\necho\nFoxtrot\n", encoding="ascii")

        adapter = FlatFileWordListAdapter(str(word_file))

        assert adapter.get_all_words() == ["delta", "echo", "foxtrot"]

    def test_load_from_non_ascii_file_raises(self, tmp_path):
        word_file = tmp_path / "words.txt"
        word_file.write_text("cafe\ncaf\u00e9\n", encoding="utf-8")

        adapter = FlatFileWordListAdapter()
        with pytest.raises(Exception, match="Failed to load words from file"):
            adapter.load_from_file(str(word_file))
