"""Tests for srs.config — config loader."""

from srs.config import get, invalidate_cache, load_config, save_config


def test_load_config_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("srs.config._config_cache", None)
    monkeypatch.setattr("srs.config.config_path", lambda: tmp_path / "config")
    cfg = load_config()
    assert cfg == {}


def test_save_and_load_config(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config"
    monkeypatch.setattr("srs.config.config_path", lambda: cfg_path)
    monkeypatch.setattr("srs.config._config_cache", None)

    save_config({"OBSIDIAN_VAULT": "/tmp/vault", "THEME": "dracula"})
    invalidate_cache()
    cfg = load_config()

    assert cfg["OBSIDIAN_VAULT"] == "/tmp/vault"
    assert cfg["THEME"] == "dracula"


def test_get_with_default(tmp_path, monkeypatch):
    monkeypatch.setattr("srs.config.config_path", lambda: tmp_path / "config")
    monkeypatch.setattr("srs.config._config_cache", None)
    assert get("NONEXISTENT", "fallback") == "fallback"


def test_get_expands_home(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config"
    cfg_path.write_text('VAULT="$HOME/my-vault"\n')
    monkeypatch.setattr("srs.config.config_path", lambda: cfg_path)
    monkeypatch.setattr("srs.config._config_cache", None)

    result = get("VAULT")
    assert "$HOME" not in result
    assert "my-vault" in result


def test_config_is_cached(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config"
    cfg_path.write_text('KEY="value"\n')
    monkeypatch.setattr("srs.config.config_path", lambda: cfg_path)
    monkeypatch.setattr("srs.config._config_cache", None)

    cfg1 = load_config()
    cfg2 = load_config()
    assert cfg1 is cfg2  # Same object, cached


def test_invalidate_cache(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config"
    cfg_path.write_text('KEY="old"\n')
    monkeypatch.setattr("srs.config.config_path", lambda: cfg_path)
    monkeypatch.setattr("srs.config._config_cache", None)

    load_config()
    invalidate_cache()
    cfg_path.write_text('KEY="new"\n')
    cfg = load_config()
    assert cfg["KEY"] == "new"
