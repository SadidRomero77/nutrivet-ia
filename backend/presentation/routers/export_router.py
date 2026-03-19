"""
ExportRouter — POST /v1/plans/{plan_id}/export.

Exporta un plan nutricional a PDF y retorna URL pre-signed (TTL 1 hora).

Solo planes en estado ACTIVE son exportables.
RBAC: owner de la mascota o veterinario asignado al plan.
"""
from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from backend.application.use_cases.export_plan_use_case import (
    ExportForbiddenError,
    ExportNotAllowedError,
    ExportPlanUseCase,
    PlanNotFoundError,
)
from backend.infrastructure.db.plan_repository import PostgreSQLPlanRepository
from backend.infrastructure.db.session import get_db_session
from backend.infrastructure.pdf.pdf_generator import PDFGenerator
from backend.infrastructure.storage.r2_client import R2StorageClient
from backend.presentation.middleware.auth_middleware import get_current_user
from backend.presentation.schemas.export_schemas import ExportResponse

router = APIRouter(tags=["export"])


def _build_export_use_case(session) -> ExportPlanUseCase:
    """Construye el ExportPlanUseCase con dependencias reales."""
    plan_repo = PostgreSQLPlanRepository(session)
    pdf_generator = PDFGenerator()

    # R2 desde env vars — si no están configuradas (dev) → usa placeholder
    account_id = os.getenv("R2_ACCOUNT_ID", "")
    access_key = os.getenv("R2_ACCESS_KEY_ID", "")
    secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "")
    bucket = os.getenv("R2_BUCKET_NAME", "nutrivet-plans")

    storage_client = R2StorageClient(
        account_id=account_id,
        access_key_id=access_key,
        secret_access_key=secret_key,
        bucket_name=bucket,
    )

    return ExportPlanUseCase(
        plan_repo=plan_repo,
        pdf_generator=pdf_generator,
        storage_client=storage_client,
    )


@router.post(
    "/v1/plans/{plan_id}/export",
    response_model=ExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Exporta plan nutricional a PDF con URL pre-signed (TTL 1h)",
)
async def export_plan(
    plan_id: uuid.UUID,
    current_user=Depends(get_current_user),
    session=Depends(get_db_session),
) -> ExportResponse:
    """
    Exporta un plan nutricional a PDF.

    Solo planes en estado **ACTIVE** son exportables.
    Retorna URL pre-signed para descarga directa (TTL exactamente 1 hora).

    Cache: mismo plan → mismo PDF en R2 (no re-genera si ya existe).

    **RBAC:** dueño de la mascota o veterinario asignado al plan.

    Constitution REGLA 8: disclaimer en todas las páginas del PDF.
    """
    use_case = _build_export_use_case(session)

    try:
        result = await use_case.export(
            plan_id=plan_id,
            user_id=current_user.user_id,
        )
    except PlanNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ExportNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except ExportForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    return ExportResponse(url=result.url, expires_at=result.expires_at)
