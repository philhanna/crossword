"""
Dependency wiring module - assembles adapters and injects them into use cases.

Single entry point: make_app(config) returns an AppContainer with all use cases,
ready for HTTP handlers or CLI commands to call.
"""

import logging

from crossword.adapters.sqlite_persistence_adapter import SQLitePersistenceAdapter
from crossword.adapters.sqlite_dictionary_adapter import SQLiteDictionaryAdapter
from crossword.adapters.acrosslite_export_adapter import AcrossLiteExportAdapter
from crossword.adapters.acrosslite_import_adapter import AcrossLiteImportAdapter
from crossword.adapters.ccxml_export_adapter import CcxmlExportAdapter
from crossword.adapters.nytimes_export_adapter import NYTimesExportAdapter
from crossword.adapters.json_export_adapter import JsonExportAdapter
from crossword.adapters.solver_pdf_export_adapter import SolverPdfExportAdapter
from crossword.adapters.sqlite_user_adapter import SQLiteUserAdapter
from crossword.adapters.dictionary_api_definition_adapter import DictionaryAPIDefinition
from crossword.adapters.memory_session_store import MemorySessionStore
from crossword.use_cases.puzzle_use_cases import PuzzleUseCases
from crossword.use_cases.word_use_cases import WordUseCases
from crossword.use_cases.export_use_cases import ExportUseCases
from crossword.use_cases.import_use_cases import ImportUseCases
from crossword.use_cases.auth_use_cases import AuthUseCases
from crossword.use_cases.definition_use_cases import DefinitionUseCases
from crossword.use_cases.user_use_cases import UserUseCases


class AppContainer:
    """
    Container holding all use cases and their dependencies.

    Instances are created by make_app() and used by HTTP handlers/CLI.
    Single-threaded; one container per process.
    """

    def __init__(self, puzzle_uc, word_uc, export_uc=None, import_uc=None,
                 auth_uc=None, user_uc=None, definition_uc=None, config=None):
        self.puzzle_uc = puzzle_uc
        self.word_uc = word_uc
        self.export_uc = export_uc
        self.import_uc = import_uc
        self.auth_uc = auth_uc
        self.user_uc = user_uc
        self.definition_uc = definition_uc
        self.config = config or {}


def make_app(config=None):
    """
    Assemble adapters and wire them into use cases.

    Args:
        config: Dict with optional keys 'dbfile', 'word_dbfile', 'word_file'
                (or None to use defaults from ~/.config/crossword/config.yaml).
                Word list load priority: word_dbfile → word_file → dbfile (legacy) → empty.

    Returns:
        AppContainer instance with all use cases ready to use

    Raises:
        Exception: If adapters fail to initialize (e.g., database not found, word file missing)
    """
    if config is None:
        # Import here to avoid circular imports and module shadowing
        from crossword import init_config
        config = init_config()

    log_level = getattr(logging, config.get("log_level", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d: %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

    logger = logging.getLogger(__name__)
    logger.info("Configuration:")
    for key, value in config.items():
        logger.info("%s = %r", key, value)

    # ========================================================================
    # Validate required config keys
    # ========================================================================

    # ========================================================================
    # Instantiate Adapters
    # ========================================================================

    dbfile = config.get("dbfile")
    if not dbfile:
        raise ValueError("config['dbfile'] is required")
    persistence = SQLitePersistenceAdapter(dbfile)
    user_adapter = SQLiteUserAdapter(persistence.conn)

    # Word list adapter — priority: word_dbfile → word_file → dbfile (legacy) → empty
    word_dbfile = config.get("word_dbfile")
    word_file = config.get("word_file")
    word_adapter = SQLiteDictionaryAdapter()
    if word_dbfile:
        word_adapter.load_from_database(word_dbfile)
    elif word_file:
        word_adapter.load_from_file(word_file)
    elif dbfile:
        try:
            word_adapter.load_from_database(dbfile)
        except Exception:
            pass  # words table absent in puzzle DB — leave adapter empty

    # Export adapters
    acrosslite_adapter = AcrossLiteExportAdapter(author_name=config.get("author_name"))
    xml_adapter = CcxmlExportAdapter(author_name=config.get("author_name"))
    nytimes_adapter = NYTimesExportAdapter(
        author_name=config.get("author_name"),
        author_address=config.get("author_address"),
        author_email=config.get("author_email"),
    )
    json_adapter = JsonExportAdapter()
    solver_pdf_adapter = SolverPdfExportAdapter()

    # ========================================================================
    # Instantiate Use Cases (with constructor injection)
    # ========================================================================

    acrosslite_import_adapter = AcrossLiteImportAdapter()

    word_uc = WordUseCases(word_adapter)
    puzzle_uc = PuzzleUseCases(persistence, word_uc=word_uc)
    export_uc = ExportUseCases(persistence, acrosslite_adapter, xml_adapter, nytimes_adapter, json_adapter, solver_pdf_adapter)
    import_uc = ImportUseCases(persistence, acrosslite_import_adapter)

    if not config.get("host"):
        raise ValueError("config['host'] is required")
    if not config.get("port"):
        raise ValueError("config['port'] is required")

    session_store = MemorySessionStore()
    auth_uc = AuthUseCases(user_adapter, session_store)
    user_uc = UserUseCases(user_adapter)

    definition_uc = DefinitionUseCases(DictionaryAPIDefinition())

    # ========================================================================
    # Assemble Container
    # ========================================================================

    return AppContainer(puzzle_uc, word_uc, export_uc, import_uc, auth_uc=auth_uc, user_uc=user_uc,
                        definition_uc=definition_uc, config=config)
