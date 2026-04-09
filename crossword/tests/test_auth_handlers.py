# crossword.tests.test_auth_handlers
import pytest
from unittest.mock import MagicMock

from crossword.domain.user import User
from crossword import sha256
from crossword.ports.auth_port import AuthError
from crossword.http_server.auth_handlers import handle_login, handle_logout, handle_me


def _make_request_handler():
    rh = MagicMock()
    rh.wfile = MagicMock()
    rh.send_response = MagicMock()
    rh.send_header = MagicMock()
    rh.end_headers = MagicMock()
    rh._send_cors_headers = MagicMock()
    from crossword.http_server.server import RequestHandler
    rh._send_json = RequestHandler._send_json.__get__(rh, RequestHandler)
    return rh


def _make_app(auth_uc):
    app = MagicMock()
    app.auth_uc = auth_uc
    return app


def _make_user():
    return User(id=1, username="alice", password=sha256("secret"))


class TestHandleLogin:

    def test_handle_login_success_sets_cookie(self):
        auth_uc = MagicMock()
        auth_uc.login.return_value = (_make_user(), "token-abc")
        rh = _make_request_handler()

        handle_login((), {}, {"username": "alice", "password": "secret"},
                     None, rh, app=_make_app(auth_uc))

        rh.send_response.assert_called_once_with(200)
        cookie_calls = [str(c) for c in rh.send_header.call_args_list]
        assert any("Set-Cookie" in c and "token-abc" in c for c in cookie_calls)

    def test_handle_login_bad_credentials_returns_401(self):
        auth_uc = MagicMock()
        auth_uc.login.side_effect = AuthError("bad")
        rh = _make_request_handler()

        handle_login((), {}, {"username": "alice", "password": "wrong"},
                     None, rh, app=_make_app(auth_uc))

        rh.send_response.assert_called_once_with(401)
        body = rh.wfile.write.call_args[0][0]
        assert b"Invalid username or password" in body


class TestHandleLogout:

    def test_handle_logout_clears_cookie(self):
        auth_uc = MagicMock()
        rh = _make_request_handler()

        handle_logout((), {}, {}, "token-abc", rh, app=_make_app(auth_uc))

        auth_uc.logout.assert_called_once_with("token-abc")
        rh.send_response.assert_called_once_with(200)
        cookie_calls = [str(c) for c in rh.send_header.call_args_list]
        assert any("Set-Cookie" in c and "Max-Age=0" in c for c in cookie_calls)


class TestHandleMe:

    def test_handle_me_authenticated(self):
        auth_uc = MagicMock()
        auth_uc.get_current_user.return_value = {"id": 1, "username": "alice"}
        rh = _make_request_handler()

        result = handle_me((), {}, {}, "token-abc", rh, app=_make_app(auth_uc))

        assert result == {"username": "alice"}

    def test_handle_me_unauthenticated_returns_401(self):
        auth_uc = MagicMock()
        auth_uc.get_current_user.return_value = None
        rh = _make_request_handler()

        result = handle_me((), {}, {}, "bad-token", rh, app=_make_app(auth_uc))

        assert result is None
        rh.send_response.assert_called_once_with(401)
