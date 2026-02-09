# backend/app.py
"""
FastAPI app: Whisper (opcional), ChatGPT (opcional) e gTTS (opcional).
Config defensiva para permitir execução mesmo sem todas as dependências.
"""

import os
import sys
import time
import logging
import base64
import tempfile
import subprocess
from typing import Optional, Tuple, Any, cast

from fastapi import (
    FastAPI, File, UploadFile, Form, HTTPException, Request, Depends, Cookie, Header, status
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

# runtime isinstance checks for form UploadFile
from starlette.datastructures import UploadFile as StarletteUploadFile

# JWT
from jose import jwt, JWTError

# defensive optional imports
try:
    from faster_whisper import WhisperModel  # type: ignore
except Exception:
    WhisperModel = None  # type: ignore

try:
    from gtts import gTTS  # type: ignore
except Exception:
    gTTS = None  # type: ignore

try:
    import pyttsx3  # type: ignore
except Exception:
    pyttsx3 = None  # type: ignore

# official OpenAI python package (optional)
try:
    import openai  # type: ignore
except Exception:
    openai = None  # type: ignore

# project config (defensive fallback)
try:
    from backend.config import settings  # type: ignore
except Exception:
    class _FallbackSettings:
        FRONTEND_ORIGINS = ["http://localhost:5174"]
        WHISPER_MODEL = "small"
        WHISPER_DEVICE = "cpu"
        WHISPER_COMPUTE = ""
        FFMPEG_BIN = "ffmpeg"
        MAX_CONTENT_LENGTH_BYTES = 10 * 1024 * 1024
        SECRET_KEY = "change-me"
        JWT_ALGORITHM = "HS256"
        JWT_EXPIRES_SECONDS = 3600
        TTS_PROVIDER = "gtts"
    settings = _FallbackSettings()  # type: ignore

# optional DB imports (defensive)
try:
    from database.session import SessionLocal  # type: ignore
    from database.models.feedback_model import Feedback  # type: ignore
except Exception:
    SessionLocal = None  # type: ignore
    Feedback = None  # type: ignore

# config values
MODEL_NAME = getattr(settings, "WHISPER_MODEL", os.getenv("WHISPER_MODEL", "small"))
DEVICE = getattr(settings, "WHISPER_DEVICE", os.getenv("WHISPER_DEVICE", "cpu"))
COMPUTE_TYPE = getattr(settings, "WHISPER_COMPUTE", os.getenv("WHISPER_COMPUTE", ""))
FFMPEG_BIN = getattr(settings, "FFMPEG_BIN", os.getenv("FFMPEG_BIN", "ffmpeg"))
MAX_UPLOAD_SIZE = getattr(settings, "MAX_CONTENT_LENGTH_BYTES", int(os.getenv("MAX_UPLOAD_SIZE_BYTES", 10 * 1024 * 1024)))

JWT_SECRET = getattr(settings, "SECRET_KEY", os.getenv("JWT_SECRET", "change-me"))
JWT_ALGORITHM = getattr(settings, "JWT_ALGORITHM", os.getenv("JWT_ALGORITHM", "HS256"))
JWT_EXPIRES_SECONDS = getattr(settings, "JWT_EXPIRES_SECONDS", int(os.getenv("JWT_EXPIRES_SECONDS", 3600)))

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
TTS_PROVIDER = getattr(settings, "TTS_PROVIDER", os.getenv("TTS_PROVIDER", "gtts")).lower()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# if openai package present, set key defensively
if openai is not None and OPENAI_API_KEY:
    try:
        # some openai versions accept openai.api_key
        setattr(openai, "api_key", OPENAI_API_KEY)
    except Exception:
        pass

LANG_MAP = {
    "pt": "pt-BR", "en": "en-US", "es": "es-ES",
    "fr": "fr-FR", "de": "de-DE", "ar": "ar-SA", "ru": "ru-RU"
}
GTTS_LANG_MAP = {"pt": "pt", "en": "en", "es": "es", "fr": "fr", "de": "de", "ar": "ar", "ru": "ru"}

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("assistant-api")

# FastAPI app
app = FastAPI(title="Assistant API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "FRONTEND_ORIGINS", ["http://localhost:5174"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# try to include auth router if available
try:
    from backend.auth import router as auth_router, get_current_user as auth_get_current_user  # type: ignore
except Exception:
    auth_router = None
    def auth_get_current_user(*args, **kwargs):
        raise HTTPException(status_code=401, detail="Auth not configured")

if auth_router is not None:
    app.include_router(auth_router)

# try to include voice router if available
try:
    from backend.voice import router as voice_router  # type: ignore
except Exception:
    voice_router = None

if voice_router is not None:
    app.include_router(voice_router)

# DB dependency
def get_db():
    if SessionLocal is None:
        raise RuntimeError("Database session not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Whisper loader (guarded)
def load_model(name: str, device: str, compute_type: Optional[str]):
    if WhisperModel is None:
        raise RuntimeError("WhisperModel not available in this environment.")
    if compute_type:
        return WhisperModel(name, device=device, compute_type=compute_type)
    return WhisperModel(name, device=device)

MODEL = None
try:
    MODEL = load_model(MODEL_NAME, DEVICE, COMPUTE_TYPE)
except Exception:
    MODEL = None
    logger.info("Whisper model not loaded (optional).")

# utilities
from shutil import which

def ensure_ffmpeg_available() -> None:
    if which(FFMPEG_BIN) is None:
        logger.debug("ffmpeg not found in PATH")
        raise RuntimeError("ffmpeg not found")

def safe_remove(path: Optional[str]):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        logger.debug("safe_remove failed for %s", path)

def run_ffmpeg_convert(input_path: str, output_path: str, sample_rate: int = 16000):
    ensure_ffmpeg_available()
    cmd = [FFMPEG_BIN, "-y", "-i", input_path, "-ar", str(sample_rate), "-ac", "1", "-vn", output_path]
    proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        stderr = proc.stderr.decode(errors="ignore") if proc.stderr else ""
        logger.error("ffmpeg failed: %s", stderr)
        raise subprocess.CalledProcessError(proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr)

def choose_tts_provider(request_provider: Optional[str]) -> str:
    return (request_provider or TTS_PROVIDER or "gtts").lower()

def should_use_chatgpt(request_flag: Optional[str]) -> bool:
    if request_flag is None:
        return bool(OPENAI_API_KEY and openai)
    val = str(request_flag).lower()
    return val in ("1", "true", "yes", "on")

def transcribe_wav_with_model(wav_path: str, language_code: Optional[str]) -> Tuple[str, Any]:
    if MODEL is None:
        raise RuntimeError("Whisper model not loaded.")
    segments, info = MODEL.transcribe(wav_path, language=language_code)
    texts = [getattr(seg, "text", "").strip() for seg in segments if getattr(seg, "text", "").strip()]
    transcription = " ".join(texts).strip()
    return transcription, info

# TTS helpers
def _synthesize_gtts_data_uri(text: str, lang_short: str) -> str:
    if gTTS is None:
        logger.debug("gTTS not available")
        return ""
    gtts_lang = GTTS_LANG_MAP.get(lang_short, "en")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp_path = tmp.name
    tmp.close()
    tts = gTTS(text=text or " ", lang=gtts_lang, slow=False)
    tts.save(tmp_path)
    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    safe_remove(tmp_path)
    return f"data:audio/mp3;base64,{b64}"

def _synthesize_pyttsx3_data_uri(text: str, lang_short: str) -> str:
    if pyttsx3 is None:
        logger.debug("pyttsx3 not available")
        return ""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tmp_path = tmp.name
    tmp.close()
    engine = pyttsx3.init()
    engine.save_to_file(text, tmp_path)
    engine.runAndWait()
    engine.stop()
    with open(tmp_path, "rb") as f:
        audio_bytes = f.read()
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    safe_remove(tmp_path)
    return f"data:audio/mp3;base64,{b64}"

def synthesize_tts_data_uri(text: str, lang_short: str, provider: Optional[str] = None) -> str:
    provider_use = (provider or TTS_PROVIDER or "gtts").lower()
    if provider_use == "pyttsx3":
        return _synthesize_pyttsx3_data_uri(text, lang_short)
    return _synthesize_gtts_data_uri(text, lang_short)

# ChatGPT wrapper (defensive, avoids direct attribute access that Pylance flags)
def call_chatgpt_for_response(user_text: str, lang: str = "pt") -> str:
    # if openai package not present, return original text
    if openai is None:
        logger.debug("OpenAI SDK not installed; returning original text")
        return user_text

    # Try multiple safe invocation patterns without assuming attributes exist
    try:
        # Pattern A: classic openai.ChatCompletion.create (some versions)
        chat_completion = getattr(openai, "ChatCompletion", None)
        if chat_completion is not None and hasattr(chat_completion, "create"):
            try:
                resp = chat_completion.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "Você é um assistente de voz conciso e educado."},
                        {"role": "user", "content": user_text}
                    ],
                    max_tokens=500,
                    temperature=0.2,
                )
                # resp may be dict-like or object-like
                choices = resp.get("choices") if isinstance(resp, dict) else getattr(resp, "choices", None)
                if choices and len(choices) > 0:
                    first = choices[0]
                    # try dict-style
                    if isinstance(first, dict):
                        msg = first.get("message") or first.get("text")
                        if isinstance(msg, dict):
                            return msg.get("content", "").strip()
                        if isinstance(msg, str):
                            return msg.strip()
                    # try object-style
                    if hasattr(first, "message"):
                        message = getattr(first, "message")
                        if isinstance(message, dict):
                            return message.get("content", "").strip()
                        if hasattr(message, "get"):
                            return message.get("content", "").strip() if message.get("content") else ""
                # fallback to continue trying other patterns
            except Exception:
                logger.debug("openai.ChatCompletion.create failed; falling back")

        # Pattern B: new-style openai client (openai.ChatCompletion.acreate or openai.ChatCompletion.create already tried)
        # Pattern C: higher-level client object (openai_client) if configured in globals
        client_obj = globals().get("openai_client")
        if client_obj:
            try:
                # use getattr to avoid static attribute checks
                chat_attr = getattr(client_obj, "chat", None)
                if chat_attr is not None:
                    completions = getattr(chat_attr, "completions", None)
                    if completions is not None and hasattr(completions, "create"):
                        resp = completions.create(
                            model=OPENAI_MODEL,
                            messages=[
                                {"role": "system", "content": "Você é um assistente útil e educado."},
                                {"role": "user", "content": user_text},
                            ],
                            max_tokens=512,
                            temperature=0.7,
                        )
                        choices = getattr(resp, "choices", None)
                        if choices:
                            first = choices[0]
                            # object-style access
                            if hasattr(first, "message") and hasattr(first.message, "content"):
                                return getattr(first.message, "content", "").strip()
                        return user_text
            except Exception:
                logger.exception("openai_client chat call failed; returning original text")
                return user_text

        # Pattern D: fallback to openai.Completion (older API)
        completion_attr = getattr(openai, "Completion", None)
        if completion_attr is not None and hasattr(completion_attr, "create"):
            try:
                resp = completion_attr.create(
                    model=OPENAI_MODEL,
                    prompt=user_text,
                    max_tokens=200,
                    temperature=0.2,
                )
                # try dict-style
                if isinstance(resp, dict):
                    choices = resp.get("choices", [])
                    if choices:
                        text = choices[0].get("text")
                        if isinstance(text, str):
                            return text.strip()
                else:
                    choices = getattr(resp, "choices", None)
                    if choices and len(choices) > 0:
                        first = choices[0]
                        if isinstance(first, dict):
                            return first.get("text", "").strip()
                        if hasattr(first, "text"):
                            return getattr(first, "text", "").strip()
            except Exception:
                logger.debug("openai.Completion.create failed; falling back")

    except Exception:
        logger.exception("call_chatgpt_for_response unexpected error")
        return user_text

    # final fallback
    return user_text

