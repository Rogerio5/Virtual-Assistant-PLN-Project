# tests/test_assistant_routes.py
import io
import os
from pathlib import Path
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.routes.assistant_routes as ar


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(ar.router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_process_command_with_text_input(monkeypatch, client):
    # Simula TTS retornando caminho relativo
    monkeypatch.setattr(ar, "text_to_speech", type("M", (), {"speak": lambda *_, **__: "static/tts/resp.mp3"}), raising=False)
    # Garante que speech_to_text não será chamado
    monkeypatch.setattr(ar, "speech_to_text", type("M", (), {"recognize": lambda *_: None}), raising=False)

    payload = {"text_input": "Qual é a previsão do tempo?"}
    resp = client.post("/assistant/process", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "Você perguntou" in data["response"]
    # base_url do TestClient é http://testserver
    assert data["audio"].startswith("http://testserver/")
    assert data["input"] == "Qual é a previsão do tempo?"


def test_process_command_with_audio_file_path(monkeypatch, tmp_path, client):
    # cria arquivo de áudio fake no disco
    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"RIFFFAKE")
    # monkeypatch para transcrição
    monkeypatch.setattr(ar, "speech_to_text", type("M", (), {"recognize": lambda path: "Transcrito do áudio"}), raising=False)
    # monkeypatch TTS
    monkeypatch.setattr(ar, "text_to_speech", type("M", (), {"speak": lambda text: "static/tts/resp2.mp3"}), raising=False)

    payload = {"audio_file": str(audio_file)}
    resp = client.post("/assistant/process", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["input"] == "Transcrito do áudio"
    assert "Você perguntou" in data["response"]
    assert data["audio"].startswith("http://testserver/")


def test_process_upload_wav_file(monkeypatch, client):
    # monkeypatch speech_to_text to return text for the uploaded wav
    monkeypatch.setattr(ar, "speech_to_text", type("M", (), {"recognize": lambda path: "texto do upload"}), raising=False)
    # monkeypatch TTS to return relative path
    monkeypatch.setattr(ar, "text_to_speech", type("M", (), {"speak": lambda text: "static/tts/upload_resp.mp3"}), raising=False)

    # envia arquivo wav via multipart/form-data
    files = {"file": ("audio.wav", b"RIFFFAKEWAV", "audio/wav")}
    resp = client.post("/assistant/process/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["input"] == "texto do upload"
    assert data["audio"].startswith("http://testserver/")


def test_process_upload_unsupported_extension(client):
    files = {"file": ("malware.exe", b"FAKE", "application/octet-stream")}
    resp = client.post("/assistant/process/upload", files=files)
    assert resp.status_code == 415
    assert "Formato não suportado" in resp.json()["detail"]


def test_process_upload_exceeds_max_size(monkeypatch, client):
    # define limite pequeno
    monkeypatch.setattr(ar, "MAX_UPLOAD_SIZE_BYTES", 5, raising=False)
    # envia arquivo maior que o limite
    files = {"file": ("big.wav", b"1234567890", "audio/wav")}
    resp = client.post("/assistant/process/upload", files=files)
    assert resp.status_code == 413
    assert "Arquivo excede o tamanho máximo" in resp.json()["detail"]


def test_process_upload_conversion_error(monkeypatch, tmp_path, client):
    # envia arquivo com extensão não-wav para forçar conversão
    # monkeypatch which to pretend ffmpeg is available
    monkeypatch.setattr(ar, "_ensure_ffmpeg_available", lambda: None, raising=False)
    # monkeypatch _convert_to_wav to raise CalledProcessError
    def raise_called(*args, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=["ffmpeg"])
    import subprocess
    monkeypatch.setattr(ar, "_convert_to_wav", raise_called, raising=False)

    # create a fake mp3 file content
    files = {"file": ("audio.mp3", b"FAKEMP3", "audio/mpeg")}
    resp = client.post("/assistant/process/upload", files=files)
    assert resp.status_code == 500
    assert "Falha ao converter" in resp.json()["detail"] or "Erro ao processar upload" in resp.json()["detail"]
