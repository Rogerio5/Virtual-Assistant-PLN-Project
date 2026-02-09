# tests/test_config.py
import importlib
import os
from pathlib import Path

import pytest

# Import module under test
import backend.config as cfg


def reload_config_module():
    """
    Força recarregar o módulo backend.config para que alterações em os.environ
    sejam refletidas na instância global `settings`.
    """
    importlib.reload(cfg)
    return cfg


def test_split_origins_empty_and_multiple():
    assert cfg._split_origins(None) == []
    assert cfg._split_origins("") == []
    assert cfg._split_origins("http://a, http://b , ,http://c") == ["http://a", "http://b", "http://c"]
    # if a list is passed, it should be returned as list
    assert cfg._split_origins(["x", "y"]) == ["x", "y"]


def test_int_env_parsing_and_default(monkeypatch):
    monkeypatch.delenv("SOME_INT", raising=False)
    assert cfg._int_env("SOME_INT", default=7) == 7

    monkeypatch.setenv("SOME_INT", "42")
    assert cfg._int_env("SOME_INT", default=0) == 42

    monkeypatch.setenv("SOME_INT", "notint")
    assert cfg._int_env("SOME_INT", default=5) == 5


def test_bool_env_parsing(monkeypatch):
    monkeypatch.delenv("FLAG", raising=False)
    assert cfg._bool_env("FLAG", default=True) is True

    for val in ("1", "true", "True", "YES", "on"):
        monkeypatch.setenv("FLAG", val)
        assert cfg._bool_env("FLAG", default=False) is True

    monkeypatch.setenv("FLAG", "0")
    assert cfg._bool_env("FLAG", default=True) is False


def test_settings_defaults_and_env_overrides(monkeypatch, tmp_path):
    # Ensure environment is clean for relevant vars
    for k in ("PROJECT_NAME", "PORT", "STATIC_DIR", "TTS_STATIC_SUBDIR", "BASE_URL", "FRONTEND_ORIGINS"):
        monkeypatch.delenv(k, raising=False)

    # Reload module to pick up cleared env
    cfg = reload_config_module()
    s = cfg.settings
    assert isinstance(s.PROJECT_NAME, str)
    assert s.PORT == 8000  # default fallback
    assert s.STATIC_DIR == "static"
    assert s.TTS_SUBDIR == "tts"
    assert s.BASE_URL is None or isinstance(s.BASE_URL, (str, type(None)))

    # Now set some env vars and reload
    monkeypatch.setenv("PROJECT_NAME", "MyApp")
    monkeypatch.setenv("PORT", "12345")
    monkeypatch.setenv("STATIC_DIR", str(tmp_path / "staticfiles"))
    monkeypatch.setenv("TTS_STATIC_SUBDIR", "mytts")
    monkeypatch.setenv("BASE_URL", "http://example.com/static")
    monkeypatch.setenv("FRONTEND_ORIGINS", "http://a.com, http://b.com")

    cfg = reload_config_module()
    s2 = cfg.settings
    assert s2.PROJECT_NAME == "MyApp"
    assert s2.PORT == 12345
    assert s2.STATIC_DIR == str(tmp_path / "staticfiles")
    assert s2.TTS_SUBDIR == "mytts"
    assert s2.BASE_URL == "http://example.com/static"
    assert s2.FRONTEND_ORIGINS == ["http://a.com", "http://b.com"]


def test_database_url_composition(monkeypatch):
    # Clear DATABASE_URL and set components
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p")
    monkeypatch.setenv("DB_HOST", "dbhost")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("DB_NAME", "mydb")

    cfg = reload_config_module()
    s = cfg.settings
    assert s.DATABASE_URL is not None
    assert "u:p@" in s.DATABASE_URL
    assert "dbhost:5433" in s.DATABASE_URL
    assert s.DATABASE_URL.endswith("/mydb")

    # If DB_USER/DB_PASSWORD missing, DATABASE_URL should be None (or unchanged if provided)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    cfg = reload_config_module()
    s2 = cfg.settings
    assert s2.DATABASE_URL is None


def test_max_content_length_default_and_env(monkeypatch):
    monkeypatch.delenv("MAX_CONTENT_LENGTH_BYTES", raising=False)
    cfg = reload_config_module()
    s = cfg.settings
    assert isinstance(s.MAX_CONTENT_LENGTH_BYTES, int)
    # override with env
    monkeypatch.setenv("MAX_CONTENT_LENGTH_BYTES", "1024")
    cfg = reload_config_module()
    s2 = cfg.settings
    assert s2.MAX_CONTENT_LENGTH_BYTES == 1024
