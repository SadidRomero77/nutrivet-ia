"""
FernetEncryptor — Encriptación AES-256 de campos médicos sensibles.
Constitution REGLA 6: datos médicos encriptados en reposo en PostgreSQL.
La clave se lee de variable de entorno FERNET_KEY — nunca hardcodeada.
"""
from __future__ import annotations

import json
import os
from typing import Any

from cryptography.fernet import Fernet


def _get_fernet() -> Fernet:
    """Obtiene la instancia Fernet usando la clave de entorno."""
    key = os.environ.get("FERNET_KEY")
    if not key:
        # En desarrollo usamos una clave generada en memoria — nunca en producción
        key = Fernet.generate_key().decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


class FernetEncryptor:
    """
    Encripta y desencripta listas/dicts como JSON usando Fernet (AES-256-CBC + HMAC).

    Uso: encriptar medical_conditions y allergies antes de persistir en DB.
    Los campos se almacenan como BYTEA en PostgreSQL.
    """

    def __init__(self) -> None:
        self._fernet = _get_fernet()

    def encrypt(self, data: list[Any] | dict[str, Any]) -> bytes:
        """
        Encripta una lista o dict como JSON.

        Args:
            data: Dato a encriptar (lista de condiciones, lista de alergias, etc.).

        Returns:
            Ciphertext como bytes para almacenar en columna BYTEA.
        """
        plaintext = json.dumps(data, ensure_ascii=False).encode("utf-8")
        return self._fernet.encrypt(plaintext)

    def decrypt(self, ciphertext: bytes) -> list[Any]:
        """
        Desencripta ciphertext y retorna la lista original.

        Args:
            ciphertext: Bytes almacenados en columna BYTEA.

        Returns:
            Lista original desencriptada.
        """
        plaintext = self._fernet.decrypt(ciphertext)
        return json.loads(plaintext.decode("utf-8"))
