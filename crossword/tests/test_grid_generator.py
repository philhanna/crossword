import pytest

from crossword.domain.grid import Grid
from crossword.domain.grid_generator import (
    BLACK,
    UNKNOWN,
    WHITE,
    GeneratorSettings,
    GridGenerator,
    _all_white_cells_connected,
    _count_black_cells,
    _generate_legal_rows,
    _line_runs_are_legal,
    _long_spans,
    _no_forced_short_white_runs,
    _no_long_word_stack,
    _partial_columns_feasible,
    _place_middle_row,
    _place_row_pair,
    _clear_row_pair,
    _clear_middle_row,
    _spans_overlap,
    _validate_grid,
)


# ---------------------------------------------------------------------------
# _generate_legal_rows
# ---------------------------------------------------------------------------

class TestGenerateLegalRows:

    def test_all_rows_have_valid_runs(self):
        for row in _generate_legal_rows(9, require_palindrome=False):
            assert _line_runs_are_legal(row)

    def test_palindrome_rows_are_palindromes(self):
        for row in _generate_legal_rows(9, require_palindrome=True):
            assert row == row[::-1]

    def test_non_palindrome_rows_include_non_palindromes(self):
        rows = _generate_legal_rows(9, require_palindrome=False)
        assert any(row != row[::-1] for row in rows)

    def test_all_rows_are_length_n(self):
        n = 11
        for row in _generate_legal_rows(n, require_palindrome=False):
            assert len(row) == n

    def test_rows_contain_only_black_and_white(self):
        for row in _generate_legal_rows(9, require_palindrome=False):
            assert all(ch in (BLACK, WHITE) for ch in row)

    def test_palindrome_rows_are_subset_of_all_rows(self):
        all_rows = set(_generate_legal_rows(9, require_palindrome=False))
        palindromes = set(_generate_legal_rows(9, require_palindrome=True))
        assert palindromes.issubset(all_rows)


# ---------------------------------------------------------------------------
# GridGenerator construction
# ---------------------------------------------------------------------------

class TestGridGeneratorInit:

    def test_valid_init(self):
        gen = GridGenerator(9)
        assert gen.n == 9

    def test_even_size_raises(self):
        with pytest.raises(ValueError):
            GridGenerator(10)

    def test_too_small_raises(self):
        with pytest.raises(ValueError):
            GridGenerator(7)

    def test_invalid_black_pct_raises(self):
        with pytest.raises(ValueError):
            GridGenerator(9, min_black_pct=0.5, max_black_pct=0.2)

    def test_negative_min_black_pct_raises(self):
        with pytest.raises(ValueError):
            GridGenerator(9, min_black_pct=-0.1, max_black_pct=0.2)

    def test_max_black_pct_above_one_raises(self):
        with pytest.raises(ValueError):
            GridGenerator(9, min_black_pct=0.1, max_black_pct=1.1)

    def test_top_rows_populated(self):
        gen = GridGenerator(9)
        assert len(gen.top_rows) > 0

    def test_middle_rows_are_palindromes(self):
        gen = GridGenerator(9)
        for row in gen.middle_rows:
            assert row == row[::-1]

    def test_seed_produces_deterministic_output(self):
        g1 = GridGenerator(9, seed=1).generate()
        g2 = GridGenerator(9, seed=1).generate()
        assert g1.get_black_cells() == g2.get_black_cells()

    def test_different_seeds_usually_differ(self):
        g1 = GridGenerator(9, seed=1).generate()
        g2 = GridGenerator(9, seed=2).generate()
        # Not guaranteed but almost certain for any reasonable seed pair
        assert g1.get_black_cells() != g2.get_black_cells()


# ---------------------------------------------------------------------------
# GridGenerator.generate()
# ---------------------------------------------------------------------------

class TestGridGeneratorGenerate:

    def test_returns_grid(self):
        gen = GridGenerator(9, seed=42)
        result = gen.generate()
        assert isinstance(result, Grid)

    def test_returns_correct_size(self):
        gen = GridGenerator(9, seed=42)
        grid = gen.generate()
        assert grid.n == 9

    def test_grid_has_rotational_symmetry(self):
        gen = GridGenerator(9, seed=42)
        grid = gen.generate()
        n = grid.n
        black = set(grid.get_black_cells())
        for r, c in black:
            assert (n + 1 - r, n + 1 - c) in black

    def test_grid_black_cell_pct_in_range(self):
        gen = GridGenerator(9, seed=42)
        grid = gen.generate()
        total = gen.n * gen.n
        pct = len(grid.get_black_cells()) / total
        assert gen.min_black_pct <= pct <= gen.max_black_pct

    def test_returns_none_when_impossible(self):
        # Force max_attempts=1 and a tiny node budget so search always bails
        gen = GridGenerator(9, seed=0, max_attempts=1)
        gen.max_nodes = 1
        result = gen.generate()
        assert result is None

    def test_size_11(self):
        gen = GridGenerator(11, seed=7)
        result = gen.generate()
        assert result is not None
        assert result.n == 11


