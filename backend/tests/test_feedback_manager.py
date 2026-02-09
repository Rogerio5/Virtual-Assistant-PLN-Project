# tests/test_feedback_manager.py
import json
from pathlib import Path
import pytest
from typing import cast, Any

import backend.services.feedback_manager as fm


def test_save_feedback_returns_id_and_logs(tmp_path, monkeypatch):
    # Redireciona o arquivo de feedback para o tmp_path
    fake_file = tmp_path / "feedbacks.json"
    monkeypatch.setattr(fm, "FEEDBACK_FILE", fake_file)

    payload = {"user": "tester", "message": "ótimo sistema!", "rating": 5}
    fid = fm.save_feedback(payload, persist=False)
    assert fid is not None
    assert isinstance(fid, str)
    # Como persist=False, o arquivo não deve existir
    assert not fake_file.exists()


def test_save_feedback_persists_file_when_requested(tmp_path, monkeypatch):
    fake_file = tmp_path / "feedbacks.json"
    monkeypatch.setattr(fm, "FEEDBACK_FILE", fake_file)

    payload = {"user": "tester2", "message": "persistir este feedback", "rating": 4}
    fid = fm.save_feedback(payload, persist=True)
    assert fid is not None
    assert fake_file.exists()

    # Verifica conteúdo do arquivo
    with fake_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Deve ser uma lista com pelo menos um registro contendo o id salvo
    assert isinstance(data, list)
    assert any(item.get("id") == fid for item in data)


def test_save_feedback_invalid_input_returns_none(tmp_path, monkeypatch):
    # Garante que função retorna None para entrada inválida
    fake_file = tmp_path / "feedbacks.json"
    monkeypatch.setattr(fm, "FEEDBACK_FILE", fake_file)

    # Use cast para satisfazer o verificador de tipos estático (Pylance)
    invalid_input = cast(Any, "isto nao eh um dict")
    result = fm.save_feedback(invalid_input, persist=True)
    assert result is None
    # Arquivo não deve ter sido criado
    assert not fake_file.exists()
