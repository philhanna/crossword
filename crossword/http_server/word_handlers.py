"""
Word handlers - word operations (suggestions, validation) via HTTP.

Routes:
  GET /api/words/suggestions?pattern=<pattern>  → get_suggestions
  GET /api/words/all                            → get_all_words
  GET /api/words/validate?word=<word>           → validate_word
  GET /api/puzzles/<name>/words/<seq>/<dir>/constraints  → get_word_constraints
  GET /api/puzzles/<name>/words/<seq>/<dir>/suggestions  → get_ranked_suggestions
"""

import logging
from crossword.ports.persistence_port import PersistenceError

logger = logging.getLogger(__name__)


def handle_get_suggestions(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Get word suggestions matching a pattern.
    GET /api/words/suggestions?pattern=?HALE
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        pattern = query_params.get("pattern")

        if not pattern or not isinstance(pattern, str):
            logger.debug("  returning: %s", {"error": "Missing or invalid 'pattern' query parameter"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing or invalid 'pattern' query parameter"}

        suggestions = app.word_uc.get_suggestions(pattern)

        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"pattern": pattern, "suggestions": suggestions, "count": len(suggestions)}

    except ValueError as e:
        logger.debug("  returning: %s", {"error": f"Invalid pattern: {str(e)}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Invalid pattern: {str(e)}"}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_get_all_words(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Get all words in the dictionary.
    GET /api/words/all
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        words = app.word_uc.get_all_words()
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"count": len(words), "words": words}

    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_validate_word(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Validate if a word is in the dictionary.
    GET /api/words/validate?word=HELLO
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        word = query_params.get("word")

        if not word or not isinstance(word, str):
            logger.debug("  returning: %s", {"error": "Missing or invalid 'word' query parameter"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing or invalid 'word' query parameter"}

        is_valid = app.word_uc.validate_word(word)

        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"word": word, "valid": is_valid}

    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_get_word_constraints(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Return letter constraints for a word based on its crossing words.
    GET /api/puzzles/<name>/words/<seq>/<direction>/constraints
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if len(path_params) > 0 else None
        seq_str = path_params[1] if len(path_params) > 1 else None
        direction = path_params[2] if len(path_params) > 2 else None

        if not name or not seq_str or not direction:
            logger.debug("  returning: %s", {"error": "Missing name, seq, or direction"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing name, seq, or direction"}

        try:
            seq = int(seq_str)
        except ValueError:
            logger.debug("  returning: %s", {"error": "seq must be an integer"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "seq must be an integer"}

        user_id = 1
        word = app.puzzle_uc.get_word_at(user_id, name, seq, direction)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return app.word_uc.get_word_constraints(word)

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


def handle_get_ranked_suggestions(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Return word suggestions for a puzzle word, ranked by crossing viability score.
    GET /api/puzzles/<name>/words/<seq>/<direction>/suggestions
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        name = path_params[0] if len(path_params) > 0 else None
        seq_str = path_params[1] if len(path_params) > 1 else None
        direction = path_params[2] if len(path_params) > 2 else None

        if not name or not seq_str or not direction:
            logger.debug("  returning: %s", {"error": "Missing name, seq, or direction"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "Missing name, seq, or direction"}

        try:
            seq = int(seq_str)
        except ValueError:
            logger.debug("  returning: %s", {"error": "seq must be an integer"})
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return {"error": "seq must be an integer"}

        user_id = 1
        input_pattern = query_params.get("pattern", None) or None
        word = app.puzzle_uc.get_word_at(user_id, name, seq, direction)
        suggestions = app.word_uc.get_ranked_suggestions(word, input_pattern)
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"suggestions": suggestions, "count": len(suggestions)}

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
