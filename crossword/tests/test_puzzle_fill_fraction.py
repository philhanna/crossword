"""
Unit tests for Puzzle.fill_fraction()
"""

from crossword import Grid, Puzzle
from crossword.tests import TestPuzzle


def test_fill_fraction_all_blank_is_zero():
    """A freshly created puzzle has no letters -> 0.0"""
    puzzle = TestPuzzle.create_puzzle()
    assert puzzle.fill_fraction() == 0.0


def test_fill_fraction_fully_filled_is_one():
    """Every white cell carries a letter -> 1.0"""
    puzzle = TestPuzzle.create_solved_atlantic_puzzle()
    assert puzzle.fill_fraction() == 1.0


def test_fill_fraction_half_filled():
    """Filling half the white cells -> ~0.5"""
    puzzle = TestPuzzle.create_puzzle()
    white = [(r, c) for (r, c), v in puzzle.cells.items() if v != Puzzle.BLACK]
    half = len(white) // 2
    for (r, c) in white[:half]:
        puzzle.set_cell(r, c, "A")
    assert puzzle.fill_fraction() == half / len(white)


def test_fill_fraction_all_black_is_zero():
    """A grid with no white cells -> 0.0 (no division by zero)"""
    n = 3
    grid = Grid(n)
    for r in range(1, n + 1):
        for c in range(1, n + 1):
            grid.add_black_cell(r, c)
    puzzle = Puzzle(grid)
    assert puzzle.fill_fraction() == 0.0
