"""
Routes for the frontend itself: the single page, its theme, and user settings.

The rest of frontend/static is served by a StaticFiles mount set up in main.
"""

import colorsys
from pathlib import Path

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse

from crossword.adapters.settings_adapter import get_settings, put_settings
from crossword.http_server.dependencies import Container
from crossword.http_server.errors import ApiError

router = APIRouter()


@router.get("/", include_in_schema=False)
def get_index():
    """Serve the single-page app."""
    index_file = get_frontend_dir() / "index.html"
    if not index_file.exists():
        raise ApiError(404, "index.html not found")
    return FileResponse(index_file, media_type="text/html")


@router.get("/static/css/theme.css", include_in_schema=False)
def get_theme_css(app: Container):
    """Serve a :root block that recolors the UI from the configured theme color."""
    theme_color = app.config.get("theme_color", "").strip()
    if not theme_color:
        return Response(content=b"", media_type="text/css")

    declarations = "\n".join(f"  {name}: {value};"
                             for name, value in _derive_palette(theme_color).items())
    return Response(content=f":root {{\n{declarations}\n}}\n", media_type="text/css")


@router.get("/api/config", tags=["config"])
def get_config(app: Container):
    """Return the handful of config values the frontend needs at startup."""
    return {"message_line_timeout_ms": app.config.get("message_line_timeout_ms", None)}


@router.get("/api/settings", tags=["settings"])
def read_settings():
    """Return the current values of the user-editable settings."""
    return get_settings()


@router.put("/api/settings", tags=["settings"])
def write_settings(body: dict):
    """Write updated settings to the user's config file."""
    return {"restart_required": put_settings(body)}


def get_frontend_dir() -> Path:
    """The frontend directory that sits beside the crossword package."""
    return Path(__file__).parent.parent.parent / "frontend"


def _derive_palette(theme_color: str) -> dict[str, str]:
    """Build the CSS custom properties for a theme from its one base color."""
    h, s, l = _hex_to_hsl(theme_color)
    return {
        '--c-primary':     theme_color,
        '--c-primary-dk':  _hsl_to_hex(h, max(s * 0.7, 0.3), min(l * 1.9, 0.52)),
        '--c-appbar-bg':   _hsl_to_hex(h, min(s, 1.0),       max(l * 0.75, 0.08)),
        '--c-appbar-text': _hsl_to_hex(h, 0.20,              0.92),
        '--c-sidebar-bg':  _hsl_to_hex(h, 0.30,              0.96),
    }


def _hex_to_hsl(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h, s, l


def _hsl_to_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return '#{:02x}{:02x}{:02x}'.format(round(r * 255), round(g * 255), round(b * 255))
