"""
Grid use cases - CRUD operations and transformations on grids.

Public interface:
  create_grid(user_id, name, size) -> None
  load_grid(user_id, name) -> Grid
  delete_grid(user_id, name) -> None
  list_grids(user_id) -> list[str]
  copy_grid(user_id, source_name, new_name) -> Grid
  open_grid_for_editing(user_id, name) -> str
  toggle_black_cell(user_id, name, r, c) -> Grid
  rotate_grid(user_id, name) -> Grid
  undo_grid(user_id, name) -> Grid
  redo_grid(user_id, name) -> Grid
  create_grid_from_puzzle(user_id, puzzle_name, grid_name) -> Grid
  get_grid_preview(user_id, name) -> dict
  get_grid_stats(user_id, name) -> dict
"""

import uuid

from crossword import Grid, GridToSVG
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

    def open_grid_for_editing(self, user_id: int, name: str) -> str:
        """
        Open a grid for editing by creating a working copy.

        The working copy is a snapshot of the grid at the time of opening.
        All edits should target the working copy name. On Save, copy the
        working copy back over the original. On Close, delete the working copy.

        Args:
            user_id: The user who owns this grid
            name: Name of the grid to open

        Returns:
            working_name: The name of the working copy (e.g. '__wc__a1b2c3d4')

        Raises:
            PersistenceError: If grid not found or save fails
        """
        working_name = f"__wc__{uuid.uuid4().hex[:8]}"
        grid = self.persistence.load_grid(user_id, name)
        grid.undo_stack = []
        grid.redo_stack = []
        self.persistence.save_grid(user_id, working_name, grid)
        return working_name

    def copy_grid(self, user_id: int, source_name: str, new_name: str) -> Grid:
        """
        Copy a grid to a new name.

        Args:
            user_id: The user who owns the grid
            source_name: Name of the grid to copy
            new_name: Name for the copy

        Returns:
            The copied Grid object

        Raises:
            PersistenceError: If source not found or save fails
            ValueError: If new_name is empty
        """
        if not new_name or not new_name.strip():
            raise ValueError("new_name must not be empty")
        grid = self.persistence.load_grid(user_id, source_name)
        grid.undo_stack = []
        grid.redo_stack = []
        self.persistence.save_grid(user_id, new_name, grid)
        return grid

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
        print(f"undo_grid: undo_stack={grid.undo_stack}  redo_stack={grid.redo_stack}")
        grid.undo()
        print(f"undo_grid: undo_stack={grid.undo_stack}  redo_stack={grid.redo_stack}")
        self.persistence.save_grid(user_id, name, grid)
        return grid

    def create_grid_from_puzzle(self, user_id: int, puzzle_name: str, grid_name: str) -> Grid:
        """
        Create a new grid by copying the grid layout from an existing puzzle.

        The black cell pattern is copied from the puzzle's grid.
        The undo/redo stacks are cleared on the new grid.

        Args:
            user_id: The user who owns the puzzle
            puzzle_name: Name of the puzzle to copy the grid from
            grid_name: Name to save the new grid under

        Returns:
            The new Grid object

        Raises:
            PersistenceError: If puzzle not found or save fails
            ValueError: If grid_name is empty
        """
        if not grid_name or not grid_name.strip():
            raise ValueError("grid_name must not be empty")
        puzzle = self.persistence.load_puzzle(user_id, puzzle_name)
        grid = puzzle.grid
        grid.undo_stack = []
        grid.redo_stack = []
        self.persistence.save_grid(user_id, grid_name, grid)
        return grid

    def get_grid_preview(self, user_id: int, name: str) -> dict:
        """
        Return a scaled-down SVG and summary heading for a grid.

        Used by the chooser to display a thumbnail for each grid.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Returns:
            Dict with keys: name, heading, width, svgstr

        Raises:
            PersistenceError: If grid not found
        """
        grid = self.persistence.load_grid(user_id, name)
        scale = 0.75
        svg = GridToSVG(grid, scale=scale)
        width = (svg.boxsize * grid.n + 32) * scale
        svgstr = svg.generate_xml()

        heading_parts = [f"{grid.get_word_count()} words"]
        wlens = grid.get_word_lengths()
        for wlen in sorted(wlens.keys(), reverse=True)[:2]:
            total = len(wlens[wlen]['alist']) + len(wlens[wlen]['dlist'])
            heading_parts.append(f"{wlen}-letter: {total}")
        heading = f"{name} ({', '.join(heading_parts)})"

        return {
            "name": name,
            "heading": heading,
            "width": width,
            "svgstr": svgstr,
        }

    def get_grid_stats(self, user_id: int, name: str) -> dict:
        """
        Return statistics and validation results for a grid.

        Args:
            user_id: The user who owns this grid
            name: Name/identifier for the grid

        Returns:
            Dict with keys: valid, errors, size, wordcount, blockcount,
            wordlengths

        Raises:
            PersistenceError: If grid not found
        """
        grid = self.persistence.load_grid(user_id, name)
        return grid.get_statistics()

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
        print(f"redo_grid: undo_stack={grid.undo_stack}  redo_stack={grid.redo_stack}")
        grid.redo()
        print(f"redo_grid: undo_stack={grid.undo_stack}  redo_stack={grid.redo_stack}")
        self.persistence.save_grid(user_id, name, grid)
        return grid
