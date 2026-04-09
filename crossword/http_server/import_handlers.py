# crossword.http_server.import_handlers
"""
Import handlers — import puzzles from external file formats.

Routes:
  POST /api/import/acrosslite → import_puzzle_from_acrosslite
"""

import logging

from crossword.adapters.acrosslite_import_adapter import ImportError
from crossword.ports.persistence_port import PersistenceError

logger = logging.getLogger(__name__)


def handle_import_puzzle_from_acrosslite(
    path_params, query_params, body_params, session_token, request_handler, app=None, current_user=None, **kwargs
):
    """
    Import a puzzle from AcrossLite text format.

    POST /api/import/acrosslite
    Body: {"name": "<puzzle-name>", "content": "<acrosslite-text>"}

    Returns:
        {"name": "<puzzle-name>"} on success
        {"error": "..."} on failure
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug(
        "  path_params=%s query_params=%s body_params keys=%s",
        path_params, query_params, list(body_params.keys()) if body_params else [],
    )

    name = (body_params.get("name") or "").strip()
    content = body_params.get("content") or ""

    if not name:
        return {"error": "Missing puzzle name"}
    if not content:
        return {"error": "Missing file content"}

    try:
        app.import_uc.import_puzzle_from_acrosslite(current_user["id"], name, content)
        logger.debug("  returning: %s", {"name": name})
        return {"name": name}
    except ValueError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        return {"error": str(e)}
    except ImportError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        return {"error": str(e)}
    except PersistenceError as e:
        logger.debug("  returning: %s", {"error": str(e)})
        return {"error": str(e)}
    except Exception as e:
        logger.debug("  returning: %s", {"error": str(e)})
        return {"error": str(e)}
    finally:
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
