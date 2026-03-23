"""
Tests Sprint 2 — NutriVet.IA
Cubre: A-02 (micronutrientes), A-05 (Ca:P validator), A-07 (PerfilNutricional),
       A-08 (breed restrictions en load_context)
"""
import pytest


# ---------------------------------------------------------------------------
# A-02 — Micronutrientes en AnimalProtein y PlantFood
# ---------------------------------------------------------------------------

class TestAnimalProteinMicronutrients:

    def test_animal_protein_has_tiaminasa_field(self):
        from backend.domain.nutrition.food_database import AnimalProtein
        ap = AnimalProtein(
            nombre="Test",
            aliases=[],
            kcal=100.0,
            proteina_g=20.0,
            grasa_g=5.0,
            carbohidratos_g=0.0,
            calcio_mg=10.0,
            fosforo_mg=200.0,
            zinc_mg=1.0,
            hierro_mg=1.0,
            taurina_mg=50.0,
            omega3_epa_dha_mg=100.0,
        )
        assert hasattr(ap, "tiene_tiaminasa")
        assert ap.tiene_tiaminasa is False  # Default

    def test_animal_protein_has_micronutrient_fields(self):
        from backend.domain.nutrition.food_database import AnimalProtein
        ap = AnimalProtein(
            nombre="Test",
            aliases=[],
            kcal=100.0,
            proteina_g=20.0,
            grasa_g=5.0,
            carbohidratos_g=0.0,
            calcio_mg=10.0,
            fosforo_mg=200.0,
            zinc_mg=1.0,
            hierro_mg=1.0,
            taurina_mg=50.0,
            omega3_epa_dha_mg=100.0,
        )
        for field in ("humedad_pct", "estado", "magnesio_mg", "potasio_mg",
                      "cobre_mg", "vitamina_d3_ui", "vitamina_a_ui",
                      "tiamina_b1_mg", "yodo_mcg", "selenio_mcg"):
            assert hasattr(ap, field), f"Falta campo {field} en AnimalProtein"

    def test_salmon_has_tiaminasa_true(self):
        from backend.domain.nutrition.food_database import PROTEINAS_ANIMALES
        salmon = next(p for p in PROTEINAS_ANIMALES if "Salmón" in p.nombre)
        assert salmon.tiene_tiaminasa is True

    def test_tilapia_has_tiaminasa_true(self):
        from backend.domain.nutrition.food_database import PROTEINAS_ANIMALES
        tilapia = next(p for p in PROTEINAS_ANIMALES if p.nombre == "Tilapia")
        assert tilapia.tiene_tiaminasa is True

    def test_trucha_has_tiaminasa_true(self):
        from backend.domain.nutrition.food_database import PROTEINAS_ANIMALES
        trucha = next(p for p in PROTEINAS_ANIMALES if p.nombre == "Trucha")
        assert trucha.tiene_tiaminasa is True

    def test_sardina_enlatada_has_tiaminasa_false(self):
        """Sardina enlatada está cocida — tiaminasa destruida."""
        from backend.domain.nutrition.food_database import PROTEINAS_ANIMALES
        sardina = next(p for p in PROTEINAS_ANIMALES if "Sardina" in p.nombre)
        assert sardina.tiene_tiaminasa is False

    def test_pechuga_pollo_has_tiaminasa_false(self):
        from backend.domain.nutrition.food_database import PROTEINAS_ANIMALES
        pollo = next(p for p in PROTEINAS_ANIMALES if "Pechuga de pollo sin" in p.nombre)
        assert pollo.tiene_tiaminasa is False

    def test_plant_food_has_new_fields(self):
        from backend.domain.nutrition.food_database import PlantFood
        pf = PlantFood(
            nombre="Test vegetal",
            aliases=[],
            estado="crudo",
            kcal=50.0,
            proteina_g=2.0,
            carbohidratos_g=10.0,
            fibra_g=3.0,
            calcio_mg=20.0,
            fosforo_mg=40.0,
            indice_glucemico=None,
        )
        assert hasattr(pf, "magnesio_mg")
        assert hasattr(pf, "potasio_mg")
        assert hasattr(pf, "humedad_pct")
        assert pf.magnesio_mg == 0.0
        assert pf.potasio_mg == 0.0


# ---------------------------------------------------------------------------
# A-05 — Ca:P Validator
# ---------------------------------------------------------------------------

