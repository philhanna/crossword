"""
Unit tests for CompareUseCases
"""

import copy
import subprocess
import sys

import pytest
from unittest.mock import Mock

from crossword import Grid, Puzzle
from crossword.adapters.acrosslite_import_adapter import AcrossLiteImportAdapter
from crossword.adapters.xd_export_adapter import XdExportAdapter
from crossword.ports.persistence_port import PersistenceError
import crossword.tests as helpers
from crossword.use_cases.compare_use_cases import CompareUseCases, PuzzleCompareError
from crossword.use_cases.import_use_cases import ImportUseCases
from crossword.use_cases.puzzle_source import PuzzleSource


def db(name):
    return PuzzleSource(PuzzleSource.DB, name)


def file(path):
    return PuzzleSource(PuzzleSource.FILE, str(path))


@pytest.fixture
def puzzles():
    """A dict standing in for the database."""
    return {
        "a": helpers.TestPuzzle.create_solved_atlantic_puzzle(),
        "b": helpers.TestPuzzle.create_solved_atlantic_puzzle(),
    }


@pytest.fixture
def uc(puzzles):
    persistence = Mock()

    def load(user_id, name):
        if name not in puzzles:
            raise PersistenceError(f"Puzzle {name!r} not found")
        return puzzles[name]

    persistence.load_puzzle.side_effect = load
    import_uc = ImportUseCases(persistence, AcrossLiteImportAdapter())
    return CompareUseCases(persistence, import_uc)


def changed(diff):
    """The +/- lines, without the file header lines."""
    return [x for x in diff if x[0] in "+-" and not x.startswith(("+++", "---"))]


def test_identical_puzzles_have_no_differences(uc):
    assert uc.compare_puzzles(1, db("a"), db("b")) == []


def test_changed_clue(uc, puzzles):
    old = puzzles["b"].get_clue(1, "A")
    puzzles["b"].set_clue(1, "A", "A new clue")
    diff = changed(uc.compare_puzzles(1, db("a"), db("b")))
    assert diff == [f"-1A DAB  {old}", "+1A DAB  A new clue"]


def test_changed_answer(uc, puzzles):
    puzzles["b"].set_text(1, "A", "DUB", check_duplicates=False)
    diff = changed(uc.compare_puzzles(1, db("a"), db("b")))
    assert len(diff) >= 2
    assert diff[0].startswith("-1A DAB")
    assert any(x.startswith("+1A DUB") for x in diff)


def test_changed_title(uc, puzzles):
    puzzles["b"].title = "Something else"
    diff = changed(uc.compare_puzzles(1, db("a"), db("b")))
    assert len(diff) == 2
    assert diff[1] == "+Title: Something else"


def test_changes_are_in_order_across_before_down(uc, puzzles):
    puzzles["b"].set_clue(1, "D", "Down change")
    puzzles["b"].set_clue(1, "A", "Across change")
    diff = changed(uc.compare_puzzles(1, db("a"), db("b")))
    plus = [x for x in diff if x.startswith("+")]
    assert plus == ["+1A DAB  Across change", "+1D DAD  Down change"] or \
        plus[0].endswith("Across change") and plus[1].endswith("Down change")


def test_old_and_new_lines_are_paired(uc, puzzles):
    puzzles["b"].title = "Something else"
    puzzles["b"].set_clue(1, "A", "Across change")
    diff = uc.compare_puzzles(1, db("a"), db("b"))
    assert [x[0] for x in diff] == ["-", "+", "-", "+"]
    assert diff[2][1:].split()[0] == diff[3][1:].split()[0] == "1A"


def test_leading_and_trailing_spaces_in_clue_ignored(uc, puzzles):
    clue = puzzles["b"].get_clue(1, "A")
    puzzles["b"].set_clue(1, "A", f"  {clue} ")
    assert uc.compare_puzzles(1, db("a"), db("b")) == []


def test_case_difference_counts(uc, puzzles):
    clue = puzzles["b"].get_clue(1, "A")
    puzzles["b"].set_clue(1, "A", clue.upper())
    assert len(changed(uc.compare_puzzles(1, db("a"), db("b")))) == 2


def test_locks_are_ignored(uc, puzzles):
    puzzles["b"].set_locked(1, "A", True)
    assert uc.compare_puzzles(1, db("a"), db("b")) == []


def test_blank_squares_shown_as_dots_and_missing_clue_blank(puzzles):
    grid = Grid(5)
    puzzle = Puzzle(grid)
    puzzle.enter_puzzle_mode()
    lines = CompareUseCases.puzzle_lines(puzzle)
    assert lines[2] == "1A ....."


def test_different_sizes_raise(uc, puzzles):
    puzzles["b"] = Puzzle(Grid(5))
    with pytest.raises(PuzzleCompareError, match="sizes differ"):
        uc.compare_puzzles(1, db("a"), db("b"))


def test_different_black_squares_raise(uc, puzzles):
    n = puzzles["a"].n
    grid = Grid(n)
    grid.add_black_cell(1, 1)
    puzzles["b"] = Puzzle(grid)
    with pytest.raises(PuzzleCompareError, match="Black squares differ"):
        uc.compare_puzzles(1, db("a"), db("b"))


def test_unknown_database_name_raises(uc):
    with pytest.raises(PuzzleCompareError, match="Cannot load nope"):
        uc.compare_puzzles(1, db("a"), db("nope"))


