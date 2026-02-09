# tests/test_speech_to_text.py
import pytest
from pathlib import Path
from types import ModuleType
import sys

import backend.services.speech_to_text as stt


class DummyModel:
    def __init__(self, text="transcrito"):
        self._text = text

    def transcribe(self, path, language=None):
        return {"text": self._text}


def make_whisper_module(model_obj):
    """
    Cria um ModuleType com função load_model que retorna model_obj.
    Usa setattr para evitar avisos de tipo do Pylance.
    """
    mod = ModuleType("whisper")
    def load_model(name):
        return model_obj
    setattr(mod, "load_model", load_model)
    return mod


def test_recognize_success(tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"FAKE")

    dummy_model = DummyModel(text="Olá mundo")
    dummy_whisper_mod = make_whisper_module(dummy_model)

    # injeta módulo whisper (ModuleType) em sys.modules
    sys.modules["whisper"] = dummy_whisper_mod

    # garante cache limpo
    stt._loaded_models.clear()

    text = stt.recognize(str(audio), model_name="base")
    assert isinstance(text, str)
    assert "Olá" in text or text == "Olá mundo"


def test_model_cached_between_calls(tmp_path):
    audio1 = tmp_path / "a1.mp3"
    audio1.write_bytes(b"FAKE1")
    audio2 = tmp_path / "a2.mp3"
    audio2.write_bytes(b"FAKE2")

    dummy_model = DummyModel(text="primeira")
    dummy_whisper_mod = make_whisper_module(dummy_model)

    sys.modules["whisper"] = dummy_whisper_mod

    stt._loaded_models.clear()

    t1 = stt.recognize(str(audio1), model_name="base")
    # altera texto do modelo para verificar reuso do mesmo objeto
    dummy_model._text = "segunda"
    t2 = stt.recognize(str(audio2), model_name="base")

    assert t1 == "primeira"
    assert t2 == "segunda"
    assert stt._loaded_models.get("base") is dummy_model


def test_recognize_missing_file():
    res = stt.recognize("arquivo_inexistente.mp3", model_name="base")
    assert res is None


def test_recognize_whisper_not_installed(monkeypatch, tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"FAKE")

    # garante que whisper não está importável
    sys.modules.pop("whisper", None)

    # força _load_whisper_model a lançar ImportError
    monkeypatch.setattr(stt, "_load_whisper_model", lambda name: (_ for _ in ()).throw(ImportError("no whisper")))

    res = stt.recognize(str(audio), model_name="base")
    assert res is None


def test_recognize_transcribe_raises(tmp_path):
    audio = tmp_path / "audio.mp3"
    audio.write_bytes(b"FAKE")

    class BadModel:
        def transcribe(self, *args, **kwargs):
            raise RuntimeError("boom")

    bad_whisper_mod = make_whisper_module(BadModel())
    sys.modules["whisper"] = bad_whisper_mod

    stt._loaded_models.clear()

    res = stt.recognize(str(audio), model_name="base")
    assert res is None
