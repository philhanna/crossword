"""
Export handlers - export grids and puzzles to various formats.

Routes:
  GET /api/export/grids/<name>/pdf          → export_grid_to_pdf
  GET /api/export/grids/<name>/png          → export_grid_to_png
  GET /api/export/puzzles/<name>/acrosslite → export_puzzle_to_acrosslite
  GET /api/export/puzzles/<name>/xml        → export_puzzle_to_xml
  GET /api/export/puzzles/<name>/nytimes    → export_puzzle_to_nytimes
"""

import logging
from crossword.ports.persistence import PersistenceError
from crossword.ports.export import ExportError

logger = logging.getLogger(__name__)


def _send_download(request_handler, data, content_type, filename):
    """Send a file-download response with Content-Disposition: attachment."""
    if isinstance(data, str):
        body = data.encode("utf-8")
    else:
        body = data
    rh = request_handler
    rh.send_response(200)
    rh.send_header("Content-Type", content_type)
    rh.send_header("Content-Disposition", f'attachment; filename="{filename}"')
    rh.send_header("Content-Length", str(len(body)))
    rh.end_headers()
    rh.wfile.write(body)


def handle_export_grid_to_pdf(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a grid to PDF format.
    GET /api/export/grids/<name>/pdf
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        return {"error": "Missing grid name"}
    try:
        pdf_bytes = app.export_uc.export_grid_to_pdf(1, name)
        _send_download(request_handler, pdf_bytes, "application/pdf", f"{name}.pdf")
        return None
    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except ExportError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def handle_export_grid_to_png(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a grid to PNG image format.
    GET /api/export/grids/<name>/png
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        return {"error": "Missing grid name"}
    try:
        png_bytes = app.export_uc.export_grid_to_png(1, name)
        _send_download(request_handler, png_bytes, "image/png", f"{name}.png")
        return None
    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except ExportError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def handle_export_puzzle_to_acrosslite(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a puzzle to AcrossLite text format (ZIP containing .txt + .json).
    GET /api/export/puzzles/<name>/acrosslite
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        return {"error": "Missing puzzle name"}
    try:
        zip_bytes = app.export_uc.export_puzzle_to_acrosslite(1, name)
        _send_download(request_handler, zip_bytes, "application/zip", f"acrosslite-{name}.zip")
        return None
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except ExportError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def handle_export_puzzle_to_xml(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a puzzle to Crossword Compiler XML format.
    GET /api/export/puzzles/<name>/xml
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        return {"error": "Missing puzzle name"}
    try:
        xml_text = app.export_uc.export_puzzle_to_xml(1, name)
        _send_download(request_handler, xml_text, "application/xml", f"{name}.xml")
        return None
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except ExportError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


def handle_export_puzzle_to_nytimes(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a puzzle in NYTimes submission format (ZIP containing .html + .svg).
    GET /api/export/puzzles/<name>/nytimes
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        return {"error": "Missing puzzle name"}
    try:
        zip_bytes = app.export_uc.export_puzzle_to_nytimes(1, name)
        _send_download(request_handler, zip_bytes, "application/zip", f"nytimes-{name}.zip")
        return None
    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except ExportError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
