"""
Concrete adapter implementations.
"""

from .flat_file_word_list_adapter import FlatFileWordListAdapter
from .sqlite_dictionary_adapter import SQLiteDictionaryAdapter
from .sqlite_persistence_adapter import SQLitePersistenceAdapter

__all__ = [
    "FlatFileWordListAdapter",
    "SQLiteDictionaryAdapter",
    "SQLitePersistenceAdapter",
]
