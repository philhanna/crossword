"""
Word handlers - word operations (suggestions, validation) via HTTP.

Routes:
  GET /api/words/suggestions?pattern=<pattern>  → get_suggestions
  GET /api/words/all                            → get_all_words
  GET /api/words/validate?word=<word>           → validate_word
"""


def handle_get_suggestions(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Get word suggestions matching a pattern.
    GET /api/words/suggestions?pattern=?HALE
    """
    try:
        pattern = query_params.get("pattern")

        if not pattern or not isinstance(pattern, str):
            return {"error": "Missing or invalid 'pattern' query parameter"}

        suggestions = app.word_uc.get_suggestions(pattern)

        return {"pattern": pattern, "suggestions": suggestions, "count": len(suggestions)}

    except ValueError as e:
        return {"error": f"Invalid pattern: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def handle_get_all_words(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Get all words in the dictionary.
    GET /api/words/all
    """
    try:
        words = app.word_uc.get_all_words()
        return {"count": len(words), "words": words}

    except Exception as e:
        return {"error": str(e)}


def handle_validate_word(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Validate if a word is in the dictionary.
    GET /api/words/validate?word=HELLO
    """
    try:
        word = query_params.get("word")

        if not word or not isinstance(word, str):
            return {"error": "Missing or invalid 'word' query parameter"}

        is_valid = app.word_uc.validate_word(word)

        return {"word": word, "valid": is_valid}

    except Exception as e:
        return {"error": str(e)}
