# backend/services/feedback_manager.py
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
import uuid

logger = logging.getLogger("feedback_manager")

# Configuração de arquivo de fallback (opcional)
DATA_DIR = Path("data")
FEEDBACK_FILE = DATA_DIR / "feedbacks.json"


def _ensure_data_dir() -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception("Não foi possível criar o diretório de dados: %s", DATA_DIR)


def _read_feedbacks() -> list:
    if not FEEDBACK_FILE.exists():
        return []
    try:
        with FEEDBACK_FILE.open("r", encoding="utf-8") as f:
            return json.load(f) or []
    except Exception:
        logger.exception("Falha ao ler arquivo de feedbacks; retornando lista vazia.")
        return []


def _write_feedbacks_atomic(feedbacks: list) -> None:
    tmp = FEEDBACK_FILE.with_suffix(".tmp")
    try:
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)
        tmp.replace(FEEDBACK_FILE)
    except Exception:
        logger.exception("Falha ao escrever arquivo de feedbacks.")


def save_feedback(feedback: Dict[str, object], persist: bool = False) -> Optional[str]:
    """
    Salva feedback do usuário.
    - feedback: dicionário com chaves como 'user', 'message', 'rating' (opcional).
    - persist: se True, salva também em arquivo JSON local (fallback).
    Retorna o id do feedback salvo (string) ou None em caso de falha.
    """
    if not isinstance(feedback, dict):
        logger.error("Feedback inválido: deve ser um dicionário.")
        return None

    try:
        fid = uuid.uuid4().hex[:12]
        record = dict(feedback)  # cópia para não modificar o original
        record.setdefault("timestamp", datetime.utcnow().isoformat())
        record["id"] = fid

        # Loga o feedback (principal comportamento atual)
        logger.info("Feedback recebido: %s", record)

        # Persistência opcional em arquivo local (útil para fallback)
        if persist:
            try:
                _ensure_data_dir()
                existing = _read_feedbacks()
                existing.append(record)
                _write_feedbacks_atomic(existing)
                logger.info("Feedback persistido localmente em %s", FEEDBACK_FILE)
            except Exception:
                logger.exception("Falha ao persistir feedback localmente.")

        return fid
    except Exception:
        logger.exception("Erro ao processar feedback.")
        return None


__all__ = ["save_feedback"]
