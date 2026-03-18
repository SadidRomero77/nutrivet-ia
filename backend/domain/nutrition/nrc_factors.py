"""
Factores NRC para el cálculo de DER — NutriVet.IA
Fuentes: NRC 2006, WSAVA 2021, Small Animal Clinical Nutrition 5th Ed.

Los factores de actividad y reproductivo se combinan en FACTOR_VIDA para
evitar sobreestimación al multiplicar ambos independientemente.

Validado por Lady Carolina Castañeda (MV, BAMPYSVET).
NUNCA modificar sin confirmación veterinaria.
"""

# --- Factor de vida (actividad × reproductivo combinado) ---
# Clave: (nivel_actividad, estado_reproductivo)

FACTOR_VIDA_PERRO: dict[tuple[str, str], float] = {
    ("sedentario",  "esterilizado"):    1.348,  # Golden case Sally ±0.5 kcal
    ("sedentario",  "no_esterilizado"): 1.600,
    ("moderado",    "esterilizado"):    1.600,
    ("moderado",    "no_esterilizado"): 2.000,
    ("activo",      "esterilizado"):    1.900,
    ("activo",      "no_esterilizado"): 2.400,
    ("muy_activo",  "esterilizado"):    2.400,
    ("muy_activo",  "no_esterilizado"): 3.000,
}

FACTOR_VIDA_GATO: dict[tuple[str, str], float] = {
    ("indoor",          "esterilizado"):    1.000,
    ("indoor",          "no_esterilizado"): 1.200,
    ("indoor_outdoor",  "esterilizado"):    1.200,
    ("indoor_outdoor",  "no_esterilizado"): 1.500,
    ("outdoor",         "esterilizado"):    1.400,
    ("outdoor",         "no_esterilizado"): 1.800,
}

# --- Factor de etapa de vida (perro) ---
# Clave: rango de edad en meses (tupla inclusive)

FACTOR_EDAD_PERRO: list[tuple[tuple[int, int], float]] = [
    ((0,  3),   3.0),   # Cachorro muy temprano: máxima demanda energética
    ((4,  12),  2.0),   # Cachorro en crecimiento
    ((13, 24),  1.2),   # Adulto joven (finaliza crecimiento)
    ((25, 9999), 1.0),  # Adulto y senior: misma demanda base
]

# --- Factor de etapa de vida (gato) ---
FACTOR_EDAD_GATO: list[tuple[tuple[int, int], float]] = [
    ((0,  6),   2.5),   # Gatito en crecimiento
    ((7,  12),  1.8),
    ((13, 9999), 1.0),  # Adulto y senior
]

# Niveles de actividad válidos por especie
ACTIVIDAD_VALIDA_PERRO: frozenset[str] = frozenset({
    "sedentario", "moderado", "activo", "muy_activo"
})

ACTIVIDAD_VALIDA_GATO: frozenset[str] = frozenset({
    "indoor", "indoor_outdoor", "outdoor"
})

ESTADO_REPRODUCTIVO_VALIDO: frozenset[str] = frozenset({
    "esterilizado", "no_esterilizado"
})
