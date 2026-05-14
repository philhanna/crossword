# crossword.ports.grid_generator_port
from abc import ABC, abstractmethod

from crossword.domain.grid import Grid


class GridGeneratorPort(ABC):
    @abstractmethod
    def generate(self, n: int, spec: list[int] | None = None) -> Grid:
        """
        Return a valid crossword grid of size n×n.

        spec: optional list of theme-word lengths (palindromic); when provided
              and the adapter supports it, constrains the grid to match the
              exact Across slot counts for each length and forbids slots in the
              gaps between those lengths or above the maximum length.

        Raises:
            RuntimeError: If no grid can be produced for the given size.
        """
        pass
