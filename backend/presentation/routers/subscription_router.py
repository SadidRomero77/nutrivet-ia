"""
Router de suscripciones — checkout PayU y webhook de confirmación.

POST /v1/subscriptions/checkout   — crea sesión de pago PayU (owner)
POST /v1/webhooks/payu            — webhook confirmación de pago (sin auth — PayU firma)
GET  /v1/subscriptions/status     — estado de suscripción del usuario autenticado
"""
from __future__ import annotations

import hashlib
import logging
import os
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.aggregates.user_account import UserTier
from backend.infrastructure.auth.jwt_service import TokenPayload
from backend.infrastructure.db.models import PaymentModel, UserModel
from backend.infrastructure.db.session import AsyncSessionLocal, get_db_session
from backend.infrastructure.payments.payu_client import (
    TIER_PRICES_COP,
    PayUConfig,
    create_payment_link,
)
from backend.infrastructure.push.fcm_client import PushNotification, send_push_to_tokens
from backend.infrastructure.db.device_token_repository import PostgreSQLDeviceTokenRepository
from backend.presentation.middleware.auth_middleware import get_current_user, require_role

logger = logging.getLogger(__name__)

router = APIRouter(tags=["subscriptions"])

# Map state_pol PayU → estado interno
_PAYU_STATE_MAP: dict[str, str] = {
    "4": "approved",
    "6": "declined",
    "104": "error",
}

# Map tier → UserTier enum
_TIER_TO_ENUM: dict[str, UserTier] = {
    "basico": UserTier.BASICO,
    "premium": UserTier.PREMIUM,
    "vet": UserTier.VET,
}


class CheckoutRequest(BaseModel):
    """Request para iniciar un checkout de suscripción."""
    tier: str = Field(..., description="basico | premium | vet")


class CheckoutResponse(BaseModel):
    """Respuesta con la URL de pago PayU."""
    redirect_url: str
    reference_code: str
    amount_cop: float
    tier: str


class SubscriptionStatusResponse(BaseModel):
    """Estado de suscripción del usuario."""
    tier: str
    tier_label: str


_TIER_LABELS: dict[str, str] = {
    "free": "Plan Free",
    "basico": "Plan Básico — $29.900 COP/mes",
    "premium": "Plan Premium — $59.900 COP/mes",
    "vet": "Plan Vet — $89.000 COP/mes",
}


@router.post("/v1/subscriptions/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> CheckoutResponse:
    """
    Crea una sesión de pago PayU para upgrade de suscripción.

    El owner es redirigido a la página de pago de PayU.
    Una vez completado el pago, PayU notifica via webhook → el tier se actualiza.
    """
    tier = body.tier.lower()
    if tier not in TIER_PRICES_COP:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Tier inválido: '{tier}'. Válidos: basico, premium, vet",
        )

    # Obtener email del usuario para PayU
    result = await session.execute(
        select(UserModel.email).where(UserModel.id == user.user_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    user_email: str = row[0]

    amount = TIER_PRICES_COP[tier]

    # Crear registro de pago en DB (estado pending)
    payment_id = uuid.uuid4()
    reference_code = str(payment_id)
    payment = PaymentModel(
        id=payment_id,
        user_id=user.user_id,
        reference_code=reference_code,
        tier=tier,
        amount_cop=amount,
        currency="COP",
        status="pending",
    )
    session.add(payment)
    await session.commit()

    # Crear link de pago en PayU
    result_checkout = await create_payment_link(
        tier=tier,
        user_id=user.user_id,
        user_email=user_email,
        payment_record_id=payment_id,
    )

    if result_checkout is None:
        # PayU no configurado.
        # La auto-aprobación solo se activa si PAYU_DEV_AUTO_APPROVE=true (explícito).
        # En producción o staging sin esta variable, el checkout falla con error claro.
        dev_auto_approve = os.getenv("PAYU_DEV_AUTO_APPROVE", "false").lower() == "true"
        if not dev_auto_approve:
            logger.error(
                "PayU no configurado y PAYU_DEV_AUTO_APPROVE no está activo. "
                "Define PAYU_MERCHANT_ID, PAYU_API_KEY y PAYU_API_LOGIN, "
                "o usa PAYU_DEV_AUTO_APPROVE=true solo en entornos de desarrollo.",
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El servicio de pagos no está disponible en este momento.",
            )
        logger.warning(
            "PAYU_DEV_AUTO_APPROVE=true — simulando aprobación para tier=%s user=%s",
            tier, user.user_id,
        )
        await _approve_payment(reference_code=reference_code)
        return CheckoutResponse(
            redirect_url="",
            reference_code=reference_code,
            amount_cop=amount,
            tier=tier,
        )

    return CheckoutResponse(
        redirect_url=result_checkout.redirect_url,
        reference_code=reference_code,
        amount_cop=amount,
        tier=tier,
    )


@router.post("/v1/webhooks/payu", status_code=status.HTTP_200_OK)
async def payu_webhook(request: Request) -> dict:
    """
    Webhook de confirmación de pago de PayU.

    PayU envía un POST con form-data cuando el estado de un pago cambia.
    Verificamos la firma antes de procesar.
    Sin autenticación JWT — la seguridad viene de la firma PayU.
    """
    try:
        form: dict[str, Any] = dict(await request.form())
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload inválido",
        )

    reference_sale: str = form.get("reference_sale", "")
    state_pol: str = str(form.get("state_pol", ""))
    value: str = str(form.get("value", ""))
    currency: str = form.get("currency", "COP")
    sign: str = form.get("sign", "")
    merchant_id: str = form.get("merchant_id", "")
    transaction_id: str = form.get("transaction_id", "")
    order_id: str = form.get("order_id", "")

    # Verificar firma PayU
    config = PayUConfig.from_env()
    if config.is_configured:
        expected_sign = hashlib.md5(
            f"{config.api_key}~{merchant_id}~{reference_sale}~{value}~{currency}~{state_pol}".encode()
        ).hexdigest()
        if expected_sign != sign:
            logger.warning(
                "PayU webhook firma inválida. reference=%s merchant=%s",
                reference_sale, merchant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firma inválida",
            )

    internal_status = _PAYU_STATE_MAP.get(state_pol, "error")
    logger.info(
        "PayU webhook: reference=%s state=%s status=%s txId=%s",
        reference_sale, state_pol, internal_status, transaction_id,
    )

    # Actualizar registro en DB y upgradear tier si aprobado
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PaymentModel).where(
                PaymentModel.reference_code == reference_sale
            )
        )
        payment = result.scalar_one_or_none()
        if payment is None:
            logger.error("PayU webhook: payment no encontrado reference=%s", reference_sale)
            return {"status": "not_found"}

        # Actualizar estado del pago (append-only via UPDATE de status solamente)
        await session.execute(
            update(PaymentModel)
            .where(PaymentModel.id == payment.id)
            .values(
                status=internal_status,
                payu_transaction_id=transaction_id or None,
                payu_order_id=order_id or None,
                raw_webhook=form,
            )
        )

        if internal_status == "approved" and payment.user_id:
            await _approve_payment_in_session(
                session=session,
                user_id=payment.user_id,
                tier=payment.tier,
            )

        await session.commit()

    return {"status": "ok"}


