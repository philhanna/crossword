# crossword.tests.test_init
import datetime
from unittest.mock import patch
import pytest
import crossword
from crossword import get_bootstrap_config, get_default_config_path, init_config


def test_get_elapsed_time():
    t1 = datetime.datetime(2024, 1, 1, 12, 0, 0, 0)
    t2 = datetime.datetime(2024, 1, 1, 12, 0, 3, 500000)
    assert crossword.get_elapsed_time(t1, t2) == pytest.approx(3.5)


def test_sha256_string():
    result = crossword.sha256("hello")
    assert isinstance(result, bytes)
    assert len(result) == 32


def test_sha256_none():
    result = crossword.sha256(None)
    assert result == crossword.sha256("")


def test_sha256_non_string():
    result = crossword.sha256(42)
    assert result == crossword.sha256("42")


def test_config_has_log_level():
    assert 'log_level' in crossword.config


def test_init_config_missing_file_uses_defaults(caplog):
    import logging
    with caplog.at_level(logging.WARNING):
        with patch('os.path.exists', return_value=False):
            cfg = init_config()
    assert 'Config file not found' in caplog.text
    assert cfg['host'] == '127.0.0.1'
    assert cfg['port'] == 5000
    assert cfg['log_level'] == 'INFO'


def test_get_bootstrap_config_uses_sample_assets_if_present():
    cfg = get_bootstrap_config()
    assert cfg['dbfile'].endswith('samples/crossword.db')
    assert cfg['word_file'].endswith('samples/words.txt')


def test_get_default_config_path_unix():
    with patch('sys.platform', 'linux'):
        assert get_default_config_path().endswith('.config/crossword/config.yaml')


def test_get_default_config_path_windows():
    with patch('sys.platform', 'win32'):
        with patch.dict('os.environ', {'APPDATA': r'C:\Users\Test\AppData\Roaming'}, clear=True):
            assert get_default_config_path() == r'C:\Users\Test\AppData\Roaming\crossword\config.yaml'


def test_get_default_config_path_windows_without_appdata_falls_back_to_unix_style():
    with patch('sys.platform', 'win32'):
        with patch.dict('os.environ', {}, clear=True):
            with patch('os.path.expanduser', return_value='/fallback/.config/crossword/config.yaml'):
                assert get_default_config_path() == '/fallback/.config/crossword/config.yaml'
