"""
Puzzle handlers - CRUD operations on puzzles via HTTP.

Routes:
  GET    /api/puzzles              → list_puzzles
  POST   /api/puzzles              → create_puzzle
  GET    /api/puzzles/<name>       → load_puzzle
  DELETE /api/puzzles/<name>       → delete_puzzle
  POST   /api/puzzles/<name>/copy          → copy_puzzle
  POST   /api/puzzles/<name>/open          → open_puzzle_for_editing
  POST   /api/puzzles/<name>/mode/grid     → switch_to_grid_mode
  POST   /api/puzzles/<name>/mode/puzzle   → switch_to_puzzle_mode
  PUT    /api/puzzles/<name>/title         → set_puzzle_title
  PUT    /api/puzzles/<name>/grid/cells/<r>/<c>  → toggle_black_cell
  POST   /api/puzzles/<name>/grid/rotate         → rotate_grid
  POST   /api/puzzles/<name>/grid/generate       → generate_grid
  POST   /api/puzzles/<name>/grid/undo           → undo_grid
  POST   /api/puzzles/<name>/grid/redo           → redo_grid
  POST   /api/puzzles/<name>/words/<seq>/<direction>/reset  → reset_word
  PUT    /api/puzzles/<name>/cells/<r>/<c>  → set_cell_letter
  GET    /api/puzzles/<name>/words/<seq>/<direction>  → get_word_at
  PUT    /api/puzzles/<name>/words/<seq>/<direction>  → set_word_clue
  POST   /api/puzzles/<name>/undo          → undo_puzzle
  POST   /api/puzzles/<name>/redo          → redo_puzzle
  GET    /api/puzzles/<name>/preview       → get_puzzle_preview
  GET    /api/puzzles/<name>/stats         → get_puzzle_stats
"""

import logging
from crossword.ports.persistence_port import PersistenceError

logger = logging.getLogger(__name__)


def _puzzle_response(puzzle):
    """Build the standard puzzle API response dict from a Puzzle object."""
    grid_cells = [False] * (puzzle.n * puzzle.n)
    for r, c in puzzle.black_cells:
        cell_idx = (r - 1) * puzzle.n + (c - 1)
        grid_cells[cell_idx] = True

    puzzle_cells = {}
    words = []

    for seq, word in sorted(puzzle.across_words.items()):
        cells_list = list(word.cell_iterator())
        words.append({
            "seq": seq,
            "direction": "across",
            "answer": word.get_text(),
            "clue": word.get_clue() or "",
            "cells": cells_list,
        })
        for idx, (r, c) in enumerate(cells_list):
            cell_idx = (r - 1) * puzzle.n + (c - 1)
            if cell_idx not in puzzle_cells:
                puzzle_cells[cell_idx] = {}
            letter = word.get_text()[idx] if word.get_text() and idx < len(word.get_text()) else None
            if letter and letter.strip():
                puzzle_cells[cell_idx]["letter"] = letter
            if idx == 0:
                puzzle_cells[cell_idx]["number"] = seq

    for seq, word in sorted(puzzle.down_words.items()):
        cells_list = list(word.cell_iterator())
        words.append({
            "seq": seq,
            "direction": "down",
            "answer": word.get_text(),
            "clue": word.get_clue() or "",
            "cells": cells_list,
        })
        for idx, (r, c) in enumerate(cells_list):
            cell_idx = (r - 1) * puzzle.n + (c - 1)
            if cell_idx not in puzzle_cells:
                puzzle_cells[cell_idx] = {}
            letter = word.get_text()[idx] if word.get_text() and idx < len(word.get_text()) else None
            if letter and letter.strip():
                puzzle_cells[cell_idx].setdefault("letter", letter)
            if idx == 0:
                puzzle_cells[cell_idx].setdefault("number", seq)

    return {
        "grid": {"size": puzzle.n, "cells": grid_cells},
        "puzzle": {"title": puzzle.title or "", "cells": puzzle_cells, "words": words},
        "mode": puzzle.last_mode,
        "grid_can_undo": bool(puzzle.grid_undo_stack),
        "grid_can_redo": bool(puzzle.grid_redo_stack),
        "puzzle_can_undo": bool(puzzle.undo_stack),
        "puzzle_can_redo": bool(puzzle.redo_stack),
        "can_undo": bool(puzzle.grid_undo_stack) if puzzle.last_mode == "grid" else bool(puzzle.undo_stack),
        "can_redo": bool(puzzle.grid_redo_stack) if puzzle.last_mode == "grid" else bool(puzzle.redo_stack),
    }


