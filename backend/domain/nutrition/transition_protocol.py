"""
Protocolo de transición dietética variable por condición — NutriVet.IA (B-05)

La duración de la transición depende de la condición gastrointestinal y del
tipo de cambio en la forma física del alimento.

Fuentes: Small Animal Clinical Nutrition 5th Ed., WSAVA 2021.
Validado por Lady Carolina Castañeda (MV, BAMPYSVET).
NUNCA modificar sin confirmación veterinaria.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransitionProtocol:
    """
    Protocolo de transición gradual para el cambio de dieta.

    min_dias:  Duración mínima recomendada.
    max_dias:  Duración máxima recomendada.
    ritmo:     Descripción del ritmo de cambio (qué % nuevo se agrega cada cuántos días).
    razon:     Por qué esta duración para este contexto.
    """

    min_dias: int
    max_dias: int
    ritmo: str
    razon: str


# ---------------------------------------------------------------------------
# Tabla de duraciones por condición / contexto
# Clave → (min_dias, max_dias, ritmo, razon)
# ---------------------------------------------------------------------------

TRANSITION_BY_CONDITION: dict[str, TransitionProtocol] = {
    "sano_no_sensible": TransitionProtocol(
        min_dias=7, max_dias=10,
        ritmo="~10% nuevo/día",
        razon="Digestión normal — adaptación microbiota en 7-10 días.",
    ),
    "sano_sensible": TransitionProtocol(
        min_dias=14, max_dias=21,
        ritmo="5-7% nuevo cada 2 días",
        razon="Tracto GI reactivo sin patología — transición más lenta para evitar diarrea.",
    ),
    "gastritis": TransitionProtocol(
        min_dias=21, max_dias=28,
        ritmo="5% nuevo cada 2-3 días",
        razon="Mucosa gástrica inflamada — cambio muy gradual para evitar irritación.",
    ),
    "pancreático": TransitionProtocol(
        min_dias=21, max_dias=28,
        ritmo="5% nuevo cada 2-3 días — vigilar signos de pancreatitis",
        razon="Páncreas extremadamente sensible al cambio brusco de grasa.",
    ),
    "hepático/hiperlipidemia": TransitionProtocol(
        min_dias=14, max_dias=21,
        ritmo="7% nuevo cada 2 días — vigilar bilirrubina",
        razon="Hígado comprometido requiere adaptación gradual a nuevo perfil lipídico.",
    ),
    "renal": TransitionProtocol(
        min_dias=14, max_dias=21,
        ritmo="7% nuevo cada 2 días — vigilar creatinina y fósforo",
        razon="Restricción de fósforo y proteína debe introducirse gradualmente.",
    ),
    "insuficiencia_cardiaca": TransitionProtocol(
        min_dias=14, max_dias=21,
        ritmo="7% nuevo cada 2 días — vigilar peso y retención de líquidos",
        razon="Cambio de sodio abrupto puede desestabilizar balance hídrico.",
    ),
    "megaesofago": TransitionProtocol(
        min_dias=30, max_dias=42,
        ritmo="Muy gradual — 5% nueva textura cada 3 días",
        razon="Adaptación a nueva textura/consistencia para evitar regurgitación y neumonía aspirativa.",
    ),
    "diabético": TransitionProtocol(
        min_dias=14, max_dias=21,
        ritmo="7% nuevo cada 2 días — vigilar glucemia durante transición",
        razon="Cambio de carbohidratos afecta glucemia — sincronizar con ajuste de insulina si aplica.",
    ),
    "barf_a_concentrado": TransitionProtocol(
        min_dias=21, max_dias=28,
        ritmo="10% concentrado/día — mezclar carne cocida con croqueta remojada",
        razon="Cambio de forma física (BARF → croqueta) — alta diferencia en contenido de agua y textura.",
    ),
    "concentrado_a_barf": TransitionProtocol(
        min_dias=21, max_dias=28,
        ritmo="10% BARF/día — agregar carne cocida antes de introducir cruda",
        razon="Microbiota adaptada a concentrado necesita tiempo para manejar proteína cruda.",
    ),
    "concentrado_a_casero_cocido": TransitionProtocol(
        min_dias=14, max_dias=21,
        ritmo="10% casero/día",
        razon="Cambio de forma física moderado — casero cocido es más similar a concentrado húmedo.",
    ),
}


def get_transition_protocol(
    conditions: list[str] | None = None,
    current_diet: str = "concentrado",
    new_diet: str = "natural",
) -> TransitionProtocol:
    """
    Determina la duración y ritmo de transición según:
    1. La condición médica más restrictiva (la que requiere más días).
    2. El tipo de cambio en la forma física del alimento.

    Args:
        conditions:    Lista de condiciones médicas activas (valores de MedicalCondition).
        current_diet:  Tipo de dieta actual: "concentrado" | "natural" | "mixto".
        new_diet:      Tipo de dieta nueva: "concentrado" | "natural" | "mixto".

    Returns:
        TransitionProtocol con la duración y ritmo adecuados.
    """
    # Detectar cambio de forma física — siempre mínimo 21 días
    physical_change = _detect_physical_change(current_diet, new_diet)

    # Iniciar con el protocolo base según cambio físico o mascota sana
    if physical_change:
        key = _get_physical_change_key(current_diet, new_diet)
        best = TRANSITION_BY_CONDITION.get(key, TRANSITION_BY_CONDITION["barf_a_concentrado"])
    else:
        best = TRANSITION_BY_CONDITION["sano_no_sensible"]

    # Seleccionar la condición más restrictiva (más días)
    for condition in (conditions or []):
        cond_protocol = TRANSITION_BY_CONDITION.get(condition)
        if cond_protocol and cond_protocol.max_dias > best.max_dias:
            best = cond_protocol

    return best


def _detect_physical_change(current_diet: str, new_diet: str) -> bool:
    """True si el cambio implica una diferencia de forma física significativa."""
    barf = {"natural", "barf"}
    concentrado = {"concentrado"}
    is_barf_now = current_diet in barf
    is_barf_new = new_diet in barf
    return is_barf_now != is_barf_new


def _get_physical_change_key(current_diet: str, new_diet: str) -> str:
    """Devuelve la clave del protocolo de cambio físico adecuada."""
    barf = {"natural", "barf"}
    if current_diet in barf and new_diet not in barf:
        return "barf_a_concentrado"
    if current_diet not in barf and new_diet in barf:
        return "concentrado_a_barf"
    return "concentrado_a_casero_cocido"
