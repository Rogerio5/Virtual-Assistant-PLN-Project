# backend/routes/assistant_routes.py
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import os
import tempfile
import subprocess
from pathlib import Path
from shutil import which

from ..services import speech_to_text, text_to_speech
from ..config import settings

logger = logging.getLogger("assistant_routes")
router = APIRouter(prefix="/assistant", tags=["Assistant"])

MAX_UPLOAD_SIZE_BYTES = getattr(settings, "MAX_CONTENT_LENGTH_BYTES", None)
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}


class AudioInput(BaseModel):
    audio_file: Optional[str] = Field(None)
    text_input: Optional[str] = Field(None)
    user_id: Optional[str] = Field("default")


class AssistantResponse(BaseModel):
    input: str
    response: str
    audio: Optional[str] = Field(None)
    actions: Optional[Dict[str, str]] = Field(None)


def _ensure_ffmpeg_available() -> None:
    if which("ffmpeg") is None:
        logger.error("ffmpeg não encontrado no PATH.")
        raise HTTPException(status_code=500, detail="ffmpeg não encontrado no servidor. Adicione ffmpeg ao PATH.")


def _convert_to_wav(input_path: str, output_path: str, sample_rate: int = 16000) -> None:
    _ensure_ffmpeg_available()
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ac", "1", "-ar", str(sample_rate),
        "-sample_fmt", "s16",
        output_path
    ]
    proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        stderr = proc.stderr.decode(errors="ignore") if proc.stderr else ""
        logger.error("ffmpeg failed (cmd=%s): %s", " ".join(cmd), stderr)
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)


def _validate_transcription_result(text: Any) -> str:
    if text is None:
        raise HTTPException(status_code=422, detail="Transcrição vazia.")
    if isinstance(text, str):
        if text.strip() == "":
            raise HTTPException(status_code=422, detail="Transcrição vazia.")
        if text.lower().startswith("erro"):
            raise HTTPException(status_code=500, detail=text)
        return text.strip()
    return str(text).strip()


def _build_audio_url(request: Request, tts_return: Optional[str]) -> Optional[str]:
    if not tts_return:
        return None
    # If already a full URL, return as-is
    if tts_return.startswith("http://") or tts_return.startswith("https://"):
        return tts_return
    # If absolute filesystem path, try to convert to a relative path under static if possible
    rel = tts_return
    # Normalize leading slashes
    rel = rel.lstrip("./").lstrip("/")
    base = str(request.base_url).rstrip("/")
    return f"{base}/{rel}"


@router.post("/process", response_model=AssistantResponse)
async def process_command(request: Request, data: AudioInput, background_tasks: BackgroundTasks):
    if not data.audio_file and not data.text_input:
        raise HTTPException(status_code=400, detail="Nenhuma entrada fornecida.")
    try:
        if data.audio_file:
            audio_path = data.audio_file
            if not os.path.exists(audio_path):
                raise HTTPException(status_code=422, detail="Arquivo de áudio não encontrado no servidor.")
            raw_text = speech_to_text.recognize(audio_path)
            text = _validate_transcription_result(raw_text)
        else:
            text = (data.text_input or "").strip()
        if not text:
            raise HTTPException(status_code=422, detail="Não foi possível obter texto da entrada.")
        response_text = f"Você perguntou: {text}"
        actions = {}
        audio_output = None
        try:
            # text_to_speech.speak should return either a URL or a relative path to the generated audio file
            audio_output = text_to_speech.speak(response_text)
        except Exception:
            logger.exception("Falha ao gerar TTS.")
            audio_output = None
        audio_url = _build_audio_url(request, audio_output)
        return AssistantResponse(input=text, response=response_text, audio=audio_url, actions=actions)
    except HTTPException:
        raise
    except subprocess.CalledProcessError as cpe:
        logger.exception("Erro ao converter áudio com ffmpeg: %s", cpe)
        raise HTTPException(status_code=500, detail="Erro ao processar arquivo de áudio (conversão).")
    except Exception as exc:
        logger.exception("Erro interno em /assistant/process: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(exc)}")


@router.post("/process/upload", response_model=AssistantResponse)
async def process_upload(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(None),
    text_input: Optional[str] = Form(None),
    user_id: Optional[str] = Form("default"),
):
    if not file and not text_input:
        raise HTTPException(status_code=400, detail="Nenhuma entrada fornecida.")
    tmp_path: Optional[str] = None
    converted_wav: Optional[str] = None
    try:
        if file:
            filename = file.filename or "upload"
            ext = Path(filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=415, detail=f"Formato não suportado: {ext}")
            content = await file.read()
            if MAX_UPLOAD_SIZE_BYTES and len(content) > MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(status_code=413, detail="Arquivo excede o tamanho máximo permitido.")
            fd, tmp_path = tempfile.mkstemp(suffix=ext)
            os.close(fd)
            with open(tmp_path, "wb") as f:
                f.write(content)
            logger.info("Arquivo recebido e salvo temporariamente em %s", tmp_path)
            if ext != ".wav":
                # Use a secure temporary file for the converted wav
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
                    converted_wav = tmp_wav.name
                try:
                    _convert_to_wav(tmp_path, converted_wav)
                    raw_text = speech_to_text.recognize(converted_wav)
                except subprocess.CalledProcessError as e:
                    logger.exception("Erro na conversão do arquivo enviado: %s", e)
                    raise HTTPException(status_code=500, detail="Falha ao converter o arquivo de áudio.")
            else:
                raw_text = speech_to_text.recognize(tmp_path)
            text = _validate_transcription_result(raw_text)
        else:
            text = (text_input or "").strip()
        if not text:
            raise HTTPException(status_code=422, detail="Não foi possível obter texto da entrada.")
        response_text = f"Você perguntou: {text}"
        actions = {}
        audio_output = None
        try:
            audio_output = text_to_speech.speak(response_text)
        except Exception:
            logger.exception("Falha ao gerar TTS.")
            audio_output = None
        audio_url = _build_audio_url(request, audio_output)
        return AssistantResponse(input=text, response=response_text, audio=audio_url, actions=actions)
    except HTTPException:
        raise
    except subprocess.CalledProcessError as cpe:
        logger.exception("Erro ao converter áudio com ffmpeg: %s", cpe)
        raise HTTPException(status_code=500, detail="Erro ao processar arquivo de áudio (conversão).")
    except Exception as exc:
        logger.exception("Erro interno em /assistant/process/upload: %s", exc)
        raise HTTPException(status_code=500, detail=f"Erro ao processar upload: {str(exc)}")
    finally:
        for p in (tmp_path, converted_wav):
            try:
                if p and os.path.exists(p):
                    os.remove(p)
                    logger.debug("Arquivo temporário removido: %s", p)
            except Exception:
                logger.exception("Falha ao remover arquivo temporário: %s", p)
    
    # no final do arquivo
__all__ = ["router"]
