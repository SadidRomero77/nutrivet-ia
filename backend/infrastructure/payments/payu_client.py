"""
PayU Colombia Client — integración de pagos para suscripciones NutriVet.IA.

Usa la API de pagos de PayU LATAM (Colombia).
Variables de entorno requeridas:
  PAYU_MERCHANT_ID   — ID de comercio asignado por PayU
  PAYU_API_KEY       — API key privada
  PAYU_API_LOGIN     — API login
  PAYU_ACCOUNT_ID    — ID de cuenta Colombia
  PAYU_ENV           — "sandbox" | "production" (default: sandbox)

Documentación: https://developers.payulatam.com/latam/es/docs/getting-started.html
"""
from __future__ import annotations

import hashlib
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Literal

import httpx

logger = logging.getLogger(__name__)

# URLs de la API
_API_URLS: dict[str, str] = {
    "sandbox": "https://sandbox.api.payulatam.com/payments-api/4.0/service.cgi",
    "production": "https://api.payulatam.com/payments-api/4.0/service.cgi",
}

# Precios en COP por tier
TIER_PRICES_COP: dict[str, float] = {
    "basico": 29_900.0,
    "premium": 59_900.0,
    "vet": 89_000.0,
}

TIER_DESCRIPTIONS: dict[str, str] = {
    "basico": "NutriVet.IA Básico — 1 mascota, planes ilimitados",
    "premium": "NutriVet.IA Premium — hasta 3 mascotas, planes ilimitados",
    "vet": "NutriVet.IA Vet — pacientes ilimitados + dashboard clínico",
}


@dataclass
class PayUConfig:
    """Configuración de PayU leída de variables de entorno."""
    merchant_id: str
    api_key: str
    api_login: str
    account_id: str
    env: Literal["sandbox", "production"]

    @classmethod
    def from_env(cls) -> "PayUConfig":
        """Carga configuración desde variables de entorno."""
        return cls(
            merchant_id=os.environ.get("PAYU_MERCHANT_ID", ""),
            api_key=os.environ.get("PAYU_API_KEY", ""),
            api_login=os.environ.get("PAYU_API_LOGIN", ""),
            account_id=os.environ.get("PAYU_ACCOUNT_ID", ""),
            env=os.environ.get("PAYU_ENV", "sandbox"),  # type: ignore
        )

    @property
    def is_configured(self) -> bool:
        """True si las credenciales están configuradas."""
        return bool(self.merchant_id and self.api_key and self.api_login)

    @property
    def api_url(self) -> str:
        return _API_URLS.get(self.env, _API_URLS["sandbox"])


@dataclass
class CheckoutResult:
    """Resultado de crear un pago en PayU."""
    reference_code: str
    redirect_url: str  # URL donde el usuario completa el pago
    order_id: str | None = None


def _generate_signature(
    api_key: str,
    merchant_id: str,
    reference_code: str,
    amount: float,
    currency: str,
) -> str:
    """
    Genera la firma MD5 requerida por PayU.

    Formato: MD5(apiKey~merchantId~referenceCode~amount~currency)
    """
    raw = f"{api_key}~{merchant_id}~{reference_code}~{amount:.2f}~{currency}"
    return hashlib.md5(raw.encode()).hexdigest()  # nosec B324 — PayU requiere MD5


def verify_webhook_signature(
    api_key: str,
    merchant_id: str,
    reference_sale: str,
    value: str,
    currency: str,
    state_pol: str,
    sign: str,
) -> bool:
    """
    Verifica la firma del webhook de PayU (confirmación de pago).

    PayU envía: MD5(apiKey~merchantId~reference_sale~value~currency~state_pol)
    Ver: https://developers.payulatam.com/latam/es/docs/getting-started/confirmacion-de-pagos.html

    Args:
        api_key: API key del comercio.
        merchant_id: ID del comercio.
        reference_sale: Código de referencia del pago.
        value: Monto formateado (e.g., "29900.00").
        currency: Moneda (e.g., "COP").
        state_pol: Estado del pago (4=aprobado, 6=declinado, 104=error).
        sign: Firma MD5 enviada por PayU en el campo `sign` del payload.

    Returns:
        True si la firma calculada coincide con la recibida de PayU.
    """
    raw = f"{api_key}~{merchant_id}~{reference_sale}~{value}~{currency}~{state_pol}"
    expected = hashlib.md5(raw.encode()).hexdigest()  # nosec B324 — PayU requiere MD5
    return expected == sign


