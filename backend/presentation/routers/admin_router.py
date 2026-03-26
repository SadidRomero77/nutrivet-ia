"""
Router de administración — solo accesible con rol admin.

Endpoints:
  GET  /v1/admin/stats                        — resumen global
  GET  /v1/admin/users                        — listar usuarios (filtros: role, tier, q)
  GET  /v1/admin/users/{user_id}              — detalle de usuario
  PATCH /v1/admin/users/{user_id}/tier        — cambiar tier
  PATCH /v1/admin/users/{user_id}/status      — activar/desactivar
  POST /v1/admin/users/create-vet             — crear cuenta vet
  GET  /v1/admin/vets/pending                 — vets pendientes de aprobación
  POST /v1/admin/vets/{user_id}/approve       — aprobar vet
  POST /v1/admin/vets/{user_id}/reject        — rechazar vet
  GET  /v1/admin/payments                     — historial de pagos
"""
from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.application.use_cases.auth_use_case import AuthUseCase
from backend.domain.aggregates.user_account import UserRole, UserTier
from backend.infrastructure.auth.jwt_service import TokenPayload
from backend.infrastructure.auth.password_service import PasswordService
from backend.infrastructure.db.models import NutritionPlanModel, PaymentModel, PetModel, UserModel
from backend.infrastructure.db.session import get_db_session
from backend.infrastructure.db.token_repository import PostgreSQLTokenRepository
from backend.infrastructure.db.user_repository import PostgreSQLUserRepository
from backend.presentation.middleware.auth_middleware import get_current_user, require_role
from backend.presentation.schemas.auth_schemas import (
    AdminChangeTierRequest,
    AdminCreateVetRequest,
    AdminOverviewStats,
    AdminRejectVetRequest,
    AdminUserResponse,
    PaymentHistoryItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin", tags=["admin"])

_VALID_TIERS = {"free", "basico", "premium", "vet"}


def _user_to_response(model: UserModel) -> AdminUserResponse:
    """Mapea UserModel → AdminUserResponse."""
    return AdminUserResponse(
        user_id=model.id,
        email=model.email,
        role=model.role,
        tier=model.tier,
        is_active=model.is_active,
        full_name=getattr(model, "full_name", None),
        phone=getattr(model, "phone", None),
        clinic_name=getattr(model, "clinic_name", None),
        specialization=getattr(model, "specialization", None),
        license_number=getattr(model, "license_number", None),
        vet_status=getattr(model, "vet_status", None),
        created_at=model.created_at.isoformat() if model.created_at else None,
    )


# ── Estadísticas globales ─────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminOverviewStats, summary="Resumen global del sistema")
async def get_overview_stats(
    session: AsyncSession = Depends(get_db_session),
    _: TokenPayload = Depends(require_role("admin")),
) -> AdminOverviewStats:
    """Retorna métricas globales: usuarios, suscripciones, ingresos."""
    total = (await session.execute(select(func.count()).select_from(UserModel))).scalar() or 0
    owners = (await session.execute(
        select(func.count()).select_from(UserModel).where(UserModel.role == "owner")
    )).scalar() or 0
    vets = (await session.execute(
        select(func.count()).select_from(UserModel).where(UserModel.role == "vet")
    )).scalar() or 0
    vets_pending = (await session.execute(
        select(func.count()).select_from(UserModel).where(
            UserModel.role == "vet", UserModel.vet_status == "pending"
        )
    )).scalar() or 0
    active_subs = (await session.execute(
        select(func.count()).select_from(UserModel).where(
            UserModel.tier.in_(["basico", "premium", "vet"]),
            UserModel.role != "admin",
        )
    )).scalar() or 0
    total_payments = (await session.execute(
        select(func.count()).select_from(PaymentModel).where(PaymentModel.status == "approved")
    )).scalar() or 0
    revenue_row = await session.execute(
        select(func.sum(PaymentModel.amount_cop)).where(PaymentModel.status == "approved")
    )
    revenue = float(revenue_row.scalar() or 0)

    return AdminOverviewStats(
        total_users=total,
        owners_count=owners,
        vets_count=vets,
        vets_pending=vets_pending,
        active_subscriptions=active_subs,
        total_payments=total_payments,
        total_revenue_cop=revenue,
    )


# ── Gestión de usuarios ───────────────────────────────────────────────────────

@router.get("/users", response_model=list[AdminUserResponse], summary="Listar usuarios")
async def list_users(
    role: Optional[str] = Query(None, description="Filtrar por rol: owner | vet | admin"),
    tier: Optional[str] = Query(None, description="Filtrar por tier: free | basico | premium | vet"),
    q: Optional[str] = Query(None, description="Buscar por email o nombre"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
    _: TokenPayload = Depends(require_role("admin")),
) -> list[AdminUserResponse]:
    """Lista todos los usuarios con filtros opcionales."""
    stmt = select(UserModel).order_by(UserModel.created_at.desc())

    if role:
        stmt = stmt.where(UserModel.role == role)
    if tier:
        stmt = stmt.where(UserModel.tier == tier)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            (UserModel.email.ilike(like)) |
            (UserModel.full_name.ilike(like))
        )

    stmt = stmt.limit(limit).offset(offset)
    result = await session.execute(stmt)
    return [_user_to_response(row) for row in result.scalars()]


@router.get("/users/{user_id}", response_model=AdminUserResponse, summary="Detalle de usuario")
async def get_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    _: TokenPayload = Depends(require_role("admin")),
) -> AdminUserResponse:
    """Retorna el perfil completo de un usuario."""
    model = await session.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return _user_to_response(model)