class TestCaPValidator:

    def test_adult_ratio_within_range_approved(self):
        from backend.domain.nutrition.ca_p_validator import validate_ca_p_ratio
        result = validate_ca_p_ratio(calcio_g=1.2, fosforo_g=0.9, contexto="adulto")
        assert result.aprobado is True
        assert result.es_bloqueante is False
        assert pytest.approx(result.ratio_actual, abs=0.01) == 1.333

    def test_ratio_below_0_8_always_bloqueante(self):
        from backend.domain.nutrition.ca_p_validator import validate_ca_p_ratio
        result = validate_ca_p_ratio(calcio_g=0.5, fosforo_g=1.0, contexto="adulto")
        assert result.aprobado is False
        assert result.es_bloqueante is True
        assert "hipocalcemia" in result.mensaje.lower()

    def test_giant_breed_puppy_tight_range(self):
        from backend.domain.nutrition.ca_p_validator import validate_ca_p_ratio
        # Ratio 2.1 — fuera del rango 1.2-1.8 para raza gigante → bloqueante
        result = validate_ca_p_ratio(calcio_g=2.1, fosforo_g=1.0, contexto="cachorro_raza_gigante")
        assert result.aprobado is False
        assert result.es_bloqueante is True

    def test_giant_breed_puppy_within_range(self):
        from backend.domain.nutrition.ca_p_validator import validate_ca_p_ratio
        result = validate_ca_p_ratio(calcio_g=1.5, fosforo_g=1.0, contexto="cachorro_raza_gigante")
        assert result.aprobado is True

    def test_fosforo_zero_returns_not_bloqueante(self):
        from backend.domain.nutrition.ca_p_validator import validate_ca_p_ratio
        result = validate_ca_p_ratio(calcio_g=1.0, fosforo_g=0.0, contexto="adulto")
        assert result.aprobado is False
        assert result.es_bloqueante is False  # No hay datos — no bloqueamos aún
        assert result.ratio_actual is None

    def test_renal_context_has_higher_ratio(self):
        from backend.domain.nutrition.ca_p_validator import CA_P_RATIOS
        min_renal, _ = CA_P_RATIOS["renal"]
        min_adulto, _ = CA_P_RATIOS["adulto"]
        assert min_renal > min_adulto  # Renal requiere más calcio relativo

    def test_gestante_context_available(self):
        from backend.domain.nutrition.ca_p_validator import validate_ca_p_ratio
        result = validate_ca_p_ratio(calcio_g=1.5, fosforo_g=1.0, contexto="gestante")
        assert result.aprobado is True

    def test_lactante_context_available(self):
        from backend.domain.nutrition.ca_p_validator import validate_ca_p_ratio
        result = validate_ca_p_ratio(calcio_g=1.5, fosforo_g=1.0, contexto="lactante")
        assert result.aprobado is True

    def test_get_ca_p_context_giant_puppy(self):
        from backend.domain.nutrition.ca_p_validator import get_ca_p_context
        ctx = get_ca_p_context(age_months=6, species="perro", is_giant_breed=True)
        assert ctx == "cachorro_raza_gigante"

    def test_get_ca_p_context_regular_puppy(self):
        from backend.domain.nutrition.ca_p_validator import get_ca_p_context
        ctx = get_ca_p_context(age_months=6, species="perro", is_giant_breed=False)
        assert ctx == "cachorro"

    def test_get_ca_p_context_adult_dog(self):
        from backend.domain.nutrition.ca_p_validator import get_ca_p_context
        ctx = get_ca_p_context(age_months=36, species="perro")
        assert ctx == "adulto"

    def test_get_ca_p_context_renal_overrides_age(self):
        from backend.domain.nutrition.ca_p_validator import get_ca_p_context
        ctx = get_ca_p_context(
            age_months=36,
            species="perro",
            medical_conditions=["renal"],
        )
        assert ctx == "renal"

    def test_get_ca_p_context_gestante(self):
        from backend.domain.nutrition.ca_p_validator import get_ca_p_context
        ctx = get_ca_p_context(
            age_months=24,
            species="perro",
            reproductive_status="gestante",
        )
        assert ctx == "gestante"

    def test_get_ca_p_context_senior_dog(self):
        from backend.domain.nutrition.ca_p_validator import get_ca_p_context
        ctx = get_ca_p_context(age_months=90, species="perro")
        assert ctx == "senior"

    def test_result_is_frozen_dataclass(self):
        from backend.domain.nutrition.ca_p_validator import validate_ca_p_ratio
        result = validate_ca_p_ratio(1.2, 0.9)
        with pytest.raises((AttributeError, TypeError)):
            result.aprobado = True  # type: ignore


# ---------------------------------------------------------------------------
# A-07 — PerfilNutricionalSchema con campos de composición corporal
# ---------------------------------------------------------------------------

