"""
Utilidades de extracción y reparación de JSON en respuestas del LLM.

Los LLMs ocasionalmente devuelven JSON envuelto en markdown (```json),
con texto antes/después, o con errores menores de sintaxis.
Este módulo extrae y repara el JSON de forma robusta.

Uso:
    parsed = extract_json(raw_llm_output)
    if parsed is None:
        raise ValueError("LLM no generó JSON parseable")
"""
from __future__ import annotations

import json
import re
from typing import Any


def extract_json(raw: str) -> dict[str, Any] | None:
    """
    Extrae el primer objeto JSON válido de un string de texto.

    Maneja:
    - Markdown code blocks: ```json ... ```
    - Texto antes del primer {
    - Texto después del último }
    - Trailing commas (reparación básica)

    Args:
        raw: Output crudo del LLM

    Returns:
        dict parseado, o None si no se encontró JSON válido.
    """
    if not raw or not raw.strip():
        return None

    # 1. Intentar parsear directo (caso feliz — LLM siguió instrucciones)
    cleaned = raw.strip()
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # 2. Extraer de markdown code blocks ```json ... ``` o ``` ... ```
    match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", cleaned, re.IGNORECASE)
    if match:
        candidate = match.group(1).strip()
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        # Intentar reparar y re-parsear
        repaired = _repair_json(candidate)
        try:
            result = json.loads(repaired)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    # 3. Extraer el contenido entre el primer { y el último }
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and start < end:
        candidate = cleaned[start : end + 1]
        try:
            result = json.loads(candidate)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass
        # Intentar reparar
        repaired = _repair_json(candidate)
        try:
            result = json.loads(repaired)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

    return None


def _repair_json(text: str) -> str:
    """
    Aplica reparaciones básicas de sintaxis JSON.

    Reparaciones:
    - Elimina trailing commas antes de } o ]
    - Reemplaza comillas simples por dobles
    - Elimina comentarios // (no válidos en JSON)
    """
    # Eliminar trailing commas: , seguido de whitespace y } o ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Eliminar comentarios de línea // ... (no estándar en JSON)
    text = re.sub(r"//[^\n]*\n", "\n", text)

    # Reemplazar comillas simples por dobles (solo si parecen comillas de string)
    # Cuidado: esta es una heurística básica, puede romper strings que contienen apostrofes
    # Solo aplicar si hay muy pocas comillas dobles (LLM usó comillas simples consistentemente)
    double_quotes = text.count('"')
    single_quotes = text.count("'")
    if single_quotes > double_quotes * 2:
        # El LLM probablemente usó comillas simples — intentar reemplazar
        text = text.replace("'", '"')

    return text


def safe_parse_plan_json(raw: str, der_kcal: float) -> dict[str, Any]:
    """
    Parsea el JSON del plan nutricional con validación básica de coherencia.

    Args:
        raw: Output crudo del LLM
        der_kcal: DER calculado para validar coherencia calórica

    Returns:
        dict con el plan parseado

    Raises:
        ValueError: Si el JSON no es parseable o falta estructura mínima
    """
    parsed = extract_json(raw)
    if parsed is None:
        raise ValueError(
            f"El LLM no generó JSON válido. Output recibido (primeros 500 chars): {raw[:500]}"
        )

    # Verificar secciones mínimas obligatorias
    required_sections = ["perfil_nutricional", "ingredientes", "porciones", "instrucciones_preparacion"]
    missing = [s for s in required_sections if s not in parsed]
    if missing:
        raise ValueError(
            f"Plan incompleto — secciones faltantes: {missing}. "
            f"El LLM generó: {list(parsed.keys())}"
        )

    # Verificar que hay ingredientes
    ingredientes = parsed.get("ingredientes", [])
    if not ingredientes or not isinstance(ingredientes, list):
        raise ValueError(
            "El plan no tiene ingredientes válidos — el LLM no generó la lista de ingredientes"
        )

    # Verificar coherencia calórica básica (advertencia, no error bloqueante)
    perfil = parsed.get("perfil_nutricional", {})
    kcal_verificadas = perfil.get("kcal_verificadas", 0)
    if kcal_verificadas > 0 and der_kcal > 0:
        desviacion = abs(kcal_verificadas - der_kcal) / der_kcal
        if desviacion > 0.20:
            # Registrar en el plan la advertencia pero no rechazar
            if "alertas_propietario" not in parsed:
                parsed["alertas_propietario"] = []
            parsed["alertas_propietario"].append(
                f"⚠ Revisión calórica pendiente: el plan calculó {kcal_verificadas:.0f} kcal "
                f"vs DER de {der_kcal:.0f} kcal ({desviacion:.0%} de diferencia)"
            )

    # Asegurar que los campos opcionales existan con valores por defecto
    parsed.setdefault("suplementos", [])
    parsed.setdefault("transicion_dieta", {
        "requiere_transicion": True,
        "duracion_dias": 10,
        "fases": [],
        "senales_de_alerta": [
            "Vómitos persistentes por más de 2 días",
            "Diarrea líquida por más de 24 horas",
        ],
    })
    parsed.setdefault("notas_clinicas", [])
    parsed.setdefault("alertas_propietario", [])

    return parsed
