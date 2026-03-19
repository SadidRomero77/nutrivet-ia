"""
IPDFGenerator — Puerto de salida para generación de PDFs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class IPDFGenerator(ABC):
    """Interfaz para generadores de PDF de planes nutricionales."""

    @abstractmethod
    def generate(self, plan_data: dict) -> bytes:
        """
        Genera el PDF del plan nutricional.

        Args:
            plan_data: Diccionario con los datos del plan (5 secciones + metadata).

        Returns:
            Bytes del PDF generado.
        """
