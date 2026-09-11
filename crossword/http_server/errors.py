"""
API errors and the exception handlers that render them.

Every failure reaches the client as {"error": "<message>"} together with an
HTTP status, which is the envelope the frontend has always read. Route
functions raise ApiError when they want to choose the status themselves;
anything else they let escape is translated by the handlers registered here.
"""

import logging
from contextlib import contextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from crossword.ports.persistence_port import PersistenceError

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """An error response: an HTTP status code plus a client-facing message."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def register_exception_handlers(app: FastAPI) -> None:
    """Install the handlers that put every error into the {"error": ...} envelope."""
    app.add_exception_handler(ApiError, _handle_api_error)
    app.add_exception_handler(RequestValidationError, _handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, _handle_http_exception)
    app.add_exception_handler(ValueError, _handle_value_error)
    app.add_exception_handler(Exception, _handle_unexpected_error)


def _handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    """Render an explicitly raised ApiError."""
    return _error_response(exc.status, exc.message)


def _handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Render bad path/query/body input as a 400, the status the API has always used."""
    return _error_response(400, _describe_validation_error(exc))


def _handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Render the exceptions Starlette itself raises, such as a missing static file."""
    return _error_response(exc.status_code, str(exc.detail))


def _handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
    """Render a use-case rejection as a 400."""
    return _error_response(400, str(exc))


def _handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Render anything unforeseen as a 500, with the traceback in the log."""
    logger.exception("Unhandled error in %s %s", request.method, request.url.path)
    return _error_response(500, str(exc))


def _error_response(status: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": message})


def _describe_validation_error(exc: RequestValidationError) -> str:
    """Turn pydantic's error list into one readable sentence."""
    parts = []
    for error in exc.errors():
        location = [str(part) for part in error["loc"] if part not in ("body", "query", "path")]
        field = ".".join(location)
        if error["type"] == "missing":
            parts.append(f"Missing '{field}'" if field else "Missing request body")
        elif field:
            parts.append(f"Invalid '{field}': {error['msg']}")
        else:
            parts.append(error["msg"])
    return "; ".join(parts) or "Invalid request"


@contextmanager
def puzzle_errors(name: str):
    """
    Translate the errors a puzzle use case raises into API errors.

    A missing puzzle becomes a 404 naming it, and a rejected argument becomes
    a 400 carrying the use case's own explanation.
    """
    try:
        yield
    except PersistenceError:
        raise ApiError(404, f"Puzzle not found: {name}")
    except ValueError as e:
        raise ApiError(400, str(e))
