# crossword.adapters.random_grid_generator_adapter
from crossword.domain.grid import Grid
from crossword.domain.grid_generator import GeneratorSettings, GridGenerator
from crossword.ports.grid_generator_port import GridGeneratorPort


class RandomGridGeneratorAdapter(GridGeneratorPort):
    def generate(self, n: int, spec: list[int] | None = None) -> Grid:
        if spec:
            generator = GridGenerator(n, spec=spec, max_black_pct=GeneratorSettings.THEME_BLACK_CELL_PERCENT_MAX)
        else:
            generator = GridGenerator(n)
        grid = generator.generate()
        if grid is None:
            if spec:
                raise RuntimeError(
                    f"Could not generate a grid matching theme spec {','.join(map(str, spec))}")
            raise RuntimeError("Grid generation failed: ran out of attempts")
        return grid