def test_missing_file_raises(uc, tmp_path):
    with pytest.raises(PuzzleCompareError, match="Cannot load"):
        uc.compare_puzzles(1, db("a"), file(tmp_path / "missing.xd"))


def test_database_puzzle_against_xd_file(uc, puzzles, tmp_path):
    path = tmp_path / "a.xd"
    path.write_text(XdExportAdapter().export_puzzle_to_xd(puzzles["a"]), encoding="utf-8")
    diff = uc.compare_puzzles(1, db("a"), file(path))
    # The format may not carry everything, but the words must match.
    assert [x for x in changed(diff) if x[1:2].isdigit() and not x[1:].startswith("Title")] == []


def test_parse_source():
    assert PuzzleSource.parse("My puzzle") == db("My puzzle")
    for name in ("x.txt", "x.PUZ", "x.ipuz", "x.xd", "x.xml"):
        assert PuzzleSource.parse(name).kind == PuzzleSource.FILE


def test_script_exit_codes(tmp_path):
    result = subprocess.run(
        [sys.executable, "tools/user/compare_puzzles.py",
         str(tmp_path / "a.xd"), str(tmp_path / "b.xd")],
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert "Cannot load" in result.stderr


# ---- Saved versions (NAME@N) ---------------------------------------------


def make_versioned(uc, versions, no_content=()):
    """
    Give puzzle "v" a history. `versions` is a list of puzzles, oldest first.
    Row ids start at 100; rows whose index is in `no_content` keep no snapshot.
    """
    rows, contents = [], {}
    for i, puzzle in enumerate(versions):
        hid = 100 + i
        has = i not in no_content
        rows.append({"id": hid, "state": "draft", "has_content": has,
                     "comment": f"save {i}", "changed_at": f"2026-01-0{i + 1}T00:00:00"})
        contents[hid] = puzzle.to_json() if has else None
    p = uc.persistence
    p.get_puzzle_state_history.side_effect = (
        lambda user_id, name: rows if name == "v" else None)
    p.get_puzzle_state_history_content.side_effect = (
        lambda user_id, name, hid: contents.get(hid))


def clue_versions(*clues):
    """Puzzles that differ only in the clue of 1 Across."""
    out = []
    for clue in clues:
        puzzle = helpers.TestPuzzle.create_solved_atlantic_puzzle()
        puzzle.set_clue(1, "A", clue)
        out.append(puzzle)
    return out


@pytest.mark.parametrize("text, name, version", [
    ("My Puzzle", "My Puzzle", None),
    ("My Puzzle@3", "My Puzzle", 3),
    ("My Puzzle@-1", "My Puzzle", -1),
    ("My Puzzle@0", "My Puzzle", 0),
    ("Fri @ 5", "Fri @ 5", None),
    ("a@b", "a@b", None),
    ("foo.xd@3", "foo.xd", 3),
])
def test_parse_version(text, name, version):
    assert PuzzleSource.parse(text) == PuzzleSource(PuzzleSource.DB, name, version)


def test_file_source_has_no_version():
    assert PuzzleSource.parse("p@2.xd") == PuzzleSource(PuzzleSource.FILE, "p@2.xd")


def test_previous_version_against_live(uc):
    make_versioned(uc, clue_versions("one", "two", "three"))
    uc.persistence.load_puzzle.side_effect = lambda u, n: clue_versions("three")[0]
    diff = uc.compare_puzzles(1, PuzzleSource.parse("v@-1"), db("v"))
    assert diff == ["-1A DAB  two", "+1A DAB  three"]


def test_absolute_and_newest_versions(uc):
    make_versioned(uc, clue_versions("one", "two", "three"))
    assert uc.compare_puzzles(1, PuzzleSource.parse("v@1"), PuzzleSource.parse("v@3")) == [
        "-1A DAB  one", "+1A DAB  three"]
    assert uc.compare_puzzles(1, PuzzleSource.parse("v@0"), PuzzleSource.parse("v@3")) == []


def test_versions_without_content_are_skipped(uc):
    make_versioned(uc, clue_versions("one", "two", "three"), no_content={1})
    versions = uc.list_versions(1, "v")
    assert [(v["number"], v["back"], v["id"]) for v in versions] == [(1, -1, 100), (2, 0, 102)]
    diff = uc.compare_puzzles(1, PuzzleSource.parse("v@-1"), PuzzleSource.parse("v@0"))
    assert diff == ["-1A DAB  one", "+1A DAB  three"]


@pytest.mark.parametrize("ref", ["v@4", "v@-3", "v@-9"])
def test_version_out_of_range_raises(uc, ref):
    make_versioned(uc, clue_versions("one", "two", "three"))
    with pytest.raises(PuzzleCompareError, match="no version"):
        uc.compare_puzzles(1, PuzzleSource.parse(ref), db("v"))


def test_puzzle_with_no_versions_raises(uc):
    make_versioned(uc, clue_versions("one"), no_content={0})
    with pytest.raises(PuzzleCompareError, match="no saved versions"):
        uc.compare_puzzles(1, PuzzleSource.parse("v@-1"), db("v"))


def test_version_of_unknown_puzzle_raises(uc):
    make_versioned(uc, clue_versions("one"))
    with pytest.raises(PuzzleCompareError, match="Cannot load"):
        uc.compare_puzzles(1, PuzzleSource.parse("nope@1"), db("v"))