class TestPerfilNutricionalSchemaA07:

    def test_schema_accepts_body_composition_fields(self):
        from backend.infrastructure.agent.prompts.json_schemas import PerfilNutricionalSchema
        perfil = PerfilNutricionalSchema(
            rer_kcal=396.0,
            der_kcal=534.0,
            proteina_pct_ms=35.0,
            grasa_pct_ms=20.0,
            racion_total_g_dia=300.0,
            kcal_verificadas=534.0,
            peso_actual_kg=10.08,
            peso_ideal_estimado_kg=9.5,
            bcs_actual=6,
            fase="mantenimiento",
            meta_peso="mantener peso actual",
        )
        assert perfil.peso_actual_kg == pytest.approx(10.08)
        assert perfil.peso_ideal_estimado_kg == pytest.approx(9.5)
        assert perfil.bcs_actual == 6
        assert perfil.fase == "mantenimiento"

    def test_schema_body_fields_optional(self):
        """Campos de composición corporal son opcionales — backward compat."""
        from backend.infrastructure.agent.prompts.json_schemas import PerfilNutricionalSchema
        perfil = PerfilNutricionalSchema(
            rer_kcal=396.0,
            der_kcal=534.0,
            proteina_pct_ms=35.0,
            grasa_pct_ms=20.0,
            racion_total_g_dia=300.0,
            kcal_verificadas=534.0,
        )
        assert perfil.peso_actual_kg is None
        assert perfil.bcs_actual is None
        assert perfil.fase is None

    def test_transicion_schema_accepts_up_to_42_days(self):
        """Megaesofago puede necesitar hasta 42 días de transición."""
        from backend.infrastructure.agent.prompts.json_schemas import TransicionSchema
        t = TransicionSchema(requiere_transicion=True, duracion_dias=42)
        assert t.duracion_dias == 42

    def test_transicion_schema_rejects_above_42(self):
        from pydantic import ValidationError
        from backend.infrastructure.agent.prompts.json_schemas import TransicionSchema
        with pytest.raises(ValidationError):
            TransicionSchema(requiere_transicion=True, duracion_dias=43)

    def test_bcs_must_be_between_1_and_9(self):
        from pydantic import ValidationError
        from backend.infrastructure.agent.prompts.json_schemas import PerfilNutricionalSchema
        with pytest.raises(ValidationError):
            PerfilNutricionalSchema(
                rer_kcal=396.0,
                der_kcal=534.0,
                proteina_pct_ms=35.0,
                grasa_pct_ms=20.0,
                racion_total_g_dia=300.0,
                kcal_verificadas=534.0,
                bcs_actual=10,  # Inválido
            )


# ---------------------------------------------------------------------------
# A-08 — Breed restrictions en load_context._pet_to_dict
# ---------------------------------------------------------------------------

class TestLoadContextBreedRestrictions:

    def _make_mock_pet(self, breed_id=None, conditions=None):
        """Crea un mock de PetProfile compatible con _pet_to_dict."""
        from unittest.mock import MagicMock
        import uuid

        pet = MagicMock()
        pet.pet_id = uuid.uuid4()
        pet.owner_id = uuid.uuid4()
        pet.species.value = "perro"
        pet.weight_kg = 25.0
        pet.age_months = 36
        pet.reproductive_status.value = "esterilizado"
        pet.activity_level.value = "moderado"
        pet.bcs.value = 5
        pet.medical_conditions = []
        pet.allergies = []
        pet.breed_id = breed_id
        return pet

    def test_pet_without_breed_has_no_breed_restrictions(self):
        from backend.infrastructure.agent.nodes.load_context import _pet_to_dict
        pet = self._make_mock_pet(breed_id=None)
        result = _pet_to_dict(pet)
        assert result["breed_id"] is None
        assert "breed_preventive_restrictions" not in result

    def test_pet_with_dalmata_has_breed_restrictions(self):
        from backend.infrastructure.agent.nodes.load_context import _pet_to_dict
        pet = self._make_mock_pet(breed_id="dalmata")
        result = _pet_to_dict(pet)
        assert result["breed_id"] == "dalmata"
        assert "breed_preventive_restrictions" in result
        r = result["breed_preventive_restrictions"]
        assert "hígado" in r["prohibited_preventive"]
        assert isinstance(r["alert"], str)

    def test_pet_with_gran_danes_has_gdv_rules(self):
        from backend.infrastructure.agent.nodes.load_context import _pet_to_dict
        pet = self._make_mock_pet(breed_id="gran_danes")
        result = _pet_to_dict(pet)
        r = result["breed_preventive_restrictions"]
        assert "sin_ejercicio_2h_post_comida" in r["special_preventive"]

    def test_pet_with_unknown_breed_no_restrictions(self):
        from backend.infrastructure.agent.nodes.load_context import _pet_to_dict
        pet = self._make_mock_pet(breed_id="raza_sin_restricciones_xyz")
        result = _pet_to_dict(pet)
        assert result["breed_id"] == "raza_sin_restricciones_xyz"
        assert "breed_preventive_restrictions" not in result

    def test_breed_id_always_present_in_dict(self):
        from backend.infrastructure.agent.nodes.load_context import _pet_to_dict
        pet = self._make_mock_pet(breed_id="labrador_retriever")
        result = _pet_to_dict(pet)
        assert "breed_id" in result
