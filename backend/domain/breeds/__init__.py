"""
Catálogo de razas — NutriVet.IA
Módulo de dominio: predisposiciones genéticas y características nutricionales por raza.
"""
from backend.domain.breeds.breed_catalog import (
    BreedInfo,
    BREED_CATALOG,
    BREED_PREDISPOSITIONS,
    get_breed,
    search_breeds,
)

__all__ = [
    "BreedInfo",
    "BREED_CATALOG",
    "BREED_PREDISPOSITIONS",
    "get_breed",
    "search_breeds",
]
