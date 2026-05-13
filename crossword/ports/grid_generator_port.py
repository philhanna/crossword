# crossword.ports.grid_generator_port
from abc import ABC, abstractmethod

from crossword.domain.grid import Grid


class GridGeneratorPort(ABC):
    @abstractmethod
    def generate(self, n: int) -> Grid:
        """
        Return a valid crossword grid of size n×n.

        Raises:
            RuntimeError: If no grid can be produced for the given size.
        """
        pass
