"""
Ports (Interfaces/Contracts) for the Hexagonal Architecture

This package defines the abstract interfaces (ports) that adapters must implement.
Ports are technology-agnostic contracts that define what operations are needed
but not how they are implemented.

Adapters implement these ports to provide concrete implementations (e.g., SQLite, file system).
"""

from .persistence_port import PersistencePort, PersistenceError
from .word_list_port import WordListPort
from .export_port import ExportPort, ExportError
from .definition_port import DefinitionProviderPort, DefinitionNotFound

__all__ = [
    "PersistencePort",
    "PersistenceError",
    "WordListPort",
    "ExportPort",
    "ExportError",
    "DefinitionProviderPort",
    "DefinitionNotFound",
]
