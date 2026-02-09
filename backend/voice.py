import os
import tempfile
import asyncio
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from .auth import get_current_user
import aiofiles
from gtts import gTTS

# imports opcionais (podem ser None se não instalados)
try:
    import openai  # type: ignore
except Exception:
    openai = None  # type: ignore

try:
    from faster_whisper import WhisperModel  # type: ignore
except Exception:
    WhisperModel = None  # type: ignore

router = APIRouter(prefix="/voice-assistant", tags=["voice"])

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
if openai and OPENAI_KEY:
    # configura a chave apenas se o pacote existir e a variável estiver definida
    try:
        openai.api_key = OPENAI_KEY  # type: ignore
    except Exception:
        # alguns clientes podem não expor api_key dessa forma; deixamos a chamada falhar mais adiante se necessário
        pass

# lazy init do modelo local faster-whisper
_whisper_model: Optional["WhisperModel"] = None  # type: ignore

def get_local_whisper_model() -> "WhisperModel":  # type: ignore
    global _whisper_model
    if _whisper_model is None:
        if WhisperModel is None:
            raise RuntimeError("faster-whisper não está disponível")
        # escolha do tamanho do modelo deve considerar seu hardware: tiny, base, small, medium, large-v2
        _whisper_model = WhisperModel("small", device="cpu", compute_type="int8_float16")  # type: ignore
    return _whisper_model  # type: ignore

async def save_upload_to_tempfile(upload: UploadFile) -> str:
    # upload.filename pode ser None; garantir string
    filename = upload.filename or "upload_audio"
    suffix = os.path.splitext(filename)[1] or ".wav"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = tmp.name
    tmp.close()
    async with aiofiles.open(tmp_path, "wb") as out:
        content = await upload.read()
        await out.write(content)
    return tmp_path

async def transcribe_with_openai(file_path: str) -> str:
    if openai is None:
        raise RuntimeError("openai não está instalado")
    # verificar se o cliente openai expõe o método esperado
    audio_api = getattr(openai, "Audio", None)
    if audio_api is None or not hasattr(audio_api, "transcribe"):
        # tentar alternativa: alguns SDKs usam openai.Audio.transcribe; se não existir, falhar com mensagem clara
        raise RuntimeError("A API de transcrição do OpenAI não está disponível nesta instalação do cliente openai")
    def _sync_transcribe():
        with open(file_path, "rb") as f:
            # type: ignore - chamada dinâmica
            resp = audio_api.transcribe("whisper-1", f)  # type: ignore
        return resp.get("text", "")
    # executar em thread para não bloquear o loop async
    return await asyncio.to_thread(_sync_transcribe)

def transcribe_with_faster_whisper(file_path: str) -> str:
    if WhisperModel is None:
        raise RuntimeError("faster-whisper não está instalado")
    model = get_local_whisper_model()
    # faster-whisper pode retornar (segments, info) ou um generator; adaptar conforme versão
    result_text = []
    try:
        segments, _info = model.transcribe(file_path, beam_size=5)  # type: ignore
        for seg in segments:
            # cada seg tem atributo text
            result_text.append(getattr(seg, "text", str(seg)))
    except TypeError:
        # fallback se a assinatura for diferente
        for seg in model.transcribe(file_path):  # type: ignore
            result_text.append(getattr(seg, "text", str(seg)))
    return " ".join(result_text)

async def chatgpt_reply(prompt: str) -> str:
    if openai is None:
        raise RuntimeError("openai não está instalado")
    chat_api = getattr(openai, "ChatCompletion", None)
    if chat_api is None or not hasattr(chat_api, "create"):
        raise RuntimeError("A API de ChatCompletion do OpenAI não está disponível nesta instalação do cliente openai")
    def _sync_chat():
        # type: ignore - chamada dinâmica
        resp = chat_api.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente de voz conciso e educado."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.2,
        )
        # compatibilidade com diferentes formatos de resposta
        choices = resp.get("choices") if isinstance(resp, dict) else getattr(resp, "choices", None)
        if choices and len(choices) > 0:
            message = choices[0].get("message") if isinstance(choices[0], dict) else getattr(choices[0], "message", None)
            if isinstance(message, dict):
                return message.get("content", "").strip()
            # algumas versões retornam diretamente text
            return choices[0].get("text", "").strip() if isinstance(choices[0], dict) else ""
        return ""
    return await asyncio.to_thread(_sync_chat)

@router.post("/transcribe-and-respond")
async def transcribe_and_respond(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    # validação básica de tipo
    content_type = file.content_type or ""
    if not content_type.startswith("audio"):
        raise HTTPException(status_code=400, detail="Envie um arquivo de áudio válido")

    # salvar upload
    tmp_in = await save_upload_to_tempfile(file)

    # 1) transcrição (tenta OpenAI, senão faster-whisper local)
    try:
        if OPENAI_KEY and openai is not None:
            transcript = await transcribe_with_openai(tmp_in)
        elif WhisperModel is not None:
            # faster-whisper é síncrono; executa em thread para não bloquear
            transcript = await asyncio.to_thread(transcribe_with_faster_whisper, tmp_in)
        else:
            raise HTTPException(status_code=500, detail="Nenhum backend de transcrição disponível (instale openai ou faster-whisper)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na transcrição: {e}")

    # 2) enviar para ChatGPT (requer OPENAI_KEY)
    reply_text: Optional[str] = None
    audio_url: Optional[str] = None
    if OPENAI_KEY and openai is not None:
        try:
            reply_text = await chatgpt_reply(transcript)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro no ChatGPT: {e}")
        # 3) gerar TTS com gTTS
        try:
            tts = gTTS(reply_text, lang="pt")
            tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp_out_path = tmp_out.name
            tmp_out.close()
            # gTTS.save é síncrono; executar em thread
            await asyncio.to_thread(tts.save, tmp_out_path)
            audio_filename = os.path.basename(tmp_out_path)
            audio_url = f"/voice-assistant/audio/{audio_filename}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erro no TTS: {e}")

    return JSONResponse({
        "transcript": transcript,
        "reply_text": reply_text,
        "audio_url": audio_url
    })

@router.get("/audio/{filename}")
def get_audio(filename: str, current_user = Depends(get_current_user)):
    # procurar no diretório temporário padrão
    path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(path):
        # tentar caminho alternativo comum em alguns sistemas
        alt = os.path.join("/tmp", filename)
        if os.path.exists(alt):
            path = alt
        else:
            raise HTTPException(status_code=404, detail="Áudio não encontrado")
    return FileResponse(path, media_type="audio/mpeg", filename=filename)