async def create_payment_link(
    tier: str,
    user_id: uuid.UUID,
    user_email: str,
    payment_record_id: uuid.UUID,
) -> CheckoutResult | None:
    """
    Crea una sesión de pago en PayU para un tier de suscripción.

    Usa el flujo Web Checkout (Payment Link) de PayU — el usuario es
    redirigido al portal de PayU para completar el pago.

    Args:
        tier: "basico" | "premium" | "vet"
        user_id: ID del usuario (para el webhook).
        user_email: Email del comprador (requerido por PayU).
        payment_record_id: ID del registro en tabla payments (referencia interna).

    Returns:
        CheckoutResult con la URL de pago, o None si PayU no está configurado.
    """
    config = PayUConfig.from_env()
    if not config.is_configured:
        logger.warning(
            "PayU no configurado — checkout omitido para tier=%s user=%s",
            tier, user_id,
        )
        return None

    amount = TIER_PRICES_COP.get(tier)
    if amount is None:
        raise ValueError(f"Tier inválido: '{tier}'. Válidos: {list(TIER_PRICES_COP)}")

    reference_code = str(payment_record_id)  # UUID del payment record
    currency = "COP"
    signature = _generate_signature(
        api_key=config.api_key,
        merchant_id=config.merchant_id,
        reference_code=reference_code,
        amount=amount,
        currency=currency,
    )

    # URL base de la app — para redirect después del pago
    app_base_url = os.environ.get("APP_BASE_URL", "https://nutrivet.app")

    payload = {
        "language": "es",
        "command": "SUBMIT_TRANSACTION",
        "merchant": {
            "apiLogin": config.api_login,
            "apiKey": config.api_key,
        },
        "transaction": {
            "order": {
                "accountId": config.account_id,
                "referenceCode": reference_code,
                "description": TIER_DESCRIPTIONS.get(tier, f"NutriVet.IA {tier}"),
                "language": "es",
                "signature": signature,
                "notifyUrl": f"{app_base_url}/v1/webhooks/payu",
                "additionalValues": {
                    "TX_VALUE": {
                        "value": amount,
                        "currency": currency,
                    }
                },
                "buyer": {
                    "emailAddress": user_email,
                },
                "shippingAddress": None,
            },
            "payer": {
                "emailAddress": user_email,
            },
            "type": "AUTHORIZATION_AND_CAPTURE",
            "paymentMethod": "ALL",  # acepta todos los métodos disponibles
            "paymentCountry": "CO",
            "deviceSessionId": str(uuid.uuid4()),
            "ipAddress": "127.0.0.1",  # sobreescrito por el gateway
            "userAgent": "NutriVetIA/1.0",
        },
        "test": config.env == "sandbox",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                config.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        logger.error("PayU HTTP error: %s", e)
        return None

    tx_response = data.get("transactionResponse", {})
    redirect_url = tx_response.get("extraParameters", {}).get(
        "BANK_URL", tx_response.get("redirectUrl", "")
    )

    if not redirect_url:
        # Para algunos métodos (PSE, etc.) PayU devuelve URL en otro campo
        redirect_url = data.get("urlPaymentReceipt", "")

    if not redirect_url:
        logger.error("PayU no retornó URL de pago. Respuesta: %s", data)
        return None

    return CheckoutResult(
        reference_code=reference_code,
        redirect_url=redirect_url,
        order_id=str(tx_response.get("orderId", "")),
    )
