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
        """Pattern with dot wildcard is anchored like a simple pattern"""
        pattern = ".PPLE"
        result = word_uc._pattern_to_regex(pattern)
        assert result == "^.PPLE$"

    def test_pattern_to_regex_bracket_syntax(self, word_uc):
        """Pattern with brackets gets anchored"""
        result = word_uc._pattern_to_regex("[AE]PPLE")
        assert result == "^[AE]PPLE$"

    def test_pattern_to_regex_pipe_syntax(self, word_uc):
        """Pattern with pipe gets anchored"""
        result = word_uc._pattern_to_regex("APPLE|AMPLE")
        assert result == "^APPLE|AMPLE$"

    def test_pattern_to_regex_plus_syntax(self, word_uc):
        """Pattern with + gets anchored"""
        result = word_uc._pattern_to_regex("A+PPLE")
        assert result == "^A+PPLE$"

    def test_pattern_to_regex_asterisk_syntax(self, word_uc):
        """Pattern with * gets anchored"""
        result = word_uc._pattern_to_regex("A*PPLE")
        assert result == "^A*PPLE$"

    def test_pattern_to_regex_caret_syntax(self, word_uc):
        """Pattern starting with ^ gets $ appended only"""
        result = word_uc._pattern_to_regex("^APPLE")
        assert result == "^APPLE$"

    def test_pattern_to_regex_paren_syntax(self, word_uc):
        """Pattern with parens gets anchored"""
        result = word_uc._pattern_to_regex("(AP)PLE")
        assert result == "^(AP)PLE$"

    def test_pattern_to_regex_constraint_pattern(self, word_uc):
        """Constraint patterns from word constraints get anchored for full-word matching"""
        result = word_uc._pattern_to_regex("G[^Q][^BGJL-NP-QTW-XZ][^DF-GJ-MQX][A-EH-JMOR-UWY][^DF-HJQX-Z]")
        assert result == "^G[^Q][^BGJL-NP-QTW-XZ][^DF-GJ-MQX][A-EH-JMOR-UWY][^DF-HJQX-Z]$"


def _make_mock_word(text, length, location, cells, crossing_words):
    """Build a mock Word with the given properties."""
    word = Mock()
    word.get_text.return_value = text
    word.length = length
    word.location = location
    word.cell_iterator.return_value = iter(cells)
    word.get_crossing_words.return_value = crossing_words
    return word


def _make_mock_crossing(text, location, cells):
    """Build a mock crossing Word."""
    cw = Mock()
    cw.get_text.return_value = text
    cw.location = location
    cw.cell_iterator.return_value = iter(cells)
    return cw


