import pytest

from crossword.adapters.sqlite_theme_adapter import SQLiteThemeAdapter


@pytest.fixture
def repo():
    return SQLiteThemeAdapter(":memory:")


def test_create_returns_theme(repo):
    theme = repo.create(1, "Birds of a Feather", [5, 7, 7, 5])
    assert theme.id == 1
    assert theme.title == "Birds of a Feather"
    assert theme.word_lengths == [5, 7, 7, 5]
    assert theme.selected_words == []


def test_ids_increment(repo):
    t1 = repo.create(1, "First", [5, 5])
    t2 = repo.create(1, "Second", [7, 7])
    assert t1.id == 1
    assert t2.id == 2


def test_get_existing(repo):
    repo.create(1, "Alpha", [5, 7, 5])
    theme = repo.get(1, 1)
    assert theme is not None
    assert theme.title == "Alpha"


def test_get_missing_returns_none(repo):
    assert repo.get(1, 99) is None


def test_get_wrong_user_returns_none(repo):
    repo.create(1, "Alpha", [5, 5])
    assert repo.get(2, 1) is None


def test_list_all(repo):
    repo.create(1, "A", [5, 5])
    repo.create(1, "B", [7, 7])
    assert len(repo.list_all(1)) == 2


def test_list_all_scoped_to_user(repo):
    repo.create(1, "A", [5, 5])
    repo.create(2, "B", [7, 7])
    assert len(repo.list_all(1)) == 1
    assert len(repo.list_all(2)) == 1


def test_update_title(repo):
    repo.create(1, "Old", [5, 5])
    updated = repo.update(1, 1, title="New")
    assert updated.title == "New"
    assert updated.word_lengths == [5, 5]


def test_update_word_lengths(repo):
    repo.create(1, "Theme", [5, 5])
    updated = repo.update(1, 1, word_lengths=[5, 7, 5])
    assert updated.word_lengths == [5, 7, 5]


def test_update_missing_returns_none(repo):
    assert repo.update(1, 99, title="X") is None


def test_delete(repo):
    repo.create(1, "Gone", [5, 5])
    assert repo.delete(1, 1) is True
    assert repo.get(1, 1) is None


def test_delete_missing_returns_false(repo):
    assert repo.delete(1, 99) is False


def test_add_word(repo):
    repo.create(1, "Theme", [5, 7, 5])
    theme = repo.add_word(1, 1, ["CRANE", "OSPREY"])
    assert "CRANE" in theme.selected_words


def test_add_word_skips_duplicates(repo):
    repo.create(1, "Theme", [5, 5])
    repo.add_word(1, 1, ["CRANE"])
    theme = repo.add_word(1, 1, ["CRANE", "HERON"])
    assert theme.selected_words.count("CRANE") == 1
    assert "HERON" in theme.selected_words


def test_remove_word(repo):
    repo.create(1, "Theme", [5, 5])
    repo.add_word(1, 1, ["CRANE", "HERON"])
    theme = repo.remove_word(1, 1, "CRANE")
    assert "CRANE" not in theme.selected_words
    assert "HERON" in theme.selected_words


def test_complete_theme(repo):
    repo.create(1, "Theme", [5, 7, 7, 5])
    repo.add_word(1, 1, ["CRANE", "PELICAN", "SPARROW", "EGRET"])
    theme = repo.get(1, 1)
    assert theme.complete is True


def test_complete_theme_wrong_order(repo):
    repo.create(1, "Theme", [5, 7, 7, 5])
    repo.add_word(1, 1, ["PELICAN", "CRANE", "SPARROW", "EGRET"])
    theme = repo.get(1, 1)
    assert theme.complete is False


def test_incomplete_theme(repo):
    repo.create(1, "Theme", [5, 7, 7, 5])
    repo.add_word(1, 1, ["CRANE"])
    theme = repo.get(1, 1)
    assert theme.complete is False
