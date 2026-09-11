"""
Puzzle routes — creating, loading, editing and describing puzzles.

Grid editing lives here too: a grid is a mode within a puzzle rather than a
separate entity, so its routes hang off /api/puzzles/{name}/grid.
"""

from fastapi import APIRouter

from crossword.http_server.dependencies import Container, UserId
from crossword.http_server.errors import ApiError, puzzle_errors
from crossword.http_server.schemas import (
    CopyPuzzleBody,
    CreatePuzzleBody,
    RenamePuzzleBody,
    SetCellLetterBody,
    SetPuzzleStateBody,
    SetPuzzleTitleBody,
    SetWordClueBody,
)
from crossword.ports.persistence_port import PersistenceError

router = APIRouter(tags=["puzzles"])


@router.get("/api/dashboard")
def get_dashboard(app: Container, user_id: UserId):
    """Return every real puzzle with the summary metadata the dashboard needs."""
    return app.puzzle_uc.get_dashboard(user_id)


@router.get("/api/puzzles")
def list_puzzles(app: Container, user_id: UserId, state: str | None = None):
    """List the current user's puzzles, optionally filtered by lifecycle state."""
    names = app.puzzle_uc.list_puzzles(user_id, state=state)
    return {"puzzles": [name for name in names if not name.startswith("__new__")]}


@router.post("/api/puzzles")
def create_puzzle(body: CreatePuzzleBody, app: Container, user_id: UserId):
    """Create an empty puzzle of the given size and return it."""
    try:
        app.puzzle_uc.create_puzzle(user_id, body.name, size=body.size)
        puzzle = app.puzzle_uc.load_puzzle(user_id, body.name)
    except PersistenceError as e:
        # Creating a puzzle never looks one up, so this is a failed write.
        raise ApiError(500, str(e))
    return _puzzle_response(puzzle)


@router.get("/api/puzzles/{name}")
def load_puzzle(name: str, app: Container, user_id: UserId):
    """Load a puzzle by name."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.load_puzzle(user_id, name)
    return _puzzle_response(puzzle)


@router.delete("/api/puzzles/{name}")
def delete_puzzle(name: str, app: Container, user_id: UserId):
    """Delete a puzzle by name."""
    with puzzle_errors(name):
        app.puzzle_uc.delete_puzzle(user_id, name)
    return {"status": "deleted", "name": name}


@router.post("/api/puzzles/{name}/copy")
def copy_puzzle(name: str, body: CopyPuzzleBody, app: Container, user_id: UserId):
    """Copy a puzzle to a new name, recording why the copy was made."""
    new_name = _require_new_name(body.new_name)
    if not body.comment or not body.comment.strip():
        raise ApiError(400, "Missing or invalid 'comment'")
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.copy_puzzle(user_id, name, new_name, body.comment)
    return {**_puzzle_response(puzzle), "name": new_name}


@router.post("/api/puzzles/{name}/rename")
def rename_puzzle(name: str, body: RenamePuzzleBody, app: Container, user_id: UserId):
    """Rename a puzzle."""
    new_name = _require_new_name(body.new_name)
    with puzzle_errors(name):
        app.puzzle_uc.rename_puzzle(user_id, name, new_name)
    return {"name": new_name}


@router.get("/api/puzzles/{name}/state")
def get_puzzle_state(name: str, app: Container, user_id: UserId):
    """Return a puzzle's lifecycle state and the fields that go with it."""
    with puzzle_errors(name):
        state = app.puzzle_uc.get_puzzle_state(user_id, name)
    return {"name": name, **state}


@router.put("/api/puzzles/{name}/state")
def set_puzzle_state(name: str, body: SetPuzzleStateBody, app: Container, user_id: UserId):
    """Apply a lifecycle transition, including reopening a puzzle as a draft."""
    try:
        new_state = app.puzzle_uc.set_puzzle_state(
            user_id, name, body.state,
            publisher=body.publisher,
            date_submitted=body.date_submitted,
            date_published=body.date_published,
        )
    except PersistenceError as e:
        raise ApiError(404, str(e))
    return {"name": name, **new_state}


