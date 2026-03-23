"""
Tests para las 4 nuevas condiciones médicas (A-04) y gestante/lactante (A-03).
NutriVet.IA — Sprint 1 v2.1
"""
import pytest
from uuid import uuid4


# ---------------------------------------------------------------------------
# A-04 — Nuevas condiciones médicas
# ---------------------------------------------------------------------------

class TestNewMedicalConditions:

    def test_insuficiencia_cardiaca_en_enum(self):
        from backend.domain.aggregates.pet_profile import MedicalCondition
        assert MedicalCondition.INSUFICIENCIA_CARDIACA.value == "insuficiencia_cardiaca"

    def test_cushing_en_enum(self):
        from backend.domain.aggregates.pet_profile import MedicalCondition
        assert MedicalCondition.CUSHING.value == "hiperadrenocorticismo_cushing"

    def test_epilepsia_en_enum(self):
        from backend.domain.aggregates.pet_profile import MedicalCondition
        assert MedicalCondition.EPILEPSIA.value == "epilepsia"

    def test_megaesofago_en_enum(self):
        from backend.domain.aggregates.pet_profile import MedicalCondition
        assert MedicalCondition.MEGAESOFAGO.value == "megaesofago"

    def test_total_conditions_is_17(self):
        from backend.domain.aggregates.pet_profile import MedicalCondition
        assert len(MedicalCondition) == 17

    def test_pet_con_insuficiencia_cardiaca_requires_vet(self):
        from backend.domain.aggregates.pet_profile import (
            MedicalCondition, PetProfile, Species, Sex, Size,
            ReproductiveStatus, DogActivityLevel, CurrentDiet,
        )
        from backend.domain.value_objects.bcs import BCS
        pet = PetProfile(
            pet_id=uuid4(), owner_id=uuid4(),
            name="Max", species=Species.PERRO, breed="Boxer",
            sex=Sex.MACHO, age_months=60, weight_kg=25.0, size=Size.GRANDE,
            reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=DogActivityLevel.SEDENTARIO,
            bcs=BCS(5), medical_conditions=[MedicalCondition.INSUFICIENCIA_CARDIACA],
            allergies=[], current_diet=CurrentDiet.CONCENTRADO,
        )
        assert pet.requires_vet_review() is True

    def test_pet_con_megaesofago_requires_vet(self):
        from backend.domain.aggregates.pet_profile import (
            MedicalCondition, PetProfile, Species, Sex, Size,
            ReproductiveStatus, DogActivityLevel, CurrentDiet,
        )
        from backend.domain.value_objects.bcs import BCS
        pet = PetProfile(
            pet_id=uuid4(), owner_id=uuid4(),
            name="Luna", species=Species.PERRO, breed="Pastor Alemán",
            sex=Sex.HEMBRA, age_months=36, weight_kg=28.0, size=Size.GRANDE,
            reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=DogActivityLevel.SEDENTARIO,
            bcs=BCS(5), medical_conditions=[MedicalCondition.MEGAESOFAGO],
            allergies=[], current_diet=CurrentDiet.NATURAL,
        )
        assert pet.requires_vet_review() is True

    def test_insuficiencia_cardiaca_restricciones_sodio(self):
        from backend.domain.safety.medical_restrictions import RESTRICTIONS_BY_CONDITION
        r = RESTRICTIONS_BY_CONDITION["insuficiencia_cardiaca"]
        assert "sodio_alto" in r.prohibited
        assert "taurina" in r.recommended
        assert "sodio_máximo_20mg_por_100kcal" in r.special_rules

    def test_insuficiencia_cardiaca_taurina_obligatoria(self):
        from backend.domain.safety.medical_restrictions import RESTRICTIONS_BY_CONDITION
        r = RESTRICTIONS_BY_CONDITION["insuficiencia_cardiaca"]
        assert "taurina_obligatoria_100mg_kg_dia" in r.special_rules

    def test_megaesofago_posicion_vertical_obligatoria(self):
        from backend.domain.safety.medical_restrictions import RESTRICTIONS_BY_CONDITION
        r = RESTRICTIONS_BY_CONDITION["megaesofago"]
        assert "POSICIÓN_VERTICAL_OBLIGATORIA_BAILEY_CHAIR" in r.special_rules
        assert "croquetas_secas_sin_remojar" in r.prohibited

    def test_epilepsia_sin_glutamato(self):
        from backend.domain.safety.medical_restrictions import RESTRICTIONS_BY_CONDITION
        r = RESTRICTIONS_BY_CONDITION["epilepsia"]
        assert "glutamato_monosódico" in r.prohibited
        assert "no_ayuno_mayor_8h" in r.special_rules

    def test_cushing_control_glucemico(self):
        from backend.domain.safety.medical_restrictions import RESTRICTIONS_BY_CONDITION
        r = RESTRICTIONS_BY_CONDITION["hiperadrenocorticismo_cushing"]
        assert "azúcares_simples" in r.prohibited
        assert "control_glucémico_como_diabético" in r.special_rules

    def test_valid_conditions_includes_all_17(self):
        from backend.domain.safety.medical_restrictions import VALID_CONDITIONS
        assert "insuficiencia_cardiaca" in VALID_CONDITIONS
        assert "hiperadrenocorticismo_cushing" in VALID_CONDITIONS
        assert "epilepsia" in VALID_CONDITIONS
        assert "megaesofago" in VALID_CONDITIONS
        assert len(VALID_CONDITIONS) == 17

    def test_pet_llm_routing_key_con_4_condiciones(self):
        """4 condiciones → routing key 4 → claude-sonnet (≥3)."""
        from backend.domain.aggregates.pet_profile import (
            MedicalCondition, PetProfile, Species, Sex, Size,
            ReproductiveStatus, DogActivityLevel, CurrentDiet,
        )
        from backend.domain.value_objects.bcs import BCS
        pet = PetProfile(
            pet_id=uuid4(), owner_id=uuid4(),
            name="Rex", species=Species.PERRO, breed="Mestizo",
            sex=Sex.MACHO, age_months=48, weight_kg=20.0, size=Size.MEDIANO,
            reproductive_status=ReproductiveStatus.ESTERILIZADO,
            activity_level=DogActivityLevel.SEDENTARIO,
            bcs=BCS(5),
            medical_conditions=[
                MedicalCondition.INSUFICIENCIA_CARDIACA,
                MedicalCondition.DIABETICO,
                MedicalCondition.RENAL,
                MedicalCondition.CUSHING,
            ],
            allergies=[], current_diet=CurrentDiet.CONCENTRADO,
        )
        assert pet.llm_routing_key() == 4


