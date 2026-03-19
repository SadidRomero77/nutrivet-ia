"""
Schemas Pydantic para el servicio de exportación de planes a PDF.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ExportResponse(BaseModel):
    """Respuesta al exportar un plan a PDF."""

    url: str = Field(..., description="URL pre-signed para descarga del PDF (TTL 1 hora).")
    expires_at: datetime = Field(
        ..., description="Timestamp UTC de expiración de la URL pre-signed."
    )
