# ⚙️ Configuração do backend/config.py

Este projeto usa **FastAPI + Pydantic v2 + pydantic-settings** para carregar variáveis de ambiente do arquivo `.env`.  
Existem duas formas de configurar o `config.py`:

---

## 🔹 Opção 1 – Declarar todos os campos explicitamente (mais segura)

Nesta abordagem, todas as variáveis esperadas no `.env` são declaradas na classe `Settings`.  
O Pydantic valida cada campo, garantindo consistência e segurança.

```python
from functools import lru_cache
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = Field(default="Virtual Assistant PLN")
    VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=True)

    # Banco de dados
    DATABASE_URL: str | None = None
    DB_NAME: str | None = None
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: str | None = None

    # SMTP
    SMTP_EMAIL: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_SERVER: str | None = None
    SMTP_PORT: str | None = None

    # JWT
    JWT_ALGORITHM: str | None = None

    # SendGrid
    SENDGRID_API_KEY: str | None = None

    # AWS
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

✅ Vantagem: validação forte, segurança.
❌ Desvantagem: precisa declarar todas as variáveis.

```

## 🔹 Opção 2 Permitir variáveis extras automaticamente (mais rápida)

Nesta abordagem, você declara apenas o essencial e permite que variáveis extras sejam aceitas sem erro.
É útil para desenvolvimento ou prototipagem rápida.

from functools import lru_cache
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = Field(default="Virtual Assistant PLN")
    VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=True)

    DB_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/assistant_db",
        description="URL de conexão com banco de dados PostgreSQL"
    )

    SECRET_KEY: str = Field(default="supersecret")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"   # <-- aceita variáveis extras sem erro

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

✅ Vantagem: rápido, não quebra se tiver variáveis extras.
❌ Desvantagem: menos validação, pode passar despercebido se faltar algo.

Opção 1 → ideal para produção, garante consistência e validação.

Opção 2 → ideal para desenvolvimento/testes, sobe rápido sem precisar declarar tudo

---

## 🔒 Futuro (produção) – validação completa


Na versão de produção, recomendamos declarar explicitamente todas as variáveis esperadas no .env, como:

Banco de dados: DB_USER, DB_PASSWORD, DB_HOST, etc.

SMTP: SMTP_EMAIL, SMTP_PASSWORD, etc.

Segurança: JWT_ALGORITHM, SENDGRID_API_KEY, AWS_SECRET_ACCESS_KEY, etc.

Isso garante validação automática e evita erros silenciosos.
