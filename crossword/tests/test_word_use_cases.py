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

    def test_input_pattern_overrides_cached_letter_in_crossing_lookup(self, word_uc, mock_word_list):
        """Live input letters are used when building crossing patterns."""
        cw1 = _make_mock_crossing("A ", "1 down", [(1, 1), (2, 1)])
        word = _make_mock_word(" ", 1, "1 across", [(1, 1)], [cw1])
        mock_word_list.get_matches.return_value = ["BA"]

        result = word_uc.get_word_constraints(word, input_pattern="B")

        mock_word_list.get_matches.assert_called_once_with("^B.$", length=cw1.length)
        assert result["word"] == "B"
        assert result["crossers"][0]["letter"] == "B"
        assert result["crossers"][0]["crossing_text"] == "B."

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

    def test_crosser_includes_letter_freq(self, word_uc, mock_word_list):
        """Each crosser includes letter_freq dict"""
        cw1 = _make_mock_crossing("AB", "1 down", [(1, 1), (2, 1)])
        word = _make_mock_word("H", 1, "1 across", [(1, 1)], [cw1])
        mock_word_list.get_matches.return_value = ["ab", "ac", "ab"]

        result = word_uc.get_word_constraints(word)

        assert "letter_freq" in result["crossers"][0]

    def test_letter_freq_counts_letters_at_crossing_index(self, word_uc, mock_word_list):
        """letter_freq tallies letters at crossing_index across matching words"""
        # across word at row 1: cells (1,1),(1,2)
        # crossing down word at col 1: cells (1,1),(2,1),(3,1) — crossing_index=1
        cw1 = _make_mock_crossing("ABC", "1 down", [(1, 1), (2, 1), (3, 1)])
        word = _make_mock_word("H ", 2, "1 across", [(1, 1), (1, 2)],
                               [cw1, _make_mock_crossing("X", "2 down", [(1, 2)])])
        mock_word_list.get_matches.side_effect = [
            ["abc", "axy", "bcd"],  # A appears 2x, B appears 1x at index 0
            ["xy"],
        ]

        result = word_uc.get_word_constraints(word)

        freq = result["crossers"][0]["letter_freq"]
        assert freq.get("A") == 2
        assert freq.get("B") == 1


class TestWordUseCasesGetRankedSuggestions:
    """Tests for get_ranked_suggestions"""

    def test_input_pattern_updates_crossing_constraints_before_ranking(self, word_uc, mock_word_list):
        """Ranked suggestions use live input, not the word's cached text."""
        cw1 = _make_mock_crossing("  ", "1 down", [(1, 1), (2, 1)])
        word = _make_mock_word(" ", 1, "1 across", [(1, 1)], [cw1])
        mock_word_list.get_matches.side_effect = [
            ["ab", "ac"],
            ["a"],
        ]

        result = word_uc.get_ranked_suggestions(word, input_pattern="A")

        first_call = mock_word_list.get_matches.call_args_list[0]
        assert first_call.args[0] == "^A.$"
        assert first_call.kwargs["length"] == cw1.length
        assert result == [{"word": "a", "score": 2}]

    def test_ranks_higher_scoring_candidate_first(self, word_uc, mock_word_list):
        """Candidate whose letters appear more in crossing words ranks first"""
        # 2-letter word; crossers: col 1 prefers E (10x), col 2 prefers R (8x)
        cw1 = _make_mock_crossing("AB", "1 down", [(1, 1), (2, 1)])
        cw2 = _make_mock_crossing("CD", "2 down", [(1, 2), (2, 2)])
        word = _make_mock_word("  ", 2, "1 across", [(1, 1), (1, 2)], [cw1, cw2])
        mock_word_list.get_matches.side_effect = [
            # crosser 1: E appears 10x, A appears 2x at index 0
            ["eb", "eb", "eb", "eb", "eb", "eb", "eb", "eb", "eb", "eb", "ab", "ab"],
            # crosser 2: R appears 8x, D appears 1x at index 0
            ["ra", "ra", "ra", "ra", "ra", "ra", "ra", "ra", "da"],
            # candidates matching pattern
            ["er", "ad"],
        ]

        result = word_uc.get_ranked_suggestions(word)

        assert result[0]["word"] == "er"   # E(10)+R(8)=18
        assert result[1]["word"] == "ad"   # A(2)+D(1)=3

    def test_returns_word_and_score_keys(self, word_uc, mock_word_list):
        """Each result dict has 'word' and 'score' keys"""
        cw1 = _make_mock_crossing("AB", "1 down", [(1, 1), (2, 1)])
        word = _make_mock_word(" ", 1, "1 across", [(1, 1)], [cw1])
        mock_word_list.get_matches.side_effect = [["ab", "cb"], ["ab"]]

        result = word_uc.get_ranked_suggestions(word)

        assert len(result) == 1
        assert "word" in result[0]
        assert "score" in result[0]

    def test_no_candidates_returns_empty_list(self, word_uc, mock_word_list):
        """Returns empty list when no candidates match the pattern"""
        cw1 = _make_mock_crossing("AB", "1 down", [(1, 1), (2, 1)])
        word = _make_mock_word(" ", 1, "1 across", [(1, 1)], [cw1])
        mock_word_list.get_matches.side_effect = [["ab"], []]

        result = word_uc.get_ranked_suggestions(word)

        assert result == []

    def test_all_blank_crossers_scores_zero(self, word_uc, mock_word_list):
        """When crossing words are all blank, all candidates score 0 but are still returned"""
        cw1 = _make_mock_crossing("  ", "1 down", [(1, 1), (2, 1)])
        word = _make_mock_word(" ", 1, "1 across", [(1, 1)], [cw1])
        mock_word_list.get_matches.side_effect = [
            [],        # crossing word matches nothing → letter_freq is empty
            ["a", "b", "c"],  # candidates
        ]

        result = word_uc.get_ranked_suggestions(word)

        assert len(result) == 3
        assert all(item["score"] == 0 for item in result)