def handle_list_puzzles(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    List all puzzles for the current user.
    GET /api/puzzles
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        user_id = current_user["id"]
        puzzles = app.puzzle_uc.list_puzzles(user_id)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"puzzles": puzzles}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_create_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Create a new puzzle.
    POST /api/puzzles
    Body: { "name": "puzzle1", "size": 15 }
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = body_params.get("name")
        size = body_params.get("size")

        if not name or not isinstance(name, str):
            logger.debug("  returning: %s", {"error": "Missing or invalid 'name'"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing or invalid 'name'"}
        if not isinstance(size, int):
            logger.debug("  returning: %s", {"error": "Missing or invalid 'size' (must be integer >= 1)"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing or invalid 'size' (must be integer >= 1)"}

        user_id = current_user["id"]
        app.puzzle_uc.create_puzzle(user_id, name, size=size)
        puzzle = app.puzzle_uc.load_puzzle(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)

    except ValueError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except PersistenceError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_load_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Load a puzzle by name.
    GET /api/puzzles/<name>
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            logger.debug("  returning: %s", {"error": "Missing puzzle name"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing puzzle name"}

        user_id = current_user["id"]
        puzzle = app.puzzle_uc.load_puzzle(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)

    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_delete_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Delete a puzzle by name.
    DELETE /api/puzzles/<name>
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            logger.debug("  returning: %s", {"error": "Missing puzzle name"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing puzzle name"}

        user_id = current_user["id"]
        app.puzzle_uc.delete_puzzle(user_id, name)

        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"status": "deleted", "name": name}

    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_open_puzzle_for_editing(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Open a puzzle for editing by creating a working copy.
    POST /api/puzzles/<name>/open
    Returns: { "original_name": "mypuzzle", "working_name": "__wc__a1b2c3d4" }
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            logger.debug("  returning: %s", {"error": "Missing puzzle name"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing puzzle name"}

        user_id = current_user["id"]
        working_name = app.puzzle_uc.open_puzzle_for_editing(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"original_name": name, "working_name": working_name}

    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_set_puzzle_title(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Set the title of a puzzle.
    PUT /api/puzzles/<name>/title
    Body: { "title": "My Puzzle Title" }
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            logger.debug("  returning: %s", {"error": "Missing puzzle name"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing puzzle name"}

        if "title" not in body_params:
            logger.debug("  returning: %s", {"error": "Missing 'title'"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing 'title'"}
        title = body_params["title"]
        if not isinstance(title, str):
            logger.debug("  returning: %s", {"error": "'title' must be a string"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "'title' must be a string"}

        user_id = current_user["id"]
        app.puzzle_uc.set_puzzle_title(user_id, name, title)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"name": name, "title": title}

    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_switch_to_grid_mode(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """Switch a puzzle working copy into Grid mode."""
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}
        user_id = current_user["id"]
        puzzle = app.puzzle_uc.switch_to_grid_mode(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_switch_to_puzzle_mode(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """Switch a puzzle working copy into Puzzle mode."""
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}
        user_id = current_user["id"]
        puzzle = app.puzzle_uc.switch_to_puzzle_mode(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_toggle_puzzle_black_cell(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Toggle a black cell in a puzzle grid.
    PUT /api/puzzles/<name>/grid/cells/<r>/<c>
    Note: Frontend sends 0-indexed coordinates, puzzle expects 1-indexed.
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if len(path_params) > 0 else None
        r = path_params[1] if len(path_params) > 1 else None
        c = path_params[2] if len(path_params) > 2 else None
        if not name or r is None or c is None:
            return {"error": "Missing name, r, or c"}
        try:
            r = int(r) + 1
            c = int(c) + 1
        except ValueError:
            return {"error": "r and c must be integers"}
        user_id = current_user["id"]
        puzzle = app.puzzle_uc.toggle_black_cell(user_id, name, r, c)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_rotate_puzzle_grid(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """Rotate a puzzle grid."""
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}
        user_id = current_user["id"]
        puzzle = app.puzzle_uc.rotate_grid(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_generate_puzzle_grid(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """Generate a random valid grid for a puzzle."""
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}
        user_id = current_user["id"]
        puzzle = app.puzzle_uc.generate_grid(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_undo_puzzle_grid(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """Undo the last Grid-mode operation on a puzzle."""
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}
        user_id = current_user["id"]
        puzzle = app.puzzle_uc.undo_grid(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_redo_puzzle_grid(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """Redo the last undone Grid-mode operation on a puzzle."""
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}
        user_id = current_user["id"]
        puzzle = app.puzzle_uc.redo_grid(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_reset_word(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Clear letters in a word that are not shared with a completed crossing word.
    POST /api/puzzles/<name>/words/<seq>/<direction>/reset
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name      = path_params[0] if len(path_params) > 0 else None
        seq       = path_params[1] if len(path_params) > 1 else None
        direction = path_params[2] if len(path_params) > 2 else None

        if not name or not seq or not direction:
            logger.debug("  returning: %s", {"error": "Missing name, seq, or direction"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing name, seq, or direction"}

        try:
            seq = int(seq)
        except ValueError:
            logger.debug("  returning: %s", {"error": "seq must be an integer"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "seq must be an integer"}

        user_id = current_user["id"]
        puzzle = app.puzzle_uc.reset_word(user_id, name, seq, direction)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)

    except ValueError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_set_cell_letter(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Set a letter in a puzzle cell.
    PUT /api/puzzles/<name>/cells/<r>/<c>
    Body: { "letter": "A" }
    Note: Frontend sends 0-indexed coordinates, puzzle expects 1-indexed
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if len(path_params) > 0 else None
        r = path_params[1] if len(path_params) > 1 else None
        c = path_params[2] if len(path_params) > 2 else None
        letter = body_params.get("letter")

        if not name or not r or not c:
            logger.debug("  returning: %s", {"error": "Missing name, r, or c"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing name, r, or c"}
        if letter is None:
            logger.debug("  returning: %s", {"error": "Missing 'letter'"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing 'letter'"}

        try:
            r = int(r) + 1  # Convert 0-indexed to 1-indexed
            c = int(c) + 1  # Convert 0-indexed to 1-indexed
        except ValueError:
            logger.debug("  returning: %s", {"error": "r and c must be integers"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "r and c must be integers"}

        user_id = current_user["id"]
        puzzle = app.puzzle_uc.set_cell_letter(user_id, name, r, c, letter)

        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {
            "name": name,
            "r": r,
            "c": c,
            "letter": letter.upper(),
        }

    except ValueError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_get_word_at(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Get a word at a numbered cell.
    GET /api/puzzles/<name>/words/<seq>/<direction>
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if len(path_params) > 0 else None
        seq = path_params[1] if len(path_params) > 1 else None
        direction = path_params[2] if len(path_params) > 2 else None

        if not name or not seq or not direction:
            logger.debug("  returning: %s", {"error": "Missing name, seq, or direction"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing name, seq, or direction"}

        try:
            seq = int(seq)
        except ValueError:
            logger.debug("  returning: %s", {"error": "seq must be an integer"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "seq must be an integer"}

        user_id = current_user["id"]
        word = app.puzzle_uc.get_word_at(user_id, name, seq, direction)

        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {
            "seq": seq,
            "direction": direction,
            "cells": list(word.cell_iterator()),
            "answer": word.get_text(),
            "clue": word.get_clue() or "",
        }

    except ValueError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_set_word_clue(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Set the clue and optionally the text for a word.
    PUT /api/puzzles/<name>/words/<seq>/<direction>
    Body: { "clue": "The answer to life", "text": "ANSWER" }
    If 'text' is provided it is applied with undo tracking.
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if len(path_params) > 0 else None
        seq = path_params[1] if len(path_params) > 1 else None
        direction = path_params[2] if len(path_params) > 2 else None
        clue = body_params.get("clue", "")
        text = body_params.get("text", None)

        if not name or not seq or not direction:
            logger.debug("  returning: %s", {"error": "Missing name, seq, or direction"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing name, seq, or direction"}

        try:
            seq = int(seq)
        except ValueError:
            logger.debug("  returning: %s", {"error": "seq must be an integer"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "seq must be an integer"}

        user_id = current_user["id"]
        puzzle = app.puzzle_uc.set_word_clue(user_id, name, seq, direction, clue, text)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)

    except ValueError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_undo_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Undo the last operation on a puzzle.
    POST /api/puzzles/<name>/undo
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            logger.debug("  returning: %s", {"error": "Missing puzzle name"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing puzzle name"}

        user_id = current_user["id"]
        puzzle = app.puzzle_uc.undo_puzzle(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)

    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_redo_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Redo the last undone operation on a puzzle.
    POST /api/puzzles/<name>/redo
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            logger.debug("  returning: %s", {"error": "Missing puzzle name"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing puzzle name"}

        user_id = current_user["id"]
        puzzle = app.puzzle_uc.redo_puzzle(user_id, name)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return _puzzle_response(puzzle)

    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}

def handle_copy_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Copy a puzzle to a new name.
    POST /api/puzzles/<name>/copy
    Body: { "new_name": "..." }
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            logger.debug("  returning: %s", {"error": "Missing puzzle name"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing puzzle name"}

        new_name = body_params.get("new_name")
        if not new_name or not isinstance(new_name, str):
            logger.debug("  returning: %s", {"error": "Missing or invalid 'new_name'"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing or invalid 'new_name'"}

        user_id = current_user["id"]
        puzzle = app.puzzle_uc.copy_puzzle(user_id, name, new_name)
        response = _puzzle_response(puzzle)
        response["name"] = new_name
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return response

    except ValueError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_get_puzzle_preview(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Return a scaled-down SVG thumbnail and summary heading for a puzzle.
    GET /api/puzzles/<name>/preview
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            logger.debug("  returning: %s", {"error": "Missing puzzle name"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing puzzle name"}

        user_id = current_user["id"]
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return app.puzzle_uc.get_puzzle_preview(user_id, name)

    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_get_puzzle_stats(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Return statistics and validation results for a puzzle.
    GET /api/puzzles/<name>/stats
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if path_params else None
        if not name:
            logger.debug("  returning: %s", {"error": "Missing puzzle name"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing puzzle name"}

        user_id = current_user["id"]
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return app.puzzle_uc.get_puzzle_stats(user_id, name)

    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
