from crossword.domain.theme import GridPattern, Theme


def test_complete_when_all_slots_filled():
    t = Theme(1, "T", [5, 7, 7, 5], ["CRANE", "PELICAN", "SPARROW", "EGRET"])
    assert t.complete is True


def test_incomplete_when_wrong_count():
    t = Theme(1, "T", [5, 7, 7, 5], ["CRANE"])
    assert t.complete is False


def test_incomplete_when_word_wrong_length():
    t = Theme(1, "T", [5, 7, 7, 5], ["CRANE", "PELICAN", "SPARROW", "EGRE"])
    assert t.complete is False


def test_incomplete_when_empty():
    t = Theme(1, "T", [5, 7, 7, 5])
    assert t.complete is False


def test_gridpattern_fields():
    gp = GridPattern(name="nyt150101.txt", size=15, grid_text=".")
    assert gp.name == "nyt150101.txt"
    assert gp.size == 15
    assert gp.grid_text == "."
