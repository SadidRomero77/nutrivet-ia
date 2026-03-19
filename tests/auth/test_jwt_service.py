"""Tests RED — JWTService (unit-02-auth-service Paso 4)."""
import time
import uuid

import pytest

from backend.domain.aggregates.user_account import UserRole, UserTier
from backend.domain.exceptions.domain_errors import DomainError
from backend.infrastructure.auth.jwt_service import JWTService, TokenPayload


@pytest.fixture
def jwt_service() -> JWTService:
    """Instancia de JWTService con secret de test."""
    return JWTService(secret_key="test-secret-superseguro-123", algorithm="HS256")


class TestAccessToken:
    """Tests de generación y verificación de access tokens."""

    def test_generar_access_token_expira_en_15min(self, jwt_service: JWTService) -> None:
        """El access token tiene expiración de 15 minutos (900 segundos)."""
        user_id = uuid.uuid4()
        token = jwt_service.create_access_token(
            user_id=user_id, role=UserRole.OWNER, tier=UserTier.FREE
        )
        assert isinstance(token, str)
        assert len(token) > 0

        # Decodificar y verificar payload
        payload = jwt_service.verify_access_token(token)
        assert payload.user_id == user_id
        assert payload.role == UserRole.OWNER
        assert payload.tier == UserTier.FREE

        # Verificar que exp está ~15 minutos en el futuro
        tiempo_restante = payload.exp - time.time()
        assert 850 < tiempo_restante < 950  # entre ~14 y ~16 min

    def test_verificar_token_valido(self, jwt_service: JWTService) -> None:
        """Verificar un token válido retorna el payload correcto."""
        user_id = uuid.uuid4()
        token = jwt_service.create_access_token(
            user_id=user_id, role=UserRole.VET, tier=UserTier.VET
        )
        payload = jwt_service.verify_access_token(token)
        assert payload.user_id == user_id
        assert payload.role == UserRole.VET
        assert payload.tier == UserTier.VET

    def test_verificar_token_invalido_lanza_error(self, jwt_service: JWTService) -> None:
        """Token con firma inválida lanza DomainError."""
        with pytest.raises(DomainError, match="token"):
            jwt_service.verify_access_token("token.invalido.firma")

    def test_verificar_token_expirado_lanza_error(self, jwt_service: JWTService) -> None:
        """Token expirado lanza DomainError."""
        user_id = uuid.uuid4()
        # Crear token con expiración inmediata (pasada)
        token = jwt_service.create_access_token(
            user_id=user_id,
            role=UserRole.OWNER,
            tier=UserTier.FREE,
            expires_seconds=-1,  # expirado en el pasado
        )
        with pytest.raises(DomainError, match="expirado"):
            jwt_service.verify_access_token(token)


class TestRefreshToken:
    """Tests de refresh tokens."""

    def test_generar_refresh_token_es_uuid(self, jwt_service: JWTService) -> None:
        """El refresh token es un UUID v4 válido."""
        token = jwt_service.create_refresh_token()
        # Debe ser un UUID válido
        parsed = uuid.UUID(token)
        assert parsed.version == 4

    def test_refresh_token_rotativo_invalida_anterior(self, jwt_service: JWTService) -> None:
        """Dos refresh tokens generados son distintos (rotativos)."""
        token1 = jwt_service.create_refresh_token()
        token2 = jwt_service.create_refresh_token()
        assert token1 != token2
