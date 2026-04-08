"""
AgentRouter — POST /v1/agent/process.

Endpoint principal del orquestador LangGraph.
Recibe mensaje del usuario, invoca el grafo y retorna la respuesta del agente.

Singleton ORCHESTRATOR compilado una vez y reutilizado entre requests.
"""
from __future__ import annotations

import json
import logging
import uuid as _uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import StreamingResponse


from backend.infrastructure.agent.nodes.intent_classifier import intent_classifier
from backend.infrastructure.agent.nodes.load_context import load_context
from backend.infrastructure.agent.orchestrator import (
    build_orchestrator,
    get_orchestrator,
    set_request_functions,
)
from backend.infrastructure.agent.state import NutriVetState
from backend.infrastructure.agent.subgraphs.consultation import (
    run_consultation_subgraph,
    run_consultation_subgraph_streaming,
)
from backend.infrastructure.db.agent_quota_repository import PostgreSQLAgentQuotaRepository
from backend.infrastructure.db.conversation_repository import PostgreSQLConversationRepository
from backend.infrastructure.agent.subgraphs.plan_generation import (
    nodo_1_verificar_contexto,
    nodo_2_calculate_nutrition,
    nodo_3_apply_restrictions,
    nodo_4_check_safety_pre,
    nodo_5_select_llm,
    nodo_6_generate_with_llm,
    nodo_7_validate_output,
    nodo_8_generate_substitutes,
    nodo_9_determine_hitl,
    nodo_10_persist_and_notify,
)
from backend.infrastructure.agent.subgraphs.scanner import run_scanner_subgraph
from backend.infrastructure.db.agent_trace_repository import PostgreSQLAgentTraceRepository
from backend.infrastructure.db.label_scan_repository import PostgreSQLLabelScanRepository
from backend.infrastructure.db.pet_repository import PostgreSQLPetRepository
from backend.infrastructure.db.plan_repository import PostgreSQLPlanRepository
from backend.infrastructure.db.session import get_db_session
from backend.presentation.middleware.auth_middleware import get_current_user
from backend.presentation.schemas.agent_schemas import AgentRequest, AgentResponse
from backend.presentation.schemas.scan_schemas import ScanResult

logger = logging.getLogger(__name__)
router = APIRouter(tags=["agent"])

# Rate limiter compartido — misma instancia que app.state.limiter
from backend.presentation.rate_limiter import limiter as _limiter

# Restricciones para upload de imágenes en /v1/agent/scan
_ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _build_plan_generation_fn(session):
    """Construye el pipeline completo del plan generation subgraph con dependencias inyectadas."""
    plan_repo = PostgreSQLPlanRepository(session)
    trace_repo = PostgreSQLAgentTraceRepository(session)

    async def plan_generation_pipeline(state: NutriVetState) -> NutriVetState:
        state = nodo_1_verificar_contexto(state)
        state = nodo_2_calculate_nutrition(state)
        state = nodo_3_apply_restrictions(state)
        state = nodo_4_check_safety_pre(state)
        state = nodo_5_select_llm(state)
        state = await nodo_6_generate_with_llm(state)
        state = nodo_7_validate_output(state)
        state = nodo_8_generate_substitutes(state)
        state = nodo_9_determine_hitl(state)
        state = await nodo_10_persist_and_notify(state, plan_repo=plan_repo, trace_repo=trace_repo)
        return state

    return plan_generation_pipeline


def _build_load_context_fn(session):
    """Construye load_context con repositorios inyectados."""
    pet_repo = PostgreSQLPetRepository(session)
    plan_repo = PostgreSQLPlanRepository(session)

    async def _load_context(state: NutriVetState) -> NutriVetState:
        return await load_context(state, pet_repo=pet_repo, plan_repo=plan_repo)

    return _load_context


def _build_consultation_fn(session):
    """Construye consultation subgraph con repositorios inyectados."""
    quota_repo = PostgreSQLAgentQuotaRepository(session)
    conversation_repo = PostgreSQLConversationRepository(session)

    async def _consultation(state: NutriVetState) -> NutriVetState:
        return await run_consultation_subgraph(
            state,
            quota_repo=quota_repo,
            conversation_repo=conversation_repo,
        )

    return _consultation


def _build_scanner_fn(session):
    """Construye scanner subgraph con LabelScanRepository inyectado."""
    label_scan_repo = PostgreSQLLabelScanRepository(session)

    async def _scanner(state: NutriVetState) -> NutriVetState:
        return await run_scanner_subgraph(state, label_scan_repo=label_scan_repo)

    return _scanner


