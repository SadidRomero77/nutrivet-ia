"""Tests de endpoints de mascotas — FastAPI con DB real."""
from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.domain.aggregates.user_account import UserRole, UserTier
from backend.infrastructure.auth.jwt_service import JWTService
from backend.infrastructure.db.base import Base
from backend.infrastructure.db.models import (  # noqa: F401
    ClaimCodeModel, PetModel, RefreshTokenModel, UserModel, WeightRecordModel,
)
from backend.infrastructure.db.session import get_db_session
from backend.presentation.middleware.auth_middleware import get_jwt_service
from backend.presentation.routers.pet_router import router

_TEST_DB_URL = os.environ.get(
    "DATABASE_URL_ASYNC",
    "postgresql+asyncpg://nutrivet:nutrivet_dev_pass@localhost:5432/nutrivet_dev",
)
_TEST_SECRET = "test-pet-router-secret"

os.environ.setdefault("FERNET_KEY", "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=")

_jwt = JWTService(secret_key=_TEST_SECRET, algorithm="HS256")


def _owner_token(tier: UserTier = UserTier.FREE) -> str:
    return _jwt.create_access_token(user_id=uuid.uuid4(), role=UserRole.OWNER, tier=tier)


def _vet_token(tier: UserTier = UserTier.VET) -> str:
    return _jwt.create_access_token(user_id=uuid.uuid4(), role=UserRole.VET, tier=tier)


def build_test_app(session_factory) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    async def _override_session():
        async with session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_jwt_service] = lambda: _jwt
    return app


@pytest_asyncio.fixture
async def async_client():
    engine = create_async_engine(_TEST_DB_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sf = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    app = build_test_app(sf)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Crear user en DB para el owner token (FK de pets)
        async with sf() as s:
            async with s.begin():
                user_id = uuid.uuid4()
                s.add(UserModel(
                    id=user_id, email=f"owner-{user_id}@test.com",
                    password_hash="h", role="owner", tier="free",
                    subscription_status="active", is_active=True,
                ))
        yield client, user_id
    await engine.dispose()


_DOG_BODY = {
    "name": "Rex",
    "species": "perro",
    "breed": "Labrador",
    "sex": "macho",
    "age_months": 24,
    "weight_kg": 28.0,
    "size": "grande",
    "reproductive_status": "esterilizado",
    "activity_level": "moderado",
    "bcs": 5,
    "medical_conditions": [],
    "allergies": [],
    "current_diet": "concentrado",
}


class TestPetEndpoints:

    @pytest.mark.asyncio
    async def test_crear_mascota_201(self, async_client) -> None:
        client, user_id = async_client
        token = _jwt.create_access_token(user_id=user_id, role=UserRole.OWNER, tier=UserTier.FREE)
        resp = await client.post("/v1/pets", json=_DOG_BODY, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 201
        assert resp.json()["name"] == "Rex"

    @pytest.mark.asyncio
    async def test_listar_mascotas(self, async_client) -> None:
        client, user_id = async_client
        token = _jwt.create_access_token(user_id=user_id, role=UserRole.OWNER, tier=UserTier.FREE)
        await client.post("/v1/pets", json=_DOG_BODY, headers={"Authorization": f"Bearer {token}"})
        resp = await client.get("/v1/pets", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_obtener_mascota(self, async_client) -> None:
        client, user_id = async_client
        token = _jwt.create_access_token(user_id=user_id, role=UserRole.OWNER, tier=UserTier.FREE)
        create_resp = await client.post("/v1/pets", json=_DOG_BODY, headers={"Authorization": f"Bearer {token}"})
        pet_id = create_resp.json()["pet_id"]
        resp = await client.get(f"/v1/pets/{pet_id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_free_tier_segunda_mascota_403(self, async_client) -> None:
        client, user_id = async_client
        token = _jwt.create_access_token(user_id=user_id, role=UserRole.OWNER, tier=UserTier.FREE)
        await client.post("/v1/pets", json=_DOG_BODY, headers={"Authorization": f"Bearer {token}"})
        resp = await client.post("/v1/pets", json={**_DOG_BODY, "name": "Max"}, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_agregar_peso_201(self, async_client) -> None:
        client, user_id = async_client
        token = _jwt.create_access_token(user_id=user_id, role=UserRole.OWNER, tier=UserTier.FREE)
        create_resp = await client.post("/v1/pets", json=_DOG_BODY, headers={"Authorization": f"Bearer {token}"})
        pet_id = create_resp.json()["pet_id"]
        resp = await client.post(
            f"/v1/pets/{pet_id}/weight",
            json={"weight_kg": 29.0, "bcs": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_sin_token_401(self, async_client) -> None:
        client, _ = async_client
        resp = await client.get("/v1/pets")
        assert resp.status_code == 401
