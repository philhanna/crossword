"""
Theme handlers - CRUD operations on themes via HTTP.

Routes:
  GET    /api/themes                         → list_themes
  POST   /api/themes                         → create_theme
  GET    /api/themes/<id>                    → get_theme
  PUT    /api/themes/<id>                    → update_theme
  DELETE /api/themes/<id>                    → delete_theme
  POST   /api/themes/<id>/words              → add_words
  DELETE /api/themes/<id>/words/<word>       → remove_word
  GET    /api/themes/<id>/grids?size=N       → search_grids
"""

import logging
from dataclasses import asdict

logger = logging.getLogger(__name__)


def _theme_dict(theme) -> dict:
    d = asdict(theme)
    d["complete"] = theme.complete
    return d


def handle_list_themes(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    user_id = current_user["id"]
    themes = app.theme_uc.list_themes(user_id)
    return {"themes": [_theme_dict(t) for t in themes]}


def handle_create_theme(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    user_id = current_user["id"]
    try:
        theme = app.theme_uc.create_theme(
            user_id,
            body_params["title"],
            body_params["word_lengths"],
            selected_words=body_params.get("selected_words"),
        )
    except ValueError as e:
        request_handler._send_error(400, str(e))
        return None
    request_handler._send_json(_theme_dict(theme), status=201)
    return None


def handle_get_theme(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    user_id = current_user["id"]
    theme_id = int(path_params[0])
    theme = app.theme_uc.get_theme(user_id, theme_id)
    if theme is None:
        request_handler._send_error(404, "not found")
        return None
    return _theme_dict(theme)


def handle_update_theme(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    user_id = current_user["id"]
    theme_id = int(path_params[0])
    try:
        theme = app.theme_uc.update_theme(
            user_id,
            theme_id,
            title=body_params.get("title"),
            word_lengths=body_params.get("word_lengths"),
        )
    except ValueError as e:
        request_handler._send_error(400, str(e))
        return None
    if theme is None:
        request_handler._send_error(404, "not found")
        return None
    return _theme_dict(theme)


def handle_delete_theme(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    user_id = current_user["id"]
    theme_id = int(path_params[0])
    ok = app.theme_uc.delete_theme(user_id, theme_id)
    if not ok:
        request_handler._send_error(404, "not found")
        return None
    request_handler.send_response(204)
    request_handler._send_cors_headers()
    request_handler.end_headers()
    return None


def handle_add_words(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    user_id = current_user["id"]
    theme_id = int(path_params[0])
    theme = app.theme_uc.add_words(user_id, theme_id, body_params["words"])
    if theme is None:
        request_handler._send_error(404, "not found")
        return None
    return _theme_dict(theme)


def handle_remove_word(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    user_id = current_user["id"]
    theme_id = int(path_params[0])
    word = path_params[1]
    theme = app.theme_uc.remove_word(user_id, theme_id, word)
    if theme is None:
        request_handler._send_error(404, "not found")
        return None
    return _theme_dict(theme)


def handle_search_grids(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    user_id = current_user["id"]
    theme_id = int(path_params[0])
    if "size" not in query_params:
        request_handler._send_error(400, "size parameter required")
        return None
    size = int(query_params["size"])
    grids = app.theme_uc.search_grids(user_id, theme_id, size)
    if grids is None:
        request_handler._send_error(404, "not found")
        return None
    return {"grids": grids}
