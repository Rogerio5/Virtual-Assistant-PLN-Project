# tests/test_voice_pipeline.py
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.app as appmod


@pytest.fixture
def client():
    return TestClient(appmod.app)


def test_process_text_with_chatgpt_and_tts(monkeypatch, client):
    # Mock ChatGPT para retornar resposta transformada
    monkeypatch.setattr(appmod, "call_chatgpt_for_response", lambda text, lang="pt": f"RESP: {text}", raising=False)
    # Mock TTS para retornar data URI previsível
    monkeypatch.setattr(appmod, "synthesize_tts_data_uri", lambda text, lang_short, provider=None: "data:audio/mp3;base64,AAA", raising=False)

    resp = client.post("/assistant/process", data={"text": "Olá", "lang": "pt", "use_chatgpt": "1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["text"].startswith("RESP:")
    assert data["audio_data_uri"].startswith("data:audio/mp3;base64,")


def test_process_text_without_chatgpt(monkeypatch, client):
    # Garante que ChatGPT não é usado e TTS retorna vazio
    monkeypatch.setattr(appmod, "call_chatgpt_for_response", lambda text, lang="pt": "SHOULD_NOT_BE_CALLED", raising=False)
    monkeypatch.setattr(appmod, "synthesize_tts_data_uri", lambda text, lang_short, provider=None: "", raising=False)

    resp = client.post("/assistant/process", data={"text": "Só texto", "use_chatgpt": "0"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["text"] == "Só texto"
    assert data["audio_data_uri"] == ""


def test_process_upload_transcription_and_tts(monkeypatch, tmp_path, client):
    # Conteúdo fake de áudio
    fake_audio = b"RIFFFAKE"

    # Bypass ffmpeg: garante disponibilidade e simula conversão
    monkeypatch.setattr(appmod, "ensure_ffmpeg_available", lambda: None, raising=False)

    def fake_convert(in_path, out_path, sample_rate=16000):
        Path(out_path).write_bytes(b"WAVFAKE")
    monkeypatch.setattr(appmod, "run_ffmpeg_convert", fake_convert, raising=False)

    # Mock transcrição, ChatGPT e TTS
    monkeypatch.setattr(appmod, "transcribe_wav_with_model", lambda wav, language_code=None: ("transcribed text", {"info": "ok"}), raising=False)
    monkeypatch.setattr(appmod, "call_chatgpt_for_response", lambda text, lang="pt": "chatgpt reply", raising=False)
    monkeypatch.setattr(appmod, "synthesize_tts_data_uri", lambda text, lang_short, provider=None: "data:audio/mp3;base64,BBB", raising=False)

    files = {"file": ("audio.mp3", fake_audio, "audio/mpeg")}
    resp = client.post("/assistant/process/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["transcription"] == "transcribed text"
    assert data["text"] == "chatgpt reply"
    assert data["audio_data_uri"].startswith("data:audio/mp3;base64,")


def test_process_upload_large_file_rejected(monkeypatch, client):
    # Define limite pequeno para teste
    monkeypatch.setattr(appmod, "MAX_UPLOAD_SIZE", 5, raising=False)
    files = {"file": ("big.wav", b"1234567890", "audio/wav")}
    resp = client.post("/assistant/process/upload", files=files)
    assert resp.status_code == 413


def test_transcribe_raises_when_model_missing(monkeypatch):
    # Garante que MODEL é None e que a função lança RuntimeError
    monkeypatch.setattr(appmod, "MODEL", None, raising=False)
    with pytest.raises(RuntimeError):
        appmod.transcribe_wav_with_model("nonexistent.wav", None)
