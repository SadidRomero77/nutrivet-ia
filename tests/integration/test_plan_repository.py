"""
Integration tests — PostgreSQLPlanRepository con PostgreSQL real (testcontainers).

Cubre persistencia y recuperación de NutritionPlan con estructura clínica completa.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.aggregates.nutrition_plan import (
    NutritionPlan, PlanModality, PlanStatus, PlanType,
)
from backend.domain.value_objects.bcs import BCSPhase
from backend.infrastructure.db.models import PetModel, UserModel
from backend.infrastructure.db.plan_repository import PostgreSQLPlanRepository


# ---------------------------------------------------------------------------
# Helpers de inserción de datos mínimos requeridos por FK
# ---------------------------------------------------------------------------

async def _insert_user(session: AsyncSession, user_id: uuid.UUID) -> None:
    """Inserta un usuario mínimo para satisfacer FK de pets.owner_id."""
    row = UserModel(
        id=user_id,
        email=f"test_{user_id.hex[:8]}@integration.test",
        password_hash="x",
        role="owner",
        tier="free",
        subscription_status="active",
        is_active=True,
    )
    session.add(row)
    await session.flush()


async def _insert_pet(
    session: AsyncSession,
    pet_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> None:
    """Inserta una mascota mínima para satisfacer FK de nutrition_plans.pet_id."""
    row = PetModel(
        id=pet_id,
        owner_id=owner_id,
        name="TestPet",
        species="perro",
        breed="Labrador",
        sex="macho",
        age_months=24,
        weight_kg=10.0,
        size="mediano",
        reproductive_status="esterilizado",
        activity_level="moderado",
        bcs=5,
        current_diet="concentrado",
        is_clinic_pet=False,
        is_active=True,
    )
    session.add(row)
    await session.flush()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAMPLE_CONTENT = {
    "perfil_nutricional": {
        "proteina_pct_ms": 25.0,
        "grasa_pct_ms": 12.0,
        "racion_total_g_dia": 350.0,
        "relacion_ca_p": 1.2,
        "omega3_mg_dia": 500.0,
    },
    "objetivos_clinicos": ["Control de peso", "Mantenimiento muscular"],
    "ingredientes": [
        {"nombre": "Pollo cocido", "cantidad_g": 150.0, "kcal": 225.0},
        {"nombre": "Arroz blanco", "cantidad_g": 100.0, "kcal": 130.0},
    ],
    "suplementos": [
        {
            "nombre": "Omega-3",
            "dosis": "500mg",
            "frecuencia": "diaria",
            "forma": "cápsula",
            "justificacion": "Control inflamatorio",
        }
    ],
    "instrucciones_preparacion": {
        "metodo": "cocción",
        "pasos": ["Cocer el pollo sin sal", "Mezclar con arroz"],
        "tiempo_preparacion_minutos": 20,
    },
    "disclaimer": (
        "NutriVet.IA es asesoría nutricional digital — "
        "no reemplaza el diagnóstico médico veterinario."
    ),
}


def _make_plan(
    owner_id: uuid.UUID,
    pet_id: uuid.UUID,
    status: PlanStatus = PlanStatus.ACTIVE,
) -> NutritionPlan:
    """Construye un NutritionPlan. owner_id y pet_id deben existir en DB antes de guardar."""
    return NutritionPlan(
        plan_id=uuid.uuid4(),
        pet_id=pet_id,
        owner_id=owner_id,
        plan_type=PlanType.ESTANDAR,
        status=status,
        modality=PlanModality.NATURAL,
        rer_kcal=396.0,
        der_kcal=534.0,
        weight_phase=BCSPhase.MANTENIMIENTO,
        llm_model_used="anthropic/claude-sonnet-4-5",
        content=_SAMPLE_CONTENT,
        approved_by_vet_id=None,
        approval_timestamp=None,
        review_date=None,
        vet_comment=None,
        agent_trace_id=uuid.uuid4(),  # NOT NULL en DB — UUID de test (no referencia real)
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_y_find_by_id(db_session):
    """Un plan guardado se puede recuperar con todos sus campos."""
    owner_id, pet_id = uuid.uuid4(), uuid.uuid4()
    await _insert_user(db_session, owner_id)
    await _insert_pet(db_session, pet_id, owner_id)

    repo = PostgreSQLPlanRepository(db_session)
    plan = _make_plan(owner_id=owner_id, pet_id=pet_id)
    await repo.save(plan)

    found = await repo.find_by_id(plan.plan_id)
    assert found is not None
    assert found.plan_id == plan.plan_id
    assert found.status == PlanStatus.ACTIVE
    assert found.rer_kcal == pytest.approx(396.0, abs=0.01)
    assert found.der_kcal == pytest.approx(534.0, abs=0.01)
    assert found.modality == PlanModality.NATURAL


@pytest.mark.asyncio
async def test_find_by_id_inexistente_retorna_none(db_session):
    """ID inexistente retorna None sin excepción."""
    repo = PostgreSQLPlanRepository(db_session)
    assert await repo.find_by_id(uuid.uuid4()) is None


@pytest.mark.asyncio
async def test_content_jsonb_persiste_estructura_clinica(db_session):
    """
    El campo content (JSONB) preserva la estructura clínica completa.

    Este test protege contra regresiones en la serialización del JSON del LLM.
    """
    owner_id, pet_id = uuid.uuid4(), uuid.uuid4()
    await _insert_user(db_session, owner_id)
    await _insert_pet(db_session, pet_id, owner_id)

    repo = PostgreSQLPlanRepository(db_session)
    plan = _make_plan(owner_id=owner_id, pet_id=pet_id)
    await repo.save(plan)

    found = await repo.find_by_id(plan.plan_id)
    content = found.content

    assert content["objetivos_clinicos"] == ["Control de peso", "Mantenimiento muscular"]
    assert len(content["ingredientes"]) == 2
    assert content["ingredientes"][0]["nombre"] == "Pollo cocido"
    assert content["perfil_nutricional"]["proteina_pct_ms"] == pytest.approx(25.0)
    assert len(content["suplementos"]) == 1
    assert content["suplementos"][0]["nombre"] == "Omega-3"


@pytest.mark.asyncio
async def test_list_by_owner_filtra_por_owner(db_session):
    """list_by_owner devuelve solo los planes del owner solicitado."""
    owner_a, pet_a1, pet_a2 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    owner_b, pet_b = uuid.uuid4(), uuid.uuid4()

    await _insert_user(db_session, owner_a)
    await _insert_user(db_session, owner_b)
    await _insert_pet(db_session, pet_a1, owner_a)
    await _insert_pet(db_session, pet_a2, owner_a)
    await _insert_pet(db_session, pet_b, owner_b)

    repo = PostgreSQLPlanRepository(db_session)
    plan_a1 = _make_plan(owner_id=owner_a, pet_id=pet_a1)
    plan_a2 = _make_plan(owner_id=owner_a, pet_id=pet_a2)
    plan_b = _make_plan(owner_id=owner_b, pet_id=pet_b)

    for p in (plan_a1, plan_a2, plan_b):
        await repo.save(p)

    planes_a = await repo.list_by_owner(owner_a)
    assert len(planes_a) == 2
    ids_a = {p.plan_id for p in planes_a}
    assert plan_a1.plan_id in ids_a
    assert plan_a2.plan_id in ids_a
    assert plan_b.plan_id not in ids_a


@pytest.mark.asyncio
async def test_plan_pending_vet_persiste_status(db_session):
    """
    Un plan PENDING_VET (mascota con condición médica) persiste su status correctamente.

    Verifica la Constitution REGLA 4: mascotas con condición médica → PENDING_VET.
    """
    owner_id, pet_id = uuid.uuid4(), uuid.uuid4()
    await _insert_user(db_session, owner_id)
    await _insert_pet(db_session, pet_id, owner_id)

    repo = PostgreSQLPlanRepository(db_session)
    plan = _make_plan(owner_id=owner_id, pet_id=pet_id, status=PlanStatus.PENDING_VET)
    plan.plan_type = PlanType.TEMPORAL_MEDICAL
    await repo.save(plan)

    found = await repo.find_by_id(plan.plan_id)
    assert found.status == PlanStatus.PENDING_VET
    assert found.plan_type == PlanType.TEMPORAL_MEDICAL


@pytest.mark.asyncio
async def test_sally_golden_case_rer_der(db_session):
    """
    G8 — Caso Sally: RER=396.0, DER=534.0 kcal persisten con precisión ±0.01.

    Protege contra pérdida de precisión floating-point en la capa de persistencia.
    """
    owner_id, pet_id = uuid.uuid4(), uuid.uuid4()
    await _insert_user(db_session, owner_id)
    await _insert_pet(db_session, pet_id, owner_id)

    repo = PostgreSQLPlanRepository(db_session)
    plan = _make_plan(owner_id=owner_id, pet_id=pet_id)
    plan.rer_kcal = 396.0
    plan.der_kcal = 534.0
    await repo.save(plan)

    found = await repo.find_by_id(plan.plan_id)
    assert found.rer_kcal == pytest.approx(396.0, abs=0.01)
    assert found.der_kcal == pytest.approx(534.0, abs=0.01)
