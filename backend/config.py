# backend/config.py
"""
Robust configuration loader for the Assistant API.

- Carrega variáveis de ambiente do arquivo .env (procura em backend/.env, projeto raiz e um nível acima).
- Normaliza FRONTEND_ORIGINS (aceita string vírgula-separada ou lista).
- Converte inteiros/booleans com tratamento seguro para evitar avisos do Pylance.
- Monta DATABASE_URL a partir de variáveis POSTGRES_* ou DB_* quando necessário.
- Fornece valores padrão seguros para desenvolvimento.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union
import os
import logging

from dotenv import load_dotenv

logger = logging.getLogger("backend.config")

# Carrega .env procurando em locais comuns:
# 1) backend/.env (quando rodando a partir da pasta backend)
# 2) projeto raiz .env (quando rodando a partir da raiz)
# 3) um nível acima (útil em alguns setups)
def _load_dotenv_if_exists() -> None:
    candidates = [
        Path(__file__).resolve().parent.joinpath(".env"),
        Path.cwd().joinpath(".env"),
        Path(__file__).resolve().parents[1].joinpath(".env"),
    ]
    for p in candidates:
        try:
            if p.exists():
                load_dotenv(dotenv_path=str(p))
                logger.debug("Loaded .env from %s", p)
                return
        except Exception:
            # não falhar se load_dotenv lançar
            logger.debug("Failed to load .env from %s", p, exc_info=True)
    logger.debug("No .env file found in common locations")

_load_dotenv_if_exists()

def _split_origins(value: Optional[Union[str, List[str]]]) -> List[str]:
    """
    Aceita:
      - None -> retorna []
      - str com vírgulas -> divide e limpa espaços
      - lista/tupla de strings -> converte cada item para str e limpa espaços
    Retorna sempre uma lista de strings limpas.
    """
    if not value:
        return []
    if isinstance(value, str):
        return [o.strip() for o in value.split(",") if o.strip()]
    if isinstance(value, (list, tuple)):
        return [str(o).strip() for o in value if str(o).strip()]
    return []

def _int_env(name: str, default: Optional[int] = None) -> Optional[int]:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        logger.debug("Environment variable %s could not be parsed as int: %r", name, v)
        return default

def _bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "yes", "on")

@dataclass
class Settings:
    # App / Infra
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Assistant API")
    DEBUG: bool = _bool_env("DEBUG", True)
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = _int_env("PORT", 8000) or 8000

    # Static / TTS
    STATIC_DIR: str = os.getenv("STATIC_DIR", "static")
    TTS_SUBDIR: str = os.getenv("TTS_STATIC_SUBDIR", "tts")
    BASE_URL: Optional[str] = os.getenv("BASE_URL") or None  # ex.: http://localhost:8000

    # CORS: aceita string vírgula-separada em FRONTEND_ORIGINS
    FRONTEND_ORIGINS_RAW: Optional[str] = os.getenv("FRONTEND_ORIGINS")
    FRONTEND_ORIGINS: List[str] = field(default_factory=list)

    # Limits (unificado name: MAX_CONTENT_LENGTH_BYTES)
    MAX_CONTENT_LENGTH_BYTES: int = _int_env("MAX_CONTENT_LENGTH_BYTES", 10 * 1024 * 1024) or (10 * 1024 * 1024)

    # Database (Postgres) - aceita DATABASE_URL ou componentes POSTGRES_/DB_
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL") or None
    DB_NAME: Optional[str] = os.getenv("DB_NAME") or None
    DB_USER: Optional[str] = os.getenv("DB_USER") or None
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD") or None
    DB_HOST: Optional[str] = os.getenv("DB_HOST") or None
    DB_PORT: Optional[int] = _int_env("DB_PORT", None)

    # Também aceita variáveis com prefixo POSTGRES_ (comum em docker-compose)
    POSTGRES_DB: Optional[str] = os.getenv("POSTGRES_DB") or None
    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER") or None
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD") or None
    POSTGRES_HOST: Optional[str] = os.getenv("POSTGRES_HOST") or None
    POSTGRES_PORT: Optional[int] = _int_env("POSTGRES_PORT", None)

    # SMTP
    SMTP_EMAIL: Optional[str] = os.getenv("SMTP_EMAIL") or None
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD") or None
    SMTP_SERVER: Optional[str] = os.getenv("SMTP_SERVER") or None
    SMTP_PORT: Optional[int] = _int_env("SMTP_PORT", None)
    SMTP_USE_TLS: bool = _bool_env("SMTP_USE_TLS", True)

    # Security / JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRES_SECONDS: int = _int_env("JWT_EXPIRES_SECONDS", 3600) or 3600
    ADMIN_API_KEY: Optional[str] = os.getenv("ADMIN_API_KEY") or None

    # Optional integrations
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY") or None
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_COMPUTE: Optional[str] = os.getenv("WHISPER_COMPUTE") or None
    FFMPEG_BIN: str = os.getenv("FFMPEG_BIN", "ffmpeg")

    # Observability / extras
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN") or None
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID") or None
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY") or None
    S3_BUCKET_NAME: Optional[str] = os.getenv("S3_BUCKET_NAME") or None

    def __post_init__(self):
        # FRONTEND_ORIGINS parsing
        try:
            self.FRONTEND_ORIGINS = _split_origins(self.FRONTEND_ORIGINS_RAW or os.getenv("FRONTEND_ORIGINS"))
            if not self.FRONTEND_ORIGINS:
                # fallback padrão para dev
                self.FRONTEND_ORIGINS = ["http://localhost:5174"]
        except Exception:
            self.FRONTEND_ORIGINS = ["http://localhost:5174"]

        # Monta DATABASE_URL a partir de componentes se não fornecida
        if not self.DATABASE_URL:
            # Prioriza DB_* (genérico) e depois POSTGRES_* (docker-compose)
            user = self.DB_USER or self.POSTGRES_USER or os.getenv("DB_USER") or os.getenv("POSTGRES_USER")
            pwd = self.DB_PASSWORD or self.POSTGRES_PASSWORD or os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD")
            host = self.DB_HOST or self.POSTGRES_HOST or os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST") or "localhost"
            port = self.DB_PORT or self.POSTGRES_PORT or _int_env("DB_PORT", None) or _int_env("POSTGRES_PORT", None) or 5432
            db = self.DB_NAME or self.POSTGRES_DB or os.getenv("DB_NAME") or os.getenv("POSTGRES_DB") or "assistant_db"
            if user and pwd:
                self.DATABASE_URL = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
            else:
                # se não há credenciais suficientes, deixa None (aplicação pode tratar)
                self.DATABASE_URL = None

        # Segurança: avisar se SECRET_KEY padrão em produção
        app_env = os.getenv("APP_ENV", os.getenv("ENV", "development")).lower()
        if (app_env == "production" or not self.DEBUG) and (not self.SECRET_KEY or self.SECRET_KEY in ("change-me", "default", "secret")):
            logger.warning("SECRET_KEY está no valor padrão em ambiente de produção. Defina SECRET_KEY forte.")

        # Debug log (não imprime segredos)
        logger.debug(
            "Settings loaded: DEBUG=%s, HOST=%s, PORT=%s, FRONTEND_ORIGINS=%s, MAX_CONTENT_LENGTH_BYTES=%s, DATABASE_URL_set=%s",
            self.DEBUG,
            self.HOST,
            self.PORT,
            self.FRONTEND_ORIGINS,
            self.MAX_CONTENT_LENGTH_BYTES,
            bool(self.DATABASE_URL),
        )

# Instância global de settings
settings = Settings()
