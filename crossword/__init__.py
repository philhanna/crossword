# Crossword model classes
__all__ = [
    'get_elapsed_time',
    'Grid',
    'NumberedCell',
    'Puzzle',
    'ToSVG', 'GridToSVG', 'PuzzleToSVG',
    'regexp',
    'Word', 'AcrossWord', 'DownWord',
    'dbfile',
    'sha256',
    'config',
]


def get_elapsed_time(stime, etime):
    diff = etime - stime
    seconds = diff.seconds + diff.microseconds / 1000000
    return seconds


def init_config():
    import os.path
    import logging
    import yaml

    this_dir = os.path.dirname(__file__)
    project_root_dir = os.path.dirname(this_dir)

    defaults = {
        'dbfile': os.path.join(project_root_dir, "samples.db"),
        'log_level': "INFO",
    }
    filename = os.path.expanduser("~/.config/crossword/config.yaml")
    if os.path.exists(filename):
        with open(filename) as f:
            loaded = yaml.safe_load(f) or {}
        options = {**defaults, **loaded}
    else:
        logging.warning(f"Config file not found: {filename}. Using default configuration. See README.md")
        options = defaults
    logging.info(f"Using database at {options['dbfile']}")
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


from .domain import *
