# backend/services/speech_to_text.py
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("speech_to_text")

# Cache do modelo carregado para evitar recarregamentos repetidos
_loaded_models: dict = {}


def _load_whisper_model(model_name: str):
    """
    Carrega e retorna o modelo whisper solicitado, usando cache para reuso.
    Lança ImportError se o pacote whisper não estiver disponível.
    """
    try:
        import whisper  # import local para evitar custo no import do módulo
    except Exception as exc:
        logger.debug("whisper import failed: %s", exc)
        raise ImportError("whisper library is not available") from exc

    if model_name in _loaded_models:
        return _loaded_models[model_name]

    model = whisper.load_model(model_name)
    _loaded_models[model_name] = model
    logger.info("Whisper model loaded: %s", model_name)
    return model


def recognize(audio_path: str, model_name: str = "base") -> Optional[str]:
    """
    Transcreve o arquivo de áudio em `audio_path` usando Whisper.
    - Retorna a string transcrita (pode ser vazia) ou None em caso de erro.
    - Não lança exceções para falhas de transcrição; apenas loga e retorna None.
    """
    try:
        # validação simples do caminho
        if not isinstance(audio_path, str) or not audio_path:
            logger.error("audio_path inválido: %r", audio_path)
            return None

        p = Path(audio_path)
        if not p.exists():
            logger.error("Arquivo de áudio não encontrado: %s", audio_path)
            return None

        model = _load_whisper_model(model_name)
        # Alguns wrappers aceitam Path diretamente; garantir str para compatibilidade
        result = model.transcribe(str(p), language="pt")
        text = str(result.get("text", "")).strip() if isinstance(result, dict) else str(result).strip()
        logger.debug("Transcrição obtida: %s", text[:200])
        return text
    except ImportError:
        logger.exception("Biblioteca 'whisper' não está instalada.")
        return None
    except Exception as exc:
        logger.exception("Erro ao transcrever com Whisper: %s", exc)
        return None
