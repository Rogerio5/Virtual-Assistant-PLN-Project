# tests/test_feedback_routes.py
import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast, Any

import pytest
from fastapi.background import BackgroundTasks

import backend.routes.feedback_routes as fr
from backend.routes.feedback_routes import FeedbackInput, FeedbackResponse


def test_generate_feedback_id_unique():
    a = fr._generate_feedback_id({"user": "u1"})
    b = fr._generate_feedback_id({"user": "u1"})
    assert isinstance(a, str) and isinstance(b, str)
    assert a != b


def test_fallback_save_feedback_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(fr, "DATA_DIR", tmp_path, raising=False)
    monkeypatch.setattr(fr, "FEEDBACK_FILE", tmp_path / "feedbacks.json", raising=False)

    feedback = {"user": "tester", "message": "otimo app", "rating": 5}
    fid = fr._fallback_save_feedback(feedback)
    assert isinstance(fid, str) and len(fid) > 0

    assert fr.FEEDBACK_FILE.exists()
    data = json.loads(fr.FEEDBACK_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert any(rec.get("id") == fid and rec.get("user") == "tester" for rec in data)


def test_write_feedbacks_atomic_replaces_file(tmp_path, monkeypatch):
    monkeypatch.setattr(fr, "DATA_DIR", tmp_path, raising=False)
    monkeypatch.setattr(fr, "FEEDBACK_FILE", tmp_path / "feedbacks.json", raising=False)

    fr._write_feedbacks_atomic([{"id": "a", "user": "u"}])
    assert fr.FEEDBACK_FILE.exists()
    first = json.loads(fr.FEEDBACK_FILE.read_text(encoding="utf-8"))
    assert first == [{"id": "a", "user": "u"}]

    fr._write_feedbacks_atomic([{"id": "b", "user": "v"}])
    second = json.loads(fr.FEEDBACK_FILE.read_text(encoding="utf-8"))
    assert second == [{"id": "b", "user": "v"}]


def test_save_feedback_via_manager_returns_various(monkeypatch):
    fake_mgr = SimpleNamespace(save_feedback=lambda fb: "abc123")
    monkeypatch.setattr(fr, "feedback_manager", fake_mgr, raising=False)
    res = fr._save_feedback_via_manager({"user": "x"})
    assert res == "abc123"

    fake_mgr = SimpleNamespace(save_feedback=lambda fb: {"id": "dictid"})
    monkeypatch.setattr(fr, "feedback_manager", fake_mgr, raising=False)
    res = fr._save_feedback_via_manager({"user": "x"})
    assert res == "dictid"

    fake_mgr = SimpleNamespace(save_feedback=lambda fb: None)
    monkeypatch.setattr(fr, "feedback_manager", fake_mgr, raising=False)
    res = fr._save_feedback_via_manager({"user": "x"})
    assert res is None


def test_save_feedback_via_manager_raises_when_missing(monkeypatch):
    fake_mgr = SimpleNamespace()
    monkeypatch.setattr(fr, "feedback_manager", fake_mgr, raising=False)
    with pytest.raises(AttributeError):
        fr._save_feedback_via_manager({"user": "x"})


def test_save_user_feedback_uses_manager(monkeypatch):
    monkeypatch.setattr(fr, "_save_feedback_via_manager", lambda fb: "okid", raising=False)

    inp = FeedbackInput(user="u", message="m", rating=4)

    class DummyBG:
        def __init__(self):
            self.tasks = []

        def add_task(self, func, *args, **kwargs):
            self.tasks.append((func, args, kwargs))

    bg = DummyBG()
    # cast para BackgroundTasks para satisfazer o verificador de tipos estático
    resp = fr.save_user_feedback(inp, cast(BackgroundTasks, bg))
    assert isinstance(resp, FeedbackResponse)
    assert resp.saved is True
    assert resp.id == "okid"
    assert bg.tasks == []


def test_save_user_feedback_fallback_when_manager_missing(monkeypatch):
    def raise_attr(fb):
        raise AttributeError("no manager")
    monkeypatch.setattr(fr, "_save_feedback_via_manager", raise_attr, raising=False)

    inp = FeedbackInput(user="u2", message="m2", rating=None)

    class DummyBG:
        def __init__(self):
            self.tasks = []

        def add_task(self, func, *args, **kwargs):
            self.tasks.append((func, args, kwargs))

    bg = DummyBG()
    resp = fr.save_user_feedback(inp, cast(BackgroundTasks, bg))
    assert isinstance(resp, FeedbackResponse)
    assert resp.saved is True
    assert resp.id is None
    assert len(bg.tasks) == 1
    func, args, kwargs = bg.tasks[0]
    assert func == fr._fallback_save_feedback
    assert isinstance(args[0], dict)
    assert args[0]["user"] == "u2"


def test_save_user_feedback_manager_error_then_fallback(monkeypatch):
    def raise_exc(fb):
        raise RuntimeError("boom")
    monkeypatch.setattr(fr, "_save_feedback_via_manager", raise_exc, raising=False)

    inp = FeedbackInput(user="u3", message="m3", rating=3)

    class DummyBG:
        def __init__(self):
            self.tasks = []

        def add_task(self, func, *args, **kwargs):
            self.tasks.append((func, args, kwargs))

    bg = DummyBG()
    resp = fr.save_user_feedback(inp, cast(BackgroundTasks, bg))
    assert isinstance(resp, FeedbackResponse)
    assert resp.saved is True
    assert resp.detail is not None
    assert len(bg.tasks) == 1
    func, args, kwargs = bg.tasks[0]
    assert func == fr._fallback_save_feedback


def test_feedback_input_validators():
    with pytest.raises(Exception):
        FeedbackInput(user="   ", message="ok")

    with pytest.raises(Exception):
        FeedbackInput(user="u", message="   ")

    with pytest.raises(Exception):
        FeedbackInput(user="u", message="ok", rating=10)
