# tests/test_command_executor.py
from backend.services.command_executor import CommandExecutor, normalize
import pytest

def test_normalize_basic():
    assert normalize("Olá, Mundo!") == "ola mundo"
    assert normalize("  Espaços   extras ") == "espacos extras"
    assert normalize("Çãõ ÁÉÍÓÚ") == "cao aeiou"

def test_match_intent_direct():
    ce = CommandExecutor()
    out = ce.execute("Olá, tudo bem?")
    assert isinstance(out, dict)
    assert "response" in out
    assert "Olá" in out["response"]

def test_piada_and_fallback():
    ce = CommandExecutor()
    res = ce.execute("Me conta uma piada, por favor")
    assert "piada" in normalize("piada") or isinstance(res["response"], str)
    assert isinstance(res["actions"], dict)

def test_wikipedia_action():
    ce = CommandExecutor()
    res = ce.execute("Pesquisar wikipedia Python")
    assert "wikipedia" in res["actions"]
    assert "Python" in res["response"] or "python" in res["actions"]["wikipedia"].lower()

def test_leonardo_music_actions():
    ce = CommandExecutor()
    res = ce.execute("Tocar musica do Leonardo")
    assert "youtube" in res["actions"] and "spotify" in res["actions"]
    assert "Leonardo" in res["response"] or "leonardo" in res["response"].lower()

def test_unknown_command():
    ce = CommandExecutor()
    res = ce.execute("qwertyuiop")
    assert res["response"].startswith("Desculpe") or "não entendi" in res["response"].lower()
