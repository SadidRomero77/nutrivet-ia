"""
Router de autenticación — FastAPI.
Endpoints: /v1/auth/register, /v1/auth/login, /v1/auth/refresh, /v1/auth/logout, /v1/auth/me.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from backend.application.use_cases.auth_use_case import (
    AuthUseCase,
    TokenResponse as UseCaseTokenResponse,
)
from backend.domain.exceptions.domain_errors import DomainError
from backend.infrastructure.auth.jwt_service import JWTService, TokenPayload
from backend.infrastructure.auth.password_service import PasswordService
from backend.infrastructure.db.session import get_db_session
from backend.infrastructure.db.token_repository import PostgreSQLTokenRepository
from backend.infrastructure.db.user_repository import PostgreSQLUserRepository
from backend.infrastructure.db.models import NutritionPlanModel, PetModel
from backend.presentation.middleware.auth_middleware import get_current_user, get_jwt_service
from backend.presentation.schemas.auth_schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TierUsageResponse,
    TokenResponse,
    UpdateProfileRequest,
    UserProfileResponse,
    UserStatsResponse,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

# Rate limiter — instancia compartida (misma que app.state.limiter)
from backend.presentation.rate_limiter import limiter as _limiter


def _build_use_case(
    session: AsyncSession,
    jwt_service: JWTService,
) -> AuthUseCase:
    """Construye el AuthUseCase con sus dependencias de infraestructura."""
    return AuthUseCase(
        user_repo=PostgreSQLUserRepository(session),
        token_repo=PostgreSQLTokenRepository(session),
        jwt_service=jwt_service,
        password_service=PasswordService(),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
)
@_limiter.limit("20/minute")  # Límite generoso para testing — ajustar a 5/minute en producción
async def register(
    request: Request,
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    """
    Registra un nuevo usuario (owner o vet) y retorna tokens JWT.

    - **email**: Correo electrónico único.
    - **password**: Mínimo 8 caracteres, una mayúscula y un número.
    - **role**: `owner` (propietario de mascota) o `vet` (veterinario).
    """
    logger.info("Intento de registro desde IP: %s", request.client.host if request.client else "unknown")
    try:
        uc = _build_use_case(session, jwt_service)
        from backend.domain.aggregates.user_account import UserRole as _UserRole
        # El schema ya validó que role es 'owner' o 'vet' (normalizado a minúsculas).
        # Cualquier valor distinto fue rechazado con 422 antes de llegar aquí.
        role_str = (body.role or "owner").lower()
        requested_role = _UserRole.VET if role_str == "vet" else _UserRole.OWNER
        result: UseCaseTokenResponse = await uc.register(
            email=str(body.email),
            password=body.password,
            role=requested_role,
            full_name=body.full_name,
            phone=body.phone,
        )
    except DomainError as exc:
        # En este punto la contraseña ya fue validada por Pydantic (schema).
        # El único DomainError que puede llegar aquí es email duplicado.
        logger.info("Registro rechazado — email duplicado: %s", str(body.email))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado. Intenta con otro o inicia sesión.",
        ) from exc
    except IntegrityError:
        logger.warning("IntegrityError en registro — probable email duplicado por concurrencia")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado. Intenta con otro o inicia sesión.",
        )

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
)
@_limiter.limit("10/minute")  # Previene brute force de contraseñas
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    """
    Autentica un usuario y retorna tokens JWT.

    Mensaje de error genérico para evitar enumeración de usuarios.
    """
    try:
        uc = _build_use_case(session, jwt_service)
        result = await uc.login(email=str(body.email), password=body.password)
    except DomainError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas.",
        )

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotar refresh token",
)
@_limiter.limit("5/minute")  # Previene rotation attacks de refresh tokens
async def refresh(
    request: Request,
    body: RefreshRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenResponse:
    """
    Rota el refresh token y emite un nuevo par de tokens.

    El refresh token anterior queda invalidado inmediatamente.
    """
    try:
        uc = _build_use_case(session, jwt_service)
        result = await uc.refresh(refresh_token=body.refresh_token)
    except DomainError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada. Inicia sesión de nuevo.",
        )

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
)
@_limiter.limit("10/minute")  # Previene logout DoS masivo
async def logout(
    request: Request,
    body: LogoutRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> None:
    """
    Cierra sesión invalidando el refresh token en DB.

    Retorna 204 No Content en todos los casos (no revela si el token era válido).
    """
    uc = _build_use_case(session, jwt_service)
    await uc.logout(refresh_token=body.refresh_token)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Perfil del usuario autenticado",
)
async def get_me(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> UserProfileResponse:
    """Obtiene el perfil del usuario autenticado."""
    user_repo = PostgreSQLUserRepository(session)
    user_obj = await user_repo.find_by_id(user.user_id)
    if user_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return UserProfileResponse(
        user_id=user_obj.id,
        email=user_obj.email,
        role=user_obj.role.value,
        tier=user_obj.tier.value,
        full_name=user_obj.full_name,
        phone=user_obj.phone,
        clinic_name=user_obj.clinic_name,
        specialization=user_obj.specialization,
        license_number=user_obj.license_number,
        vet_status=user_obj.vet_status,
    )


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    summary="Actualizar perfil del usuario autenticado",
)
async def update_me(
    body: UpdateProfileRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> UserProfileResponse:
    """Actualiza nombre, teléfono y/o datos clínicos del usuario autenticado."""
    user_repo = PostgreSQLUserRepository(session)
    user_obj = await user_repo.find_by_id(user.user_id)
    if user_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    user_obj.update_profile(
        full_name=body.full_name,
        phone=body.phone,
        clinic_name=body.clinic_name,
        specialization=body.specialization,
        license_number=body.license_number,
    )
    await user_repo.save(user_obj)
    await session.commit()

    return UserProfileResponse(
        user_id=user_obj.id,
        email=user_obj.email,
        role=user_obj.role.value,
        tier=user_obj.tier.value,
        full_name=user_obj.full_name,
        phone=user_obj.phone,
        clinic_name=user_obj.clinic_name,
        specialization=user_obj.specialization,
        license_number=user_obj.license_number,
        vet_status=user_obj.vet_status,
    )


@router.patch(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cambiar contraseña del usuario autenticado",
)
@_limiter.limit("5/minute")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> None:
    """
    Cambia la contraseña del usuario autenticado.

    Requiere la contraseña actual para verificar identidad.
    """
    user_repo = PostgreSQLUserRepository(session)
    user_obj = await user_repo.find_by_id(user.user_id)
    if user_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    pw_service = PasswordService()
    if not pw_service.verify_password(body.current_password, user_obj.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual no es correcta.",
        )

    user_obj.password_hash = pw_service.hash_password(body.new_password)
    await user_repo.save(user_obj)
    await session.commit()


@router.get(
    "/me/stats",
    response_model=UserStatsResponse,
    summary="Estadísticas de actividad del usuario autenticado",
)
async def get_my_stats(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> UserStatsResponse:
    """
    Retorna conteos de actividad según el rol.

    - Owner: mascotas registradas y planes activos.
    - Vet: pacientes asignados y planes pendientes de revisión.
    """
    uid = user.user_id

    if user.role == "owner":
        pets_count_row = await session.execute(
            select(func.count()).select_from(PetModel).where(
                PetModel.owner_id == uid, PetModel.is_clinic_pet.is_(False)
            )
        )
        pets_count = pets_count_row.scalar() or 0

        active_plans_row = await session.execute(
            select(func.count()).select_from(NutritionPlanModel).join(
                PetModel, NutritionPlanModel.pet_id == PetModel.id
            ).where(
                PetModel.owner_id == uid,
                NutritionPlanModel.status == "ACTIVE",
            )
        )
        active_plans_count = active_plans_row.scalar() or 0

        return UserStatsResponse(
            pets_count=pets_count,
            active_plans_count=active_plans_count,
        )

    # Rol vet
    patients_count_row = await session.execute(
        select(func.count()).select_from(PetModel).where(PetModel.vet_id == uid)
    )
    patients_count = patients_count_row.scalar() or 0

    pending_plans_row = await session.execute(
        select(func.count()).select_from(NutritionPlanModel).join(
            PetModel, NutritionPlanModel.pet_id == PetModel.id
        ).where(
            PetModel.vet_id == uid,
            NutritionPlanModel.status == "PENDING_VET",
        )
    )
    pending_plans_count = pending_plans_row.scalar() or 0

    return UserStatsResponse(
        patients_count=patients_count,
        pending_plans_count=pending_plans_count,
    )


@router.get(
    "/vet/{vet_id}/profile",
    response_model=UserProfileResponse,
    summary="Perfil público de un veterinario",
)
async def get_vet_profile(
    vet_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> UserProfileResponse:
    """Obtiene el perfil público de un veterinario (nombre y contacto)."""
    user_repo = PostgreSQLUserRepository(session)
    vet = await user_repo.find_by_id(vet_id)
    if vet is None or vet.role.value != 'vet':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veterinario no encontrado.")
    return UserProfileResponse(
        user_id=vet.id,
        email=vet.email,
        role=vet.role.value,
        tier=vet.tier.value,
        full_name=vet.full_name,
        phone=vet.phone,
        clinic_name=vet.clinic_name,
        specialization=vet.specialization,
        license_number=vet.license_number,
        vet_status=vet.vet_status,
    )


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Solicitar recuperación de contraseña",
)
@_limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> dict:
    """
    Genera un token de reset de contraseña para el email indicado.

    Siempre responde con el mismo mensaje — no revela si el email existe (OWASP A01).
    En producción, el token se envía por email. En desarrollo se loggea.
    """
    user_repo = PostgreSQLUserRepository(session)
    user_obj = await user_repo.find_by_email(str(body.email).lower())

    if user_obj is not None:
        reset_token = jwt_service.create_reset_token(user_obj.id)
        # En producción: enviar por email. En desarrollo: loggear para testing.
        logger.info(
            "Password reset token for %s: %s",
            body.email,
            reset_token,
        )

    return {"message": "Si el email está registrado, recibirás las instrucciones de recuperación."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Restablecer contraseña con token",
)
@_limiter.limit("5/minute")
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    session: AsyncSession = Depends(get_db_session),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> None:
    """
    Restablece la contraseña del usuario usando el token de reset.

    El token es válido por 15 minutos y de un solo uso (TTL via JWT exp).
    """
    try:
        user_id = jwt_service.verify_reset_token(body.token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación es inválido o ha expirado.",
        )

    user_repo = PostgreSQLUserRepository(session)
    user_obj = await user_repo.find_by_id(user_id)
    if user_obj is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace de recuperación es inválido o ha expirado.",
        )

    pw_service = PasswordService()
    user_obj.password_hash = pw_service.hash_password(body.new_password)
    await user_repo.save(user_obj)
    await session.commit()
    logger.info("Password reset completado para user_id=%s", user_id)


@router.get(
    "/me/tier-usage",
    response_model=TierUsageResponse,
    summary="Cuota de uso del tier actual",
)
async def get_tier_usage(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> TierUsageResponse:
    """
    Retorna el uso de planes según el tier del usuario.

    Reglas:
    - Free: 1 plan total — no puede generar más.
    - Básico: 1 nuevo plan por mes.
    - Premium/Vet: ilimitados.
    """
    from backend.domain.aggregates.user_account import UserTier
    from backend.infrastructure.db.models import PetModel as _PetModel

    uid = user.user_id
    tier_value = user.tier.value

    # Contar planes totales del usuario
    total_plans_row = await session.execute(
        select(func.count()).select_from(NutritionPlanModel).join(
            PetModel, NutritionPlanModel.pet_id == PetModel.id
        ).where(
            PetModel.owner_id == uid,
        )
    )
    plans_total = total_plans_row.scalar() or 0

    # Determinar límites por tier
    if tier_value == "free":
        limit = 1
        remaining = max(0, limit - plans_total)
        can_generate = remaining > 0
    elif tier_value == "basico":
        # 1 plan nuevo por mes
        from datetime import datetime, timezone
        from sqlalchemy import and_
        start_of_month = datetime.now(timezone.utc).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        monthly_row = await session.execute(
            select(func.count()).select_from(NutritionPlanModel).join(
                PetModel, NutritionPlanModel.pet_id == PetModel.id
            ).where(
                and_(
                    PetModel.owner_id == uid,
                    NutritionPlanModel.created_at >= start_of_month,
                )
            )
        )
        plans_this_month = monthly_row.scalar() or 0
        limit = 1
        remaining = max(0, limit - plans_this_month)
        can_generate = remaining > 0
    else:
        # Premium / Vet — ilimitados
        limit = None
        remaining = None
        can_generate = True

    return TierUsageResponse(
        tier=tier_value,
        plans_total=plans_total,
        plans_limit=limit,
        plans_remaining=remaining,
        can_generate_plan=can_generate,
    )
