"""
NRCCalculator — Cálculo determinista de RER y DER.

REGLA 3 de la Constitution: el cálculo calórico NUNCA lo hace el LLM.
Este módulo es Python puro — cero dependencias externas.

Fórmulas:
    RER = 70 × peso_kg^0.75  (kcal/día)
    DER = RER × factor_vida × factor_edad × bcs_modifier

Golden case validado: Sally (10.08 kg) → RER ≈ 396 kcal, DER ≈ 534 kcal/día (±0.5 kcal)
Validado por Lady Carolina Castañeda (MV, BAMPYSVET).
"""

from backend.domain.exceptions.domain_errors import InvalidWeightError, NRCCalculationError
from backend.domain.nutrition.nrc_factors import (
    ACTIVIDAD_VALIDA_GATO,
    ACTIVIDAD_VALIDA_PERRO,
    ESTADO_REPRODUCTIVO_VALIDO,
    FACTOR_EDAD_GATO,
    FACTOR_EDAD_PERRO,
    FACTOR_VIDA_GATO,
    FACTOR_VIDA_PERRO,
)
from backend.domain.value_objects.bcs import BCS


class NRCCalculator:
    """
    Calculador estático de requerimientos energéticos NRC.
    Todos los métodos son métodos de clase — no requiere instanciación.
    """

    @classmethod
    def calculate_rer(cls, weight_kg: float) -> float:
        """
        Calcula la Tasa de Energía en Reposo (RER).

        Args:
            weight_kg: Peso corporal en kilogramos. Debe ser > 0.

        Returns:
            RER en kcal/día.

        Raises:
            InvalidWeightError: Si el peso es ≤ 0.
        """
        if weight_kg <= 0:
            raise InvalidWeightError(weight_kg)
        return 70.0 * (weight_kg ** 0.75)

    @classmethod
    def calculate_der(
        cls,
        rer: float,
        age_months: int,
        reproductive_status: str,
        activity_level: str,
        species: str,
        bcs: int,
    ) -> float:
        """
        Calcula el Requerimiento Energético Diario (DER).

        DER = RER × factor_vida × factor_edad × bcs_modifier

        Args:
            rer: RER calculado previamente (kcal/día).
            age_months: Edad en meses.
            reproductive_status: "esterilizado" | "no_esterilizado".
            activity_level: Nivel de actividad válido para la especie.
            species: "perro" | "gato".
            bcs: Body Condition Score (1-9).

        Returns:
            DER en kcal/día.

        Raises:
            NRCCalculationError: Si algún parámetro es inválido.
        """
        if reproductive_status not in ESTADO_REPRODUCTIVO_VALIDO:
            raise NRCCalculationError(
                f"Estado reproductivo inválido: '{reproductive_status}'. "
                f"Válidos: {sorted(ESTADO_REPRODUCTIVO_VALIDO)}"
            )

        factor_vida = cls._get_factor_vida(species, activity_level, reproductive_status)
        factor_edad = cls._get_factor_edad(species, age_months)
        bcs_modifier = BCS(bcs).der_modifier

        return rer * factor_vida * factor_edad * bcs_modifier

    @classmethod
    def get_ideal_weight_estimate(cls, weight_kg: float, bcs: int) -> float:
        """
        Estima el peso ideal a partir del peso real y el BCS.

        Cada unidad de BCS por encima de 5 representa aproximadamente un 10%
        de exceso de grasa corporal. Para BCS por debajo de 5, el animal está
        por debajo del peso ideal.

        Usado en el Weight Journey para calcular RER sobre peso ideal en fase
        de reducción (BCS ≥ 7).

        Args:
            weight_kg: Peso real del animal en kg.
            bcs: Body Condition Score (1-9).

        Returns:
            Peso ideal estimado en kg.
        """
        if bcs == 5:
            return weight_kg
        # Factor de ajuste: 10% por unidad de BCS respecto al ideal (BCS 5)
        excess_factor = 1.0 + (bcs - 5) * 0.1
        return weight_kg / excess_factor

    # --- Métodos privados ---

    @classmethod
    def _get_factor_vida(
        cls, species: str, activity_level: str, reproductive_status: str
    ) -> float:
        """Obtiene el factor combinado (actividad × reproductivo) para la especie."""
        if species == "perro":
            if activity_level not in ACTIVIDAD_VALIDA_PERRO:
                raise NRCCalculationError(
                    f"Actividad inválida para perro: '{activity_level}'. "
                    f"Válidos: {sorted(ACTIVIDAD_VALIDA_PERRO)}"
                )
            return FACTOR_VIDA_PERRO[(activity_level, reproductive_status)]
        elif species == "gato":
            if activity_level not in ACTIVIDAD_VALIDA_GATO:
                raise NRCCalculationError(
                    f"Actividad inválida para gato: '{activity_level}'. "
                    f"Válidos: {sorted(ACTIVIDAD_VALIDA_GATO)}"
                )
            return FACTOR_VIDA_GATO[(activity_level, reproductive_status)]
        else:
            raise NRCCalculationError(
                f"Especie inválida: '{species}'. Válidas: 'perro', 'gato'"
            )

    @classmethod
    def _get_factor_edad(cls, species: str, age_months: int) -> float:
        """Obtiene el factor de etapa de vida según la especie y edad."""
        tabla = FACTOR_EDAD_PERRO if species == "perro" else FACTOR_EDAD_GATO
        for (min_age, max_age), factor in tabla:
            if min_age <= age_months <= max_age:
                return factor
        # Fallback: adulto
        return 1.0
