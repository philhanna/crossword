# Crossword model classes
__all__ = [
    'Grid',
    'NumberedCell',
    'Puzzle',
    'ToSVG', 'GridToSVG', 'PuzzleToSVG',
    'Visitor',
    'WordList',
    'Word', 'AcrossWord', 'DownWord',
    'dbfile',
    'sha256',
    'config',
]


def init_config():
    import os.path
    import logging
    import configparser

    defaults = {
        'dbfile': "samples.db",
        'log_level': "INFO",
    }
    filename = os.path.expanduser("~/.crossword.ini")
    config = configparser.ConfigParser(defaults=defaults)
    if os.path.exists(filename):
        config.read(filename)
    else:
        msg = f"Using default configuration because .config.ini file was not found.  See README.md"
        logging.warning(msg)
    options = {}
    for k, v in config['DEFAULT'].items():
        options[k] = v
    return options


config = init_config()


def dbfile():
    return config['dbfile']


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


from .numbered_cell import *
from .visitor import *
from .grid import *
from .word import *
from .puzzle import *
from .to_svg import *
from .wordlist import *
