"""
HTTP Server main entry point - registers all routes and starts the server.
"""

from crossword.http_server.server import create_server, start_server
from crossword.wiring import make_app

# Import all handlers
from crossword.http_server.static_handlers import handle_get_index, handle_get_login, handle_get_static, handle_get_config
from crossword.http_server.puzzle_handlers import (
    handle_list_puzzles,
    handle_create_puzzle,
    handle_load_puzzle,
    handle_delete_puzzle,
    handle_copy_puzzle,
    handle_rename_puzzle,
    handle_open_puzzle_for_editing,
    handle_switch_to_grid_mode,
    handle_switch_to_puzzle_mode,
    handle_set_puzzle_title,
    handle_toggle_puzzle_black_cell,
    handle_rotate_puzzle_grid,
    handle_generate_puzzle_grid,
    handle_undo_puzzle_grid,
    handle_redo_puzzle_grid,
    handle_reset_word,
    handle_set_cell_letter,
    handle_get_word_at,
    handle_set_word_clue,
    handle_undo_puzzle,
    handle_redo_puzzle,
    handle_get_puzzle_preview,
    handle_get_puzzle_stats,
    handle_get_fill_order,
)
from crossword.http_server.word_handlers import (
    handle_get_suggestions,
    handle_get_all_words,
    handle_validate_word,
    handle_get_word_constraints,
    handle_get_ranked_suggestions,
)
from crossword.http_server.export_handlers import (
    handle_export_puzzle_to_acrosslite,
    handle_export_puzzle_to_xml,
    handle_export_puzzle_to_nytimes,
    handle_export_puzzle_to_json,
)
from crossword.http_server.import_handlers import handle_import_puzzle_from_acrosslite
from crossword.http_server.auth_handlers import handle_login, handle_logout, handle_me


def register_routes(router):
    """
    Register all API routes with the router.
    """
    # Auth routes (public)
    router.add_route("POST", r"^/api/auth/login$", handle_login, requires_auth=False)
    router.add_route("POST", r"^/api/auth/logout$", handle_logout, requires_auth=False)
    router.add_route("GET", r"^/api/auth/me$", handle_me, requires_auth=False)

    # Static file serving (public)
    router.add_route("GET", r"^/$", handle_get_index, requires_auth=False)
    router.add_route("GET", r"^/login$", handle_get_login, requires_auth=False)
    router.add_route("GET", r"^/static/(.+)$", handle_get_static, requires_auth=False)

    # Frontend configuration
    router.add_route("GET", r"^/api/config$", handle_get_config, requires_auth=False)

    # Puzzle routes
    router.add_route("GET", r"^/api/puzzles$", handle_list_puzzles)
    router.add_route("POST", r"^/api/puzzles$", handle_create_puzzle)
    router.add_route("GET", r"^/api/puzzles/([^/]+)$", handle_load_puzzle)
    router.add_route("DELETE", r"^/api/puzzles/([^/]+)$", handle_delete_puzzle)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/copy$", handle_copy_puzzle)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/rename$", handle_rename_puzzle)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/open$", handle_open_puzzle_for_editing)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/mode/grid$", handle_switch_to_grid_mode)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/mode/puzzle$", handle_switch_to_puzzle_mode)
    router.add_route("PUT",  r"^/api/puzzles/([^/]+)/title$", handle_set_puzzle_title)
    router.add_route("PUT", r"^/api/puzzles/([^/]+)/grid/cells/(\d+)/(\d+)$", handle_toggle_puzzle_black_cell)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/grid/rotate$", handle_rotate_puzzle_grid)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/grid/generate$", handle_generate_puzzle_grid)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/grid/undo$", handle_undo_puzzle_grid)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/grid/redo$", handle_redo_puzzle_grid)
    router.add_route("PUT", r"^/api/puzzles/([^/]+)/cells/(\d+)/(\d+)$", handle_set_cell_letter)
    router.add_route("GET",  r"^/api/puzzles/([^/]+)/words/(\d+)/([a-z]+)$", handle_get_word_at)
    router.add_route("PUT",  r"^/api/puzzles/([^/]+)/words/(\d+)/([a-z]+)$", handle_set_word_clue)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/words/(\d+)/([a-z]+)/reset$", handle_reset_word)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/undo$", handle_undo_puzzle)
    router.add_route("POST", r"^/api/puzzles/([^/]+)/redo$", handle_redo_puzzle)
    router.add_route("GET", r"^/api/puzzles/([^/]+)/preview$", handle_get_puzzle_preview)
    router.add_route("GET", r"^/api/puzzles/([^/]+)/stats$", handle_get_puzzle_stats)
    router.add_route("GET", r"^/api/puzzles/([^/]+)/fill-order$", handle_get_fill_order)

    # Word routes
    router.add_route("GET", r"^/api/words/suggestions$", handle_get_suggestions)
    router.add_route("GET", r"^/api/words/all$", handle_get_all_words)
    router.add_route("GET", r"^/api/words/validate$", handle_validate_word)
    router.add_route("GET", r"^/api/puzzles/([^/]+)/words/(\d+)/([a-z]+)/constraints$", handle_get_word_constraints)
    router.add_route("GET", r"^/api/puzzles/([^/]+)/words/(\d+)/([a-z]+)/suggestions$", handle_get_ranked_suggestions)

    # Export routes
    router.add_route("GET", r"^/api/export/puzzles/([^/]+)/acrosslite$", handle_export_puzzle_to_acrosslite)
    router.add_route("GET", r"^/api/export/puzzles/([^/]+)/xml$", handle_export_puzzle_to_xml)
    router.add_route("GET", r"^/api/export/puzzles/([^/]+)/nytimes$", handle_export_puzzle_to_nytimes)
    router.add_route("GET", r"^/api/export/puzzles/([^/]+)/json$", handle_export_puzzle_to_json)

    # Import routes
    router.add_route("POST", r"^/api/import/acrosslite$", handle_import_puzzle_from_acrosslite)


def run_http_server(config=None):
    """
    Start the HTTP server with all routes registered.

    Args:
        config: Configuration dict. Required keys: 'dbfile', 'host', 'port'.
                If None, loaded from ~/.config/crossword/config.yaml.
    """
    print(f"Initializing app...")
    app_container = make_app(config)

    host = app_container.config["host"]
    port = int(app_container.config["port"])

    print(f"Creating HTTP server...")
    server, router = create_server(port=port, host=host)

    print(f"Registering routes...")
    register_routes(router)

    print(f"Starting HTTP server on http://{host}:{port}")
    start_server(server, router, app_container, host=host, port=port)
