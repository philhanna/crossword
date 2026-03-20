"""
Dependency wiring module - assembles adapters and injects them into use cases.

Single entry point: make_app(config) returns an AppContainer with all use cases,
ready for HTTP handlers or CLI commands to call.
"""

from crossword.adapters.sqlite_adapter import SQLiteAdapter
from crossword.adapters.dictionary_adapter import DictionaryAdapter
from crossword.use_cases.grid_use_cases import GridUseCases
from crossword.use_cases.puzzle_use_cases import PuzzleUseCases
from crossword.use_cases.word_use_cases import WordUseCases
from crossword.use_cases.export_use_cases import ExportUseCases


class AppContainer:
    """
    Container holding all use cases and their dependencies.

    Instances are created by make_app() and used by HTTP handlers/CLI.
    Single-threaded; one container per process.
    """

    def __init__(self, grid_uc, puzzle_uc, word_uc, export_uc=None):
        self.grid_uc = grid_uc
        self.puzzle_uc = puzzle_uc
        self.word_uc = word_uc
        self.export_uc = export_uc


def make_app(config=None):
    """
    Assemble adapters and wire them into use cases.

    Args:
        config: Dict with keys 'dbfile' and 'word_file' (or None to use defaults from ~/.crossword.ini)

    Returns:
        AppContainer instance with all use cases ready to use

    Raises:
        Exception: If adapters fail to initialize (e.g., database not found, word file missing)
    """
    if config is None:
        # Import here to avoid circular imports and module shadowing
        from crossword import init_config
        config = init_config()

    # ========================================================================
    # Instantiate Adapters
    # ========================================================================

    # Persistence adapter (SQLite)
    dbfile = config.get("dbfile")
    if not dbfile:
        raise ValueError("config['dbfile'] is required")
    persistence = SQLiteAdapter(dbfile)

    # Word list adapter (Dictionary)
    word_adapter = DictionaryAdapter()
    # Try to load from database first (most common case)
    try:
        word_adapter.load_from_database(dbfile)
    except Exception:
        # If that fails, try to load from a file if specified
        word_file = config.get("word_file")
        if word_file:
            word_adapter.load_from_file(word_file)
        else:
            # If no word file, adapter will just have empty dict (acceptable for testing)
            pass

    # Export adapter (not yet implemented; will be None)
    export_adapter = None

    # ========================================================================
    # Instantiate Use Cases (with constructor injection)
    # ========================================================================

    grid_uc = GridUseCases(persistence)
    puzzle_uc = PuzzleUseCases(persistence)
    word_uc = WordUseCases(word_adapter)
    export_uc = ExportUseCases(persistence, export_adapter) if export_adapter else None

    # ========================================================================
    # Assemble Container
    # ========================================================================

    return AppContainer(grid_uc, puzzle_uc, word_uc, export_uc)
