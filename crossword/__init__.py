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


def get_default_config_path():
    import os
    import sys

    if sys.platform == "win32":
        import ntpath
        appdata = os.environ.get("APPDATA")
        if appdata:
            return ntpath.join(appdata, "crossword", "config.yaml")

    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/crossword/config.yaml")

    return os.path.expanduser("~/.config/crossword/config.yaml")


def get_bootstrap_config():
    import os
    import os.path

    this_dir = os.path.dirname(__file__)
    project_root_dir = os.path.dirname(this_dir)
    samples_dir = os.path.join(project_root_dir, "samples")

    options = {
        'host': "127.0.0.1",
        'port': 5000,
        'log_level': "INFO",
        'message_line_timeout_ms': 2000,
        'author_name': "Your Name",
        'author_address': "123 Main St, City, ST 12345",
        'author_email': "you@example.com",
    }

    sample_dbfile = os.path.join(samples_dir, "crossword.db")
    if os.path.exists(sample_dbfile):
        options['dbfile'] = sample_dbfile

    sample_word_file = os.path.join(samples_dir, "words.txt")
    if os.path.exists(sample_word_file):
        options['word_file'] = sample_word_file

    return options


def init_config():
    import os
    import os.path
    import logging
    import yaml

    defaults = get_bootstrap_config()
    filename = get_default_config_path()
    if os.path.exists(filename):
        with open(filename) as f:
            loaded = yaml.safe_load(f) or {}
        options = {**defaults, **loaded}
    else:
        logging.warning(
            "Config file not found: %s. Using bootstrap configuration. "
            "Save settings to create it permanently.",
            filename,
        )
        options = defaults

    if os.environ.get('DATABASE_URL'):
        options['database_url'] = os.environ['DATABASE_URL']

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
