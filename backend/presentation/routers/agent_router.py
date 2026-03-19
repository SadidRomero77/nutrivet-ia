"""
AgentRouter — POST /v1/agent/process.

Endpoint principal del orquestador LangGraph.
Recibe mensaje del usuario, invoca el grafo y retorna la respuesta del agente.

Singleton ORCHESTRATOR compilado una vez y reutilizado entre requests.
"""
from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, status

from backend.infrastructure.agent.nodes.intent_classifier import intent_classifier
from backend.infrastructure.agent.nodes.load_context import load_context
from backend.infrastructure.agent.orchestrator import build_orchestrator
from backend.infrastructure.agent.state import NutriVetState
from backend.infrastructure.agent.subgraphs.consultation_stub import consultation_stub
from backend.infrastructure.agent.subgraphs.plan_generation import (
    nodo_6_generate_with_llm,
    nodo_7_validate_output,
    nodo_8_generate_substitutes,
    nodo_9_determine_hitl,
    nodo_2_calculate_nutrition,
    nodo_3_apply_restrictions,
    nodo_4_check_safety_pre,
    nodo_5_select_llm,
    nodo_1_verificar_contexto,
    nodo_10_persist_and_notify,
)
from backend.infrastructure.agent.subgraphs.scanner_stub import scanner_stub
from backend.infrastructure.db.session import get_db_session
from backend.infrastructure.db.pet_repository import PostgreSQLPetRepository
from backend.infrastructure.db.plan_repository import PostgreSQLPlanRepository
from backend.infrastructure.db.agent_trace_repository import PostgreSQLAgentTraceRepository
from backend.presentation.middleware.auth_middleware import get_current_user
from backend.presentation.schemas.agent_schemas import AgentRequest, AgentResponse

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

    orchestrator = build_orchestrator(
        load_context_fn=load_context_fn,
        intent_classifier_fn=intent_classifier,
        plan_generation_fn=plan_generation_fn,
        consultation_fn=consultation_stub,
        scanner_fn=scanner_stub,
    )

    try:
        result = await orchestrator.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el agente: {str(e)}",
        ) from e

    return AgentResponse.from_state(result)
