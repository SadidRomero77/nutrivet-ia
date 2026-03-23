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
    FACTOR_GESTACION_GATO,
    FACTOR_GESTACION_PERRO,
    FACTOR_LACTANCIA_BASE_GATO,
    FACTOR_LACTANCIA_BASE_PERRO,
    FACTOR_LACTANCIA_MAX_CACHORROS,
    FACTOR_LACTANCIA_MAX_GATITOS,
    FACTOR_LACTANCIA_POR_CACHORRO,
    FACTOR_LACTANCIA_POR_GATITO,
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
        num_offspring: int = 0,
        gestation_week: int = 0,
        breed_adult_months: int = 0,
    ) -> float:
        """
        Calcula el Requerimiento Energético Diario (DER).

        Fórmula base: DER = RER × factor_vida × factor_edad × bcs_modifier
        Estados especiales:
          gestante:  DER = RER × factor_gestacion(semana) × bcs_modifier
          lactante:  DER = RER × (base + coef × n_crías)  — sin bcs_modifier

        Args:
            rer: RER calculado previamente (kcal/día).
            age_months: Edad en meses.
            reproductive_status: "esterilizado" | "no_esterilizado" |
                                  "gestante" | "lactante".
            activity_level: Nivel de actividad válido para la especie.
            species: "perro" | "gato".
            bcs: Body Condition Score (1-9).
            num_offspring: Número de crías (usado solo si lactante).
            gestation_week: Semana de gestación 1-9 (0 = desconocida).
            breed_adult_months: Edad de madurez de la raza en meses (0 = usar default
                                de la especie). Para razas gigantes (Gran Danés,
                                Bernes, Rottweiler) este valor es 18-24 — el factor
                                cachorro se aplica hasta esa edad, no hasta los 12 meses.

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

        # --- Estado especial: GESTANTE ---
        if reproductive_status == "gestante":
            factor_gestacion = cls._get_factor_gestacion(species, gestation_week)
            bcs_modifier = BCS(bcs).der_modifier
            return rer * factor_gestacion * bcs_modifier

        # --- Estado especial: LACTANTE ---
        # La lactancia anula el bcs_modifier — la hembra está en hipercalórico fisiológico.
        if reproductive_status == "lactante":
            return cls._calculate_der_lactante(rer, species, num_offspring)

        # --- Cálculo estándar ---
        factor_vida = cls._get_factor_vida(species, activity_level, reproductive_status)
        factor_edad = cls._get_factor_edad(species, age_months, breed_adult_months)
        bcs_modifier = BCS(bcs).der_modifier

        return rer * factor_vida * factor_edad * bcs_modifier

    @classmethod
    def get_ideal_weight_by_species(
        cls,
        weight_kg: float,
        bcs: int,
        species: str,
    ) -> float:
        """
        Estima el peso ideal con lógica diferenciada por especie (A-06).

        Perros: cada unidad de BCS sobre 5 ≈ 10% exceso de peso corporal.
        Gatos:  distribución de grasa diferente — cada unidad sobre 5 ≈ 400g exceso.

        Args:
            weight_kg: Peso real en kg.
            bcs: Body Condition Score (1-9).
            species: "perro" | "gato".

        Returns:
            Peso ideal estimado en kg.
        """
        if bcs == 5:
            return weight_kg

        if species == "gato":
            bcs_offset = bcs - 5
            if bcs_offset > 0:
                return max(weight_kg - (bcs_offset * 0.4), 0.5)
            return weight_kg + (abs(bcs_offset) * 0.3)

        # Perro (y fallback)
        excess_factor = 1.0 + (bcs - 5) * 0.1
        return weight_kg / excess_factor

    @classmethod
    def get_ideal_weight_estimate(cls, weight_kg: float, bcs: int) -> float:
        """Compatibilidad hacia atrás — usa lógica de perro. Usar get_ideal_weight_by_species."""
        return cls.get_ideal_weight_by_species(weight_kg, bcs, "perro")
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
    def _get_factor_edad(
        cls, species: str, age_months: int, breed_adult_months: int = 0
    ) -> float:
        """
        Obtiene el factor de etapa de vida según la especie y edad.

        Para razas gigantes (breed_adult_months ≥ 18), el factor cachorro (2.0)
        se aplica hasta la edad de madurez real de la raza.
        Ejemplo: Gran Danés 14 meses → factor 2.0 (cachorro), NO 1.2 (adulto joven).
        Sin breed_adult_months se usa la tabla genérica por especie.
        """
        # Lógica especial para razas gigantes en perros
        if species == "perro" and breed_adult_months >= 18:
            if age_months <= 3:
                return 3.0   # Cachorro muy temprano
            elif age_months <= breed_adult_months:
                return 2.0   # Cachorro hasta la madurez real de la raza
            elif age_months <= 24:
                return 1.2   # Adulto joven post-madurez
            else:
                return 1.0   # Adulto / senior

        tabla = FACTOR_EDAD_PERRO if species == "perro" else FACTOR_EDAD_GATO
        for (min_age, max_age), factor in tabla:
            if min_age <= age_months <= max_age:
                return factor
        # Fallback: adulto
        return 1.0

    @classmethod
    def _get_factor_gestacion(cls, species: str, gestation_week: int) -> float:
        """
        Retorna el factor de gestación según especie y semana.
        Si gestation_week == 0 (desconocida), usa promedio_seguro.
        """
        tabla = (
            FACTOR_GESTACION_PERRO if species == "perro"
            else FACTOR_GESTACION_GATO
        )
        if gestation_week == 0:
            return tabla["promedio_seguro"]
        if gestation_week <= 4:
            return tabla["primera_mitad"]
        return tabla["segunda_mitad"]

    @classmethod
    def _calculate_der_lactante(
        cls,
        rer: float,
        species: str,
        num_offspring: int,
    ) -> float:
        """
        DER para hembra lactante.
        Perro: DER = RER × (4.0 + 0.2 × min(n_cachorros, 8))
        Gato:  DER = RER × (2.0 + 0.3 × min(n_gatitos, 6))
        """
        if species == "perro":
            n = min(num_offspring, FACTOR_LACTANCIA_MAX_CACHORROS)
            factor = FACTOR_LACTANCIA_BASE_PERRO + (FACTOR_LACTANCIA_POR_CACHORRO * n)
        else:
            n = min(num_offspring, FACTOR_LACTANCIA_MAX_GATITOS)
            factor = FACTOR_LACTANCIA_BASE_GATO + (FACTOR_LACTANCIA_POR_GATITO * n)
        return rer * factor
