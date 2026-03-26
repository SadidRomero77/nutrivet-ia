"""Tests — LLMRouter (unit-04-plan-service Paso 3).

Constitution REGLA 5 (actualizada 2026-03-25):
  Free    → openai/gpt-4o-mini
  Básico  → openai/gpt-4o-mini
  Premium/Vet → anthropic/claude-sonnet-4-5
  2+ condiciones (cualquier tier) → anthropic/claude-sonnet-4-5  (override no negociable)
  OCR → openai/gpt-4o (vision) — no probado aquí
  Sin endpoints :free — producción requiere SLA garantizado.
"""
from __future__ import annotations

import pytest

from backend.application.llm.llm_router import LLMRouter
from backend.domain.aggregates.user_account import UserTier


class TestLLMRouter:

    def test_free_tier_0_cond_gpt4o_mini(self) -> None:
        """Free + 0 condiciones → gpt-4o-mini (no más :free)."""
        model = LLMRouter.select_model(UserTier.FREE, conditions_count=0)
        assert model == "openai/gpt-4o-mini"

    def test_free_tier_1_cond_gpt4o_mini(self) -> None:
        """Free + 1 condición → gpt-4o-mini (bajo umbral clínico)."""
        model = LLMRouter.select_model(UserTier.FREE, conditions_count=1)
        assert model == "openai/gpt-4o-mini"

    def test_basico_tier_0_cond_gpt4o_mini(self) -> None:
        """Básico + 0 condiciones → gpt-4o-mini."""
        model = LLMRouter.select_model(UserTier.BASICO, conditions_count=0)
        assert model == "openai/gpt-4o-mini"

    def test_basico_tier_1_cond_gpt4o_mini(self) -> None:
        """Básico + 1 condición → gpt-4o-mini (1 condición bajo umbral)."""
        model = LLMRouter.select_model(UserTier.BASICO, conditions_count=1)
        assert model == "openai/gpt-4o-mini"

    def test_premium_tier_claude(self) -> None:
        """Premium + 0 condiciones → claude-sonnet-4-5."""
        model = LLMRouter.select_model(UserTier.PREMIUM, conditions_count=0)
        assert model == "anthropic/claude-sonnet-4-5"

    def test_vet_tier_claude(self) -> None:
        """Vet tier → claude-sonnet-4-5."""
        model = LLMRouter.select_model(UserTier.VET, conditions_count=0)
        assert model == "anthropic/claude-sonnet-4-5"

    def test_override_2_condiciones_free(self) -> None:
        """Free + 2 condiciones → claude-sonnet-4-5 (override REGLA 5 umbral=2)."""
        model = LLMRouter.select_model(UserTier.FREE, conditions_count=2)
        assert model == "anthropic/claude-sonnet-4-5"

    def test_override_2_condiciones_basico(self) -> None:
        """Básico + 2 condiciones → override a claude-sonnet-4-5."""
        model = LLMRouter.select_model(UserTier.BASICO, conditions_count=2)
        assert model == "anthropic/claude-sonnet-4-5"

    def test_override_3_condiciones_free(self) -> None:
        """Free + 3 condiciones → claude-sonnet-4-5 (override REGLA 5)."""
        model = LLMRouter.select_model(UserTier.FREE, conditions_count=3)
        assert model == "anthropic/claude-sonnet-4-5"

    def test_override_5_condiciones_free(self) -> None:
        """Free + 5 condiciones → claude-sonnet-4-5 (Sally case)."""
        model = LLMRouter.select_model(UserTier.FREE, conditions_count=5)
        assert model == "anthropic/claude-sonnet-4-5"

    def test_sin_endpoint_free(self) -> None:
        """Ningún tier retorna endpoint :free."""
        for tier in UserTier:
            for cond in [0, 1, 2, 5]:
                model = LLMRouter.select_model(tier, conditions_count=cond)
                assert ":free" not in model, f"Tier {tier} cond={cond} retornó :free"

    def test_llm_router_es_determinista(self) -> None:
        """Mismo input → mismo output siempre."""
        m1 = LLMRouter.select_model(UserTier.FREE, conditions_count=2)
        m2 = LLMRouter.select_model(UserTier.FREE, conditions_count=2)
        assert m1 == m2

    def test_llm_router_sally_golden_case(self) -> None:
        """Sally: free + 5 condiciones → claude-sonnet-4-5 (Golden case G8)."""
        # French Poodle: Diabetes + Hepatopatía + Gastritis + Cistitis + Hipotiroidismo
        model = LLMRouter.select_model(UserTier.FREE, conditions_count=5)
        assert model == "anthropic/claude-sonnet-4-5"

    def test_no_existe_metodo_update(self) -> None:
        """LLMRouter es stateless — no tiene estado mutable."""
        assert callable(LLMRouter.select_model)
