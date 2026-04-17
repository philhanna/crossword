"""
Concrete adapter implementations.
"""

from .dictionary_api_definition_adapter import DictionaryAPIDefinition
from .sqlite_dictionary_adapter import SQLiteDictionaryAdapter
from .sqlite_persistence_adapter import SQLitePersistenceAdapter

__all__ = [
    "DictionaryAPIDefinition",
    "SQLiteDictionaryAdapter",
    "SQLitePersistenceAdapter",
]
