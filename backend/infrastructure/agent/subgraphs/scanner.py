"""
ScannerSubgraph — Reemplaza el stub de unit-05.

5 nodos:
  1. image_validator   → clasifica imagen (gpt-4o vision)
  2. upload_to_r2      → sube a Cloudflare R2 antes del OCR
  3. ocr_with_gpt4o    → extrae ingredientes y valores nutricionales
  4. evaluate_nutrition → semáforo determinístico (sin LLM)
  5. persist_scan      → guarda en label_scans + agent_trace

Constitution REGLA 7: solo tabla nutricional o lista de ingredientes.
ADR-019: gpt-4o siempre para OCR.
"""
from __future__ import annotations

import asyncio
import base64
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from backend.application.interfaces.label_scan_repository import ILabelScanRepository
from backend.infrastructure.agent.nodes.image_validator import (
    IMAGE_TYPE_REJECTED,
    classify_image_type,
)
from backend.infrastructure.agent.nodes.nutritional_evaluator import (
    evaluate_semaphore,
)
from backend.infrastructure.agent.state import NutriVetState
from backend.infrastructure.llm.openrouter_client import OpenRouterClient

_OCR_MODEL = "openai/gpt-4o"
_DISCLAIMER = (
    "NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario."
)

_OCR_SYSTEM_PROMPT = """Eres un extractor de información nutricional para etiquetas de alimentos de mascotas.
Analiza la imagen y extrae:
1. Lista de ingredientes (si hay)
2. Valores nutricionales (proteínas, grasas, fibra, humedad, cenizas, etc.)

Responde SOLO con JSON válido:
{
  "image_type": "nutrition_table" | "ingredient_list",
  "ingredients": ["ingrediente1", "ingrediente2", ...],
  "nutritional_profile": {
    "proteinas": 25.0,
    "grasas": 10.0,
    ...
  }
}

NO incluyas nombre de marca ni información del fabricante."""


# ── Funciones inyectables (para testing con mocks) ────────────────────────────

async def _classify_image(
    image_bytes: bytes,
    mime_type: str,
    llm_client: OpenRouterClient | None = None,
) -> str:
    """Wrapper inyectable para classify_image_type."""
    return await classify_image_type(
        image_bytes=image_bytes,
        mime_type=mime_type,
        llm_client=llm_client,
    )


async def _upload_to_r2(
    image_bytes: bytes,
    mime_type: str,
    scan_id: str,
) -> str:
    """
    Sube imagen a Cloudflare R2 y retorna URL pre-signed (TTL 1h).

    Usa R2StorageClient con las credenciales estándar del proyecto
    (R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME).
    En dev sin R2 configurado → retorna URL placeholder para que el pipeline continúe.
    """
    from backend.infrastructure.storage.r2_client import R2StorageClient

    ext = mime_type.split("/")[-1]
    object_key = f"scans/{scan_id}.{ext}"

    try:
        storage = R2StorageClient.from_env()
        # upload() y generate_presigned_url() son sync (boto3) — correr en thread
        await asyncio.to_thread(storage.upload, object_key, image_bytes, mime_type)
        return await asyncio.to_thread(storage.generate_presigned_url, object_key)
    except Exception:
        # Sin R2 configurado (dev/test) → placeholder; el pipeline continúa
        return f"r2://scans/{scan_id}"


async def _run_ocr(
    model: str,
    image_url: str,
    image_bytes: bytes,
    mime_type: str,
    llm_client: OpenRouterClient | None = None,
) -> str:
    """Ejecuta OCR con gpt-4o (vision). Siempre gpt-4o — ADR-019."""
    client = llm_client or OpenRouterClient()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    user_prompt = f"data:{mime_type};base64,{image_base64}"

    response = await client.generate(
        model=model,
        system_prompt=_OCR_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.0,
    )
    return response.content


async def _persist_scan(
    pet_id: str,
    user_id: str,
    image_url: str,
    image_type: str,
    semaphore: str,
    ingredients: list[str],
    issues: list[str],
    recomendacion: str,
    scan_id: uuid.UUID,
    label_scan_repo: ILabelScanRepository | None,
) -> str:
    """
    Persiste el resultado del escaneo en label_scans.

    Si label_scan_repo es None (tests sin DB), loggea y retorna scan_id sin persistir.
    """
    import logging
    _logger = logging.getLogger(__name__)

    if label_scan_repo is None:
        _logger.debug("label_scan_repo no disponible — skip persist scan %s", scan_id)
        return str(scan_id)

    try:
        await label_scan_repo.save(
            scan_id=scan_id,
            pet_id=uuid.UUID(pet_id) if pet_id else uuid.uuid4(),
            user_id=uuid.UUID(user_id) if user_id else uuid.uuid4(),
            image_url=image_url,
            image_type=image_type,
            semaphore=semaphore,
            ingredients=ingredients,
            issues=issues,
            recomendacion=recomendacion,
            created_at=datetime.now(timezone.utc),
        )
    except Exception:
        _logger.exception("Error al persistir scan %s — resultado retornado igual", scan_id)

    return str(scan_id)


# ── Pipeline principal ────────────────────────────────────────────────────────

