"""
OpenRouterClient — Cliente async para OpenRouter API.

Características:
  - Timeout 30s por request
  - Retry × 2 con backoff exponencial (2s, 4s)
  - Fallback a modelo inferior si falla tras 3 intentos
  - Registra latencia y tokens en retorno
  - Nunca incluye PII en prompts (Constitution REGLA 6)
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


# Fallback chain si el modelo primario falla (IDs verificados contra OpenRouter API)
# No se usan endpoints :free — sin SLA, rate limits compartidos entre todos los usuarios.
_FALLBACK_CHAIN: dict[str, str] = {
    "anthropic/claude-sonnet-4-5": "openai/gpt-4o-mini",
    # gpt-4o-mini no tiene fallback inferior — es el piso de calidad aceptable
}

_OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
_TIMEOUT_SECONDS = 30
_RETRY_DELAYS = [2.0, 4.0]  # backoff exponencial


class LLMResponse:
    """Respuesta estructurada del LLM."""

    def __init__(
        self,
        content: str,
        model_used: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
    ) -> None:
        self.content = content
        self.model_used = model_used
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.latency_ms = latency_ms


class OpenRouterClient:
    """
    Cliente async para OpenRouter API.

    Uso:
        client = OpenRouterClient()
        response = await client.generate(
            model="anthropic/claude-sonnet-4-5",
            system_prompt="...",
            user_prompt="...",
        )
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self._api_key:
            raise ValueError(
                "OPENROUTER_API_KEY no configurada. "
                "Agrégala a .env.dev o como variable de entorno."
            )
        self._http_referer = os.environ.get("OPENROUTER_REFERER", "https://nutrivet-ia.com")

    async def generate(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Genera texto con el modelo dado. Retry × 2 con backoff, fallback si falla.

        Args:
            model: Identificador del modelo en OpenRouter.
            system_prompt: Instrucciones del sistema (sin PII).
            user_prompt: Prompt del usuario (sin PII).
            temperature: Temperatura del modelo (0.3 para plans nutricionales).

        Returns:
            LLMResponse con content, model_used, tokens y latencia.

        Raises:
            RuntimeError: Si todos los reintentos y fallbacks fallan.
        """
        current_model = model
        last_error: Exception | None = None

        for attempt in range(3):  # 3 intentos: 0, 1, 2
            try:
                return await self._call(current_model, system_prompt, user_prompt, temperature, max_tokens)
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                last_error = e
                if attempt < len(_RETRY_DELAYS):
                    await asyncio.sleep(_RETRY_DELAYS[attempt])
                else:
                    # Agoté reintentos — intentar fallback
                    fallback = _FALLBACK_CHAIN.get(current_model, current_model)
                    if fallback != current_model:
                        current_model = fallback
                        # Reiniciar contador con fallback
                        try:
                            return await self._call(
                                current_model, system_prompt, user_prompt, temperature, max_tokens
                            )
                        except Exception as fe:
                            last_error = fe

        logger.error(
            "OpenRouter: todos los intentos fallaron para modelo '%s'. Error: %s",
            model, type(last_error).__name__,
        )
        raise RuntimeError("El servicio de IA no está disponible temporalmente. Intenta de nuevo.")

    async def _call(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Realiza una llamada HTTP al API de OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": self._http_referer,
            "X-Title": "NutriVet.IA",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,  # Límite explícito — previene costos descontrolados (OWASP LLM10)
        }

        start = time.monotonic()
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            resp = await client.post(_OPENROUTER_API_URL, json=payload, headers=headers)
            resp.raise_for_status()

        latency_ms = int((time.monotonic() - start) * 1000)

        try:
            data = resp.json()
        except Exception as parse_err:
            raise ValueError(f"Respuesta JSON inválida de OpenRouter: {type(parse_err).__name__}") from parse_err

        try:
            choice = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as struct_err:
            raise ValueError(f"Estructura de respuesta inesperada de OpenRouter: {type(struct_err).__name__}") from struct_err

        usage = data.get("usage", {})

        return LLMResponse(
            content=choice,
            model_used=data.get("model", model),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
        )
