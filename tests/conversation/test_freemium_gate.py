"""
Tests RED — FreemiumGate (NUT-82 · Paso 3).

Free tier: 3 preguntas/día × 3 días = 9 total.
Emergencias: bypass incondicional.
Tiers pagados: bypass.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock
from dataclasses import dataclass

from backend.infrastructure.agent.nodes.freemium_gate import (
    FreemiumGateError,
    check_freemium_gate,
)


@dataclass
class _MockQuota:
    daily_count: int = 0
    total_count: int = 0
    last_reset_date: str = "2026-03-19"


def _mock_quota_repo(daily: int = 0, total: int = 0) -> AsyncMock:
    quota = _MockQuota(daily_count=daily, total_count=total)
    repo = AsyncMock()
    repo.get_or_create.return_value = quota
    repo.increment.return_value = None
    repo.reset_daily.return_value = None
    return repo


class TestFreemiumGate:

    @pytest.mark.asyncio
    async def test_emergencia_no_cuota(self) -> None:
        """Emergency bypassa la cuota — siempre pasa aunque tenga 9/9."""
        repo = _mock_quota_repo(daily=3, total=9)
        # No debe levantar error
        await check_freemium_gate(
            user_id="user-1",
            user_tier="FREE",
            intent="emergency",
            quota_repo=repo,
        )
        repo.increment.assert_not_called()

    @pytest.mark.asyncio
    async def test_free_bloquea_al_superar_total(self) -> None:
        """Free tier con 9/9 usadas → FreemiumGateError."""
        repo = _mock_quota_repo(daily=0, total=9)
        with pytest.raises(FreemiumGateError, match="upgrade"):
            await check_freemium_gate(
                user_id="user-1",
                user_tier="FREE",
                intent="nutritional",
                quota_repo=repo,
            )

    @pytest.mark.asyncio
    async def test_free_bloquea_al_superar_diario(self) -> None:
        """Free tier con 3 preguntas hoy → FreemiumGateError en la 4ta."""
        repo = _mock_quota_repo(daily=3, total=5)
        with pytest.raises(FreemiumGateError, match="día"):
            await check_freemium_gate(
                user_id="user-1",
                user_tier="FREE",
                intent="nutritional",
                quota_repo=repo,
            )

    @pytest.mark.asyncio
    async def test_free_pasa_con_cuota_disponible(self) -> None:
        """Free tier con 1/3 diarias usadas → pasa."""
        repo = _mock_quota_repo(daily=1, total=3)
        await check_freemium_gate(
            user_id="user-1",
            user_tier="FREE",
            intent="nutritional",
            quota_repo=repo,
        )
        repo.increment.assert_called_once()

    @pytest.mark.asyncio
    async def test_tier_basico_sin_limite(self) -> None:
        """Tier BASICO → sin gate, sin incremento de cuota Free."""
        repo = _mock_quota_repo(daily=99, total=999)
        await check_freemium_gate(
            user_id="user-1",
            user_tier="BASICO",
            intent="nutritional",
            quota_repo=repo,
        )
        repo.get_or_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_tier_premium_sin_limite(self) -> None:
        """Tier PREMIUM → sin gate."""
        repo = _mock_quota_repo()
        await check_freemium_gate(
            user_id="user-1",
            user_tier="PREMIUM",
            intent="nutritional",
            quota_repo=repo,
        )
        repo.get_or_create.assert_not_called()

    @pytest.mark.asyncio
    async def test_incremento_atomico_antes_llm(self) -> None:
        """El incremento de cuota ocurre ANTES de la llamada LLM."""
        repo = _mock_quota_repo(daily=0, total=0)
        await check_freemium_gate(
            user_id="user-1",
            user_tier="FREE",
            intent="nutritional",
            quota_repo=repo,
        )
        repo.increment.assert_called_once_with("user-1")
