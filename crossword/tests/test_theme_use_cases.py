import pytest

from crossword.adapters.sqlite_theme_adapter import SQLiteThemeAdapter
from crossword.adapters.sqlite_grid_adapter import SQLiteGridAdapter
from crossword.use_cases.theme_use_cases import ThemeUseCases

USER = 1


@pytest.fixture
def uc():
    repo = SQLiteThemeAdapter(":memory:")
    return ThemeUseCases(repo, SQLiteGridAdapter(None))


def test_create_valid_palindrome(uc):
    t = uc.create_theme(USER, "Test", [5, 7, 7, 5])
    assert t.title == "Test"
    assert t.word_lengths == [5, 7, 7, 5]


def test_create_single_element_palindrome(uc):
    t = uc.create_theme(USER, "Test", [7])
    assert t.word_lengths == [7]


def test_create_rejects_non_palindrome(uc):
    with pytest.raises(ValueError, match="palindromic"):
        uc.create_theme(USER, "Bad", [5, 7])


def test_create_with_selected_words(uc):
    t = uc.create_theme(USER, "T", [5, 7, 5], selected_words=["CRANE", "PELICAN", "EGRET"])
    assert t.selected_words == ["CRANE", "PELICAN", "EGRET"]


def test_update_valid_palindrome(uc):
    uc.create_theme(USER, "T", [5, 5])
    t = uc.update_theme(USER, 1, word_lengths=[5, 7, 5])
    assert t.word_lengths == [5, 7, 5]


def test_update_rejects_non_palindrome(uc):
    uc.create_theme(USER, "T", [5, 5])
    with pytest.raises(ValueError, match="palindromic"):
        uc.update_theme(USER, 1, word_lengths=[5, 7])


def test_update_title_only_skips_palindrome_check(uc):
    uc.create_theme(USER, "Old", [5, 5])
    t = uc.update_theme(USER, 1, title="New")
    assert t.title == "New"


def test_update_missing_returns_none(uc):
    assert uc.update_theme(USER, 99, title="X") is None


def test_get_existing(uc):
    uc.create_theme(USER, "Birds", [5, 7, 7, 5])
    t = uc.get_theme(USER, 1)
    assert t is not None
    assert t.title == "Birds"


def test_get_missing_returns_none(uc):
    assert uc.get_theme(USER, 99) is None


def test_list_themes(uc):
    uc.create_theme(USER, "A", [5, 5])
    uc.create_theme(USER, "B", [7, 7])
    assert len(uc.list_themes(USER)) == 2


def test_delete(uc):
    uc.create_theme(USER, "Gone", [5, 5])
    assert uc.delete_theme(USER, 1) is True
    assert uc.get_theme(USER, 1) is None


def test_delete_missing_returns_false(uc):
    assert uc.delete_theme(USER, 99) is False


def test_add_words(uc):
    uc.create_theme(USER, "T", [5, 7, 5])
    t = uc.add_words(USER, 1, ["CRANE"])
    assert "CRANE" in t.selected_words


def test_remove_word(uc):
    uc.create_theme(USER, "T", [5, 5])
    uc.add_words(USER, 1, ["CRANE"])
    t = uc.remove_word(USER, 1, "CRANE")
    assert "CRANE" not in t.selected_words


def test_search_grids_returns_none_for_missing_theme(uc):
    assert uc.search_grids(USER, 99, 15) is None


def test_search_grids_returns_empty_list_when_no_db(uc):
    uc.create_theme(USER, "T", [5, 7, 7, 5])
    result = uc.search_grids(USER, 1, 15)
    assert result == []
