"""
AgentRouter — POST /v1/agent/process.

Endpoint principal del orquestador LangGraph.
Recibe mensaje del usuario, invoca el grafo y retorna la respuesta del agente.

Singleton ORCHESTRATOR compilado una vez y reutilizado entre requests.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
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
from backend.infrastructure.agent.subgraphs.consultation_stub import consultation_stub
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
from backend.infrastructure.agent.subgraphs.scanner_stub import scanner_stub
from backend.infrastructure.db.agent_trace_repository import PostgreSQLAgentTraceRepository
from backend.infrastructure.db.pet_repository import PostgreSQLPetRepository
from backend.infrastructure.db.plan_repository import PostgreSQLPlanRepository
from backend.infrastructure.db.session import get_db_session
from backend.presentation.middleware.auth_middleware import get_current_user
from backend.presentation.schemas.agent_schemas import AgentRequest, AgentResponse
from backend.presentation.schemas.scan_schemas import ScanResult

logger = logging.getLogger(__name__)
router = APIRouter(tags=["agent"])


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


@router.post(
    "/v1/agent/process",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesa mensaje del usuario con el orquestador LangGraph",
)
async def process_message(
    request: AgentRequest,
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
        pet_id=request.pet_id,
        user_tier=current_user.tier.value.upper(),
        user_role=current_user.role.value,
        message=request.message,
        modality=request.modality or "natural",
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
        consultation_fn=consultation_stub,
        scanner_fn=scanner_stub,
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
async def scan_label(
    pet_id: str,
    image: UploadFile = File(...),
    current_user=Depends(get_current_user),
) -> ScanResult:
    """
    Escanea una etiqueta nutricional con gpt-4o (vision).

    Solo acepta imagen de tabla nutricional o lista de ingredientes.
    NUNCA logos, marcas o empaques frontales (Constitution REGLA 7).
    """
    image_bytes = await image.read()
    mime_type = image.content_type or "image/jpeg"

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
async def chat(
    request: AgentRequest,
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
        pet_id=request.pet_id or "",
        user_tier=current_user.tier.value.upper(),
        user_role=current_user.role.value,
        message=request.message,
        modality=request.modality or "natural",
        agent_traces=[],
        conversation_history=[],
        medical_restrictions=[],
        allergy_list=[],
        requires_vet_review=False,
    )

    # Cargar historial previo si hay pet_id
    if request.pet_id:
        try:
            history = await conversation_repo.list_by_pet(request.pet_id, limit=10)
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
