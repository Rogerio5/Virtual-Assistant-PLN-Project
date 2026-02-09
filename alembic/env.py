# alembic/env.py
import os
import sys
from logging.config import fileConfig
from typing import Dict, Any, cast

from sqlalchemy import engine_from_config, pool
from alembic import context

# Carrega .env em desenvolvimento (opcional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

config = context.config

# Sobrescreve a URL do alembic.ini com a variável de ambiente DATABASE_URL, se existir
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Configura logging do Alembic
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------
# IMPORTE AQUI O SEU METADATA REAL
# Ajuste o caminho abaixo para onde seu Base está definido.
# Exemplo comum: from backend.db.base import Base
# ---------------------------------------------------------------------
target_metadata = None
try:
    # Tenta localizar automaticamente em caminhos comuns
    _possible_paths = [
        "backend.db.base",
        "backend.db.models",
        "database.base",
        "database.models",
        "app.db.base",
        "models",
    ]
    for path in _possible_paths:
        try:
            module = __import__(path, fromlist=["Base", "metadata"])
            if hasattr(module, "Base"):
                target_metadata = getattr(module, "Base").metadata
                break
            if hasattr(module, "metadata"):
                target_metadata = getattr(module, "metadata")
                break
        except Exception:
            continue
except Exception:
    target_metadata = None

# Se não encontrou automaticamente, descomente e ajuste a linha abaixo:
# from backend.db.base import Base
# target_metadata = Base.metadata

# ---------------------------------------------------------------------
# Funções padrão do Alembic para rodar migrações offline/online
# ---------------------------------------------------------------------
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # Recupera a seção de configuração e garante que não seja None
    section = config.get_section(config.config_ini_section)
    if section is None:
        raise RuntimeError(f"Config section not found: {config.config_ini_section}")

    # Cast para satisfazer o verificador de tipos (Pylance)
    section_typed = cast(Dict[str, Any], section)

    connectable = engine_from_config(
        section_typed,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
