import pytest

from crossword.adapters.random_grid_generator_adapter import RandomGridGeneratorAdapter
from crossword.domain.grid_generator import GeneratorSettings


def _black_pct(grid):
    return len(grid.get_black_cells()) / (grid.n * grid.n)


def test_generates_grid_without_spec():
    grid = RandomGridGeneratorAdapter().generate(9)
    assert grid.n == 9
    assert _black_pct(grid) <= GeneratorSettings.BLACK_CELL_PERCENT_MAX


def test_generates_grid_with_spec_within_theme_black_limit():
    grid = RandomGridGeneratorAdapter().generate(15, [11, 15, 11])
    assert grid.n == 15
    assert _black_pct(grid) <= GeneratorSettings.THEME_BLACK_CELL_PERCENT_MAX


def test_unbuildable_spec_raises_runtime_error():
    with pytest.raises(RuntimeError, match="theme spec 5,7,5"):
        RandomGridGeneratorAdapter().generate(11, [5, 7, 5])