@router.get("/api/puzzles/{name}/state/history")
def get_puzzle_state_history(name: str, app: Container, user_id: UserId):
    """Return every recorded state transition for a puzzle, oldest first."""
    with puzzle_errors(name):
        history = app.puzzle_uc.get_puzzle_state_history(user_id, name)
    return {"name": name, "history": history}


@router.post("/api/puzzles/{name}/state/history/{history_id}/restore")
def restore_puzzle_from_history(name: str, history_id: int, app: Container, user_id: UserId):
    """
    Open an old snapshot of a puzzle for editing as a new working copy.

    The live puzzle and its state are left alone.
    """
    try:
        working_name = app.puzzle_uc.restore_puzzle_from_history(user_id, name, history_id)
    except PersistenceError as e:
        raise ApiError(404, str(e))
    return {"original_name": name, "working_name": working_name}


@router.post("/api/puzzles/{name}/open")
def open_puzzle_for_editing(name: str, app: Container, user_id: UserId):
    """Open a puzzle for editing by creating a working copy of it."""
    with puzzle_errors(name):
        working_name = app.puzzle_uc.open_puzzle_for_editing(user_id, name)
    return {"original_name": name, "working_name": working_name}


@router.post("/api/puzzles/{name}/mode/grid")
def switch_to_grid_mode(name: str, app: Container, user_id: UserId):
    """Switch a puzzle working copy into Grid mode."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.switch_to_grid_mode(user_id, name)
    return _puzzle_response(puzzle)


@router.post("/api/puzzles/{name}/mode/puzzle")
def switch_to_puzzle_mode(name: str, app: Container, user_id: UserId):
    """Switch a puzzle working copy into Puzzle mode."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.switch_to_puzzle_mode(user_id, name)
    return _puzzle_response(puzzle)


@router.put("/api/puzzles/{name}/title")
def set_puzzle_title(name: str, body: SetPuzzleTitleBody, app: Container, user_id: UserId):
    """Set the title of a puzzle."""
    with puzzle_errors(name):
        app.puzzle_uc.set_puzzle_title(user_id, name, body.title)
    return {"name": name, "title": body.title}


@router.put("/api/puzzles/{name}/grid/cells/{r}/{c}")
def toggle_black_cell(name: str, r: int, c: int, app: Container, user_id: UserId):
    """Toggle a black cell. The frontend counts from zero, the puzzle from one."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.toggle_black_cell(user_id, name, r + 1, c + 1)
    return _puzzle_response(puzzle)


@router.post("/api/puzzles/{name}/grid/rotate")
def rotate_grid(name: str, app: Container, user_id: UserId):
    """Rotate a puzzle grid a quarter turn."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.rotate_grid(user_id, name)
    return _puzzle_response(puzzle)


@router.post("/api/puzzles/{name}/grid/generate")
def generate_grid(name: str, app: Container, user_id: UserId, spec: str | None = None):
    """
    Fill a puzzle with a randomly generated valid grid.

    When the generator cannot satisfy the request it says so in a notice
    rather than failing, so the editor can keep the grid it already has.
    """
    with puzzle_errors(name):
        try:
            puzzle = app.puzzle_uc.generate_grid(user_id, name, _parse_spec(spec))
        except RuntimeError as e:
            return {"notice": str(e)}
    return _puzzle_response(puzzle)


@router.post("/api/puzzles/{name}/grid/undo")
def undo_grid(name: str, app: Container, user_id: UserId):
    """Undo the last Grid-mode operation."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.undo_grid(user_id, name)
    return _puzzle_response(puzzle)


@router.post("/api/puzzles/{name}/grid/redo")
def redo_grid(name: str, app: Container, user_id: UserId):
    """Redo the last undone Grid-mode operation."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.redo_grid(user_id, name)
    return _puzzle_response(puzzle)


