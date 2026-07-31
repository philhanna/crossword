from crossword.domain.word_similarity import find_duplicate, is_near_duplicate


class TestIsNearDuplicate:

    def test_exact_match_is_a_duplicate(self):
        assert is_near_duplicate("CAT", "CAT")

    def test_exact_match_is_case_insensitive(self):
        assert is_near_duplicate("cat", "CAT")

    def test_plain_plural(self):
        assert is_near_duplicate("CAT", "CATS")
        assert is_near_duplicate("CATS", "CAT")

    def test_es_plural(self):
        assert is_near_duplicate("BOX", "BOXES")
        assert is_near_duplicate("BOXES", "BOX")

    def test_ies_plural(self):
        assert is_near_duplicate("CITY", "CITIES")
        assert is_near_duplicate("CITIES", "CITY")

    def test_y_after_vowel_is_not_ies_plural(self):
        # "toy" pluralizes as "toys", not "toies"
        assert is_near_duplicate("TOY", "TOYS")
        assert not is_near_duplicate("TOY", "TOIES")

    def test_ves_plural_for_f(self):
        assert is_near_duplicate("WOLF", "WOLVES")
        assert is_near_duplicate("WOLVES", "WOLF")

    def test_ves_plural_for_fe(self):
        assert is_near_duplicate("KNIFE", "KNIVES")
        assert is_near_duplicate("KNIVES", "KNIFE")

    def test_unrelated_words_are_not_duplicates(self):
        assert not is_near_duplicate("CAT", "DOG")
        assert not is_near_duplicate("CAT", "CATE")

    def test_similar_length_words_are_not_duplicates(self):
        assert not is_near_duplicate("CARE", "CORE")


class TestFindDuplicate:

    def test_returns_matching_word(self):
        assert find_duplicate("CATS", ["DOG", "CAT", "BIRD"]) == "CAT"

    def test_returns_none_when_no_conflict(self):
        assert find_duplicate("CATS", ["DOG", "BIRD"]) is None

    def test_returns_none_for_empty_list(self):
        assert find_duplicate("CATS", []) is None

    def test_is_case_insensitive(self):
        assert find_duplicate("cats", ["cat"]) == "cat"
