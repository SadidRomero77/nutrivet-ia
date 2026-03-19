"""
Alembic env.py — NutriVet.IA
Soporta URL desde variable de entorno DATABASE_URL (prioridad) o alembic.ini.
Importa Base.metadata cuando los modelos SQLAlchemy estén definidos.
"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Objeto de configuración de Alembic
config = context.config

# Configurar logging desde el .ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Leer DATABASE_URL desde entorno si existe (prioridad sobre alembic.ini)
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Importar metadata de los modelos para autogenerate (unit-02+).
from backend.infrastructure.db.models import Base  # noqa: E402, F401
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline (sin conexión activa)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo online (con conexión activa)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
