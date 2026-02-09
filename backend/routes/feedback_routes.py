# backend/routes/feedback_routes.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import logging
import json
import os
from pathlib import Path
import time
import hashlib

from ..services import feedback_manager

logger = logging.getLogger("feedback_routes")
router = APIRouter(
    prefix="/feedback",
    tags=["Feedback"],
    responses={404: {"description": "Não encontrado"}},
)

DATA_DIR = Path("data")
FEEDBACK_FILE = DATA_DIR / "feedbacks.json"


# -------------------------
# Modelos
# -------------------------
class FeedbackInput(BaseModel):
    user: str = Field(..., description="Nome ou identificador do usuário")
    message: str = Field(..., description="Mensagem de feedback")
    rating: Optional[int] = Field(default=None, description="Avaliação opcional (1-5)")

    @validator("user")
    def user_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("O campo 'user' não pode ser vazio.")
        return v.strip()

    @validator("message")
    def message_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("O campo 'message' não pode ser vazio.")
        return v.strip()

    @validator("rating")
    def rating_must_be_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is None:
            return v
        if not (1 <= v <= 5):
            raise ValueError("O campo 'rating' deve estar entre 1 e 5.")
        return v


class FeedbackResponse(BaseModel):
    status: str
    saved: bool
    id: Optional[str] = None
    detail: Optional[str] = None


# -------------------------
# Helpers
# -------------------------
def _generate_feedback_id(feedback: Dict[str, Any]) -> str:
    raw_id = f"{feedback.get('user','')}-{time.time()}"
    return hashlib.sha1(raw_id.encode("utf-8")).hexdigest()[:12]


def _read_existing_feedbacks() -> list:
    if not FEEDBACK_FILE.exists():
        return []
    try:
        with FEEDBACK_FILE.open("r", encoding="utf-8") as f:
            return json.load(f) or []
    except Exception:
        logger.exception("Falha ao ler arquivo de feedbacks; retornando lista vazia.")
        return []


def _write_feedbacks_atomic(feedbacks: list) -> None:
    """
    Escreve o arquivo de feedbacks de forma simples e segura.
    Usa um arquivo temporário e renomeia para evitar corrupção parcial.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = FEEDBACK_FILE.with_suffix(".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(feedbacks, f, ensure_ascii=False, indent=2)
        tmp_path.replace(FEEDBACK_FILE)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                logger.debug("Não foi possível remover arquivo temporário %s", tmp_path)


def _fallback_save_feedback(feedback: Dict[str, Any]) -> str:
    """
    Salva feedback localmente em um arquivo JSON como fallback.
    Retorna um id gerado (timestamp + hash simples).
    """
    try:
        existing = _read_existing_feedbacks()
        fid = _generate_feedback_id(feedback)
        feedback_record = {"id": fid, **feedback}
        existing.append(feedback_record)
        _write_feedbacks_atomic(existing)
        logger.info("Feedback salvo no fallback local: %s", FEEDBACK_FILE)
        return fid
    except Exception as exc:
        logger.exception("Falha ao salvar feedback no fallback local: %s", exc)
        raise


def _save_feedback_via_manager(feedback: Dict[str, Any]) -> Optional[str]:
    """
    Tenta usar feedback_manager.save_feedback. Se o manager retornar um id, retorna-o.
    Se o manager não expuser a função, lança AttributeError.
    """
    if hasattr(feedback_manager, "save_feedback") and callable(getattr(feedback_manager, "save_feedback")):
        try:
            result = feedback_manager.save_feedback(feedback)
            if isinstance(result, str):
                return result
            if isinstance(result, dict) and "id" in result:
                return result.get("id")
            return None
        except Exception:
            logger.exception("Erro ao salvar feedback via feedback_manager.")
            raise
    else:
        raise AttributeError("feedback_manager não expõe 'save_feedback'.")


# -------------------------
# Endpoint
# -------------------------
@router.post(
    "/",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar feedback do usuário",
)
def save_user_feedback(feedback: FeedbackInput, background_tasks: BackgroundTasks):
    """
    Recebe feedback do usuário e tenta salvá-lo usando o feedback_manager.
    - Se feedback_manager.save_feedback estiver disponível, usa-o.
    - Caso contrário, salva em arquivo local (fallback) em background.
    Retorna status e indicador se foi salvo.
    """
    feedback_dict = feedback.dict()
    logger.info("Recebido feedback de %s", feedback_dict.get("user"))

    # Tenta salvar via feedback_manager (sincrono). Se falhar, agenda fallback em background.
    try:
        fid = _save_feedback_via_manager(feedback_dict)
        return FeedbackResponse(status="Feedback registrado com sucesso", saved=True, id=fid)
    except AttributeError:
        # manager não disponível: usa fallback em background
        try:
            background_tasks.add_task(_fallback_save_feedback, feedback_dict)
            logger.warning("feedback_manager indisponível. Salvando feedback via fallback em background.")
            return FeedbackResponse(status="Feedback recebido; salvando localmente", saved=True)
        except Exception as exc:
            logger.exception("Falha ao agendar fallback de salvamento: %s", exc)
            raise HTTPException(status_code=500, detail="Erro ao salvar feedback (fallback).")
    except Exception as exc:
        # Se o manager existe mas falhou ao salvar, tenta fallback em background
        logger.exception("Erro ao salvar via feedback_manager: %s", exc)
        try:
            background_tasks.add_task(_fallback_save_feedback, feedback_dict)
            return FeedbackResponse(status="Erro no salvamento principal; fallback agendado", saved=True, detail=str(exc))
        except Exception as exc2:
            logger.exception("Falha ao agendar fallback após erro do manager: %s", exc2)
            raise HTTPException(status_code=500, detail=f"Erro ao salvar feedback: {str(exc)}")


__all__ = ["router"]
