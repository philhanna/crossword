"""
Unit tests for WordUseCases
"""

import pytest
from unittest.mock import Mock
from crossword.use_cases.word_use_cases import WordUseCases


@pytest.fixture
def mock_word_list():
    """Create a mock word list adapter"""
    return Mock()


@pytest.fixture
def word_uc(mock_word_list):
    """Create a WordUseCases instance with mock word list"""
    return WordUseCases(mock_word_list)


class TestWordUseCasesGetSuggestions:
    """Tests for get_suggestions"""

    def test_get_suggestions_with_wildcards(self, word_uc, mock_word_list):
        """Get suggestions using ? wildcards"""
        mock_word_list.get_matches.return_value = ["APPLE", "AMPLE"]

        result = word_uc.get_suggestions("?PPLE")

        # Should convert ? to . and add anchors
        mock_word_list.get_matches.assert_called_once()
        assert result == ["APPLE", "AMPLE"]

    def test_get_suggestions_with_regex(self, word_uc, mock_word_list):
        """Get suggestions using full regex pattern"""
        mock_word_list.get_matches.return_value = ["HELLO", "HALLO"]

        result = word_uc.get_suggestions("^H[AE]LLO$")

        mock_word_list.get_matches.assert_called_once()
        assert result == ["HELLO", "HALLO"]

    def test_get_suggestions_no_matches(self, word_uc, mock_word_list):
        """Get suggestions with no matches"""
        mock_word_list.get_matches.return_value = []

        result = word_uc.get_suggestions("ZZZZZZ")

        assert result == []

    def test_get_suggestions_invalid_regex(self, word_uc, mock_word_list):
        """Get suggestions with invalid regex"""
        mock_word_list.get_matches.side_effect = ValueError("Invalid regex")

        with pytest.raises(ValueError, match="Invalid pattern"):
            word_uc.get_suggestions("[invalid(regex")

    def test_get_suggestions_case_insensitive(self, word_uc, mock_word_list):
        """Suggestions work case-insensitively"""
        mock_word_list.get_matches.return_value = ["apple"]

        result = word_uc.get_suggestions("?PPLE")

        # Pattern should be converted case-insensitively
        assert result == ["apple"]

    def test_get_suggestions_dot_wildcard(self, word_uc, mock_word_list):
        """Get suggestions using . for wildcard (treated as regex)"""
        mock_word_list.get_matches.return_value = ["APPLE", "AMPLE", "ANGLE"]

        result = word_uc.get_suggestions(".PPLE")

        # . should be treated as regex any-char, passed to port
        assert result == ["APPLE", "AMPLE", "ANGLE"]


class TestWordUseCasesGetAllWords:
    """Tests for get_all_words"""

    def test_get_all_words_success(self, word_uc, mock_word_list):
        """Get all words from dictionary"""
        words = ["APPLE", "BANANA", "CHERRY"]
        mock_word_list.get_all_words.return_value = words

        result = word_uc.get_all_words()

        assert result == words
        mock_word_list.get_all_words.assert_called_once()

    def test_get_all_words_empty(self, word_uc, mock_word_list):
        """Get all words when dictionary is empty"""
        mock_word_list.get_all_words.return_value = []

        result = word_uc.get_all_words()

        assert result == []


class TestWordUseCasesValidateWord:
    """Tests for validate_word"""

    def test_validate_word_exists(self, word_uc, mock_word_list):
        """Validate word that exists"""
        mock_word_list.get_all_words.return_value = ["apple", "banana", "cherry"]

        result = word_uc.validate_word("APPLE")

        assert result is True

    def test_validate_word_exists_lowercase(self, word_uc, mock_word_list):
        """Validate word with lowercase input"""
        mock_word_list.get_all_words.return_value = ["apple", "banana", "cherry"]

        result = word_uc.validate_word("apple")

        assert result is True

    def test_validate_word_not_exists(self, word_uc, mock_word_list):
        """Validate word that doesn't exist"""
        mock_word_list.get_all_words.return_value = ["apple", "banana", "cherry"]

        result = word_uc.validate_word("zebra")

        assert result is False

    def test_validate_word_empty_string(self, word_uc, mock_word_list):
        """Validate empty string"""
        mock_word_list.get_all_words.return_value = ["apple"]

        result = word_uc.validate_word("")

        assert result is False

    def test_validate_word_none(self, word_uc, mock_word_list):
        """Validate None"""
        mock_word_list.get_all_words.return_value = ["apple"]

        result = word_uc.validate_word(None)

        assert result is False

    def test_validate_word_non_string(self, word_uc, mock_word_list):
        """Validate non-string input"""
        mock_word_list.get_all_words.return_value = ["apple"]

        result = word_uc.validate_word(123)

        assert result is False


class TestWordUseCasesPatternToRegex:
    """Tests for _pattern_to_regex helper"""

    def test_pattern_to_regex_with_wildcards(self, word_uc):
        """Convert ? pattern to regex"""
        pattern = "?PPLE"
        result = word_uc._pattern_to_regex(pattern)
        assert result == "^.PPLE$"

    def test_pattern_to_regex_full_wildcards(self, word_uc):
        """Convert all ? pattern"""
        pattern = "?????"
        result = word_uc._pattern_to_regex(pattern)
        assert result == "^.....$"

    def test_pattern_to_regex_with_regex_syntax(self, word_uc):
        """Detect and pass through regex pattern"""
        pattern = "^[A-Z]{5}$"
        result = word_uc._pattern_to_regex(pattern)
        assert result == pattern

    def test_pattern_to_regex_mixed_syntax(self, word_uc):
        """Pattern with dot is treated as regex"""
        pattern = ".PPLE"
        result = word_uc._pattern_to_regex(pattern)
        # Contains dot, so treated as regex, not converted
        assert result == pattern

    def test_pattern_to_regex_bracket_syntax(self, word_uc):
        """Pattern with brackets is treated as regex"""
        pattern = "[AE]PPLE"
        result = word_uc._pattern_to_regex(pattern)
        assert result == pattern

    def test_pattern_to_regex_pipe_syntax(self, word_uc):
        """Pattern with pipe is treated as regex"""
        pattern = "APPLE|AMPLE"
        result = word_uc._pattern_to_regex(pattern)
        assert result == pattern

    def test_pattern_to_regex_plus_syntax(self, word_uc):
        """Pattern with + is treated as regex"""
        pattern = "A+PPLE"
        result = word_uc._pattern_to_regex(pattern)
        assert result == pattern

    def test_pattern_to_regex_asterisk_syntax(self, word_uc):
        """Pattern with * is treated as regex"""
        pattern = "A*PPLE"
        result = word_uc._pattern_to_regex(pattern)
        assert result == pattern

    def test_pattern_to_regex_caret_syntax(self, word_uc):
        """Pattern with ^ is treated as regex"""
        pattern = "^APPLE"
        result = word_uc._pattern_to_regex(pattern)
        assert result == pattern

    def test_pattern_to_regex_paren_syntax(self, word_uc):
        """Pattern with parens is treated as regex"""
        pattern = "(AP)PLE"
        result = word_uc._pattern_to_regex(pattern)
        assert result == pattern