class TestWordUseCasesGetWordConstraints:
    """Tests for get_word_constraints"""

    def test_returns_required_keys(self, word_uc, mock_word_list):
        """Result contains word, length, crossers, pattern"""
        # 2-letter word at (1,1),(1,2)
        # crossing words: down at col 1 (cells (1,1)) and col 2 (cells (1,2))
        cw1 = _make_mock_crossing("AB", "1 down", [(1, 1), (2, 1)])
        cw2 = _make_mock_crossing("CD", "2 down", [(1, 2), (2, 2)])
        word = _make_mock_word("HI", 2, "1 across", [(1, 1), (1, 2)], [cw1, cw2])
        mock_word_list.get_matches.side_effect = [["AB", "AC"], ["CD"]]

        result = word_uc.get_word_constraints(word)

        assert "word" in result
        assert "length" in result
        assert "crossers" in result
        assert "pattern" in result

    def test_length_matches_word(self, word_uc, mock_word_list):
        """length field equals word.length"""
        cw1 = _make_mock_crossing("AB", "1 down", [(1, 1), (2, 1)])
        cw2 = _make_mock_crossing("CD", "2 down", [(1, 2), (2, 2)])
        word = _make_mock_word("HI", 2, "1 across", [(1, 1), (1, 2)], [cw1, cw2])
        mock_word_list.get_matches.side_effect = [["AB"], ["CD"]]

        result = word_uc.get_word_constraints(word)

        assert result["length"] == 2

    def test_blank_letters_shown_as_dots(self, word_uc, mock_word_list):
        """Spaces in word text are shown as dots in result"""
        cw1 = _make_mock_crossing("AB", "1 down", [(1, 1), (2, 1)])
        word = _make_mock_word(" ", 1, "1 across", [(1, 1)], [cw1])
        mock_word_list.get_matches.return_value = ["AB", "AC"]

        result = word_uc.get_word_constraints(word)

        assert result["word"] == "."

    def test_crossers_count_equals_word_length(self, word_uc, mock_word_list):
        """Number of crossers equals word length"""
        cw1 = _make_mock_crossing("AB", "1 down", [(1, 1), (2, 1)])
        cw2 = _make_mock_crossing("CD", "2 down", [(1, 2), (2, 2)])
        cw3 = _make_mock_crossing("EF", "3 down", [(1, 3), (2, 3)])
        word = _make_mock_word("CAT", 3, "1 across", [(1, 1), (1, 2), (1, 3)], [cw1, cw2, cw3])
        mock_word_list.get_matches.side_effect = [["AB"], ["CD"], ["EF"]]

        result = word_uc.get_word_constraints(word)

        assert len(result["crossers"]) == 3

    def test_crosser_pos_is_one_indexed(self, word_uc, mock_word_list):
        """crosser pos values are 1-indexed"""
        cw1 = _make_mock_crossing("AB", "1 down", [(1, 1), (2, 1)])
        cw2 = _make_mock_crossing("CD", "2 down", [(1, 2), (2, 2)])
        word = _make_mock_word("HI", 2, "1 across", [(1, 1), (1, 2)], [cw1, cw2])
        mock_word_list.get_matches.side_effect = [["AB"], ["CD"]]

        result = word_uc.get_word_constraints(word)

        assert result["crossers"][0]["pos"] == 1
        assert result["crossers"][1]["pos"] == 2

    def test_crossing_index_computed_correctly(self, word_uc, mock_word_list):
        """crossing_index is 1-indexed position in crossing word"""
        # Across word at row 2: cells (2,1),(2,2)
        # Crossing down word at col 1: cells (1,1),(2,1),(3,1) — crosses at index 2
        cw1 = _make_mock_crossing("ABC", "1 down", [(1, 1), (2, 1), (3, 1)])
        cw2 = _make_mock_crossing("XY", "5 down", [(1, 2), (2, 2)])
        word = _make_mock_word("HI", 2, "2 across", [(2, 1), (2, 2)], [cw1, cw2])
        mock_word_list.get_matches.side_effect = [["ABC"], ["XY"]]

        result = word_uc.get_word_constraints(word)

        assert result["crossers"][0]["crossing_index"] == 2

    def test_pattern_concatenates_regexps(self, word_uc, mock_word_list):
        """pattern is concatenation of all crosser regexps"""
        cw1 = _make_mock_crossing("A ", "1 down", [(1, 1), (2, 1)])
        cw2 = _make_mock_crossing("B ", "2 down", [(1, 2), (2, 2)])
        word = _make_mock_word("HI", 2, "1 across", [(1, 1), (1, 2)], [cw1, cw2])
        # Both crossing words yield single letters → single-letter regexps
        mock_word_list.get_matches.side_effect = [["AB", "AC"], ["BD", "BE"]]

        result = word_uc.get_word_constraints(word)

        # Pattern must equal the joined regexps of all crossers
        expected = "".join(c["regexp"] for c in result["crossers"])
        assert result["pattern"] == expected

    def test_no_dictionary_matches_falls_back_to_current_letter(self, word_uc, mock_word_list):
        """If no dictionary words match a crossing pattern, use the current letter"""
        cw1 = _make_mock_crossing("XYZ", "1 down", [(1, 1), (2, 1), (3, 1)])
        word = _make_mock_word("A", 1, "1 across", [(1, 1)], [cw1])
        mock_word_list.get_matches.return_value = []  # nothing matches

        result = word_uc.get_word_constraints(word)

        assert result["crossers"][0]["regexp"] == "A"
        assert result["crossers"][0]["choices"] == 1

    def test_all_blank_crossing_matches_all_letters(self, word_uc, mock_word_list):
        """An all-blank crossing word matches many words → broad constraint"""
        cw1 = _make_mock_crossing("  ", "1 down", [(1, 1), (2, 1)])
        cw2 = _make_mock_crossing("  ", "2 down", [(1, 2), (2, 2)])
        word = _make_mock_word("H ", 2, "1 across", [(1, 1), (1, 2)], [cw1, cw2])
        # Many matches with varied first letters
        mock_word_list.get_matches.side_effect = [
            ["AB", "CB", "EB"],  # letters A, C, E at index 1
            [],
        ]

        result = word_uc.get_word_constraints(word)

        assert result["crossers"][0]["choices"] == 3
        assert "A" in result["crossers"][0]["regexp"] or "[" in result["crossers"][0]["regexp"]