# ---------------------------------------------------------------------------
# Grid placement helpers
# ---------------------------------------------------------------------------

class TestPlaceAndClearHelpers:

    def _blank(self, n):
        return [[UNKNOWN] * n for _ in range(n)]

    def test_place_row_pair_sets_top_and_bottom(self):
        grid = self._blank(9)
        row = "...#....#"
        _place_row_pair(grid, 0, row)
        assert "".join(grid[0]) == row
        assert "".join(grid[8]) == row[::-1]

    def test_place_row_pair_maintains_symmetry(self):
        grid = self._blank(9)
        row = "...#.#..."
        _place_row_pair(grid, 1, row)
        n = 9
        for c in range(n):
            assert grid[1][c] == grid[n - 2][n - 1 - c]

    def test_clear_row_pair_resets_to_unknown(self):
        grid = self._blank(9)
        _place_row_pair(grid, 0, "...#....#")
        _clear_row_pair(grid, 0)
        assert all(grid[0][c] == UNKNOWN for c in range(9))
        assert all(grid[8][c] == UNKNOWN for c in range(9))

    def test_place_middle_row(self):
        grid = self._blank(9)
        row = "...#.#..."
        _place_middle_row(grid, row)
        assert "".join(grid[4]) == row

    def test_clear_middle_row(self):
        grid = self._blank(9)
        _place_middle_row(grid, "...#.#...")
        _clear_middle_row(grid)
        assert all(grid[4][c] == UNKNOWN for c in range(9))


# ---------------------------------------------------------------------------
# _count_black_cells
# ---------------------------------------------------------------------------

class TestCountBlackCells:

    def test_empty_grid(self):
        grid = [[WHITE] * 3 for _ in range(3)]
        assert _count_black_cells(grid) == 0

    def test_all_black(self):
        grid = [[BLACK] * 3 for _ in range(3)]
        assert _count_black_cells(grid) == 9

    def test_mixed(self):
        grid = [[BLACK, WHITE, BLACK], [WHITE, WHITE, WHITE]]
        assert _count_black_cells(grid) == 2


# ---------------------------------------------------------------------------
# _no_forced_short_white_runs
# ---------------------------------------------------------------------------

class TestNoForcedShortWhiteRuns:

    def test_all_white_ok(self):
        assert _no_forced_short_white_runs(list(WHITE * 9))

    def test_short_run_at_start(self):
        line = list(WHITE + WHITE + BLACK + WHITE * 6)
        assert not _no_forced_short_white_runs(line)

    def test_short_run_in_middle(self):
        line = list(WHITE * 3 + BLACK + WHITE + BLACK + WHITE * 3)
        assert not _no_forced_short_white_runs(line)

    def test_unknown_keeps_run_open(self):
        # WW? — run is not closed, should pass
        line = [WHITE, WHITE, UNKNOWN]
        assert _no_forced_short_white_runs(line)

    def test_valid_runs(self):
        line = list(WHITE * 3 + BLACK + WHITE * 4)
        assert _no_forced_short_white_runs(line)


# ---------------------------------------------------------------------------
# _line_runs_are_legal
# ---------------------------------------------------------------------------

class TestLineRunsAreLegal:

    def test_all_white_legal(self):
        assert _line_runs_are_legal(WHITE * 9)

    def test_run_of_two_illegal(self):
        assert not _line_runs_are_legal(WHITE * 2 + BLACK + WHITE * 6)

    def test_run_of_one_illegal(self):
        assert not _line_runs_are_legal(BLACK + WHITE + BLACK + WHITE * 6)

    def test_runs_of_three_or_more_legal(self):
        assert _line_runs_are_legal(WHITE * 3 + BLACK + WHITE * 5)

    def test_all_black_legal(self):
        assert _line_runs_are_legal(BLACK * 9)


# ---------------------------------------------------------------------------
# _all_white_cells_connected
# ---------------------------------------------------------------------------

class TestAllWhiteCellsConnected:

    def test_single_connected_region(self):
        grid = [
            [WHITE, WHITE, WHITE],
            [WHITE, BLACK, WHITE],
            [WHITE, WHITE, WHITE],
        ]
        assert _all_white_cells_connected(grid)

    def test_disconnected_regions(self):
        grid = [
            [WHITE, BLACK, WHITE],
            [BLACK, BLACK, BLACK],
            [WHITE, BLACK, WHITE],
        ]
        assert not _all_white_cells_connected(grid)

    def test_no_white_cells(self):
        grid = [[BLACK] * 3 for _ in range(3)]
        assert not _all_white_cells_connected(grid)

    def test_single_white_cell(self):
        grid = [[BLACK, BLACK], [BLACK, WHITE]]
        assert _all_white_cells_connected(grid)


