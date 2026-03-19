"""Tests RED — Middleware RBAC (unit-02-auth-service Paso 10)."""
from __future__ import annotations

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from backend.domain.aggregates.user_account import UserRole, UserTier
from backend.infrastructure.auth.jwt_service import JWTService
from backend.presentation.middleware.auth_middleware import (
    get_current_user,
    get_jwt_service,
    require_role,
    TokenPayload,
)

import uuid

_TEST_SECRET = "test-rbac-secret-789"

# JWTService con clave de test
_jwt = JWTService(secret_key=_TEST_SECRET, algorithm="HS256")


def _make_token(role: UserRole, tier: UserTier = UserTier.FREE) -> str:
    return _jwt.create_access_token(user_id=uuid.uuid4(), role=role, tier=tier)


# App de test que expone endpoints con RBAC
app = FastAPI()

# Override: usar el mismo JWT secret que los tokens generados en el test
app.dependency_overrides[get_jwt_service] = lambda: _jwt


@app.get("/owner-only")
async def owner_endpoint(
    user: TokenPayload = Depends(require_role("owner")),
) -> dict:
    return {"role": user.role.value}


@app.get("/vet-only")
async def vet_endpoint(
    user: TokenPayload = Depends(require_role("vet")),
) -> dict:
    return {"role": user.role.value}


@app.get("/any-auth")
async def any_auth_endpoint(
    user: TokenPayload = Depends(get_current_user),
) -> dict:
    return {"role": user.role.value}


client = TestClient(app, raise_server_exceptions=False)


class TestRBACMiddleware:
    """Tests del middleware de autenticación y autorización."""

    def test_require_role_owner_con_token_owner(self) -> None:
        """Token de owner accede a endpoint de owner → 200."""
        token = _make_token(UserRole.OWNER)
        resp = client.get("/owner-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["role"] == "owner"

    def test_require_role_vet_con_token_owner_falla(self) -> None:
        """Token de owner NO accede a endpoint de vet → 403."""
        token = _make_token(UserRole.OWNER)
        resp = client.get("/vet-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    def test_require_role_vet_con_token_vet(self) -> None:
        """Token de vet accede a endpoint de vet → 200."""
        token = _make_token(UserRole.VET, UserTier.VET)
        resp = client.get("/vet-only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["role"] == "vet"

    def test_token_expirado_retorna_401(self) -> None:
        """Token expirado retorna 401."""
        expired_token = _jwt.create_access_token(
            user_id=uuid.uuid4(),
            role=UserRole.OWNER,
            tier=UserTier.FREE,
            expires_seconds=-1,
        )
        resp = client.get("/any-auth", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401

    def test_sin_token_retorna_401(self) -> None:
        """Sin Authorization header retorna 401."""
        resp = client.get("/any-auth")
        assert resp.status_code == 401

    def test_token_invalido_retorna_401(self) -> None:
        """Token malformado retorna 401."""
        resp = client.get("/any-auth", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401