@router.put("/api/puzzles/{name}/cells/{r}/{c}")
def set_cell_letter(name: str, r: int, c: int, body: SetCellLetterBody,
                    app: Container, user_id: UserId):
    """Set a letter in a cell. The frontend counts from zero, the puzzle from one."""
    row, column = r + 1, c + 1
    with puzzle_errors(name):
        app.puzzle_uc.set_cell_letter(user_id, name, row, column, body.letter)
    return {"name": name, "r": row, "c": column, "letter": body.letter.upper()}


@router.get("/api/puzzles/{name}/words/{seq}/{direction}")
def get_word_at(name: str, seq: int, direction: str, app: Container, user_id: UserId):
    """Return the word starting at a numbered cell, with its clue."""
    with puzzle_errors(name):
        word = app.puzzle_uc.get_word_at(user_id, name, seq, direction)
    return {
        "seq": seq,
        "direction": direction,
        "cells": list(word.cell_iterator()),
        "answer": word.get_text(),
        "clue": word.get_clue() or "",
    }


@router.put("/api/puzzles/{name}/words/{seq}/{direction}")
def set_word_clue(name: str, seq: int, direction: str, body: SetWordClueBody,
                  app: Container, user_id: UserId):
    """
    Set a word's clue, and optionally its text and locked flag.

    Text and locked changes are recorded on the undo stack.
    """
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.set_word_clue(
            user_id, name, seq, direction, body.clue, body.text, body.locked)
    return _puzzle_response(puzzle)


@router.post("/api/puzzles/{name}/undo")
def undo_puzzle(name: str, app: Container, user_id: UserId):
    """Undo the last Puzzle-mode operation."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.undo_puzzle(user_id, name)
    return _puzzle_response(puzzle)


@router.post("/api/puzzles/{name}/redo")
def redo_puzzle(name: str, app: Container, user_id: UserId):
    """Redo the last undone Puzzle-mode operation."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.redo_puzzle(user_id, name)
    return _puzzle_response(puzzle)


@router.post("/api/puzzles/{name}/clear")
def clear_puzzle(name: str, app: Container, user_id: UserId):
    """Blank the text and clue of every unlocked word."""
    with puzzle_errors(name):
        puzzle = app.puzzle_uc.clear_unlocked(user_id, name)
    return _puzzle_response(puzzle)


@router.get("/api/puzzles/{name}/preview")
def get_puzzle_preview(name: str, app: Container, user_id: UserId):
    """Return a scaled-down SVG thumbnail and summary heading."""
    with puzzle_errors(name):
        return app.puzzle_uc.get_puzzle_preview(user_id, name)


@router.get("/api/puzzles/{name}/stats")
def get_puzzle_stats(name: str, app: Container, user_id: UserId):
    """Return statistics and validation results for a puzzle."""
    with puzzle_errors(name):
        return app.puzzle_uc.get_puzzle_stats(user_id, name)


@router.get("/api/puzzles/{name}/fill-order")
def get_fill_order(name: str, app: Container, user_id: UserId):
    """Return ranked fill-order suggestions for a puzzle."""
    with puzzle_errors(name):
        return app.puzzle_uc.get_fill_order(user_id, name)


def _require_new_name(new_name: str | None) -> str:
    """Reject a missing or blank target name the way the API always has."""
    if not new_name or not isinstance(new_name, str):
        raise ApiError(400, "Missing or invalid 'new_name'")
    return new_name


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
            "locked": word.is_locked(),
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
            "locked": word.is_locked(),
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


def _parse_spec(raw: str | None) -> list[int] | None:
    """Parse a comma-separated spec query parameter into a list of ints, or None."""
    if not raw:
        return None
    try:
        return [int(x) for x in raw.split(",") if x.strip()]
    except ValueError:
        return None
