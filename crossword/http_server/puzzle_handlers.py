"""
Puzzle handlers - CRUD operations on puzzles via HTTP.

Routes:
  GET    /api/puzzles              → list_puzzles
  POST   /api/puzzles              → create_puzzle
  GET    /api/puzzles/<name>       → load_puzzle
  DELETE /api/puzzles/<name>       → delete_puzzle
  PUT    /api/puzzles/<name>/cells/<r>/<c>  → set_cell_letter
  GET    /api/puzzles/<name>/words/<seq>/<direction>  → get_word_at
  PUT    /api/puzzles/<name>/words/<seq>/<direction>  → set_word_clue
  POST   /api/puzzles/<name>/undo          → undo_puzzle
  POST   /api/puzzles/<name>/redo          → redo_puzzle
  PUT    /api/puzzles/<name>/grid          → replace_puzzle_grid
"""

from crossword.ports.persistence import PersistenceError


def handle_list_puzzles(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    List all puzzles for the current user.
    GET /api/puzzles
    """
    try:
        user_id = 1
        puzzles = app.puzzle_uc.list_puzzles(user_id)
        return {"puzzles": puzzles}
    except Exception as e:
        return {"error": str(e)}


def handle_create_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Create a new puzzle from a grid.
    POST /api/puzzles
    Body: { "name": "puzzle1", "grid_name": "grid1" }
    """
    try:
        name = body_params.get("name")
        grid_name = body_params.get("grid_name")

        if not name or not isinstance(name, str):
            return {"error": "Missing or invalid 'name'"}
        if not grid_name or not isinstance(grid_name, str):
            return {"error": "Missing or invalid 'grid_name'"}

        user_id = 1
        app.puzzle_uc.create_puzzle(user_id, name, grid_name)

        return {"status": "created", "name": name, "grid_name": grid_name}

    except PersistenceError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def handle_load_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Load a puzzle by name.
    GET /api/puzzles/<name>
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}

        user_id = 1
        puzzle = app.puzzle_uc.load_puzzle(user_id, name)

        response = {
            "name": name,
            "size": puzzle.n,
            "black_cells": list(puzzle.black_cells),
            "puzzle_json": puzzle.to_json(),
            "across_words": {},
            "down_words": {},
        }

        for seq, word in puzzle.across_words.items():
            response["across_words"][str(seq)] = {
                "seq": seq,
                "cells": [(r, c) for r, c in word.cells],
                "letters": word.letters(),
                "clue": word.clue() if hasattr(word, "clue") else "",
            }

        for seq, word in puzzle.down_words.items():
            response["down_words"][str(seq)] = {
                "seq": seq,
                "cells": [(r, c) for r, c in word.cells],
                "letters": word.letters(),
                "clue": word.clue() if hasattr(word, "clue") else "",
            }

        return response

    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_delete_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Delete a puzzle by name.
    DELETE /api/puzzles/<name>
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}

        user_id = 1
        app.puzzle_uc.delete_puzzle(user_id, name)

        return {"status": "deleted", "name": name}

    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_set_cell_letter(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Set a letter in a puzzle cell.
    PUT /api/puzzles/<name>/cells/<r>/<c>
    Body: { "letter": "A" }
    """
    try:
        name = path_params[0] if len(path_params) > 0 else None
        r = path_params[1] if len(path_params) > 1 else None
        c = path_params[2] if len(path_params) > 2 else None
        letter = body_params.get("letter")

        if not name or not r or not c:
            return {"error": "Missing name, r, or c"}
        if letter is None:
            return {"error": "Missing 'letter'"}

        try:
            r = int(r)
            c = int(c)
        except ValueError:
            return {"error": "r and c must be integers"}

        user_id = 1
        puzzle = app.puzzle_uc.set_cell_letter(user_id, name, r, c, letter)

        return {
            "name": name,
            "r": r,
            "c": c,
            "letter": letter.upper(),
            "puzzle_json": puzzle.to_json(),
        }

    except ValueError as e:
        return {"error": str(e)}
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_get_word_at(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Get a word at a numbered cell.
    GET /api/puzzles/<name>/words/<seq>/<direction>
    """
    try:
        name = path_params[0] if len(path_params) > 0 else None
        seq = path_params[1] if len(path_params) > 1 else None
        direction = path_params[2] if len(path_params) > 2 else None

        if not name or not seq or not direction:
            return {"error": "Missing name, seq, or direction"}

        try:
            seq = int(seq)
        except ValueError:
            return {"error": "seq must be an integer"}

        user_id = 1
        word = app.puzzle_uc.get_word_at(user_id, name, seq, direction)

        return {
            "seq": seq,
            "direction": direction,
            "cells": [(r, c) for r, c in word.cells],
            "letters": word.letters(),
            "clue": word.clue() if hasattr(word, "clue") else "",
        }

    except ValueError as e:
        return {"error": str(e)}
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_set_word_clue(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Set a clue for a word.
    PUT /api/puzzles/<name>/words/<seq>/<direction>
    Body: { "clue": "The answer to life" }
    """
    try:
        name = path_params[0] if len(path_params) > 0 else None
        seq = path_params[1] if len(path_params) > 1 else None
        direction = path_params[2] if len(path_params) > 2 else None
        clue = body_params.get("clue", "")

        if not name or not seq or not direction:
            return {"error": "Missing name, seq, or direction"}

        try:
            seq = int(seq)
        except ValueError:
            return {"error": "seq must be an integer"}

        user_id = 1
        puzzle = app.puzzle_uc.set_word_clue(user_id, name, seq, direction, clue)

        return {
            "name": name,
            "seq": seq,
            "direction": direction,
            "clue": clue,
            "puzzle_json": puzzle.to_json(),
        }

    except ValueError as e:
        return {"error": str(e)}
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_undo_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Undo the last operation on a puzzle.
    POST /api/puzzles/<name>/undo
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}

        user_id = 1
        puzzle = app.puzzle_uc.undo_puzzle(user_id, name)

        return {
            "name": name,
            "puzzle_json": puzzle.to_json(),
        }

    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_redo_puzzle(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Redo the last undone operation on a puzzle.
    POST /api/puzzles/<name>/redo
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}

        user_id = 1
        puzzle = app.puzzle_uc.redo_puzzle(user_id, name)

        return {
            "name": name,
            "puzzle_json": puzzle.to_json(),
        }

    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_replace_puzzle_grid(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Replace the grid of a puzzle with a new grid.
    PUT /api/puzzles/<name>/grid
    Body: { "new_grid_name": "grid2" }
    """
    try:
        name = path_params[0] if path_params else None
        new_grid_name = body_params.get("new_grid_name")

        if not name:
            return {"error": "Missing puzzle name"}
        if not new_grid_name or not isinstance(new_grid_name, str):
            return {"error": "Missing or invalid 'new_grid_name'"}

        user_id = 1
        puzzle = app.puzzle_uc.replace_puzzle_grid(user_id, name, new_grid_name)

        return {
            "name": name,
            "new_grid_name": new_grid_name,
            "puzzle_json": puzzle.to_json(),
        }

    except ValueError as e:
        return {"error": str(e)}
    except PersistenceError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
