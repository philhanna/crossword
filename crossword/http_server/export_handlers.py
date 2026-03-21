"""
Export handlers - export grids and puzzles to various formats.

Routes:
  GET /api/export/grids/<name>/pdf          → export_grid_to_pdf
  GET /api/export/grids/<name>/png          → export_grid_to_png
  GET /api/export/puzzles/<name>/acrosslite → export_puzzle_to_acrosslite
  GET /api/export/puzzles/<name>/xml        → export_puzzle_to_xml
  GET /api/export/puzzles/<name>/nytimes    → export_puzzle_to_nytimes
"""

from crossword.ports.persistence import PersistenceError


def handle_export_grid_to_pdf(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a grid to PDF format.
    GET /api/export/grids/<name>/pdf
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        if not app.export_uc:
            return {"error": "Export functionality not yet implemented"}

        user_id = 1
        pdf_bytes = app.export_uc.export_grid_to_pdf(user_id, name)
        return pdf_bytes

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_export_grid_to_png(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a grid to PNG image format.
    GET /api/export/grids/<name>/png
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing grid name"}

        if not app.export_uc:
            return {"error": "Export functionality not yet implemented"}

        user_id = 1
        png_bytes = app.export_uc.export_grid_to_png(user_id, name)
        return png_bytes

    except PersistenceError:
        return {"error": f"Grid not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_export_puzzle_to_acrosslite(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a puzzle to AcrossLite text format (ZIP containing .txt + .json).
    GET /api/export/puzzles/<name>/acrosslite
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}

        if not app.export_uc:
            return {"error": "Export functionality not yet implemented"}

        user_id = 1
        zip_bytes = app.export_uc.export_puzzle_to_acrosslite(user_id, name)
        return zip_bytes

    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_export_puzzle_to_xml(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a puzzle to Crossword Compiler XML format.
    GET /api/export/puzzles/<name>/xml
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}

        if not app.export_uc:
            return {"error": "Export functionality not yet implemented"}

        user_id = 1
        xml_text = app.export_uc.export_puzzle_to_xml(user_id, name)
        return xml_text

    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_export_puzzle_to_nytimes(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a puzzle in NYTimes submission format (ZIP containing .html + .svg).
    GET /api/export/puzzles/<name>/nytimes
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}

        if not app.export_uc:
            return {"error": "Export functionality not yet implemented"}

        user_id = 1
        zip_bytes = app.export_uc.export_puzzle_to_nytimes(user_id, name)
        return zip_bytes

    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}
