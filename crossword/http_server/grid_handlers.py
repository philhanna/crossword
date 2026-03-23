"""
Grid handlers - CRUD operations on grids via HTTP.

Routes:
  GET    /api/grids              → list_grids
  POST   /api/grids              → create_grid
  POST   /api/grids/from-puzzle  → create_grid_from_puzzle
  GET    /api/grids/<name>       → load_grid
  DELETE /api/grids/<name>       → delete_grid
  POST   /api/grids/<name>/copy          → copy_grid
  POST   /api/grids/<name>/open          → open_grid_for_editing
  PUT    /api/grids/<name>/cells/<r>/<c>  → toggle_black_cell
  POST   /api/grids/<name>/rotate        → rotate_grid
  POST   /api/grids/<name>/undo          → undo_grid
  POST   /api/grids/<name>/redo          → redo_grid
  GET    /api/grids/<name>/preview       → get_grid_preview
  GET    /api/grids/<name>/stats         → get_grid_stats
"""

import logging
import traceback
from crossword.ports.persistence import PersistenceError

logger = logging.getLogger(__name__)


def _grid_response(grid):
    cells = [False] * (grid.n * grid.n)
    for r, c in grid.black_cells:
        cells[(r - 1) * grid.n + (c - 1)] = True
    return {
        "size": grid.n,
        "cells": cells,
        "can_undo": bool(grid.undo_stack),
        "can_redo": bool(grid.redo_stack),
    }


def handle_list_grids(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    List all grids for the current user.
    GET /api/grids
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        user_id = 1
        grids = app.grid_uc.list_grids(user_id)
        return {"grids": grids}
    except Exception as e:
        return {"error": str(e)}


def handle_create_grid(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Create a new grid.
    POST /api/grids
    Body: { "name": "grid1", "size": 15 }
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = body_params.get("name")
        size = body_params.get("size")

        if not name or not isinstance(name, str):
            return {"error": "Missing or invalid 'name'"}
        if not isinstance(size, int) or size < 1:
            return {"error": "Missing or invalid 'size' (must be integer >= 1)"}

        user_id = 1
        app.grid_uc.create_grid(user_id, name, size)

        # Load the grid to return full data for frontend rendering
        grid = app.grid_uc.load_grid(user_id, name)
        cells = [False] * (size * size)
        for r, c in grid.black_cells:
            cell_idx = (r - 1) * size + (c - 1)  # Convert 1-indexed (r,c) to 0-indexed flat index
            cells[cell_idx] = True

        return {
            "size": size,
            "cells": cells,
        }

    except ValueError as e:
        return {"error": str(e)}
    except PersistenceError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def handle_create_grid_from_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Create a new grid from the layout of an existing puzzle.
    POST /api/grids/from-puzzle
    Body: { "puzzle_name": "...", "grid_name": "..." }
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        puzzle_name = body_params.get("puzzle_name")
        grid_name = body_params.get("grid_name")

        if not puzzle_name or not isinstance(puzzle_name, str):
            return {"error": "Missing or invalid 'puzzle_name'"}
        if not grid_name or not isinstance(grid_name, str):
            return {"error": "Missing or invalid 'grid_name'"}

        user_id = 1
        grid = app.grid_uc.create_grid_from_puzzle(user_id, puzzle_name, grid_name)

        cells = [False] * (grid.n * grid.n)
        for r, c in grid.black_cells:
            cell_idx = (r - 1) * grid.n + (c - 1)
            cells[cell_idx] = True

        return {
            "name": grid_name,
            "size": grid.n,
            "cells": cells,
        }

    except ValueError as e:
        return {"error": str(e)}
    except PersistenceError:
        return {"error": f"Puzzle not found: {puzzle_name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_load_grid(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Load a grid by name.
    GET /api/grids/<name>
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        user_id = 1
        grid = app.grid_uc.load_grid(user_id, name)

        # Convert black_cells set to cells array for frontend
        cells = [False] * (grid.n * grid.n)
        for r, c in grid.black_cells:
            cell_idx = (r - 1) * grid.n + (c - 1)  # Convert 1-indexed (r,c) to 0-indexed flat index
            cells[cell_idx] = True

        return {
            "size": grid.n,
            "cells": cells,
        }

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_delete_grid(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Delete a grid by name.
    DELETE /api/grids/<name>
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        user_id = 1
        app.grid_uc.delete_grid(user_id, name)

        return {"status": "deleted", "name": name}

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_copy_grid(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Copy a grid to a new name.
    POST /api/grids/<name>/copy
    Body: { "new_name": "..." }
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        new_name = body_params.get("new_name")
        if not new_name or not isinstance(new_name, str):
            return {"error": "Missing or invalid 'new_name'"}

        user_id = 1
        grid = app.grid_uc.copy_grid(user_id, name, new_name)

        cells = [False] * (grid.n * grid.n)
        for r, c in grid.black_cells:
            cell_idx = (r - 1) * grid.n + (c - 1)
            cells[cell_idx] = True

        return {
            "name": new_name,
            "size": grid.n,
            "cells": cells,
        }

    except ValueError as e:
        return {"error": str(e)}
    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_open_grid_for_editing(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Open a grid for editing by creating a working copy.
    POST /api/grids/<name>/open
    Returns: { "original_name": "mygrid", "working_name": "__wc__a1b2c3d4" }
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        user_id = 1
        working_name = app.grid_uc.open_grid_for_editing(user_id, name)
        return {"original_name": name, "working_name": working_name}

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_toggle_black_cell(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Toggle a black cell in a grid.
    PUT /api/grids/<name>/cells/<r>/<c>
    Note: Frontend sends 0-indexed coordinates, grid expects 1-indexed
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if len(path_params) > 0 else None
        r = path_params[1] if len(path_params) > 1 else None
        c = path_params[2] if len(path_params) > 2 else None

        if not name or not r or not c:
            return {"error": "Missing name, r, or c"}

        try:
            r = int(r) + 1  # Convert 0-indexed to 1-indexed
            c = int(c) + 1  # Convert 0-indexed to 1-indexed
        except ValueError:
            return {"error": "r and c must be integers"}

        user_id = 1
        grid = app.grid_uc.toggle_black_cell(user_id, name, r, c)
        return _grid_response(grid)

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        print(f"ERROR in handle_toggle_black_cell: {e}")
        print(traceback.format_exc())
        return {"error": f"Toggle failed: {str(e)}"}


def handle_rotate_grid(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Rotate a grid 90 degrees counterclockwise.
    POST /api/grids/<name>/rotate
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        user_id = 1
        grid = app.grid_uc.rotate_grid(user_id, name)
        return _grid_response(grid)

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_undo_grid(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Undo the last operation on a grid.
    POST /api/grids/<name>/undo
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        user_id = 1
        grid = app.grid_uc.undo_grid(user_id, name)
        return _grid_response(grid)

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_redo_grid(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Redo the last undone operation on a grid.
    POST /api/grids/<name>/redo
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        user_id = 1
        grid = app.grid_uc.redo_grid(user_id, name)
        return _grid_response(grid)

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_get_grid_preview(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Return a scaled-down SVG thumbnail and summary heading for a grid.
    GET /api/grids/<name>/preview
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        user_id = 1
        return app.grid_uc.get_grid_preview(user_id, name)

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_get_grid_stats(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Return statistics and validation results for a grid.
    GET /api/grids/<name>/stats
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        user_id = 1
        return app.grid_uc.get_grid_stats(user_id, name)

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}