async def run_scanner_subgraph(
    state: NutriVetState,
    llm_client: OpenRouterClient | None = None,
    label_scan_repo: ILabelScanRepository | None = None,
) -> NutriVetState:
    """
    Ejecuta el pipeline completo del scanner.

    Nodo 1: Clasifica imagen
    Nodo 2: Sube a R2
    Nodo 3: OCR con gpt-4o
    Nodo 4: Evalúa semáforo
    Nodo 5: Persiste resultado
    """
    image_bytes: bytes = state.get("scan_image_bytes", b"")
    mime_type: str = state.get("scan_mime_type", "image/jpeg")
    pet = state.get("pet_profile") or {}
    scan_uuid = uuid.uuid4()
    scan_id = str(scan_uuid)

    # ── Validación de tamaño de imagen (pre-clasificación) ────────────────────
    _MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB
    if len(image_bytes) > _MAX_IMAGE_BYTES:
        size_mb = len(image_bytes) / (1024 * 1024)
        error_msg = (
            f"❌ La imagen es demasiado grande ({size_mb:.1f} MB). "
            "El tamaño máximo permitido es 10 MB. "
            "Por favor, comprime la imagen antes de enviarla."
        )
        return {**state, "error": error_msg, "response": error_msg, "scan_semaphore": None}

    if not image_bytes:
        error_msg = "❌ No se recibió imagen. Por favor, selecciona una foto de la etiqueta nutricional."
        return {**state, "error": error_msg, "response": error_msg, "scan_semaphore": None}

    # ── Nodo 1: Clasificar imagen (REGLA 7) ───────────────────────────────────
    try:
        image_type = await _classify_image(image_bytes, mime_type, llm_client)
    except Exception:
        import logging as _logging
        _logging.getLogger(__name__).exception("Error al clasificar imagen — asumiendo rejected")
        error_msg = (
            "❌ No se pudo analizar la imagen en este momento. "
            "Por favor, inténtalo de nuevo en unos segundos."
        )
        return {**state, "error": error_msg, "response": error_msg, "scan_semaphore": None}

    if image_type == IMAGE_TYPE_REJECTED:
        error_msg = (
            "❌ Solo se acepta imagen de la tabla nutricional o la lista de ingredientes. "
            "Por favor, fotografía únicamente esa sección de la etiqueta — "
            "no el empaque frontal, logo o marca del producto."
        )
        return {
            **state,
            "error": error_msg,
            "response": error_msg,
            "scan_semaphore": None,
        }

    # ── Nodo 2: Upload a R2 ───────────────────────────────────────────────────
    image_url = await _upload_to_r2(
        image_bytes=image_bytes,
        mime_type=mime_type,
        scan_id=scan_id,
    )

    # ── Nodo 3: OCR con gpt-4o ────────────────────────────────────────────────
    ocr_raw = await _run_ocr(
        model=_OCR_MODEL,
        image_url=image_url,
        image_bytes=image_bytes,
        mime_type=mime_type,
        llm_client=llm_client,
    )

    try:
        ocr_data: dict[str, Any] = json.loads(ocr_raw)
    except json.JSONDecodeError:
        ocr_data = {"ingredients": [], "nutritional_profile": {}}

    ingredients: list[str] = ocr_data.get("ingredients", [])
    nutritional_profile: dict[str, Any] = ocr_data.get("nutritional_profile", {})

    # ── Nodo 4: Semáforo determinístico ───────────────────────────────────────
    semaphore_result = evaluate_semaphore(
        ingredients=ingredients,
        nutritional_profile=nutritional_profile,
        pet_profile=pet,
    )

    # ── Nodo 5: Persistir ─────────────────────────────────────────────────────
    await _persist_scan(
        pet_id=pet.get("pet_id", ""),
        user_id=state.get("user_id", ""),
        image_url=image_url,
        image_type=image_type,
        semaphore=semaphore_result.color,
        ingredients=ingredients,
        issues=semaphore_result.issues,
        recomendacion=semaphore_result.recomendacion,
        scan_id=scan_uuid,
        label_scan_repo=label_scan_repo,
    )

    response = (
        f"🔍 **Resultado del escaneo**\n\n"
        f"**Semáforo**: {semaphore_result.color}\n\n"
        f"**Ingredientes detectados**: {', '.join(ingredients) if ingredients else 'ninguno'}\n\n"
    )
    if semaphore_result.issues:
        response += "**Problemas detectados**:\n" + "\n".join(f"• {i}" for i in semaphore_result.issues) + "\n\n"

    response += f"**Recomendación**: {semaphore_result.recomendacion}"

    traces = list(state.get("agent_traces", []))
    traces.append({
        "event": "scanner_ocr",
        "llm_model": _OCR_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "semaphore": semaphore_result.color,
        "ingredients_count": len(ingredients),
    })

    return {
        **state,
        "scan_semaphore": semaphore_result.color,
        "scan_ingredients": ingredients,
        "scan_issues": semaphore_result.issues,
        "response": response,
        "agent_traces": traces,
    }


# Alias para compatibilidad con el orquestador (reemplaza el stub)
async def scanner_subgraph(state: NutriVetState) -> NutriVetState:
    """Entry point para el orquestador LangGraph."""
    return await run_scanner_subgraph(state)
