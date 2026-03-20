"""
Tests for DictionaryAdapter - Word list adapter tests
"""

import pytest
from pathlib import Path
from crossword.adapters.dictionary_adapter import DictionaryAdapter


class TestDictionaryAdapter:
    """Test suite for DictionaryAdapter"""

    @pytest.fixture
    def adapter(self):
        """Create a dictionary adapter with test words"""
        adapter = DictionaryAdapter()
        adapter._words = {
            'hello', 'world', 'python', 'test', 'apple', 'application',
            'cat', 'dog', 'bird', 'bear', 'books', 'book'
        }
        return adapter

    def test_get_all_words(self, adapter):
        """Test getting all words"""
        words = adapter.get_all_words()
        assert len(words) == 12
        assert 'hello' in words
        assert words == sorted(words)

    def test_get_matches_exact_length(self, adapter):
        """Test pattern matching for exact word lengths"""
        # Match 4-letter words
        matches = adapter.get_matches("^.{4}$")
        assert 'test' in matches
        assert 'book' in matches
        assert 'hello' not in matches

    def test_get_matches_starting_letter(self, adapter):
        """Test pattern matching by starting letter"""
        # Words starting with 'a'
        matches = adapter.get_matches("^a")
        assert 'apple' in matches
        assert 'application' in matches
        assert 'hello' not in matches

    def test_get_matches_ending_letter(self, adapter):
        """Test pattern matching by ending letter"""
        # Words ending with 'e'
        matches = adapter.get_matches("e$")
        assert 'apple' in matches
        assert 'hello' not in matches

    def test_get_matches_contains_pattern(self, adapter):
        """Test pattern matching for contained patterns"""
        # Words containing 'app'
        matches = adapter.get_matches("app")
        assert 'apple' in matches
        assert 'application' in matches
        assert 'hello' not in matches

    def test_get_matches_case_insensitive(self, adapter):
        """Test that matching is case-insensitive"""
        adapter._words.add('HELLO')
        matches = adapter.get_matches("^hello$")
        assert any(m.lower() == 'hello' for m in matches)

    def test_get_matches_no_results(self, adapter):
        """Test pattern with no matches"""
        matches = adapter.get_matches("^xyz$")
        assert matches == []

    def test_get_matches_invalid_pattern(self, adapter):
        """Test that invalid regex raises ValueError"""
        with pytest.raises(ValueError):
            adapter.get_matches("[invalid(regex")

    def test_load_from_file(self):
        """Test loading words from a text file"""
        # Use the test words file
        test_file = Path(__file__).parent.parent / "data" / "words.txt"
        if not test_file.exists():
            pytest.skip(f"Test words file not found at {test_file}")

        adapter = DictionaryAdapter()
        adapter.load_from_file(str(test_file))

        # Should have loaded many words
        words = adapter.get_all_words()
        assert len(words) > 0

        # Check that some expected words are there
        assert 'aaa' in words or 'aaagames' in words

    def test_load_from_database(self):
        """Test loading words from the samples.db database"""
        db_path = Path(__file__).parent.parent.parent / "samples.db"
        if not db_path.exists():
            pytest.skip(f"samples.db not found at {db_path}")

        adapter = DictionaryAdapter()
        adapter.load_from_database(str(db_path))

        # Should have loaded 72,106 words
        words = adapter.get_all_words()
        assert len(words) > 70000

    def test_word_pattern_search_crossword(self):
        """Test realistic crossword pattern search"""
        db_path = Path(__file__).parent.parent.parent / "samples.db"
        if not db_path.exists():
            pytest.skip(f"samples.db not found at {db_path}")

        adapter = DictionaryAdapter()
        adapter.load_from_database(str(db_path))

        # Pattern: 5-letter words starting with A
        matches = adapter.get_matches("^a.{3}$")
        assert len(matches) > 0
        assert all(len(w) == 5 for w in matches)
        assert all(w.startswith('a') for w in matches)

        # Pattern: 4-letter words with vowels at positions 1 and 3
        matches = adapter.get_matches("^[aeiou].[aeiou].$")
        assert len(matches) > 0