# ---------------------------------------------------------------------------
# A-03 — Gestación y Lactancia
# ---------------------------------------------------------------------------

class TestReproductiveStatusSpecial:

    def test_gestante_en_enum(self):
        from backend.domain.aggregates.pet_profile import ReproductiveStatus
        assert ReproductiveStatus.GESTANTE.value == "gestante"

    def test_lactante_en_enum(self):
        from backend.domain.aggregates.pet_profile import ReproductiveStatus
        assert ReproductiveStatus.LACTANTE.value == "lactante"

    def test_crear_pet_gestante(self):
        from backend.domain.aggregates.pet_profile import (
            PetProfile, Species, Sex, Size, ReproductiveStatus,
            DogActivityLevel, CurrentDiet,
        )
        from backend.domain.value_objects.bcs import BCS
        pet = PetProfile(
            pet_id=uuid4(), owner_id=uuid4(),
            name="Bella", species=Species.PERRO, breed="Labrador",
            sex=Sex.HEMBRA, age_months=24, weight_kg=28.0, size=Size.GRANDE,
            reproductive_status=ReproductiveStatus.GESTANTE,
            activity_level=DogActivityLevel.SEDENTARIO,
            bcs=BCS(5), medical_conditions=[], allergies=[],
            current_diet=CurrentDiet.MIXTO,
            num_offspring=6, gestation_week=7,
        )
        assert pet.reproductive_status == ReproductiveStatus.GESTANTE
        assert pet.gestation_week == 7
        assert pet.num_offspring == 6

    def test_crear_pet_lactante(self):
        from backend.domain.aggregates.pet_profile import (
            PetProfile, Species, Sex, Size, ReproductiveStatus,
            DogActivityLevel, CurrentDiet,
        )
        from backend.domain.value_objects.bcs import BCS
        pet = PetProfile(
            pet_id=uuid4(), owner_id=uuid4(),
            name="Bella", species=Species.PERRO, breed="Labrador",
            sex=Sex.HEMBRA, age_months=24, weight_kg=26.0, size=Size.GRANDE,
            reproductive_status=ReproductiveStatus.LACTANTE,
            activity_level=DogActivityLevel.SEDENTARIO,
            bcs=BCS(5), medical_conditions=[], allergies=[],
            current_diet=CurrentDiet.MIXTO,
            num_offspring=5,
        )
        assert pet.reproductive_status == ReproductiveStatus.LACTANTE
        assert pet.num_offspring == 5


