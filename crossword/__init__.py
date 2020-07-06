# Crossword model classes
__all__ = [
    'PuzzlePublishAcrossLite',
    'Configuration',
    'Grid',
    'NumberedCell',
    'PuzzlePublishNYTimes',
    'Puzzle',
    'ToSVG', 'GridToSVG', 'PuzzleToSVG',
    'Visitor',
    'WordList',
    'Word', 'AcrossWord', 'DownWord',
    'sha256',
]

from .numbered_cell import *
from .configuration import *
from .visitor import *
from .grid import *
from .word import *
from .puzzle import *
from .to_svg import *
from .puzzle_publish_acrosslite import *
from .puzzle_publish_nytimes import *
from .wordlist import *


def sha256(s):
    """ Computes a sha256 checksum for a string """
    if s is None:
        s = ""
    elif type(s) != str:
        s = str(s)

    import hashlib
    m = hashlib.sha256()
    m.update(bytes(s, 'utf-8'))
    value = m.digest()

    return value