async def _approve_payment(reference_code: str) -> None:
    """Aprueba un pago internamente (modo dev sin PayU configurado)."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PaymentModel).where(
                PaymentModel.reference_code == reference_code
            )
        )
        payment = result.scalar_one_or_none()
        if payment and payment.user_id:
            await session.execute(
                update(PaymentModel)
                .where(PaymentModel.id == payment.id)
                .values(status="approved")
            )
            await _approve_payment_in_session(
                session=session,
                user_id=payment.user_id,
                tier=payment.tier,
            )
            await session.commit()


async def _approve_payment_in_session(
    session: AsyncSession,
    user_id: uuid.UUID,
    tier: str,
) -> None:
    """
    Actualiza el tier del usuario y envía push notification de confirmación.

    Args:
        session: Sesión de DB activa.
        user_id: ID del usuario.
        tier: Tier a asignar ("basico" | "premium" | "vet").
    """
    tier_enum = _TIER_TO_ENUM.get(tier)
    if tier_enum is None:
        logger.error("Tier inválido en _approve_payment: %s", tier)
        return

    await session.execute(
        update(UserModel)
        .where(UserModel.id == user_id)
        .values(tier=tier_enum.value, subscription_status="active")
    )

    logger.info("Tier y subscription_status actualizados: user=%s → %s", user_id, tier)

    # Push notification: confirmar upgrade al usuario
    try:
        token_repo = PostgreSQLDeviceTokenRepository(session)
        tokens = await token_repo.get_tokens_for_user(user_id)
        if tokens:
            await send_push_to_tokens(
                tokens=tokens,
                notification=PushNotification(
                    title="¡Suscripción activada!",
                    body=f"Tu plan {tier.capitalize()} está activo. Disfruta todas las funciones.",
                    data={"event": "subscription_activated", "tier": tier},
                ),
            )
    except Exception as e:
        logger.error("Error enviando push de suscripción: %s", e)


@router.get("/v1/subscriptions/history", response_model=list[dict], summary="Historial de pagos del usuario")
async def get_payment_history(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(require_role("owner")),
) -> list[dict]:
    """Retorna los pagos del usuario autenticado ordenados por fecha descendente."""
    result = await session.execute(
        select(PaymentModel)
        .where(PaymentModel.user_id == user.user_id)
        .order_by(PaymentModel.created_at.desc())
        .limit(20)
    )
    return [
        {
            "payment_id": str(row.id),
            "tier": row.tier,
            "amount_cop": float(row.amount_cop),
            "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in result.scalars()
    ]


@router.get("/v1/subscriptions/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    session: AsyncSession = Depends(get_db_session),
    user: TokenPayload = Depends(get_current_user),
) -> SubscriptionStatusResponse:
    """Retorna el tier de suscripción actual del usuario autenticado."""
    result = await session.execute(
        select(UserModel.tier).where(UserModel.id == user.user_id)
    )
    row = result.first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")

    tier = row[0]
    return SubscriptionStatusResponse(
        tier=tier,
        tier_label=_TIER_LABELS.get(tier, tier),
    )
