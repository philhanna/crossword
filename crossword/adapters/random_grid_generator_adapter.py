# crossword.adapters.random_grid_generator_adapter
from crossword.domain.grid import Grid
from crossword.domain.grid_generator import GridGenerator
from crossword.ports.grid_generator_port import GridGeneratorPort


class RandomGridGeneratorAdapter(GridGeneratorPort):
    def generate(self, n: int) -> Grid:
        grid = GridGenerator(n).generate()
        if grid is None:
            raise RuntimeError("Grid generation failed: ran out of attempts")
        return grid
