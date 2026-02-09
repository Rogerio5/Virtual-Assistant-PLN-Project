# backend/services/text_to_speech.py
from pathlib import Path
from typing import Optional
import uuid
import logging

# Import settings with a safe fallback for typing tools
try:
    from ..config import settings
except Exception:  # pragma: no cover - fallback for static analysis / tests
    class _DummySettings:
        STATIC_DIR = "static"
        TTS_SUBDIR = "tts"
        BASE_URL = ""
    settings = _DummySettings()

logger = logging.getLogger("text_to_speech")

# Diretório onde os arquivos TTS serão salvos (resolvido em tempo de import)
STATIC_TTS_DIR: Path = Path(settings.STATIC_DIR) / settings.TTS_SUBDIR
STATIC_TTS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_filename(prefix: str = "response") -> str:
    """
    Gera um nome de arquivo único e seguro.
    """
    return f"{prefix}_{uuid.uuid4().hex[:12]}.mp3"


def speak(text: str, lang: str = "pt-br", filename_prefix: str = "response") -> Optional[str]:
    """
    Sintetiza `text` em um arquivo MP3 usando gTTS.
    - Retorna uma URL completa se settings.BASE_URL estiver configurado,
      caso contrário retorna o caminho relativo dentro de STATIC_DIR/TTS_SUBDIR.
    - Em caso de erro ou texto vazio retorna None.
    """
    if not text or not text.strip():
        logger.warning("Texto vazio recebido para síntese de voz.")
        return None

    # Import dinâmico para facilitar testes (mock) e evitar dependência obrigatória
    try:
        from gtts import gTTS  # type: ignore
    except Exception as exc:
        logger.exception("gTTS não disponível: %s", exc)
        return None

    filename = _safe_filename(filename_prefix)
    filepath = STATIC_TTS_DIR / filename

    try:
        tts = gTTS(text=text, lang=lang)
        # gTTS.save aceita caminho como str
        tts.save(str(filepath))

        # monta caminho relativo para retorno (sempre usando barras)
        rel_path = Path(settings.STATIC_DIR) / settings.TTS_SUBDIR / filename
        rel_path_str = rel_path.as_posix().lstrip("./").lstrip("/")

        # Garantir que BASE_URL seja uma string não-nula antes de chamar rstrip
        base_url_raw = getattr(settings, "BASE_URL", "")
        base = str(base_url_raw or "").rstrip("/")
        if base:
            return f"{base}/{rel_path_str}"
        return rel_path_str
    except Exception as e:
        logger.exception("Erro na síntese de voz: %s", e)
        # tenta remover arquivo parcial se existir
        try:
            if filepath.exists():
                filepath.unlink()
        except Exception:
            logger.debug("Não foi possível remover arquivo parcial %s", filepath)
        return None
