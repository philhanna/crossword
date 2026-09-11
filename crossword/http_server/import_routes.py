"""
Import routes — create a puzzle from a file the user uploaded.

The frontend reads the file in the browser and posts its contents, as text for
the text formats and base64 for the one binary format.
"""

import base64
from contextlib import contextmanager

from fastapi import APIRouter

from crossword.http_server.dependencies import Container, UserId
from crossword.http_server.errors import ApiError
from crossword.http_server.schemas import ImportPuzBody, ImportTextBody
from crossword.ports.import_port import PuzzleImportError
from crossword.ports.persistence_port import PersistenceError

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/acrosslite")
def import_from_acrosslite(body: ImportTextBody, app: Container, user_id: UserId):
    """Import a puzzle from AcrossLite text format."""
    name, content = _require_text_upload(body)
    with _import_errors():
        app.import_uc.import_puzzle_from_acrosslite(user_id, name, content)
    return {"name": name}


@router.post("/xd")
def import_from_xd(body: ImportTextBody, app: Container, user_id: UserId):
    """Import a puzzle from xd format."""
    name, content = _require_text_upload(body)
    with _import_errors():
        app.import_uc.import_puzzle_from_xd(user_id, name, content)
    return {"name": name}


@router.post("/ipuz")
def import_from_ipuz(body: ImportTextBody, app: Container, user_id: UserId):
    """Import a puzzle from ipuz format."""
    name, content = _require_text_upload(body)
    with _import_errors():
        app.import_uc.import_puzzle_from_ipuz(user_id, name, content)
    return {"name": name}


@router.post("/ccxml")
def import_from_ccxml(body: ImportTextBody, app: Container, user_id: UserId):
    """Import a puzzle from Crossword Compiler XML format."""
    name, content = _require_text_upload(body)
    with _import_errors():
        app.import_uc.import_puzzle_from_ccxml(user_id, name, content)
    return {"name": name}


@router.post("/puz")
def import_from_puz(body: ImportPuzBody, app: Container, user_id: UserId):
    """Import a puzzle from AcrossLite binary format."""
    name = (body.name or "").strip()
    if not name:
        raise ApiError(400, "Missing puzzle name")
    if not body.content_b64:
        raise ApiError(400, "Missing file content")
    try:
        content = base64.b64decode(body.content_b64)
    except Exception:
        raise ApiError(500, "Invalid base64 encoding")

    with _import_errors():
        app.import_uc.import_puzzle_from_puz(user_id, name, content)
    return {"name": name}


def _require_text_upload(body: ImportTextBody) -> tuple[str, str]:
    """Pull the puzzle name and file contents out of an upload, or reject it."""
    name = (body.name or "").strip()
    if not name:
        raise ApiError(400, "Missing puzzle name")
    if not body.content:
        raise ApiError(400, "Missing file content")
    return name, body.content


@contextmanager
def _import_errors():
    """A file the importer cannot use is the caller's problem, so report a 400."""
    try:
        yield
    except (ValueError, PuzzleImportError, PersistenceError) as e:
        raise ApiError(400, str(e))
