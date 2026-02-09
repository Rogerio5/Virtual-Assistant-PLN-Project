# tests/test_gravar_audio.py
import asyncio
import subprocess
from pathlib import Path
import pytest
from types import SimpleNamespace

import backend.services.gravar_audio as ga


def test_save_bytes_to_file_and_remove(tmp_path):
    content = b"TESTAUDIO"
    out = ga.save_bytes_to_file(content, prefix="testaudio", ext=".wav", dest_dir=tmp_path)
    assert out.exists()
    read = out.read_bytes()
    assert read == content

    # remove_file deve retornar True e o arquivo não deve existir depois
    removed = ga.remove_file(out)
    assert removed is True
    assert not out.exists()


@pytest.mark.asyncio
async def test_save_upload_file(tmp_path):
    # cria um "UploadFile" simulado com método async read e filename
    class DummyUpload:
        def __init__(self, filename: str, content: bytes):
            self.filename = filename
            self._content = content

        async def read(self):
            return self._content

    dummy = DummyUpload("meu_audio.mp3", b"FAKE_MP3_BYTES")
    out_path = await ga.save_upload_file(dummy, dest_dir=tmp_path)
    assert out_path.exists()
    assert out_path.read_bytes() == b"FAKE_MP3_BYTES"


def test_convert_to_wav_monkeypatched_ffmpeg(tmp_path, monkeypatch):
    """
    Simula a execução do ffmpeg criando o arquivo de saída esperado.
    Não requer ffmpeg real no PATH.
    """
    # cria um arquivo de entrada fake
    in_file = tmp_path / "input.mp3"
    in_file.write_bytes(b"FAKE_MP3")

    # monkeypatch para pular verificação de ffmpeg no PATH
    monkeypatch.setattr(ga, "_ensure_ffmpeg_available", lambda: None)

    # monkeypatch subprocess.run para simular sucesso e criar o arquivo de saída
    def fake_run(cmd, stdout=None, stderr=None):
        # o último argumento do cmd é o caminho de saída
        out_path = Path(cmd[-1])
        out_path.write_bytes(b"RIFF....WAVE")  # conteúdo WAV fake
        fake = SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
        return fake

    monkeypatch.setattr(subprocess, "run", fake_run)

    out_wav = ga.convert_to_wav(in_file, sample_rate=16000)
    assert out_wav.exists()
    assert out_wav.suffix == ".wav" or out_wav.name.endswith(".converted.wav")
    assert out_wav.read_bytes().startswith(b"RIFF")

    # cleanup
    assert ga.remove_file(out_wav) is True


def test_convert_to_wav_failure_removes_partial(tmp_path, monkeypatch):
    in_file = tmp_path / "input2.mp3"
    in_file.write_bytes(b"FAKE_MP3")

    monkeypatch.setattr(ga, "_ensure_ffmpeg_available", lambda: None)

    # Simula falha do ffmpeg e criação de arquivo parcial
    def fake_run_fail(cmd, stdout=None, stderr=None):
        out_path = Path(cmd[-1])
        out_path.write_bytes(b"PARTIAL")
        fake = SimpleNamespace(returncode=1, stdout=b"", stderr=b"error")
        return fake

    monkeypatch.setattr(subprocess, "run", fake_run_fail)

    with pytest.raises(RuntimeError):
        ga.convert_to_wav(in_file)

    # arquivo parcial deve ter sido removido pela função
    out_file = in_file.with_suffix(".converted.wav")
    assert not out_file.exists()
