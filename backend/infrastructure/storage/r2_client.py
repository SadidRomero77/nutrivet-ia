"""
R2StorageClient — Cliente S3-compatible para Cloudflare R2.

- upload(): put_object con retry × 2.
- exists(): head_object con try/except.
- generate_presigned_url(): TTL hardcoded 3600s (no configurable — Constitution).
"""
from __future__ import annotations

import logging
import time

import boto3
from botocore.exceptions import ClientError

from backend.application.interfaces.storage_client import IStorageClient

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2  # 1 intento original + 2 retries = 3 total


class R2StorageClient(IStorageClient):
    """
    Cliente boto3 S3-compatible para Cloudflare R2.

    Configuración via parámetros o variables de entorno.
    Si las credenciales no están disponibles en dev → falla con mensaje claro.
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
    ) -> None:
        self._bucket = bucket_name
        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        self._s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )

    @classmethod
    def from_env(cls) -> "R2StorageClient":
        """
        Construye el cliente desde variables de entorno.

        Requiere: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME.
        """
        import os
        return cls(
            account_id=os.environ["R2_ACCOUNT_ID"],
            access_key_id=os.environ["R2_ACCESS_KEY_ID"],
            secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
            bucket_name=os.environ["R2_BUCKET_NAME"],
        )

    def upload(self, key: str, data: bytes, content_type: str) -> str:
        """
        Sube un objeto a R2 con retry × 2.

        Args:
            key: Clave del objeto (e.g. "pdfs/plan-uuid.pdf").
            data: Bytes del contenido.
            content_type: MIME type.

        Returns:
            La clave del objeto subido.

        Raises:
            ClientError: Tras 3 intentos fallidos.
        """
        last_error: Exception | None = None
        for attempt in range(1 + _MAX_RETRIES):
            try:
                self._s3.put_object(
                    Bucket=self._bucket,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                )
                return key
            except ClientError as exc:
                last_error = exc
                if attempt < _MAX_RETRIES:
                    logger.warning(
                        "R2 upload intento %d/%d fallido: %s — reintentando...",
                        attempt + 1,
                        1 + _MAX_RETRIES,
                        exc,
                    )
                    time.sleep(0.5 * (attempt + 1))

        raise last_error  # type: ignore[misc]

    def exists(self, key: str) -> bool:
        """
        Verifica si el objeto existe en R2.

        Args:
            key: Clave del objeto.

        Returns:
            True si existe, False si no.
        """
        try:
            self._s3.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False

    def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Genera URL pre-signed para descarga.

        TTL hardcoded a 3600s (no configurable externamente — Constitution).

        Args:
            key: Clave del objeto.
            expires_in: TTL en segundos — siempre 3600.

        Returns:
            URL pre-signed con TTL de 1 hora.
        """
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