# JWT helpers
def create_jwt_token(subject: str, expires_in: int = JWT_EXPIRES_SECONDS) -> str:
    now = int(time.time())
    payload = {"sub": subject, "iat": now, "exp": now + expires_in}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None

def get_current_user_cookie(access_token: Optional[str] = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_jwt_token(access_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise HTTPException(status_code=401, detail="Invalid token subject")
    return sub

# Pydantic models for docs
from pydantic import BaseModel, Field

class FeedbackOut(BaseModel):
    id: int
    user_id: str
    comment: str
    rating: int
    created_at: str

class FeedbackCreate(BaseModel):
    user_id: str = Field(..., description="Identificador do usuário")
    comment: str = Field(..., description="Comentário do usuário")
    rating: int = Field(..., ge=1, le=5, description="Avaliação de 1 a 5")

# Basic endpoints
@app.get("/", tags=["default"])
def read_root():
    return {"status": "ok", "message": "Assistant API running"}

@app.get("/health", tags=["default"])
def health():
    return {"status": "ok", "message": "API running"}

# Robust /assistant/process
@app.post("/assistant/process", tags=["assistant"], response_model=None)
async def process_text(request: Request) -> Any:
    text: Optional[str] = None
    lang: Optional[str] = None
    tts_provider: Optional[str] = None
    use_chatgpt: Optional[str] = None

    content_type = (request.headers.get("content-type") or "").lower()

    # JSON
    if content_type.startswith("application/json"):
        try:
            body = await request.json()
            if isinstance(body, dict):
                t = body.get("text")
                if t is not None:
                    text = str(t)
                l = body.get("lang")
                if l is not None:
                    lang = str(l)
                tp = body.get("tts_provider")
                if tp is not None:
                    tts_provider = str(tp)
                ug = body.get("use_chatgpt")
                if ug is not None:
                    use_chatgpt = str(ug)
        except Exception:
            raise HTTPException(status_code=400, detail="There was an error parsing the body")

    # form-data or urlencoded
    elif content_type.startswith("multipart/form-data") or content_type.startswith("application/x-www-form-urlencoded"):
        form = await request.form()
        val = form.get("text")
        if isinstance(val, str):
            text = val
        elif isinstance(val, StarletteUploadFile):
            text = None

        val = form.get("lang")
        if isinstance(val, str):
            lang = val
        elif isinstance(val, StarletteUploadFile):
            lang = None

        val = form.get("tts_provider")
        if isinstance(val, str):
            tts_provider = val
        elif isinstance(val, StarletteUploadFile):
            tts_provider = None

        val = form.get("use_chatgpt")
        if isinstance(val, str):
            use_chatgpt = val
        elif isinstance(val, StarletteUploadFile):
            use_chatgpt = None

    # fallback raw body
    else:
        try:
            raw = await request.body()
            logger.debug("RAW BODY fallback: %s", raw.decode(errors="ignore"))
            if raw:
                import json
                try:
                    j = json.loads(raw.decode("utf-8"))
                    if isinstance(j, dict):
                        t = j.get("text")
                        if t is not None:
                            text = str(t)
                        l = j.get("lang")
                        if l is not None:
                            lang = str(l)
                        tp = j.get("tts_provider")
                        if tp is not None:
                            tts_provider = str(tp)
                        ug = j.get("use_chatgpt")
                        if ug is not None:
                            use_chatgpt = str(ug)
                except Exception:
                    pass
        except Exception:
            pass

    # normalize
    text_str: Optional[str] = text if isinstance(text, str) else None
    lang_str: Optional[str] = lang if isinstance(lang, str) else None
    tts_provider_str: Optional[str] = tts_provider if isinstance(tts_provider, str) else None
    use_chatgpt_str: Optional[str] = use_chatgpt if isinstance(use_chatgpt, str) else None

    if not text_str:
        raise HTTPException(status_code=422, detail="text is required")

    if should_use_chatgpt(use_chatgpt_str):
        processed = call_chatgpt_for_response(text_str, lang=(lang_str or "pt"))
    else:
        processed = text_str

    provider = choose_tts_provider(tts_provider_str)
    try:
        audio_data_uri = synthesize_tts_data_uri(processed, (lang_str or "pt")[:2], provider=provider)
    except Exception:
        logger.exception("TTS generation failed")
        audio_data_uri = ""

    return {"status": "ok", "text": processed, "audio_data_uri": audio_data_uri, "tts_provider": provider}

@app.post("/assistant/process/upload", tags=["assistant"])
async def process_upload(
    file: UploadFile = File(...),
    lang: Optional[str] = Form(None),
    tts_provider: Optional[str] = Form(None),
    use_chatgpt: Optional[str] = Form(None),
):
    contents = await file.read()
    if MAX_UPLOAD_SIZE and len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}")
    tmp_in_path = tmp_in.name
    tmp_in.write(contents)
    tmp_in.close()

    tmp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_wav_path = tmp_wav.name
    tmp_wav.close()

    try:
        try:
            run_ffmpeg_convert(tmp_in_path, tmp_wav_path, sample_rate=16000)
        except subprocess.CalledProcessError:
            logger.exception("ffmpeg conversion failed")
            raise HTTPException(status_code=500, detail="Audio conversion failed")
        except Exception:
            logger.exception("ffmpeg check failed")
            raise HTTPException(status_code=500, detail="Audio conversion failed")

        try:
            transcription, info = transcribe_wav_with_model(tmp_wav_path, language_code=(lang or None))
        except Exception:
            logger.exception("transcription failed")
            raise HTTPException(status_code=500, detail="Transcription failed")

        if should_use_chatgpt(use_chatgpt):
            processed = call_chatgpt_for_response(transcription, lang=(lang or "pt"))
        else:
            processed = transcription

        provider = choose_tts_provider(tts_provider)
        try:
            audio_data_uri = synthesize_tts_data_uri(processed, (lang or "pt")[:2], provider=provider)
        except Exception:
            logger.exception("TTS generation failed")
            audio_data_uri = ""

        return {
            "status": "ok",
            "transcription": transcription,
            "text": processed,
            "audio_data_uri": audio_data_uri,
            "tts_provider": provider,
            "whisper_info": getattr(info, "__dict__", str(info))
        }
    finally:
        safe_remove(tmp_in_path)
        safe_remove(tmp_wav_path)

@app.post("/admin/reload-model", tags=["admin"])
async def reload_model(api_key: Optional[str] = Header(None)):
    if not ADMIN_API_KEY or api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    global MODEL
    try:
        MODEL = load_model(MODEL_NAME, DEVICE, COMPUTE_TYPE)
        return {"status": "ok", "message": "model reloaded"}
    except Exception:
        logger.exception("Failed to reload model")
        raise HTTPException(status_code=500, detail="Failed to reload model")

# protected example
@app.get("/protected/data", tags=["protected"])
async def protected_data(user: str = Depends(auth_get_current_user)):
    return {"status": "ok", "user": user, "message": f"Olá {user}, você acessou rota protegida"}

# serve tmp audio files if any
@app.get("/voice-assistant/audio/{filename}", tags=["voice"])
def get_audio_file(filename: str, current_user = Depends(auth_get_current_user)):
    path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Áudio não encontrado")
    return FileResponse(path, media_type="audio/mpeg", filename=filename)

# consistent HTTPException handler
@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

# startup
@app.on_event("startup")
def on_startup():
    logger.info("Starting Assistant API (dev).")
    if MODEL is None:
        logger.info("Whisper model not loaded; voice transcription may use OpenAI or be unavailable.")
    if openai is None:
        logger.info("OpenAI SDK not installed or OPENAI_API_KEY not set; ChatGPT/Whisper API unavailable.")
    try:
        logger.info("Allowed CORS origins: %s", getattr(settings, "FRONTEND_ORIGINS", ["http://localhost:5174"]))
    except Exception:
        pass

# run block
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.app:app", host="127.0.0.1", port=port, reload=True)
