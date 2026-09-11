"""
Word routes — suggestions, crossing constraints and dictionary definitions.
"""

from fastapi import APIRouter

from crossword.http_server.dependencies import Container, UserId
from crossword.http_server.errors import ApiError, puzzle_errors
from crossword.ports.definition_port import DefinitionNotFound

router = APIRouter(tags=["words"])


@router.get("/api/words/suggestions")
def get_suggestions(app: Container, user_id: UserId, pattern: str,
                    length: int | None = None, puzzle: str | None = None,
                    seq: int | None = None, direction: str | None = None):
    """
    Return word-list entries matching a pattern.

    Given a puzzle, a sequence number and a direction, the search is scoped to
    that word's length and drops anything that repeats, or nearly repeats, a
    complete word already used elsewhere in the puzzle. Without that context an
    explicit length can scope the search instead.
    """
    exclude_words = None
    if puzzle and seq is not None and direction:
        with puzzle_errors(puzzle):
            word = app.puzzle_uc.get_word_at(user_id, puzzle, seq, direction)
        exclude_words = app.word_uc.get_other_complete_words(word)
        length = word.length

    try:
        suggestions = app.word_uc.get_suggestions(pattern, exclude_words, length=length)
    except ValueError as e:
        raise ApiError(400, f"Invalid pattern: {e}")
    return {"pattern": pattern, "suggestions": suggestions, "count": len(suggestions)}


@router.get("/api/puzzles/{name}/words/{seq}/{direction}/constraints")
def get_word_constraints(name: str, seq: int, direction: str, app: Container, user_id: UserId):
    """Return the letters each cell of a word may still take, given its crossings."""
    with puzzle_errors(name):
        word = app.puzzle_uc.get_word_at(user_id, name, seq, direction)
        return app.word_uc.get_word_constraints(word)


@router.get("/api/puzzles/{name}/words/{seq}/{direction}/suggestions")
def get_ranked_suggestions(name: str, seq: int, direction: str,
                           app: Container, user_id: UserId, pattern: str | None = None):
    """Return suggestions for a word, ranked by how well their crossings can be filled."""
    with puzzle_errors(name):
        word = app.puzzle_uc.get_word_at(user_id, name, seq, direction)
        suggestions = app.word_uc.get_ranked_suggestions(word, pattern or None)
    return {"suggestions": suggestions, "count": len(suggestions)}


@router.get("/api/words/{word}/definitions")
def get_word_definitions(word: str, app: Container):
    """Return dictionary definitions for a word."""
    try:
        return app.definition_uc.lookup(word)
    except DefinitionNotFound:
        raise ApiError(404, f"No definitions found for '{word}'")
