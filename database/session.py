# backend/database/session.py
import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Base para os modelos
Base = declarative_base()

# URL do banco (vem do .env ou usa padrão)
# Recomendo usar o driver psycopg2 explicitamente em URLs de Postgres:
# postgresql+psycopg2://user:pass@host:port/dbname
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

# Validação simples para evitar usar credenciais padrão em produção
if not DATABASE_URL:
    # Em desenvolvimento você pode definir um fallback local, mas é melhor falhar rápido
    # para evitar usar credenciais embutidas acidentalmente.
    raise RuntimeError(
        "DATABASE_URL não está definida. Defina a variável de ambiente DATABASE_URL ou configure um .env."
    )

# Engine e sessão
# pool_pre_ping evita erros com conexões "zumbis"
# future=True ativa a API 2.0 do SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, future=True)

# SessionLocal com tipagem explícita
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

def get_db() -> Generator[Session, None, None]:
    """
    Dependência para FastAPI / uso geral.

    Uso típico em FastAPI:
        from fastapi import Depends
        from database.session import get_db

        def endpoint(db: Session = Depends(get_db)):
            ...

    Gera uma sessão e garante fechamento no finally.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
