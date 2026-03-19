"""
Base de SQLAlchemy para todos los modelos ORM de NutriVet.IA.
Los modelos importan desde aquí para que Alembic detecte el metadata.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base declarativa compartida por todos los modelos ORM."""
    pass
