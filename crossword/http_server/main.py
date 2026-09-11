"""
Application assembly — build the FastAPI app and run it under uvicorn.

create_app() wires the use cases, installs the routers and error handlers, and
returns an app that tests can drive directly. run_http_server() is what the
command line and the systemd unit call.
"""

import logging
from importlib.metadata import PackageNotFoundError, version

import uvicorn
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from crossword.http_server import (
    export_routes,
    import_routes,
    puzzle_routes,
    static_routes,
    word_routes,
)
from crossword.http_server.errors import register_exception_handlers
from crossword.wiring import make_app

logger = logging.getLogger(__name__)


def run_http_server(config=None):
    """
    Serve the crossword app.

    Args:
        config: Configuration dict. Required keys: 'dbfile', 'host', 'port'.
                If None, loaded from the platform default config path.
    """
    app = create_app(config)
    settings = app.state.container.config
    host = settings["host"]
    port = int(settings["port"])

    logger.info("Starting HTTP server on http://%s:%s", host, port)
    uvicorn.run(app, host=host, port=port, log_config=None)


def create_app(config=None, container=None) -> FastAPI:
    """
    Build the FastAPI application.

    Args:
        config: Configuration dict, or None to load the platform default.
        container: An already wired AppContainer, for tests and for callers
                   that assemble their own dependencies. Wired from config
                   when omitted.

    Returns:
        A FastAPI app with the wired use cases on app.state.container.
    """
    if container is None:
        logger.info("Initializing app")
        container = make_app(config)

    app = FastAPI(
        title="Crossword Puzzle Editor API",
        description="REST API for building, editing and exchanging crossword puzzles.",
        version=_package_version(),
    )
    app.state.container = container

    # Allow cross-origin calls so tools such as an external API browser can
    # exercise the API from a different port.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Accept"],
    )
    app.middleware("http")(_log_request)

    register_exception_handlers(app)
    register_routes(app)
    return app


def _package_version() -> str:
    try:
        return version("crossword")
    except PackageNotFoundError:
        return "0.0.0"


async def _log_request(request, call_next):
    """Trace each request at debug level, the way the old handler did."""
    logger.debug("Entering %s %s", request.method, request.url.path)
    try:
        return await call_next(request)
    finally:
        logger.debug("Leaving %s %s", request.method, request.url.path)


def register_routes(app: FastAPI) -> None:
    """
    Install every router, then the static file mount.

    Order matters: the generated theme stylesheet lives at a path inside
    /static, so its route has to be in place before the mount that would
    otherwise look for a file of that name on disk.
    """
    app.include_router(static_routes.router)
    app.include_router(puzzle_routes.router)
    app.include_router(word_routes.router)
    app.include_router(export_routes.router)
    app.include_router(import_routes.router)

    static_dir = static_routes.get_frontend_dir() / "static"
    if not static_dir.is_dir():
        logger.warning("Static directory not found: %s", static_dir)
    app.mount("/static", StaticFiles(directory=static_dir, check_dir=False), name="static")


def iter_routes(app: FastAPI):
    """
    Yield every API route in the app, in registration order.

    FastAPI keeps the routes of an included router nested inside a wrapper, so
    walking app.routes alone would only find the wrappers.
    """
    yield from _walk_routes(app.router.routes)


def _walk_routes(routes):
    for route in routes:
        included = getattr(route, "original_router", None)
        if included is not None:
            yield from _walk_routes(included.routes)
        elif isinstance(route, APIRoute):
            yield route
