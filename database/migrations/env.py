import os
import sys
from logging.config import fileConfig
from typing import Any, Dict

from sqlalchemy import engine_from_config, pool
from alembic import context
from alembic.config import Config as AlembicConfig

# --- Ajuste de path para encontrar a raiz do projeto ---
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT_DIR)

# Carregar variáveis do .env
from dotenv import load_dotenv
load_dotenv()

# Importar Base e modelos
from database.session import Base
from database import models  # garante que os modelos sejam carregados

# Configuração do Alembic
# anotar explicitamente para o analisador de tipos
config: AlembicConfig = context.config  # type: ignore[assignment]

# Lê a URL do banco do .env
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # evita que o ConfigParser interprete '%' como interpolação
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Configuração de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadados dos modelos (para autogenerate)
target_metadata: Any = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrations no modo offline (gera SQL sem conectar ao banco)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Executa migrations no modo online (conecta ao banco)."""
    # normaliza a seção de configuração para Dict[str, Any] (nunca None)
    raw_conf = config.get_section(config.config_ini_section)
    configuration: Dict[str, Any] = dict(raw_conf or {})

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