# ---------------------------------------------------------------------------
# _long_spans / _spans_overlap / _no_long_word_stack
# ---------------------------------------------------------------------------

class TestLongSpans:

    def test_no_long_spans(self):
        assert _long_spans(WHITE * 5 + BLACK + WHITE * 4) == []

    def test_one_long_span(self):
        spans = _long_spans(WHITE * 8 + BLACK)
        assert len(spans) == 1
        assert spans[0] == (0, 7)

    def test_multiple_long_spans(self):
        line = WHITE * 8 + BLACK + WHITE * 8
        spans = _long_spans(line)
        assert len(spans) == 2


class TestSpansOverlap:

    def test_overlap(self):
        assert _spans_overlap([(0, 5)], [(3, 8)])

    def test_no_overlap(self):
        assert not _spans_overlap([(0, 3)], [(5, 8)])

    def test_touching_but_not_overlapping(self):
        assert not _spans_overlap([(0, 3)], [(4, 8)])

    def test_contained(self):
        assert _spans_overlap([(1, 6)], [(2, 4)])

    def test_empty_spans(self):
        assert not _spans_overlap([], [(0, 5)])


class TestNoLongWordStack:

    def test_both_short_ok(self):
        line = WHITE * 5 + BLACK + WHITE * 3
        assert _no_long_word_stack(line, line)

    def test_stacked_long_words(self):
        long_line = WHITE * 9
        assert not _no_long_word_stack(long_line, long_line)

    def test_long_vs_short_ok(self):
        long_line = WHITE * 9
        short_line = WHITE * 5 + BLACK + WHITE * 3
        assert _no_long_word_stack(long_line, short_line)


# ---------------------------------------------------------------------------
# _partial_columns_feasible
# ---------------------------------------------------------------------------

class TestPartialColumnsFeasible:

    def test_feasible_grid(self):
        grid = [[WHITE] * 9 for _ in range(9)]
        assert _partial_columns_feasible(grid)

    def test_infeasible_due_to_short_column_run(self):
        grid = [[WHITE] * 3 for _ in range(3)]
        grid[0][1] = BLACK
        grid[2][1] = BLACK
        # column 1: W B W — run of 1 on each side
        assert not _partial_columns_feasible(grid)


# ---------------------------------------------------------------------------
# _validate_grid
# ---------------------------------------------------------------------------

class TestValidateGrid:

    def _make_valid_9x9(self):
        """A hand-crafted 9x9 grid that passes all validation rules."""
        W, B = WHITE, BLACK
        return [
            [W, W, W, B, W, W, W, W, W],
            [W, W, W, B, W, W, W, W, W],
            [W, W, W, B, W, W, W, W, W],
            [B, B, B, B, W, W, W, W, W],
            [W, W, W, W, W, W, W, W, W],
            [W, W, W, W, W, B, B, B, B],
            [W, W, W, W, W, B, W, W, W],
            [W, W, W, W, W, B, W, W, W],
            [W, W, W, W, W, B, W, W, W],
        ]

    def test_valid_grid_passes(self):
        gen = GridGenerator(9, seed=42)
        grid = gen.generate()
        n = grid.n
        raw = []
        black_set = set(grid.get_black_cells())
        for r in range(1, n + 1):
            row = []
            for c in range(1, n + 1):
                row.append(BLACK if (r, c) in black_set else WHITE)
            raw.append(row)
        ok, reason = _validate_grid(raw)
        assert ok, reason

    def test_symmetry_violation(self):
        W, B = WHITE, BLACK
        grid = [[W] * 9 for _ in range(9)]
        grid[0][0] = B  # no symmetric partner
        ok, reason = _validate_grid(grid)
        assert not ok
        assert "symmetry" in reason

    def test_no_white_cells(self):
        grid = [[BLACK] * 9 for _ in range(9)]
        ok, reason = _validate_grid(grid)
        assert not ok
        assert "white" in reason

    def test_illegal_across_run(self):
        W, B = WHITE, BLACK
        # Build a symmetric grid where row 0 has a run of 2
        grid = [[W] * 9 for _ in range(9)]
        grid[0][0] = B
        grid[0][3] = B
        grid[8][8] = B
        grid[8][5] = B
        ok, reason = _validate_grid(grid)
        assert not ok

    def test_disconnected_white_cells(self):
        W, B = WHITE, BLACK
        # All black except two disconnected white patches, symmetric
        grid = [[B] * 9 for _ in range(9)]
        for c in range(9):
            grid[0][c] = W
            grid[8][c] = W
        ok, reason = _validate_grid(grid)
        assert not ok
