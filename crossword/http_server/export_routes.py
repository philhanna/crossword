"""
Export routes — download a puzzle in one of the interchange formats.

Every response is an attachment, so the browser saves it instead of showing it.
"""

from fastapi import APIRouter, Response

from crossword.adapters.settings_adapter import get_settings
from crossword.http_server.dependencies import Container, UserId
from crossword.http_server.errors import puzzle_errors

router = APIRouter(prefix="/api/export/puzzles", tags=["export"])


@router.get("/{name}/acrosslite")
def export_to_acrosslite(name: str, app: Container, user_id: UserId):
    """Export to AcrossLite text format."""
    with puzzle_errors(name):
        text = app.export_uc.export_puzzle_to_acrosslite(user_id, name)
    return _download(text, "text/plain", f"{name}.txt")


@router.get("/{name}/xml")
def export_to_xml(name: str, app: Container, user_id: UserId):
    """Export to Crossword Compiler XML format."""
    with puzzle_errors(name):
        text = app.export_uc.export_puzzle_to_xml(user_id, name)
    return _download(text, "application/xml", f"{name}.xml")


@router.get("/{name}/nytimes")
def export_to_nytimes(name: str, app: Container, user_id: UserId):
    """Export in New York Times submission format."""
    with puzzle_errors(name):
        pdf_bytes = app.export_uc.export_puzzle_to_nytimes(user_id, name)
    return _download(pdf_bytes, "application/pdf", f"{_author_last_name()}_{name}.pdf")


@router.get("/{name}/solver-pdf")
def export_to_solver_pdf(name: str, app: Container, user_id: UserId):
    """Export a compact solver PDF: an empty grid plus the clues."""
    with puzzle_errors(name):
        pdf_bytes = app.export_uc.export_puzzle_to_solver_pdf(user_id, name)
    return _download(pdf_bytes, "application/pdf", f"{name}.pdf")


@router.get("/{name}/solved-pdf")
def export_to_solved_pdf(name: str, app: Container, user_id: UserId):
    """Export a solved PDF: the filled-in grid plus the clues."""
    with puzzle_errors(name):
        pdf_bytes = app.export_uc.export_puzzle_to_solved_pdf(user_id, name)
    return _download(pdf_bytes, "application/pdf", f"{name}-solution.pdf")


@router.get("/{name}/puz")
def export_to_puz(name: str, app: Container, user_id: UserId):
    """Export to AcrossLite binary format."""
    with puzzle_errors(name):
        puz_bytes = app.export_uc.export_puzzle_to_puz(user_id, name)
    return _download(puz_bytes, "application/octet-stream", f"{name}.puz")


@router.get("/{name}/xd")
def export_to_xd(name: str, app: Container, user_id: UserId):
    """Export to xd format."""
    with puzzle_errors(name):
        text = app.export_uc.export_puzzle_to_xd(user_id, name)
    return _download(text, "text/plain; charset=utf-8", f"{name}.xd")


@router.get("/{name}/ipuz")
def export_to_ipuz(name: str, app: Container, user_id: UserId):
    """Export to ipuz format."""
    with puzzle_errors(name):
        text = app.export_uc.export_puzzle_to_ipuz(user_id, name)
    return _download(text, "application/x-ipuz+json", f"{name}.ipuz")


def _download(data, media_type: str, filename: str) -> Response:
    """Wrap exported text or bytes in a file-download response."""
    body = data.encode("utf-8") if isinstance(data, str) else data
    return Response(
        content=body,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _author_last_name() -> str:
    """The surname the New York Times expects in a submission filename."""
    author_name = get_settings().get("author_name", "").strip()
    return author_name.split()[-1] if author_name else "nytimes"
