"""
Static file handlers - serve index.html and static assets (CSS, JS).
"""

import colorsys
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
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        frontend_dir = get_frontend_dir()
        index_file = frontend_dir / "index.html"

        if index_file.exists():
            with open(index_file, "rb") as f:
                request_handler._send_bytes(f.read(), content_type="text/html")
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return None

        request_handler._send_error(404, "index.html not found")
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return None
    except Exception as e:
        request_handler._send_error(500, str(e))
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return None


def handle_get_config(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Return frontend configuration derived from config.yaml.
    GET /api/config
    """
    try:
        config = app.config if app else {}
        return {
            "message_line_timeout_ms": config.get("message_line_timeout_ms", None),
        }
    except Exception as e:
        request_handler._send_error(500, str(e))
        return None


def _hex_to_hsl(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, s, l


def _hsl_to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return '#{:02x}{:02x}{:02x}'.format(round(r * 255), round(g * 255), round(b * 255))


def _derive_palette(theme_color):
    h, s, l = _hex_to_hsl(theme_color)
    return {
        '--c-primary':    theme_color,
        '--c-primary-dk': _hsl_to_hex(h, max(s * 0.7, 0.3), min(l * 1.9, 0.52)),
        '--c-appbar-bg':  _hsl_to_hex(h, min(s, 1.0),       max(l * 0.75, 0.08)),
        '--c-appbar-text':_hsl_to_hex(h, 0.20,               0.92),
        '--c-sidebar-bg': _hsl_to_hex(h, 0.30,               0.96),
    }


def handle_get_theme_css(path_params, query_params, body_params, session_token, request_handler, app=None, **kwargs):
    """
    Serve a dynamically computed :root override for theme colors.
    GET /static/css/theme.css
    """
    try:
        config = app.config if app else {}
        theme_color = config.get('theme_color', '').strip()

        if not theme_color:
            request_handler._send_bytes(b'', content_type='text/css')
            return None

        palette = _derive_palette(theme_color)
        lines = ['  ' + k + ': ' + v + ';' for k, v in palette.items()]
        css = ':root {\n' + '\n'.join(lines) + '\n}\n'
        request_handler._send_bytes(css.encode(), content_type='text/css')
        return None
    except Exception as e:
        request_handler._send_error(500, str(e))
        return None


def handle_get_static(path_params, query_params, body_params, session_token, request_handler, **kwargs):
    """
    Serve static assets (CSS, JS, etc.).
    GET /static/<filename>
    """
    logger.debug("Entering %s %s", request_handler.command, request_handler.path)
    logger.debug("  path_params=%s query_params=%s body_params=%s", path_params, query_params, body_params)
    try:
        filename = path_params[0] if path_params else ""

        # Prevent directory traversal
        if ".." in filename or filename.startswith("/"):
            request_handler._send_error(403, "Forbidden")
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return None

        frontend_dir = get_frontend_dir()
        file_path = frontend_dir / "static" / filename

        # Ensure the file is within the static directory
        try:
            file_path = file_path.resolve()
            static_dir = (frontend_dir / "static").resolve()
            if not str(file_path).startswith(str(static_dir)):
                request_handler._send_error(403, "Forbidden")
                logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
                return None
        except Exception:
            request_handler._send_error(403, "Forbidden")
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
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
            logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
            return None

        request_handler._send_error(404, f"File not found: {filename}")
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return None
    except Exception as e:
        request_handler._send_error(500, str(e))
        logger.debug("Leaving %s %s", request_handler.command, request_handler.path)
        return None
