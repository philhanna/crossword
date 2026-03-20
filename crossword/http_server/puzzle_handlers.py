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

        # Load the puzzle to return full data for frontend rendering
        puzzle = app.puzzle_uc.load_puzzle(user_id, name)
        grid_cells = [False] * (puzzle.n * puzzle.n)
        for r, c in puzzle.black_cells:
            cell_idx = (r - 1) * puzzle.n + (c - 1)  # Convert 1-indexed (r,c) to 0-indexed flat index
            grid_cells[cell_idx] = True

        # Build puzzle cells with letter and number info
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
                "pattern": word.get_text() if word.get_text() else "?" * len(cells_list),
            })

            # Add cell info for puzzle rendering
            for idx, (r, c) in enumerate(cells_list):
                cell_idx = (r - 1) * puzzle.n + (c - 1)  # Convert 1-indexed to 0-indexed flat index
                if cell_idx not in puzzle_cells:
                    puzzle_cells[cell_idx] = {}
                if word.get_text() and idx < len(word.get_text()):
                    puzzle_cells[cell_idx]["letter"] = word.get_text()[idx]
                # Add number if this is the start of an across word
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
                "pattern": word.get_text() if word.get_text() else "?" * len(cells_list),
            })

        return {
            "grid": {
                "size": puzzle.n,
                "cells": grid_cells,
            },
            "puzzle": {
                "cells": puzzle_cells,
                "words": words,
            }
        }

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

        # Build grid cells
        grid_cells = [False] * (puzzle.n * puzzle.n)
        for r, c in puzzle.black_cells:
            cell_idx = (r - 1) * puzzle.n + (c - 1)  # Convert 1-indexed (r,c) to 0-indexed flat index
            grid_cells[cell_idx] = True

        # Build puzzle cells with letter and number info
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
                "pattern": word.get_text() if word.get_text() else "?" * len(cells_list),
            })

            # Add cell info for puzzle rendering
            for idx, (r, c) in enumerate(cells_list):
                cell_idx = (r - 1) * puzzle.n + (c - 1)  # Convert 1-indexed to 0-indexed flat index
                if cell_idx not in puzzle_cells:
                    puzzle_cells[cell_idx] = {}
                if word.get_text() and idx < len(word.get_text()):
                    puzzle_cells[cell_idx]["letter"] = word.get_text()[idx]
                # Add number if this is the start of an across word
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
                "pattern": word.get_text() if word.get_text() else "?" * len(cells_list),
            })

        return {
            "grid": {
                "size": puzzle.n,
                "cells": grid_cells,
            },
            "puzzle": {
                "cells": puzzle_cells,
                "words": words,
            }
        }

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
    Note: Frontend sends 0-indexed coordinates, puzzle expects 1-indexed
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
            r = int(r) + 1  # Convert 0-indexed to 1-indexed
            c = int(c) + 1  # Convert 0-indexed to 1-indexed
        except ValueError:
            return {"error": "r and c must be integers"}

        user_id = 1
        puzzle = app.puzzle_uc.set_cell_letter(user_id, name, r, c, letter)

        return {
            "name": name,
            "r": r,
            "c": c,
            "letter": letter.upper(),
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
            "cells": list(word.cell_iterator()),
            "answer": word.get_text(),
            "clue": word.get_clue() or "",
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

        # Build response with full puzzle data
        grid_cells = [False] * (puzzle.n * puzzle.n)
        for r, c in puzzle.black_cells:
            cell_idx = (r - 1) * puzzle.n + (c - 1)  # Convert 1-indexed to 0-indexed
            grid_cells[cell_idx] = True

        puzzle_cells = {}
        words = []

        for seq, word in sorted(puzzle.across_words.items()):
            cells_list = list(word.cell_iterator())
            words.append({"seq": seq, "direction": "across", "clue": word.get_clue() or ""})

            # Add cell info for puzzle rendering
            for idx, (r, c) in enumerate(cells_list):
                cell_idx = (r - 1) * puzzle.n + (c - 1)  # Convert 1-indexed to 0-indexed
                if cell_idx not in puzzle_cells:
                    puzzle_cells[cell_idx] = {}
                if word.get_text() and idx < len(word.get_text()):
                    puzzle_cells[cell_idx]["letter"] = word.get_text()[idx]
                if idx == 0:
                    puzzle_cells[cell_idx]["number"] = seq

        for seq, word in sorted(puzzle.down_words.items()):
            cells_list = list(word.cell_iterator())
            words.append({"seq": seq, "direction": "down", "clue": word.get_clue() or ""})

        return {
            "grid": {"size": puzzle.n, "cells": grid_cells},
            "puzzle": {"cells": puzzle_cells, "words": words},
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

        # Build response with full puzzle data
        grid_cells = [False] * (puzzle.n * puzzle.n)
        for r, c in puzzle.black_cells:
            cell_idx = (r - 1) * puzzle.n + (c - 1)  # Convert 1-indexed to 0-indexed
            grid_cells[cell_idx] = True

        puzzle_cells = {}
        words = []

        for seq, word in sorted(puzzle.across_words.items()):
            cells_list = list(word.cell_iterator())
            words.append({"seq": seq, "direction": "across", "clue": word.get_clue() or ""})

            # Add cell info for puzzle rendering
            for idx, (r, c) in enumerate(cells_list):
                cell_idx = (r - 1) * puzzle.n + (c - 1)  # Convert 1-indexed to 0-indexed
                if cell_idx not in puzzle_cells:
                    puzzle_cells[cell_idx] = {}
                if word.get_text() and idx < len(word.get_text()):
                    puzzle_cells[cell_idx]["letter"] = word.get_text()[idx]
                if idx == 0:
                    puzzle_cells[cell_idx]["number"] = seq

        for seq, word in sorted(puzzle.down_words.items()):
            cells_list = list(word.cell_iterator())
            words.append({"seq": seq, "direction": "down", "clue": word.get_clue() or ""})

        return {
            "grid": {"size": puzzle.n, "cells": grid_cells},
            "puzzle": {"cells": puzzle_cells, "words": words},
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
