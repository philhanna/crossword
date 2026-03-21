"""
HTTP Server main entry point - registers all routes and starts the server.
"""

from crossword.http_server.server import create_server, start_server
from crossword.wiring import make_app

# Import all handlers
from crossword.http_server.static_handlers import handle_get_index, handle_get_static
from crossword.http_server.grid_handlers import (
    handle_list_grids,
    handle_create_grid,
    handle_create_grid_from_puzzle,
    handle_load_grid,
    handle_delete_grid,
    handle_copy_grid,
    handle_open_grid_for_editing,
    handle_toggle_black_cell,
    handle_rotate_grid,
    handle_undo_grid,
    handle_redo_grid,
)
from crossword.http_server.puzzle_handlers import (
    handle_list_puzzles,
    handle_create_puzzle,
    handle_load_puzzle,
    handle_delete_puzzle,
    handle_copy_puzzle,
    handle_open_puzzle_for_editing,
    handle_set_puzzle_title,
    handle_reset_word,
    handle_set_cell_letter,
    handle_get_word_at,
    handle_set_word_clue,
    handle_undo_puzzle,
    handle_redo_puzzle,
    handle_replace_puzzle_grid,
)
from crossword.http_server.word_handlers import (
    handle_get_suggestions,
    handle_get_all_words,
    handle_validate_word,
)
from crossword.http_server.export_handlers import (
    handle_export_grid_to_pdf,
    handle_export_grid_to_png,
    handle_export_puzzle_to_puz,
    handle_export_puzzle_to_xml,
)


def register_routes(router):
    """
    Register all API routes with the router.
    """
    # Static file serving
    router.add_route("GET", r"^/$", handle_get_index)
    router.add_route("GET", r"^/static/(.+)$", handle_get_static)

    # Grid routes
    router.add_route("GET", r"^/api/grids$", handle_list_grids)
    router.add_route("POST", r"^/api/grids$", handle_create_grid)
    router.add_route("POST", r"^/api/grids/from-puzzle$", handle_create_grid_from_puzzle)
    router.add_route("GET", r"^/api/grids/([^/]+)$", handle_load_grid)
    router.add_route("DELETE", r"^/api/grids/([^/]+)$", handle_delete_grid)
    router.add_route("POST", r"^/api/grids/([^/]+)/copy$", handle_copy_grid)
    router.add_route("POST", r"^/api/grids/([^/]+)/open$", handle_open_grid_for_editing)
    router.add_route("PUT", r"^/api/grids/([^/]+)/cells/(\d+)/(\d+)$", handle_toggle_black_cell)
    router.add_route("POST", r"^/api/grids/([^/]+)/rotate$", handle_rotate_grid)
    router.add_route("POST", r"^/api/grids/([^/]+)/undo$", handle_undo_grid)
    router.add_route("POST", r"^/api/grids/([^/]+)/redo$", handle_redo_grid)

    # Puzzle routes
    router.add_route("GET", r"^/api/puzzles$", handle_list_puzzles)
    router.add_route("POST", r"^/api/puzzles$", handle_create_puzzle)
    router.add_route("GET", r"^/api/puzzles/([^/]+)$", handle_load_puzzle)
    router.add_route("DELETE", r"^/api/puzzles/([^/]+)$", handle_delete_puzzle)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/copy$", handle_copy_puzzle)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/open$", handle_open_puzzle_for_editing)
    router.add_route("PUT",  r"^/api/puzzles/([^/]+)/title$", handle_set_puzzle_title)
    router.add_route("PUT", r"^/api/puzzles/([^/]+)/cells/(\d+)/(\d+)$", handle_set_cell_letter)
    router.add_route("GET",  r"^/api/puzzles/([^/]+)/words/(\d+)/([a-z]+)$", handle_get_word_at)
    router.add_route("PUT",  r"^/api/puzzles/([^/]+)/words/(\d+)/([a-z]+)$", handle_set_word_clue)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/words/(\d+)/([a-z]+)/reset$", handle_reset_word)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/undo$", handle_undo_puzzle)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/redo$", handle_redo_puzzle)
    router.add_route("PUT", r"^/api/puzzles/([^/]+)/grid$", handle_replace_puzzle_grid)

    # Word routes
    router.add_route("GET", r"^/api/words/suggestions$", handle_get_suggestions)
    router.add_route("GET", r"^/api/words/all$", handle_get_all_words)
    router.add_route("GET", r"^/api/words/validate$", handle_validate_word)

    # Export routes
    router.add_route("GET", r"^/api/export/grids/([^/]+)/pdf$", handle_export_grid_to_pdf)
    router.add_route("GET", r"^/api/export/grids/([^/]+)/png$", handle_export_grid_to_png)
    router.add_route("GET", r"^/api/export/puzzles/([^/]+)/puz$", handle_export_puzzle_to_puz)
    router.add_route("GET", r"^/api/export/puzzles/([^/]+)/xml$", handle_export_puzzle_to_xml)


def run_http_server(host: str = "127.0.0.1", port: int = 5000, config=None):
    """
    Start the HTTP server with all routes registered.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to listen on (default: 5000)
        config: Configuration dict with 'dbfile' and optionally 'word_file'
    """
    print(f"Initializing app...")
    app_container = make_app(config)

    print(f"Creating HTTP server...")
    server, router = create_server(port=port, host=host)

    print(f"Registering routes...")
    register_routes(router)

    print(f"Starting HTTP server on http://{host}:{port}")
    start_server(server, router, app_container, host=host, port=port)


if __name__ == "__main__":
    import sys
    import os

    # Optionally read config from env or default
    config = None  # Will use defaults from ~/.crossword.ini

    # Optional: accept port from command line
    port = int(os.environ.get("CROSSWORD_PORT", "5000"))
    host = os.environ.get("CROSSWORD_HOST", "127.0.0.1")

    run_http_server(host=host, port=port, config=config)
