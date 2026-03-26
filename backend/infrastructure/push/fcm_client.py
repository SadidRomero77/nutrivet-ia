"""
FCM Client — envío de push notifications vía Firebase Cloud Messaging HTTP v1.

Usa Service Account JSON (FCM_SERVICE_ACCOUNT_JSON env var).
Si la variable no está configurada, el envío se omite silenciosamente (modo dev).

Documentación FCM HTTP v1:
https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages/send
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Base URL de FCM HTTP v1 — FCM_PROJECT_ID se lee de la service account
_FCM_BASE_URL = "https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

# Scopes OAuth2 requeridos por FCM HTTP v1
_FCM_SCOPES = ["https://www.googleapis.com/auth/firebase.messaging"]


@dataclass
class PushNotification:
    """Payload de una notificación push."""
    title: str
    body: str
    data: dict[str, str] | None = None  # datos extras para la app


async def _get_access_token() -> tuple[str, str] | None:
    """
    Obtiene un access token OAuth2 para FCM usando la Service Account.

    Returns:
        Tupla (access_token, project_id) o None si no hay configuración.
    """
    raw = os.environ.get("FCM_SERVICE_ACCOUNT_JSON", "")
    if not raw:
        return None

    try:
        sa = json.loads(raw)
        project_id: str = sa["project_id"]
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("FCM_SERVICE_ACCOUNT_JSON inválido: %s", e)
        return None

    try:
        # Importamos google-auth solo si está disponible
        import google.auth.transport.requests  # type: ignore
        import google.oauth2.service_account  # type: ignore

        credentials = google.oauth2.service_account.Credentials.from_service_account_info(
            sa, scopes=_FCM_SCOPES
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token, project_id
    except ImportError:
        logger.warning(
            "google-auth no instalado — push notifications deshabilitadas. "
            "Instalar: pip install google-auth"
        )
        return None
    except Exception as e:
        logger.error("Error obteniendo token FCM: %s", e)
        return None


async def send_push_to_tokens(
    tokens: list[str],
    notification: PushNotification,
) -> int:
    """
    Envía una notificación push a una lista de device tokens FCM.

    Args:
        tokens: Lista de FCM device tokens.
        notification: Contenido de la notificación.

    Returns:
        Cantidad de tokens que recibieron la notificación exitosamente.
    """
    if not tokens:
        return 0

    auth = await _get_access_token()
    if auth is None:
        logger.debug(
            "FCM no configurado — push omitida: '%s'", notification.title
        )
        return 0

    access_token, project_id = auth
    url = _FCM_BASE_URL.format(project_id=project_id)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    success_count = 0
    async with httpx.AsyncClient(timeout=10.0) as client:
        for token in tokens:
            payload: dict[str, Any] = {
                "message": {
                    "token": token,
                    "notification": {
                        "title": notification.title,
                        "body": notification.body,
                    },
                }
            }
            if notification.data:
                payload["message"]["data"] = notification.data

            try:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    success_count += 1
                else:
                    logger.warning(
                        "FCM push fallida para token ...%s: %s — %s",
                        token[-8:], resp.status_code, resp.text[:200],
                    )
            except httpx.HTTPError as e:
                logger.error("FCM error de red para token ...%s: %s", token[-8:], e)

    logger.info(
        "FCM push '%s' enviada: %d/%d tokens exitosos",
        notification.title, success_count, len(tokens),
    )
    return success_count
