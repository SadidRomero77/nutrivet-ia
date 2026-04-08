"""
Integration tests — PostgreSQLPlanJobRepository con PostgreSQL real (testcontainers).

Cubre el ciclo de vida completo del job y los campos de progreso agregados en C1.
Si Docker no está disponible, los tests se saltan automáticamente.
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from backend.domain.value_objects.plan_job import PlanJob, PlanJobStatus
from backend.infrastructure.db.plan_job_repository import PostgreSQLPlanJobRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job(pet_id: uuid.UUID | None = None, owner_id: uuid.UUID | None = None) -> PlanJob:
    return PlanJob(
        job_id=uuid.uuid4(),
        pet_id=pet_id or uuid.uuid4(),
        owner_id=owner_id or uuid.uuid4(),
        modality="natural",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_y_find_by_id(db_session):
    """Un job recién creado se puede recuperar por ID con todos sus campos."""
    repo = PostgreSQLPlanJobRepository(db_session)
    job = _make_job()

    await repo.save(job)

    found = await repo.find_by_id(job.job_id)
    assert found is not None
    assert found.job_id == job.job_id
    assert found.status == PlanJobStatus.QUEUED
    assert found.progress_step == 0
    assert found.progress_message == ""
    assert found.plan_id is None


@pytest.mark.asyncio
async def test_find_by_id_inexistente_retorna_none(db_session):
    """Buscar un ID que no existe retorna None sin lanzar excepción."""
    repo = PostgreSQLPlanJobRepository(db_session)
    result = await repo.find_by_id(uuid.uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_ciclo_queued_processing_ready(db_session):
    """QUEUED → PROCESSING → READY con plan_id persistido correctamente."""
    repo = PostgreSQLPlanJobRepository(db_session)
    job = _make_job()
    await repo.save(job)

    # Transición a PROCESSING
    job.mark_processing()
    await repo.update(job)
    found = await repo.find_by_id(job.job_id)
    assert found.status == PlanJobStatus.PROCESSING

    # Transición a READY
    plan_id = uuid.uuid4()
    job.mark_ready(plan_id=plan_id)
    await repo.update(job)
    found = await repo.find_by_id(job.job_id)
    assert found.status == PlanJobStatus.READY
    assert found.plan_id == plan_id


@pytest.mark.asyncio
async def test_ciclo_processing_failed(db_session):
    """PROCESSING → FAILED con mensaje de error persistido."""
    repo = PostgreSQLPlanJobRepository(db_session)
    job = _make_job()
    await repo.save(job)

    job.mark_processing()
    await repo.update(job)

    job.mark_failed(error_message="LLM timeout")
    await repo.update(job)

    found = await repo.find_by_id(job.job_id)
    assert found.status == PlanJobStatus.FAILED
    assert found.error_message == "LLM timeout"


@pytest.mark.asyncio
async def test_update_progress_persiste_step_y_message(db_session):
    """
    update_progress actualiza progress_step y progress_message en DB.

    Este test verifica el flujo de feedback progresivo (C1):
    el endpoint de polling debe ver el paso actual del worker en tiempo real.
    """
    repo = PostgreSQLPlanJobRepository(db_session)
    job = _make_job()
    await repo.save(job)

    job.mark_processing()
    await repo.update(job)

    # Simula los pasos del worker
    pasos = [
        (1, "Cargando perfil de la mascota..."),
        (2, "Calculando requerimientos calóricos (NRC)..."),
        (6, "Generando plan nutricional con IA..."),
        (10, "Guardando plan en base de datos..."),
    ]
    for step, message in pasos:
        job.update_progress(step=step, message=message)
        await repo.update(job)

        found = await repo.find_by_id(job.job_id)
        assert found.progress_step == step, f"esperado step={step}, obtenido={found.progress_step}"
        assert found.progress_message == message


@pytest.mark.asyncio
async def test_progress_no_cambia_status(db_session):
    """update_progress no altera el status del job."""
    repo = PostgreSQLPlanJobRepository(db_session)
    job = _make_job()
    await repo.save(job)

    job.mark_processing()
    await repo.update(job)

    job.update_progress(step=5, message="Seleccionando modelo de IA...")
    await repo.update(job)

    found = await repo.find_by_id(job.job_id)
    assert found.status == PlanJobStatus.PROCESSING  # sin cambio
    assert found.progress_step == 5


@pytest.mark.asyncio
async def test_mark_ready_preserva_progress_fields(db_session):
    """Al hacer mark_ready, los campos de progreso del último update se preservan en DB."""
    repo = PostgreSQLPlanJobRepository(db_session)
    job = _make_job()
    await repo.save(job)

    job.mark_processing()
    job.update_progress(step=10, message="Guardando plan en base de datos...")
    await repo.update(job)

    plan_id = uuid.uuid4()
    job.mark_ready(plan_id=plan_id)
    await repo.update(job)

    found = await repo.find_by_id(job.job_id)
    assert found.status == PlanJobStatus.READY
    assert found.plan_id == plan_id
    assert found.progress_step == 10
