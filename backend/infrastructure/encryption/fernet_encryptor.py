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
    """
    Obtiene la instancia Fernet usando la clave de entorno.

    CRITICAL: Si FERNET_KEY no está configurada, falla ruidosamente.
    Una clave generada en memoria se pierde al reiniciar → todos los datos
    médicos encriptados quedan irrecuperables (Constitution REGLA 6).

    Para generar una clave válida:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    """
    key = os.environ.get("FERNET_KEY")
    if not key:
        raise RuntimeError(
            "FERNET_KEY no está configurada. "
            "Sin esta clave los datos médicos encriptados son irrecuperables al reiniciar. "
            "Genera una con: python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\" "
            "y agrégala a .env.dev o a las variables de entorno del contenedor."
        )
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
