"""
Schemas Pydantic para el scanner de etiquetas nutricionales.

ScanResult NO incluye brand_name — principio de imparcialidad.
Disclaimer obligatorio en toda respuesta (REGLA 8).
"""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

_DISCLAIMER = (
    "NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario."
)


class ScanResult(BaseModel):
    """
    Resultado del escaneo de etiqueta nutricional.

    NUNCA incluye brand_name — principio de imparcialidad (REGLA 7).
    """

    scan_id: Optional[str] = Field(None, description="ID del registro de escaneo")
    image_type: str = Field(..., description="nutrition_table | ingredient_list")
    semaphore: str = Field(..., description="ROJO | AMARILLO | VERDE")
    ingredients_detected: list[str] = Field(
        default_factory=list, description="Ingredientes detectados por OCR"
    )
    issues: list[str] = Field(
        default_factory=list, description="Problemas detectados (tóxicos, restricciones, alergias)"
    )
    recomendacion: str = Field(..., description="Recomendación al usuario")
    image_url: Optional[str] = Field(None, description="URL en Cloudflare R2")
    disclaimer: str = Field(
        default=_DISCLAIMER,
        description="Aviso legal obligatorio (REGLA 8)",
    )
    # brand_name está EXCLUIDO intencionalmente — principio de imparcialidad
