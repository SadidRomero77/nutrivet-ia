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
    Cliente async para OpenRouter API con connection pool persistente.

    El httpx.AsyncClient se crea una vez y se reutiliza entre requests,
    evitando el overhead de crear/destruir conexiones TCP por cada llamada.

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
        self._client: httpx.AsyncClient | None = None

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
            except (httpx.TimeoutException, httpx.HTTPStatusError, ValueError) as e:
                last_error = e

                # Manejar 429 Rate Limit con Retry-After del header
                if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 429:
                    retry_after = float(e.response.headers.get("Retry-After", _RETRY_DELAYS[min(attempt, len(_RETRY_DELAYS) - 1)]))
                    retry_after = min(retry_after, 60.0)  # cap a 60s para evitar bloqueos largos
                    logger.warning(
                        "OpenRouter 429 rate limit en '%s' — esperando %.1fs (intento %d/3)",
                        current_model, retry_after, attempt + 1,
                    )
                    await asyncio.sleep(retry_after)
                    continue

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

    def _get_client(self) -> httpx.AsyncClient:
        """Retorna el httpx.AsyncClient persistente (lazy init)."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=_TIMEOUT_SECONDS,
                limits=httpx.Limits(
                    max_connections=20,
                    max_keepalive_connections=10,
                    keepalive_expiry=30,
                ),
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "HTTP-Referer": self._http_referer,
                    "X-Title": "NutriVet.IA",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Cierra el pool de conexiones. Llamar al apagar la app."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _call(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Realiza una llamada HTTP al API de OpenRouter."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,  # Límite explícito — previene costos descontrolados (OWASP LLM10)
        }

        client = self._get_client()
        start = time.monotonic()
        resp = await client.post(_OPENROUTER_API_URL, json=payload)
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