@router.post(
    "/v1/agent/process",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesa mensaje del usuario con el orquestador LangGraph",
)
@_limiter.limit("10/minute")  # Protege contra abuso de LLM calls (costo directo)
async def process_message(
    request: Request,
    body: AgentRequest,
    current_user=Depends(get_current_user),
    session=Depends(get_db_session),
) -> AgentResponse:
    """
    Endpoint principal del agente NutriVet.IA.

    Recibe el mensaje del usuario, lo enruta al subgrafo correcto y retorna
    la respuesta del agente con disclaimer obligatorio (REGLA 8).
    """
    initial_state = NutriVetState(
        user_id=str(current_user.user_id),
        pet_id=body.pet_id,
        user_tier=current_user.tier.value.upper(),
        user_role=current_user.role.value,
        message=body.message,
        modality=body.modality or "natural",
        agent_traces=[],
        conversation_history=[],
        medical_restrictions=[],
        allergy_list=[],
        requires_vet_review=False,
    )

    load_context_fn = _build_load_context_fn(session)
    plan_generation_fn = _build_plan_generation_fn(session)

    # Singleton: el grafo se compiló una vez al inicio. Sólo configuramos
    # las funciones con dependencias DB para este request (aisladas por ContextVar).
    set_request_functions(
        load_context_fn=load_context_fn,
        intent_classifier_fn=intent_classifier,
        plan_generation_fn=plan_generation_fn,
        consultation_fn=_build_consultation_fn(session),
        scanner_fn=_build_scanner_fn(session),
    )
    orchestrator = get_orchestrator()

    try:
        result = await orchestrator.ainvoke(initial_state)
    except Exception as e:
        logger.exception("Error en orquestador LangGraph: %s", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando el mensaje. Por favor intenta de nuevo.",
        ) from e

    return AgentResponse.from_state(result)


@router.post(
    "/v1/agent/scan",
    response_model=ScanResult,
    status_code=status.HTTP_200_OK,
    summary="Escanea etiqueta nutricional — solo tabla nutricional o lista de ingredientes",
)
@_limiter.limit("5/minute")  # OCR con gpt-4o vision: más caro, límite más estricto
async def scan_label(
    request: Request,
    pet_id: str,
    image: UploadFile = File(...),
    current_user=Depends(get_current_user),
    session=Depends(get_db_session),
) -> ScanResult:
    """
    Escanea una etiqueta nutricional con gpt-4o (vision).

    Solo acepta imagen de tabla nutricional o lista de ingredientes.
    NUNCA logos, marcas o empaques frontales (Constitution REGLA 7).
    """
    import uuid as _uuid

    # Validar formato de pet_id
    try:
        pet_uuid = _uuid.UUID(pet_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="pet_id inválido.")

    # Validar que el usuario tiene acceso a esta mascota (Constitution REGLA 6)
    pet_repo = PostgreSQLPetRepository(session)
    pet = await pet_repo.find_by_id(pet_uuid)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mascota no encontrada.")

    is_owner = pet.owner_id == current_user.user_id
    is_assigned_vet = (
        current_user.role.value == "vet"
        and pet.vet_id is not None
        and pet.vet_id == current_user.user_id
    )
    if not (is_owner or is_assigned_vet):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")

    # Validar MIME type antes de leer bytes (content_type es user-controlled)
    mime_type = image.content_type or ""
    if mime_type not in _ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Formato no soportado. Usa JPEG, PNG, WebP o GIF.",
        )

    # Leer con límite de tamaño para prevenir DoS (OWASP A05 / LLM10)
    image_bytes = await image.read()
    if len(image_bytes) > _MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Imagen demasiado grande. Máximo 5 MB.",
        )

    initial_state = NutriVetState(
        user_id=str(current_user.user_id),
        pet_id=pet_id,
        user_tier=current_user.tier.value.upper(),
        user_role=current_user.role.value,
        message="analiza esta etiqueta",
        modality="concentrado",
        scan_image_bytes=image_bytes,
        scan_mime_type=mime_type,
        agent_traces=[],
        conversation_history=[],
        medical_restrictions=[],
        allergy_list=[],
        requires_vet_review=False,
    )

    try:
        result_state = await run_scanner_subgraph(initial_state)
    except Exception as e:
        logger.exception("Error en scanner subgraph: %s", type(e).__name__)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando la imagen. Por favor intenta de nuevo.",
        ) from e

    if result_state.get("error"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=result_state["error"],
        )

    return ScanResult(
        image_type=result_state.get("scan_semaphore") and "nutrition_table" or "unknown",
        semaphore=result_state.get("scan_semaphore", "VERDE"),
        ingredients_detected=result_state.get("scan_ingredients", []),
        issues=result_state.get("scan_issues", []),
        recomendacion=result_state.get("response", ""),
    )


