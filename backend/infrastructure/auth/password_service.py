"""
PasswordService — Hashing y verificación de contraseñas con bcrypt.
Nunca almacenar contraseñas en texto plano.
"""
import bcrypt


class PasswordService:
    """
    Servicio de gestión de contraseñas.

    Usa bcrypt con factor de coste 12 (configurable).
    Compatible con bcrypt >= 4.x.
    """

    def __init__(self, rounds: int = 12) -> None:
        """
        Args:
            rounds: Factor de coste bcrypt (default 12).
        """
        self._rounds = rounds

    def hash_password(self, password: str) -> str:
        """
        Genera el hash bcrypt de una contraseña en texto plano.

        Args:
            password: Contraseña en texto plano. Nunca persistir este valor.

        Returns:
            Hash bcrypt seguro para almacenar en DB.
        """
        salt = bcrypt.gensalt(rounds=self._rounds)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain: str, hashed: str) -> bool:
        """
        Verifica si una contraseña en texto plano coincide con el hash almacenado.

        Args:
            plain: Contraseña en texto plano ingresada por el usuario.
            hashed: Hash bcrypt almacenado en DB.

        Returns:
            True si coinciden, False en caso contrario.
        """
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
