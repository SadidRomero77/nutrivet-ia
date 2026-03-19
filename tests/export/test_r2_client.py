"""
Tests RED — R2StorageClient (NUT-94 · Paso 4).

Verifica:
- upload() retorna r2 key.
- generate_presigned_url() TTL exactamente 3600s.
- exists() true/false según objeto en R2.
- upload falla → retry x2.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch, call
import pytest


class TestR2StorageClient:

    def test_upload_retorna_r2_key(self) -> None:
        """upload() retorna la clave del objeto en R2."""
        from backend.infrastructure.storage.r2_client import R2StorageClient

        mock_s3 = MagicMock()
        mock_s3.put_object.return_value = {}

        with patch("backend.infrastructure.storage.r2_client.boto3.client", return_value=mock_s3):
            client = R2StorageClient(
                account_id="acct",
                access_key_id="key",
                secret_access_key="secret",
                bucket_name="plans",
            )
            key = client.upload(
                key="pdfs/plan-001.pdf",
                data=b"%PDF-fake",
                content_type="application/pdf",
            )

        assert key == "pdfs/plan-001.pdf"
        mock_s3.put_object.assert_called_once()

    def test_presigned_url_ttl_es_exactamente_3600(self) -> None:
        """generate_presigned_url() llama generate_presigned_url con ExpiresIn=3600."""
        from backend.infrastructure.storage.r2_client import R2StorageClient

        mock_s3 = MagicMock()
        mock_s3.generate_presigned_url.return_value = "https://r2.dev/plan.pdf?sig=abc"

        with patch("backend.infrastructure.storage.r2_client.boto3.client", return_value=mock_s3):
            client = R2StorageClient(
                account_id="acct",
                access_key_id="key",
                secret_access_key="secret",
                bucket_name="plans",
            )
            url = client.generate_presigned_url("pdfs/plan-001.pdf")

        assert url.startswith("https://")
        mock_s3.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "plans", "Key": "pdfs/plan-001.pdf"},
            ExpiresIn=3600,
        )

    def test_exists_true_si_objeto_en_r2(self) -> None:
        """exists() retorna True si el objeto existe en R2."""
        from backend.infrastructure.storage.r2_client import R2StorageClient

        mock_s3 = MagicMock()
        mock_s3.head_object.return_value = {"ContentLength": 12345}

        with patch("backend.infrastructure.storage.r2_client.boto3.client", return_value=mock_s3):
            client = R2StorageClient(
                account_id="acct",
                access_key_id="key",
                secret_access_key="secret",
                bucket_name="plans",
            )
            result = client.exists("pdfs/plan-001.pdf")

        assert result is True

    def test_exists_false_si_objeto_no_en_r2(self) -> None:
        """exists() retorna False si el objeto no existe (ClientError 404)."""
        from botocore.exceptions import ClientError
        from backend.infrastructure.storage.r2_client import R2StorageClient

        mock_s3 = MagicMock()
        mock_s3.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject"
        )

        with patch("backend.infrastructure.storage.r2_client.boto3.client", return_value=mock_s3):
            client = R2StorageClient(
                account_id="acct",
                access_key_id="key",
                secret_access_key="secret",
                bucket_name="plans",
            )
            result = client.exists("pdfs/plan-noexiste.pdf")

        assert result is False

    def test_upload_falla_retry_x2(self) -> None:
        """upload() con error R2 → retry ×2 → levanta excepción tras 3 intentos."""
        from backend.infrastructure.storage.r2_client import R2StorageClient
        from botocore.exceptions import ClientError

        error = ClientError(
            {"Error": {"Code": "InternalError", "Message": "R2 error"}}, "PutObject"
        )
        mock_s3 = MagicMock()
        mock_s3.put_object.side_effect = error

        with patch("backend.infrastructure.storage.r2_client.boto3.client", return_value=mock_s3):
            client = R2StorageClient(
                account_id="acct",
                access_key_id="key",
                secret_access_key="secret",
                bucket_name="plans",
            )
            with pytest.raises(Exception):
                client.upload("pdfs/plan.pdf", b"data", "application/pdf")

        # 1 intento original + 2 retries = 3 llamadas total
        assert mock_s3.put_object.call_count == 3
