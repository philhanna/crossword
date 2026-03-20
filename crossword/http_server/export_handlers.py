"""
Export handlers - export grids and puzzles to various formats.

Routes:
  GET /api/export/grids/<name>/pdf      → export_grid_to_pdf
  GET /api/export/grids/<name>/png      → export_grid_to_png
  GET /api/export/puzzles/<name>/puz    → export_puzzle_to_puz
  GET /api/export/puzzles/<name>/xml    → export_puzzle_to_xml
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

        # Return bytes; server will call _send_bytes with application/pdf content-type
        # Note: server doesn't know about content-type from return value, so this needs custom handling
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


def handle_export_puzzle_to_puz(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a puzzle to AcrossLite .puz binary format.
    GET /api/export/puzzles/<name>/puz
    """
    try:
        name = path_params[0] if path_params else None
        if not name:
            return {"error": "Missing puzzle name"}

        if not app.export_uc:
            return {"error": "Export functionality not yet implemented"}

        user_id = 1
        puz_bytes = app.export_uc.export_puzzle_to_puz(user_id, name)

        return puz_bytes

    except PersistenceError:
        return {"error": f"Puzzle not found: {name}"}
    except Exception as e:
        return {"error": str(e)}


def handle_export_puzzle_to_xml(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Export a puzzle to XML text format.
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
