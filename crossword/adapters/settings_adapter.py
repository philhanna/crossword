import os
import yaml

SETTINGS_KEYS = [
    'host',
    'port',
    'dbfile',
    'xdfile',
    'word_file',
    'log_level',
    'message_line_timeout_ms',
    'theme_color',
    'author_name',
    'author_address',
    'author_email',
]

_RESTART_REQUIRED_KEYS = {'host', 'port', 'log_level', 'dbfile', 'xdfile', 'word_file', 'theme_color'}


def _config_path():
    from crossword import get_default_config_path
    return get_default_config_path()


def _load():
    path = _config_path()
    if os.path.exists(path):
        with open(path) as f:
            return yaml.safe_load(f) or {}
    from crossword import get_bootstrap_config
    return get_bootstrap_config()


def get_settings():
    loaded = _load()
    return {k: str(loaded[k]) if k in loaded else '' for k in SETTINGS_KEYS}


def put_settings(new_values):
    """Merge new_values into the user config file. Returns True if a restart is required."""
    path = _config_path()
    current = _load()
    os.makedirs(os.path.dirname(path), exist_ok=True)

    restart_required = False
    for k in SETTINGS_KEYS:
        if k not in new_values:
            continue
        v = new_values[k]
        old = str(current.get(k, ''))
        if v != old and k in _RESTART_REQUIRED_KEYS:
            restart_required = True
        if v == '':
            current.pop(k, None)
        else:
            current[k] = v

    with open(path, 'w') as f:
        yaml.safe_dump(current, f, default_flow_style=False, allow_unicode=True)

    return restart_required