@router.post(
    "/v1/agent/chat",
    status_code=status.HTTP_200_OK,
    summary="Chat conversacional nutricional — respuesta en streaming SSE",
)
@_limiter.limit("20/minute")  # Chat tiene freemium gate interno, límite menos estricto
async def chat(
    request: Request,
    body: AgentRequest,
    current_user=Depends(get_current_user),
    session=Depends(get_db_session),
) -> StreamingResponse:
    """
    Endpoint de chat conversacional nutricional.

    Respuesta en Server-Sent Events (SSE) — chunks de texto progresivos.
    Consultas médicas → referral determinístico (sin LLM).
    Emergencias → bypass de freemium gate.
    Free tier: 3 preguntas/día × 3 días = 9 total.

    Constitution REGLA 8: disclaimer en último chunk.
    Constitution REGLA 9: consultas médicas → remite al vet.
    """
    quota_repo = PostgreSQLAgentQuotaRepository(session)
    conversation_repo = PostgreSQLConversationRepository(session)

    initial_state = NutriVetState(
        user_id=str(current_user.user_id),
        pet_id=body.pet_id or "",
        user_tier=current_user.tier.value.upper(),
        user_role=current_user.role.value,
        message=body.message,
        modality=body.modality or "natural",
        agent_traces=[],
        conversation_history=[],
        medical_restrictions=[],
        allergy_list=[],
        requires_vet_review=False,
    )

    # Cargar contexto completo de la mascota (pet_profile + plan activo)
    # Constitution REGLA 9: el agente necesita el perfil para responder sin pedir datos ya conocidos.
    if body.pet_id:
        try:
            context_state = await load_context(
                initial_state,
                pet_repo=PostgreSQLPetRepository(session),
                plan_repo=PostgreSQLPlanRepository(session),
            )
            # Preservar solo si no hubo error de acceso
            if not context_state.get("error"):
                initial_state = context_state
        except Exception as ctx_err:
            logger.warning("No se pudo cargar contexto de mascota: %s", ctx_err)

    # Cargar historial previo si hay pet_id
    if body.pet_id:
        try:
            history = await conversation_repo.list_by_pet(body.pet_id, limit=20)
            initial_state = {**initial_state, "conversation_history": history}
        except Exception as hist_err:
            logger.warning("No se pudo cargar historial conversacional: %s", hist_err)

    async def _event_stream():
        """
        Genera el stream SSE con la respuesta del agente — streaming real chunk a chunk.

        Cada chunk del LLM se envía inmediatamente como evento SSE individual.
        El cliente Flutter puede mostrar el texto progresivamente.
        """
        try:
            gen = await run_consultation_subgraph_streaming(
                initial_state,
                quota_repo=quota_repo,
                conversation_repo=conversation_repo,
            )
            async for chunk in gen:
                if chunk:
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            logger.exception("Error en consultation subgraph: %s", type(exc).__name__)
            yield f"data: {json.dumps({'error': 'Error procesando tu consulta. Por favor intenta de nuevo.'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/v1/agent/conversations/{pet_id}",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Historial de conversaciones de una mascota para visualización",
)
async def get_conversation_history(
    pet_id: str,
    limit: int = Query(30, ge=1, le=100),
    current_user=Depends(get_current_user),
    session=Depends(get_db_session),
) -> list[dict[str, Any]]:
    """
    Retorna el historial de conversaciones de una mascota para mostrar en la UI.

    Cada elemento: {role: 'user'|'agent', content: str, created_at: str ISO8601}

    El cliente (Flutter) muestra estos mensajes al abrir la pantalla de chat
    para que el usuario vea el historial de la sesión anterior.

    RBAC: solo el owner de la mascota o el vet asignado puede acceder.
    """
    try:
        pet_uuid = _uuid.UUID(pet_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="pet_id inválido.")

    # Verificar ownership — Constitution REGLA 6 (aislamiento de datos)
    pet_repo = PostgreSQLPetRepository(session)
    pet = await pet_repo.find_by_id(pet_uuid)
    if pet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mascota no encontrada.")
    is_owner = pet.owner_id == current_user.user_id
    is_vet = (
        current_user.role.value == "vet"
        and pet.vet_id is not None
        and pet.vet_id == current_user.user_id
    )
    if not (is_owner or is_vet):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso denegado.")

    conversation_repo = PostgreSQLConversationRepository(session)
    return await conversation_repo.list_for_display(pet_id=pet_id, limit=limit)


@router.get(
    "/v1/agent/quota",
    status_code=status.HTTP_200_OK,
    summary="Cuota del agente conversacional del usuario actual",
)
async def get_agent_quota(
    current_user=Depends(get_current_user),
    session=Depends(get_db_session),
) -> dict[str, Any]:
    """
    Retorna el estado actual de la cuota del agente conversacional.

    Free tier: daily_limit=3, total_limit=9. Tiers pagados: sin límite (null).
    Usado por el cliente Flutter para mostrar el contador "2/3 hoy".
    """
    from backend.infrastructure.agent.nodes.freemium_gate import (
        DAILY_LIMIT, TOTAL_LIMIT, FREE_TIER,
    )

    quota_repo = PostgreSQLAgentQuotaRepository(session)
    tier_upper = current_user.tier.value.upper()
    is_free = tier_upper == FREE_TIER

    if is_free:
        quota = await quota_repo.get_or_create(str(current_user.user_id))
        daily_count = quota.daily_count
        total_count = quota.total_count
        can_ask = daily_count < DAILY_LIMIT and total_count < TOTAL_LIMIT
        return {
            "is_free_tier": True,
            "daily_count": daily_count,
            "daily_limit": DAILY_LIMIT,
            "total_count": total_count,
            "total_limit": TOTAL_LIMIT,
            "can_ask": can_ask,
        }

    # Tiers pagados: cuota ilimitada
    return {
        "is_free_tier": False,
        "daily_count": None,
        "daily_limit": None,
        "total_count": None,
        "total_limit": None,
        "can_ask": True,
    }
