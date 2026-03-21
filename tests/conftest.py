"""
Conftest raíz de NutriVet.IA — fixtures compartidas por toda la suite.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    """
    Resetea el storage in-memory de los rate limiters antes de cada test.

    En tests, todas las requests vienen de 127.0.0.1 (testclient), por lo que
    el limiter acumula hits entre tests y produce 429 inesperados.

    Los limiters de slowapi exponen reset() que limpia el MemoryStorage.
    """
    from backend.presentation.routers.auth_router import _limiter as auth_limiter
    from backend.presentation.routers.agent_router import _limiter as agent_limiter

    for limiter in (auth_limiter, agent_limiter):
        try:
            limiter.reset()
        except Exception:
            pass

    yield
