"""
Static file handlers - serve index.html and static assets (CSS, JS).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_frontend_dir():
    """Get the frontend directory path."""
    # Frontend is at crossword/frontend/
    project_root = Path(__file__).parent.parent.parent
    return project_root / "frontend"


def handle_get_index(path_params, query_params, body_params, session_token, request_handler, **kwargs):
    """
    Serve index.html for root path.
    GET /
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        frontend_dir = get_frontend_dir()
        index_file = frontend_dir / "index.html"

        if index_file.exists():
            with open(index_file, "rb") as f:
                request_handler._send_bytes(f.read(), content_type="text/html")
            return None

        request_handler._send_error(404, "index.html not found")
        return None
    except Exception as e:
        request_handler._send_error(500, str(e))
        return None


def handle_get_static(path_params, query_params, body_params, session_token, request_handler, **kwargs):
    """
    Serve static assets (CSS, JS, etc.).
    GET /static/<filename>
    """
    logger.debug("%s %s path_params=%s query_params=%s body_params=%s", request_handler.command, request_handler.path, path_params, query_params, body_params)
    try:
        filename = path_params[0] if path_params else ""

        # Prevent directory traversal
        if ".." in filename or filename.startswith("/"):
            request_handler._send_error(403, "Forbidden")
            return None

        frontend_dir = get_frontend_dir()
        file_path = frontend_dir / "static" / filename

        # Ensure the file is within the static directory
        try:
            file_path = file_path.resolve()
            static_dir = (frontend_dir / "static").resolve()
            if not str(file_path).startswith(str(static_dir)):
                request_handler._send_error(403, "Forbidden")
                return None
        except Exception:
            request_handler._send_error(403, "Forbidden")
            return None

        if file_path.exists() and file_path.is_file():
            # Determine content type
            suffix = file_path.suffix.lower()
            content_type_map = {
                ".css": "text/css",
                ".js": "application/javascript",
                ".html": "text/html",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".json": "application/json",
                ".woff": "font/woff",
                ".woff2": "font/woff2",
                ".ttf": "font/ttf",
                ".eot": "application/vnd.ms-fontobject",
            }
            content_type = content_type_map.get(suffix, "application/octet-stream")

            with open(file_path, "rb") as f:
                request_handler._send_bytes(f.read(), content_type=content_type)
            return None

        request_handler._send_error(404, f"File not found: {filename}")
        return None
    except Exception as e:
        request_handler._send_error(500, str(e))
        return None
