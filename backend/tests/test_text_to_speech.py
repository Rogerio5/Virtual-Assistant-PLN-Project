# tests/test_text_to_speech.py
import sys
from pathlib import Path
import pytest

import backend.services.text_to_speech as tts_module


class DummyGTTS:
    def __init__(self, text: str, lang: str = "pt-br"):
        self.text = text
        self.lang = lang

    def save(self, path: str):
        # evita literal de bytes com caracteres não ASCII
        Path(path).write_bytes(f"MP3:{self.lang}:{self.text}".encode("utf-8"))


class RaisingGTTS(DummyGTTS):
    def save(self, path: str):
        raise RuntimeError("gTTS falhou")


def _prepare_tmp_dir(monkeypatch, tmp_path):
    dest = tmp_path / "tts"
    dest.mkdir(parents=True, exist_ok=True)
    # substitui STATIC_TTS_DIR do módulo para apontar para tmp_path/tts
    monkeypatch.setattr(tts_module, "STATIC_TTS_DIR", dest, raising=False)
    # garante settings coerentes para compor rel_path
    monkeypatch.setattr(tts_module.settings, "STATIC_DIR", str(tmp_path), raising=False)
    monkeypatch.setattr(tts_module.settings, "TTS_SUBDIR", "tts", raising=False)
    return dest


def test_speak_empty_text_returns_none(monkeypatch, tmp_path):
    _prepare_tmp_dir(monkeypatch, tmp_path)
    assert tts_module.speak("") is None
    assert tts_module.speak("   ") is None


def test_speak_creates_file_and_returns_relative_path(monkeypatch, tmp_path):
    dest = _prepare_tmp_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(tts_module, "gTTS", DummyGTTS, raising=False)
    monkeypatch.setattr(tts_module.settings, "BASE_URL", "", raising=False)

    out = tts_module.speak("Olá mundo", lang="pt-br", filename_prefix="test")
    assert isinstance(out, str)
    assert out.endswith(".mp3") or "test" in out

    created = list(dest.glob("test_*.mp3"))
    assert len(created) == 1
    # compara usando encode para evitar literal de bytes com caracteres não ASCII
    assert created[0].read_bytes().startswith("MP3:pt-br:Olá mundo".encode("utf-8"))


def test_speak_returns_full_url_when_base_url_set(monkeypatch, tmp_path):
    dest = _prepare_tmp_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(tts_module, "gTTS", DummyGTTS, raising=False)
    monkeypatch.setattr(tts_module.settings, "BASE_URL", "http://localhost/static", raising=False)

    out = tts_module.speak("Teste URL", lang="pt-br", filename_prefix="urltest")
    assert isinstance(out, str)
    assert out.startswith("http://localhost/static/")
    created = list(dest.glob("urltest_*.mp3"))
    assert len(created) == 1


def test_speak_handles_gtts_exception_and_returns_none(monkeypatch, tmp_path):
    dest = _prepare_tmp_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(tts_module, "gTTS", RaisingGTTS, raising=False)
    monkeypatch.setattr(tts_module.settings, "BASE_URL", "", raising=False)

    res = tts_module.speak("vai falhar", lang="pt-br", filename_prefix="failtest")
    assert res is None
    assert not any(dest.glob("failtest_*.mp3"))


def test_multiple_calls_generate_unique_filenames(monkeypatch, tmp_path):
    dest = _prepare_tmp_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(tts_module, "gTTS", DummyGTTS, raising=False)
    monkeypatch.setattr(tts_module.settings, "BASE_URL", "", raising=False)

    out1 = tts_module.speak("um", filename_prefix="uniq")
    out2 = tts_module.speak("dois", filename_prefix="uniq")
    assert out1 != out2

    files = list(dest.glob("uniq_*.mp3"))
    assert len(files) == 2
