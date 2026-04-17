# crossword.tests.test_init
import datetime
from unittest.mock import patch
import pytest
import crossword
from crossword import init_config


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
    assert 'dbfile' not in cfg
    assert cfg['log_level'] == 'INFO'