@router.patch("/users/{user_id}/tier", response_model=AdminUserResponse, summary="Cambiar tier")
async def change_user_tier(
    user_id: uuid.UUID,
    body: AdminChangeTierRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(require_role("admin")),
) -> AdminUserResponse:
    """Cambia el tier de suscripción de un usuario manualmente."""
    if body.tier not in _VALID_TIERS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tier inválido. Válidos: {', '.join(_VALID_TIERS)}",
        )
    model = await session.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    model.tier = body.tier
    await session.commit()
    await session.refresh(model)
    logger.info("Admin %s cambió tier de user %s → %s", admin.user_id, user_id, body.tier)
    return _user_to_response(model)


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse, summary="Activar/desactivar usuario")
async def toggle_user_status(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(require_role("admin")),
) -> AdminUserResponse:
    """Alterna el estado activo/inactivo de un usuario."""
    model = await session.get(UserModel, user_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    if str(model.id) == str(admin.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta.",
        )

    model.is_active = not model.is_active
    await session.commit()
    await session.refresh(model)
    logger.info(
        "Admin %s %s user %s",
        admin.user_id,
        "activó" if model.is_active else "desactivó",
        user_id,
    )
    return _user_to_response(model)


@router.post(
    "/users/create-vet",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cuenta de veterinario",
)
async def create_vet(
    body: AdminCreateVetRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(require_role("admin")),
) -> AdminUserResponse:
    """
    Crea una cuenta de veterinario verificada (vet_status=approved).

    Solo accesible por admin. El vet recibe credenciales para acceder a la app.
    """
    uc = AuthUseCase(
        user_repo=PostgreSQLUserRepository(session),
        token_repo=PostgreSQLTokenRepository(session),
        jwt_service=None,  # type: ignore[arg-type]  # no emitimos JWT aquí
        password_service=PasswordService(),
    )
    # Verificar que el email no esté en uso
    user_repo = PostgreSQLUserRepository(session)
    existing = await user_repo.find_by_email(str(body.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado.",
        )

    pw_service = PasswordService()
    from backend.domain.aggregates.user_account import UserAccount
    vet = UserAccount.create(
        email=str(body.email),
        password_hash=pw_service.hash(body.password),
        role=UserRole.VET,
        full_name=body.full_name,
        phone=body.phone,
    )
    vet.clinic_name = body.clinic_name
    vet.specialization = body.specialization
    vet.license_number = body.license_number
    vet.vet_status = "approved"  # creado por admin → aprobado directamente

    await user_repo.save(vet)
    await session.commit()

    model = await session.get(UserModel, vet.id)
    logger.info("Admin %s creó vet %s (%s)", admin.user_id, vet.id, body.email)
    return _user_to_response(model)  # type: ignore[arg-type]


# ── Aprobación de vets ────────────────────────────────────────────────────────

@router.get("/vets/pending", response_model=list[AdminUserResponse], summary="Vets pendientes de aprobación")
async def list_pending_vets(
    session: AsyncSession = Depends(get_db_session),
    _: TokenPayload = Depends(require_role("admin")),
) -> list[AdminUserResponse]:
    """Lista los veterinarios con vet_status=pending."""
    result = await session.execute(
        select(UserModel)
        .where(UserModel.role == "vet", UserModel.vet_status == "pending")
        .order_by(UserModel.created_at.asc())
    )
    return [_user_to_response(row) for row in result.scalars()]


@router.post("/vets/{user_id}/approve", response_model=AdminUserResponse, summary="Aprobar vet")
async def approve_vet(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(require_role("admin")),
) -> AdminUserResponse:
    """Aprueba un veterinario — puede firmar planes a partir de este momento."""
    model = await session.get(UserModel, user_id)
    if model is None or model.role != "vet":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinario no encontrado.")
    model.vet_status = "approved"
    await session.commit()
    await session.refresh(model)
    logger.info("Admin %s aprobó vet %s", admin.user_id, user_id)
    return _user_to_response(model)


@router.post("/vets/{user_id}/reject", response_model=AdminUserResponse, summary="Rechazar vet")
async def reject_vet(
    user_id: uuid.UUID,
    body: AdminRejectVetRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(require_role("admin")),
) -> AdminUserResponse:
    """Rechaza un veterinario — no puede firmar planes."""
    model = await session.get(UserModel, user_id)
    if model is None or model.role != "vet":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinario no encontrado.")
    model.vet_status = "rejected"
    await session.commit()
    await session.refresh(model)
    logger.info(
        "Admin %s rechazó vet %s. Comentario: %s",
        admin.user_id, user_id, body.comment or "(sin comentario)",
    )
    return _user_to_response(model)


# ── Pagos ─────────────────────────────────────────────────────────────────────

@router.get("/payments", response_model=list[PaymentHistoryItem], summary="Historial de pagos global")
async def list_payments(
    user_id: Optional[uuid.UUID] = Query(None, description="Filtrar por usuario"),
    payment_status: Optional[str] = Query(None, alias="status", description="pending | approved | declined"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
    _: TokenPayload = Depends(require_role("admin")),
) -> list[PaymentHistoryItem]:
    """Lista todos los pagos del sistema con filtros opcionales."""
    stmt = select(PaymentModel).order_by(PaymentModel.created_at.desc())
    if user_id:
        stmt = stmt.where(PaymentModel.user_id == user_id)
    if payment_status:
        stmt = stmt.where(PaymentModel.status == payment_status)
    stmt = stmt.limit(limit).offset(offset)

    result = await session.execute(stmt)
    return [
        PaymentHistoryItem(
            payment_id=row.id,
            tier=row.tier,
            amount_cop=float(row.amount_cop),
            status=row.status,
            created_at=row.created_at.isoformat() if row.created_at else None,
        )
        for row in result.scalars()
    ]