class TestNRCCalculatorGestacionLactancia:

    def test_gestacion_segunda_mitad_perro(self):
        """Perra gestante semana 6 debe tener DER > 2x RER (factor 3.0 × bcs_modifier)."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(25.0)
        der = NRCCalculator.calculate_der(
            rer=rer,
            age_months=24,
            reproductive_status="gestante",
            activity_level="sedentario",
            species="perro",
            bcs=5,
            gestation_week=6,
        )
        # Factor segunda mitad = 3.0, bcs_modifier BCS5 = 1.0
        expected = rer * 3.0 * 1.0
        assert abs(der - expected) < 1.0, f"DER gestante semana 6: {der} vs esperado {expected}"

    def test_gestacion_primera_mitad_perro(self):
        """Perra gestante semana 2 debe tener factor 1.6."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(25.0)
        der = NRCCalculator.calculate_der(
            rer=rer, age_months=24, reproductive_status="gestante",
            activity_level="sedentario", species="perro", bcs=5, gestation_week=2,
        )
        expected = rer * 1.6
        assert abs(der - expected) < 1.0

    def test_gestacion_semana_desconocida_usa_promedio(self):
        """Semana 0 (desconocida) → factor promedio_seguro = 2.0."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(25.0)
        der = NRCCalculator.calculate_der(
            rer=rer, age_months=24, reproductive_status="gestante",
            activity_level="sedentario", species="perro", bcs=5, gestation_week=0,
        )
        expected = rer * 2.0
        assert abs(der - expected) < 1.0

    def test_lactancia_perro_5_cachorros(self):
        """Perra lactante 5 cachorros: DER = RER × (4.0 + 0.2 × 5) = RER × 5.0"""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(25.0)
        der = NRCCalculator.calculate_der(
            rer=rer, age_months=24, reproductive_status="lactante",
            activity_level="sedentario", species="perro", bcs=5, num_offspring=5,
        )
        expected = rer * 5.0
        assert abs(der - expected) < 1.0

    def test_lactancia_perro_cap_8_cachorros(self):
        """10 cachorros → capped a 8 → factor 4.0 + 0.2 × 8 = 5.6"""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(25.0)
        der_10 = NRCCalculator.calculate_der(
            rer=rer, age_months=24, reproductive_status="lactante",
            activity_level="sedentario", species="perro", bcs=5, num_offspring=10,
        )
        der_8 = NRCCalculator.calculate_der(
            rer=rer, age_months=24, reproductive_status="lactante",
            activity_level="sedentario", species="perro", bcs=5, num_offspring=8,
        )
        assert abs(der_10 - der_8) < 0.1, "Cap de 8 cachorros no funciona"

    def test_lactancia_gata_3_gatitos(self):
        """Gata lactante 3 gatitos: DER = RER × (2.0 + 0.3 × 3) = RER × 2.9"""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(4.0)
        der = NRCCalculator.calculate_der(
            rer=rer, age_months=24, reproductive_status="lactante",
            activity_level="indoor", species="gato", bcs=5, num_offspring=3,
        )
        expected = rer * 2.9
        assert abs(der - expected) < 0.5

    def test_lactancia_mayor_que_adulto_normal(self):
        """DER lactante siempre > DER adulto normal (hipercalórico fisiológico)."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(25.0)
        der_lactante = NRCCalculator.calculate_der(
            rer=rer, age_months=24, reproductive_status="lactante",
            activity_level="sedentario", species="perro", bcs=5, num_offspring=4,
        )
        der_adulto = NRCCalculator.calculate_der(
            rer=rer, age_months=24, reproductive_status="esterilizado",
            activity_level="sedentario", species="perro", bcs=5,
        )
        assert der_lactante > der_adulto * 2, (
            f"DER lactante ({der_lactante:.1f}) no es >2x adulto ({der_adulto:.1f})"
        )

    def test_gestacion_gata_segunda_mitad(self):
        """Gata gestante semana 6 → factor 2.0."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        rer = NRCCalculator.calculate_rer(4.0)
        der = NRCCalculator.calculate_der(
            rer=rer, age_months=24, reproductive_status="gestante",
            activity_level="indoor", species="gato", bcs=5, gestation_week=6,
        )
        expected = rer * 2.0
        assert abs(der - expected) < 0.5


# ---------------------------------------------------------------------------
# A-06 — BCS diferenciado por especie
# ---------------------------------------------------------------------------

class TestIdealWeightBySpecies:

    def test_bcs5_retorna_peso_actual_perro(self):
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        assert NRCCalculator.get_ideal_weight_by_species(10.0, 5, "perro") == 10.0

    def test_bcs5_retorna_peso_actual_gato(self):
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        assert NRCCalculator.get_ideal_weight_by_species(4.0, 5, "gato") == 4.0

    def test_perro_bcs8_peso_ideal_menor(self):
        """BCS 8 en perro → 30% exceso → peso ideal = peso / 1.3"""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        ideal = NRCCalculator.get_ideal_weight_by_species(13.0, 8, "perro")
        expected = 13.0 / 1.3
        assert abs(ideal - expected) < 0.1

    def test_gato_bcs8_usa_400g_por_unidad(self):
        """BCS 8 en gato → 3 unidades sobre 5 → 3 × 400g = 1.2kg menos"""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        ideal = NRCCalculator.get_ideal_weight_by_species(6.2, 8, "gato")
        expected = 6.2 - (3 * 0.4)  # 6.2 - 1.2 = 5.0
        assert abs(ideal - expected) < 0.1

    def test_perro_vs_gato_diferente_logica(self):
        """Perro y gato con mismo peso/BCS deben tener pesos ideales distintos."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        ideal_perro = NRCCalculator.get_ideal_weight_by_species(6.0, 7, "perro")
        ideal_gato = NRCCalculator.get_ideal_weight_by_species(6.0, 7, "gato")
        assert ideal_perro != ideal_gato

    def test_backward_compat_get_ideal_weight_estimate(self):
        """get_ideal_weight_estimate sigue funcionando (backward compat)."""
        from backend.domain.nutrition.nrc_calculator import NRCCalculator
        # Debe usar lógica de perro — mismo resultado que get_ideal_weight_by_species
        old = NRCCalculator.get_ideal_weight_estimate(10.0, 7)
        new = NRCCalculator.get_ideal_weight_by_species(10.0, 7, "perro")
        assert abs(old - new) < 0.01
