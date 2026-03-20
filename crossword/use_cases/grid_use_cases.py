"""
Grid use cases - CRUD operations and transformations on grids.

Public interface:
  create_grid(user_id, name, size) -> None
  load_grid(user_id, name) -> Grid
  delete_grid(user_id, name) -> None
  list_grids(user_id) -> list[str]
  toggle_black_cell(user_id, name, r, c) -> Grid
  rotate_grid(user_id, name) -> Grid
  undo_grid(user_id, name) -> Grid
  redo_grid(user_id, name) -> Grid
"""

from crossword import Grid
from crossword.ports.persistence import PersistencePort, PersistenceError


class GridUseCases:
    """
    Orchestrates grid operations via the persistence port.

    Constructor injection: takes a PersistencePort instance.
    No framework dependencies, single-threaded.
    """

    def __init__(self, persistence: PersistencePort):
        self.persistence = persistence

    def create_grid(self, user_id: int, name: str, size: int) -> None:
        """
        Create a new grid of the specified size and save it.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid
            size: Size of the grid (n x n)

        Raises:
            PersistenceError: If save fails
            ValueError: If size is invalid
        """
        if size < 1:
            raise ValueError(f"Grid size must be at least 1, got {size}")
        grid = Grid(size)
        self.persistence.save_grid(user_id, name, grid)

    def load_grid(self, user_id: int, name: str) -> Grid:
        """
        Load a grid from persistent storage.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Returns:
            Grid object

        Raises:
            PersistenceError: If grid not found or loading fails
        """
        return self.persistence.load_grid(user_id, name)

    def delete_grid(self, user_id: int, name: str) -> None:
        """
        Delete a grid from persistent storage.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Raises:
            PersistenceError: If grid not found or deletion fails
        """
        self.persistence.delete_grid(user_id, name)

    def list_grids(self, user_id: int) -> list[str]:
        """
        List all grid names owned by the user.

        Args:
            user_id: The user who owns the grids

        Returns:
            List of grid names, sorted most recent first

        Raises:
            PersistenceError: If listing fails
        """
        return self.persistence.list_grids(user_id)

    def toggle_black_cell(self, user_id: int, name: str, r: int, c: int) -> Grid:
        """
        Toggle a cell between black and white in a grid, saving the change.

        If the cell is black, it becomes white. If white, it becomes black.
        Also toggles the symmetric cell (180-degree rotation).

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid
            r: Row (1-indexed)
            c: Column (1-indexed)

        Returns:
            Updated Grid object

        Raises:
            PersistenceError: If load/save fails
        """
        grid = self.persistence.load_grid(user_id, name)

        if grid.is_black_cell(r, c):
            grid.remove_black_cell(r, c)
        else:
            grid.add_black_cell(r, c)

        self.persistence.save_grid(user_id, name, grid)
        return grid

    def rotate_grid(self, user_id: int, name: str) -> Grid:
        """
        Rotate a grid 90 degrees counterclockwise and save the change.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Returns:
            Updated Grid object

        Raises:
            PersistenceError: If load/save fails
        """
        grid = self.persistence.load_grid(user_id, name)
        grid.rotate()
        self.persistence.save_grid(user_id, name, grid)
        return grid

    def undo_grid(self, user_id: int, name: str) -> Grid:
        """
        Undo the last operation on a grid.

        Only affects black cell operations (add/remove), not rotations.
        If nothing to undo, does nothing.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Returns:
            Updated Grid object

        Raises:
            PersistenceError: If load/save fails
        """
        grid = self.persistence.load_grid(user_id, name)

        if grid.undo_stack:
            r, c = grid.undo_stack.pop()
            grid.redo_stack.append((r, c))

            # Undoing a black cell operation: toggle the cell
            if grid.is_black_cell(r, c):
                grid.remove_black_cell(r, c)
            else:
                grid.add_black_cell(r, c)

        self.persistence.save_grid(user_id, name, grid)
        return grid

    def redo_grid(self, user_id: int, name: str) -> Grid:
        """
        Redo the last undone operation on a grid.

        If nothing to redo, does nothing.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Returns:
            Updated Grid object

        Raises:
            PersistenceError: If load/save fails
        """
        grid = self.persistence.load_grid(user_id, name)

        if grid.redo_stack:
            r, c = grid.redo_stack.pop()
            grid.undo_stack.append((r, c))

            # Redoing: toggle the cell
            if grid.is_black_cell(r, c):
                grid.remove_black_cell(r, c)
            else:
                grid.add_black_cell(r, c)

        self.persistence.save_grid(user_id, name, grid)
        return grid
