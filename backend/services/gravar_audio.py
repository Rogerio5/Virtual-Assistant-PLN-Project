# backend/services/gravar_audio.py
"""
Serviço utilitário para salvar e manipular arquivos de áudio enviados ao servidor.

Funções principais:
- save_upload_file: salva um UploadFile do FastAPI em disco de forma segura.
- save_bytes_to_file: salva bytes em arquivo com nome gerado.
- convert_to_wav: converte um arquivo de áudio para WAV (mono, 16kHz, s16) usando ffmpeg.
- remove_file: remove arquivo com tratamento de erros.

Observações:
- Requer ffmpeg no PATH para conversão.
- Os arquivos são salvos por padrão em 'uploads/audio'.
"""

from typing import Optional, Tuple
import logging
import os
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from shutil import which

logger = logging.getLogger("gravar_audio")

BASE_DIR = Path("uploads") / "audio"
BASE_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_ffmpeg_available() -> None:
    if which("ffmpeg") is None:
        logger.error("ffmpeg não encontrado no PATH.")
        raise RuntimeError("ffmpeg não encontrado no servidor. Instale ffmpeg ou adicione ao PATH.")


def _generate_filename(prefix: str = "audio", ext: str = ".wav") -> str:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    name = f"{prefix}_{ts}{ext}"
    return name


async def save_upload_file(upload_file, dest_dir: Optional[Path] = None) -> Path:
    """
    Salva um UploadFile (FastAPI) em disco e retorna o Path salvo.
    Uso:
        path = await save_upload_file(file)
    """
    if dest_dir is None:
        dest_dir = BASE_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = upload_file.filename or _generate_filename(prefix="upload", ext="")
    ext = Path(filename).suffix or ""
    safe_name = _generate_filename(prefix=Path(filename).stem, ext=ext or ".bin")
    out_path = dest_dir / safe_name

    # Leitura assíncrona do UploadFile
    content = await upload_file.read()
    with open(out_path, "wb") as f:
        f.write(content)
    logger.info("Upload salvo em %s", out_path)
    return out_path


def save_bytes_to_file(content: bytes, prefix: str = "audio", ext: str = ".wav", dest_dir: Optional[Path] = None) -> Path:
    """
    Salva bytes em arquivo no diretório de uploads e retorna o Path.
    """
    if dest_dir is None:
        dest_dir = BASE_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = _generate_filename(prefix=prefix, ext=ext)
    out_path = dest_dir / filename
    with open(out_path, "wb") as f:
        f.write(content)
    logger.info("Bytes salvos em %s", out_path)
    return out_path


def convert_to_wav(input_path: Path, sample_rate: int = 16000) -> Path:
    """
    Converte um arquivo de áudio para WAV (mono, sample_rate, s16) usando ffmpeg.
    Retorna o Path do arquivo WAV gerado.
    Lança RuntimeError em caso de falha.
    """
    _ensure_ffmpeg_available()

    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {input_path}")

    # Gera arquivo temporário seguro no mesmo diretório de destino
    out_file = input_path.with_suffix(".converted.wav")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-sample_fmt",
        "s16",
        str(out_file),
    ]
    logger.debug("Executando ffmpeg: %s", " ".join(cmd))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        stderr = proc.stderr.decode(errors="ignore") if proc.stderr else ""
        logger.error("ffmpeg falhou ao converter %s: %s", input_path, stderr)
        # tenta remover arquivo de saída parcial
        try:
            if out_file.exists():
                out_file.unlink()
        except Exception:
            logger.debug("Não foi possível remover arquivo de saída parcial %s", out_file)
        raise RuntimeError(f"Falha na conversão para WAV: {stderr}")

    logger.info("Arquivo convertido para WAV: %s", out_file)
    return out_file


def remove_file(path: Path) -> bool:
    """
    Remove um arquivo do sistema de arquivos. Retorna True se removido, False caso contrário.
    """
    try:
        if path and path.exists():
            path.unlink()
            logger.debug("Arquivo removido: %s", path)
            return True
        return False
    except Exception as exc:
        logger.exception("Falha ao remover arquivo %s: %s", path, exc)
        return False


__all__ = [
    "save_upload_file",
    "save_bytes_to_file",
    "convert_to_wav",
    "remove_file",
    "BASE_DIR",
]
