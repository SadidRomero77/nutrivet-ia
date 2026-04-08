"""
ILabelScanRepository — Puerto de salida para persistencia de escaneos de etiquetas.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime


class ILabelScanRepository(ABC):
    """Interfaz de repositorio para LabelScan."""

    @abstractmethod
    async def save(
        self,
        *,
        scan_id: uuid.UUID,
        pet_id: uuid.UUID,
        user_id: uuid.UUID,
        image_url: str,
        image_type: str,
        semaphore: str,
        ingredients: list[str],
        issues: list[str],
        recomendacion: str,
        created_at: datetime,
    ) -> uuid.UUID:
        """
        Persiste un resultado de escaneo. Retorna el scan_id.

        Args:
            scan_id:       UUID generado por el scanner.
            pet_id:        UUID de la mascota objetivo (anónimo — sin nombre).
            user_id:       UUID del usuario que realizó el escaneo.
            image_url:     URL de la imagen en R2 (presigned o path).
            image_type:    "nutrition_table" | "ingredient_list".
            semaphore:     "ROJO" | "AMARILLO" | "VERDE".
            ingredients:   Lista de ingredientes detectados por OCR.
            issues:        Problemas detectados en la evaluación.
            recomendacion: Texto de recomendación para el owner.
            created_at:    Timestamp de creación.
        """
