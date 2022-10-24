# Crossword model classes
__all__ = [
    'dbfile',
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
        msg = f".crossword.ini file was not found. Using default configuration. See README.md"
        logging.warning(msg)
        # Adjust dbfile for correct path, relative to the package
        this_dir = os.path.dirname(__file__)
        project_root_dir = os.path.dirname(this_dir)
        v = config['DEFAULT']['dbfile']
        dbfile = os.path.join(project_root_dir, v)
        config['DEFAULT']['dbfile'] = dbfile
    options = {}
    for k, v in config['DEFAULT'].items():
        options[k] = v
    logging.info(f"Using database at {options['dbfile']}")
    return options


config = init_config()


def dbfile():
    return config['dbfile']

