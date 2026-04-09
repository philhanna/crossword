# crossword.http_server.auth_handlers
"""
Auth handlers — login, logout, and session introspection.

Routes (all public — no auth required):
  POST /api/auth/login   → handle_login
  POST /api/auth/logout  → handle_logout
  GET  /api/auth/me      → handle_me
"""

import json
import logging
from crossword.ports.auth_port import AuthError

logger = logging.getLogger(__name__)

_SESSION_COOKIE = "session={}; HttpOnly; SameSite=Lax; Path=/"
_CLEAR_COOKIE = "session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"


def handle_login(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    POST /api/auth/login
    Body: {username, password}
    Success: {username} + Set-Cookie
    Failure: 401 {error: "Invalid username or password"}
    """
    username = body_params.get("username", "")
    password = body_params.get("password", "")

    try:
        user, token = app.auth_uc.login(username, password)
    except AuthError:
        request_handler._send_json({"error": "Invalid username or password"}, status=401)
        return None

    body = json.dumps({"username": user.username}).encode("utf-8")
    request_handler.send_response(200)
    request_handler.send_header("Content-Type", "application/json")
    request_handler.send_header("Content-Length", len(body))
    request_handler.send_header("Set-Cookie", _SESSION_COOKIE.format(token))
    request_handler._send_cors_headers()
    request_handler.end_headers()
    request_handler.wfile.write(body)
    return None


def handle_logout(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    POST /api/auth/logout
    Clears session cookie. Returns 200 {}.
    """
    if session_token:
        app.auth_uc.logout(session_token)

    body = json.dumps({}).encode("utf-8")
    request_handler.send_response(200)
    request_handler.send_header("Content-Type", "application/json")
    request_handler.send_header("Content-Length", len(body))
    request_handler.send_header("Set-Cookie", _CLEAR_COOKIE)
    request_handler._send_cors_headers()
    request_handler.end_headers()
    request_handler.wfile.write(body)
    return None


def handle_me(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    GET /api/auth/me
    Returns {username} if authenticated, else 401.
    """
    session = app.auth_uc.get_current_user(session_token) if session_token else None
    if session is None:
        request_handler._send_json({"error": "Not authenticated"}, status=401)
        return None
    return {"username": session["username"]}
