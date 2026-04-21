"""
Concrete adapter implementations.
"""

from .dictionary_api_definition_adapter import DictionaryAPIDefinition
from .flat_file_word_list_adapter import FlatFileWordListAdapter
from .sqlite_persistence_adapter import SQLitePersistenceAdapter

__all__ = [
    "DictionaryAPIDefinition",
    "FlatFileWordListAdapter",
    "SQLitePersistenceAdapter",
]
