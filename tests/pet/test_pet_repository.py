"""Tests de integración — PetRepository + WeightRepository + ClaimCodeRepository con DB real."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.domain.aggregates.pet_profile import (
    CurrentDiet, DogActivityLevel, MedicalCondition,
    PetProfile, ReproductiveStatus, Sex, Size, Species,
)
from backend.domain.value_objects.bcs import BCS
from backend.infrastructure.db.base import Base
from backend.infrastructure.db.models import ClaimCodeModel, PetModel, WeightRecordModel  # noqa: F401
from backend.infrastructure.db.claim_code_repository import PostgreSQLClaimCodeRepository
from backend.infrastructure.db.pet_repository import PostgreSQLPetRepository
from backend.infrastructure.db.weight_repository import PostgreSQLWeightRepository

_TEST_DB_URL = os.environ.get(
    "DATABASE_URL_ASYNC",
    "postgresql+asyncpg://nutrivet:nutrivet_dev_pass@localhost:5432/nutrivet_dev",
)

# Clave Fernet de test
os.environ.setdefault(
    "FERNET_KEY",
    "ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=",
)


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(_TEST_DB_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()
    await engine.dispose()


def _make_pet(owner_id: uuid.UUID | None = None) -> PetProfile:
    return PetProfile(
        pet_id=uuid.uuid4(),
        owner_id=owner_id or uuid.uuid4(),
        name="Firulais",
        species=Species.PERRO,
        breed="Labrador",
        sex=Sex.MACHO,
        age_months=24,
        weight_kg=28.0,
        size=Size.GRANDE,
        reproductive_status=ReproductiveStatus.ESTERILIZADO,
        activity_level=DogActivityLevel.MODERADO,
        bcs=BCS(5),
        medical_conditions=[MedicalCondition.GASTRITIS],
        allergies=["pollo", "trigo"],
        current_diet=CurrentDiet.CONCENTRADO,
    )


class TestPetRepository:

    @pytest.mark.asyncio
    async def test_save_y_find_by_id(self, db_session: AsyncSession) -> None:
        """Guardar mascota y recuperarla — campos médicos desencriptados."""
        # Necesitamos un user válido en DB para el FK
        from backend.infrastructure.db.models import UserModel
        user = UserModel(
            id=uuid.uuid4(), email=f"u{uuid.uuid4()}@t.com",
            password_hash="h", role="owner", tier="free",
            subscription_status="active", is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        repo = PostgreSQLPetRepository(db_session)
        pet = _make_pet(owner_id=user.id)
        await repo.save(pet)
        await db_session.flush()

        found = await repo.find_by_id(pet.pet_id)
        assert found is not None
        assert found.name == "Firulais"
        assert MedicalCondition.GASTRITIS in found.medical_conditions
        assert "pollo" in found.allergies

    @pytest.mark.asyncio
    async def test_campos_medicos_encriptados_en_db(self, db_session: AsyncSession) -> None:
        """Verificar que medical_conditions está como BYTEA en DB (no texto plano)."""
        from backend.infrastructure.db.models import UserModel
        user = UserModel(
            id=uuid.uuid4(), email=f"u{uuid.uuid4()}@t.com",
            password_hash="h", role="owner", tier="free",
            subscription_status="active", is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        repo = PostgreSQLPetRepository(db_session)
        pet = _make_pet(owner_id=user.id)
        await repo.save(pet)
        await db_session.flush()

        raw = await db_session.get(PetModel, pet.pet_id)
        assert isinstance(raw.medical_conditions_enc, (bytes, memoryview))
        assert b"gastritis" not in raw.medical_conditions_enc

    @pytest.mark.asyncio
    async def test_count_by_owner(self, db_session: AsyncSession) -> None:
        """count_by_owner retorna el número correcto de mascotas."""
        from backend.infrastructure.db.models import UserModel
        user = UserModel(
            id=uuid.uuid4(), email=f"u{uuid.uuid4()}@t.com",
            password_hash="h", role="owner", tier="free",
            subscription_status="active", is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        repo = PostgreSQLPetRepository(db_session)
        assert await repo.count_by_owner(user.id) == 0

        await repo.save(_make_pet(owner_id=user.id))
        await db_session.flush()
        assert await repo.count_by_owner(user.id) == 1


class TestWeightRepository:

    @pytest.mark.asyncio
    async def test_append_y_list(self, db_session: AsyncSession) -> None:
        """Agregar registros de peso y listarlos."""
        from backend.infrastructure.db.models import UserModel
        user = UserModel(
            id=uuid.uuid4(), email=f"u{uuid.uuid4()}@t.com",
            password_hash="h", role="owner", tier="free",
            subscription_status="active", is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        pet_repo = PostgreSQLPetRepository(db_session)
        pet = _make_pet(owner_id=user.id)
        await pet_repo.save(pet)
        await db_session.flush()

        weight_repo = PostgreSQLWeightRepository(db_session)
        await weight_repo.append(
            pet_id=pet.pet_id, weight_kg=28.0, bcs=BCS(5),
            recorded_by=user.id, recorded_at=datetime.now(timezone.utc),
        )
        await db_session.flush()

        records = await weight_repo.list_by_pet(pet.pet_id)
        assert len(records) == 1
        assert records[0]["weight_kg"] == 28.0


class TestClaimCodeRepository:

    @pytest.mark.asyncio
    async def test_save_find_y_mark_used(self, db_session: AsyncSession) -> None:
        """Guardar claim code, encontrarlo y marcarlo como usado."""
        from backend.infrastructure.db.models import UserModel
        user = UserModel(
            id=uuid.uuid4(), email=f"u{uuid.uuid4()}@t.com",
            password_hash="h", role="vet", tier="vet",
            subscription_status="active", is_active=True,
        )
        db_session.add(user)
        await db_session.flush()

        pet_repo = PostgreSQLPetRepository(db_session)
        pet = _make_pet(owner_id=user.id)
        await pet_repo.save(pet)
        await db_session.flush()

        claim_repo = PostgreSQLClaimCodeRepository(db_session)
        expires = datetime.now(timezone.utc) + timedelta(days=30)
        await claim_repo.save(pet_id=pet.pet_id, code="ABCD1234", expires_at=expires)
        await db_session.flush()

        found = await claim_repo.find_by_code("ABCD1234")
        assert found is not None
        assert found["used"] is False

        await claim_repo.mark_used("ABCD1234")
        await db_session.flush()

        found2 = await claim_repo.find_by_code("ABCD1234")
        assert found2["used"] is True
