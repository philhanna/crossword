"""
Export handlers - export puzzles to various formats.

Routes:
  GET /api/export/puzzles/<name>/acrosslite  → export_puzzle_to_acrosslite
  GET /api/export/puzzles/<name>/xml         → export_puzzle_to_xml
  GET /api/export/puzzles/<name>/nytimes     → export_puzzle_to_nytimes
  GET /api/export/puzzles/<name>/json        → export_puzzle_to_json
  GET /api/export/puzzles/<name>/solver-pdf  → export_puzzle_to_solver_pdf
"""

import logging
from crossword.ports.persistence_port import PersistenceError
from crossword.ports.export_port import ExportError

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
    rh._send_cors_headers()
    rh.end_headers()
    rh.wfile.write(body)


def handle_export_puzzle_to_acrosslite(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Export a puzzle to AcrossLite text format (ZIP containing .txt + .json).
    GET /api/export/puzzles/<name>/acrosslite
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        logger.debug("  returning: %s", {"error": "Missing puzzle name"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": "Missing puzzle name"}
    try:
        txt = app.export_uc.export_puzzle_to_acrosslite(current_user["id"], name)
        _send_download(request_handler, txt, "text/plain", f"acrosslite-{name}.txt")
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return None
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except ExportError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_export_puzzle_to_xml(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Export a puzzle to Crossword Compiler XML format.
    GET /api/export/puzzles/<name>/xml
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        logger.debug("  returning: %s", {"error": "Missing puzzle name"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": "Missing puzzle name"}
    try:
        xml_text = app.export_uc.export_puzzle_to_xml(current_user["id"], name)
        _send_download(request_handler, xml_text, "application/xml", f"{name}.xml")
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return None
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except ExportError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_export_puzzle_to_json(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Export a puzzle to JSON format.
    GET /api/export/puzzles/<name>/json
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        logger.debug("  returning: %s", {"error": "Missing puzzle name"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": "Missing puzzle name"}
    try:
        json_text = app.export_uc.export_puzzle_to_json(current_user["id"], name)
        _send_download(request_handler, json_text, "application/json", f"{name}.json")
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return None
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except ExportError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_export_puzzle_to_solver_pdf(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Export a puzzle to compact solver PDF (empty grid + clues).
    GET /api/export/puzzles/<name>/solver-pdf
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        logger.debug("  returning: %s", {"error": "Missing puzzle name"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": "Missing puzzle name"}
    try:
        pdf_bytes = app.export_uc.export_puzzle_to_solver_pdf(current_user["id"], name)
        _send_download(request_handler, pdf_bytes, "application/pdf", f"{name}-solver.pdf")
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return None
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except ExportError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}


def handle_export_puzzle_to_nytimes(path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs):
    """
    Export a puzzle in NYTimes submission format (ZIP containing .html + .svg).
    GET /api/export/puzzles/<name>/nytimes
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    name = path_params[0] if path_params else None
    if not name:
        logger.debug("  returning: %s", {"error": "Missing puzzle name"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": "Missing puzzle name"}
    try:
        pdf_bytes = app.export_uc.export_puzzle_to_nytimes(current_user["id"], name)
        _send_download(request_handler, pdf_bytes, "application/pdf", f"nytimes-{name}.pdf")
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return None
    except PersistenceError:
        logger.debug("  returning: %s", {"error": f"Puzzle not found: {name}"})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": f"Puzzle not found: {name}"}
    except ExportError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return {"error": str(e)}
