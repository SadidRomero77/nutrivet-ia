"""
IStorageClient — Puerto de salida para almacenamiento de objetos (R2 / S3).
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class IStorageClient(ABC):
    """Interfaz para clientes de almacenamiento S3-compatible."""

    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str) -> str:
        """
        Sube un objeto al bucket.

        Args:
            key: Clave del objeto (e.g. "pdfs/plan-uuid.pdf").
            data: Bytes del contenido.
            content_type: MIME type (e.g. "application/pdf").

        Returns:
            La clave del objeto subido.
        """

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Verifica si un objeto existe en el bucket.

        Args:
            key: Clave del objeto.

        Returns:
            True si existe, False si no.
        """

    @abstractmethod
    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Genera una URL pre-firmada para descarga.

        Args:
            key: Clave del objeto.
            expires_in: TTL en segundos (default 3600 — no configurable externamente).

        Returns:
            URL pre-firmada con TTL.
        """
