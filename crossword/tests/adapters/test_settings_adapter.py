import os

import yaml

from crossword.adapters import settings_adapter


def test_get_settings_falls_back_to_bootstrap_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    monkeypatch.setattr(settings_adapter, "_config_path", lambda: str(config_path))

    values = settings_adapter.get_settings()

    assert values["host"] == "127.0.0.1"
    assert values["port"] == "5000"
    assert values["dbfile"].endswith("samples/crossword.db")
    assert values["word_file"].endswith("samples/words.txt")
    assert values["theme_color"] == "#154d71"


def test_put_settings_creates_parent_directory(tmp_path, monkeypatch):
    config_dir = tmp_path / ".config" / "crossword"
    config_path = config_dir / "config.yaml"
    monkeypatch.setattr(settings_adapter, "_config_path", lambda: str(config_path))

    restart_required = settings_adapter.put_settings({
        "host": "127.0.0.1",
        "port": "5000",
        "dbfile": "/tmp/crossword.db",
        "theme_color": "#123456",
    })

    assert restart_required is True
    assert config_path.exists()
    with open(config_path) as f:
        saved = yaml.safe_load(f)
    assert saved["dbfile"] == "/tmp/crossword.db"
    assert saved["theme_color"] == "#123456"


def test_put_settings_preserves_unknown_keys(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("database_url: sqlite:///keep-me.db\nhost: 127.0.0.1\n", encoding="utf-8")
    monkeypatch.setattr(settings_adapter, "_config_path", lambda: str(config_path))

    restart_required = settings_adapter.put_settings({
        "host": "0.0.0.0",
    })

    assert restart_required is True
    with open(config_path) as f:
        saved = yaml.safe_load(f)
    assert saved["database_url"] == "sqlite:///keep-me.db"
    assert saved["host"] == "0.0.0.0"
