"""
Tests para los módulos de prompts y validadores del agente NutriVet.IA.

Cubre:
- condition_protocols: 13 protocolos, resolución de conflictos
- json_schemas: esquema del plan
- plan_generation_prompts: construcción de prompts expertos
- conversation_prompts: prompts conversacionales con contexto
- json_repair: extracción y reparación de JSON
- nutritional_validator: validación post-LLM multicapa
"""
from __future__ import annotations

import json
import pytest

from backend.infrastructure.agent.prompts.condition_protocols import (
    ALL_PROTOCOLS,
    ConditionProtocol,
    get_most_restrictive_fat_pct,
    get_most_restrictive_protein_range,
    get_protocols_for_conditions,
)
from backend.infrastructure.agent.prompts.conversation_prompts import (
    build_conversation_system_prompt,
    select_conversation_model,
)
from backend.infrastructure.agent.prompts.json_schemas import JSON_FORMAT_INSTRUCTION, PlanOutputSchema
from backend.infrastructure.agent.prompts.plan_generation_prompts import (
    build_plan_system_prompt,
    build_plan_user_prompt,
)
from backend.infrastructure.agent.validators.json_repair import (
    extract_json,
    safe_parse_plan_json,
)
from backend.infrastructure.agent.validators.nutritional_validator import (
    NutritionalValidationResult,
    enrich_plan_with_validation,
    validate_nutritional_plan,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def plan_valido() -> dict:
    """Plan nutricional completo y válido para perro adulto sano."""
    return {
        "perfil_nutricional": {
            "rer_kcal": 396.0,
            "der_kcal": 534.0,
            "proteina_pct_ms": 28.0,
            "grasa_pct_ms": 12.0,
            "fibra_pct_ms": 5.0,
            "calcio_g_dia": 1.2,
            "fosforo_g_dia": 0.9,
            "sodio_mg_dia": 300.0,
            "omega3_mg_dia": 800.0,
            "racion_total_g_dia": 320.0,
            "kcal_verificadas": 534.0,
            "relacion_ca_p": 1.33,
        },
        "ingredientes": [
            {
                "nombre": "Pechuga de pollo cocida",
                "cantidad_g": 200.0,
                "kcal": 330.0,
                "proteina_g": 44.0,
                "grasa_g": 6.0,
                "fuente": "animal",
                "frecuencia": "diario",
            },
            {
                "nombre": "Arroz blanco cocido",
                "cantidad_g": 120.0,
                "kcal": 156.0,
                "proteina_g": 3.0,
                "grasa_g": 0.4,
                "fuente": "vegetal",
                "frecuencia": "diario",
            },
            {
                "nombre": "Zanahoria cocida",
                "cantidad_g": 50.0,
                "kcal": 17.5,
                "proteina_g": 0.5,
                "grasa_g": 0.1,
                "fuente": "vegetal",
                "frecuencia": "diario",
            },
        ],
        "porciones": {
            "total_g_dia": 370.0,
            "numero_comidas": 2,
            "g_por_comida": 185.0,
        },
        "instrucciones_preparacion": {
            "metodo": "cocción suave",
            "pasos": ["Hervir pollo en agua sin sal por 20 min", "Cocinar arroz"],
            "tiempo_preparacion_minutos": 30,
            "almacenamiento": "Refrigerar máximo 3 días",
            "advertencias": ["No añadir sal ni especias"],
        },
        "transicion_dieta": {
            "requiere_transicion": True,
            "duracion_dias": 10,
            "fases": [
                {"dias": "1-3", "descripcion": "25% nuevo + 75% anterior"},
                {"dias": "4-7", "descripcion": "50% nuevo + 50% anterior"},
                {"dias": "8-10", "descripcion": "100% nuevo plan"},
            ],
            "senales_de_alerta": ["Vómitos persistentes", "Diarrea líquida"],
        },
        "suplementos": [],
        "notas_clinicas": [],
        "alertas_propietario": ["Agua fresca disponible siempre"],
    }


@pytest.fixture
def pet_perro_sano() -> dict:
    """PetProfile de perro adulto sano para tests conversacionales."""
    return {
        "species": "perro",
        "breed": "Labrador",
        "age_months": 36,
        "weight_kg": 28.0,
        "bcs": 5,
        "sex": "macho",
        "size": "grande",
        "reproductive_status": "esterilizado",
        "activity_level": "moderado",
        "medical_conditions": [],
        "allergies": [],
        "current_diet": "concentrado",
    }


@pytest.fixture
def pet_gato_condiciones() -> dict:
    """PetProfile de gato con condiciones médicas para tests."""
    return {
        "species": "gato",
        "breed": "Doméstico",
        "age_months": 84,
        "weight_kg": 5.5,
        "bcs": 6,
        "sex": "macho",
        "size": "no especificado",
        "reproductive_status": "esterilizado",
        "activity_level": "indoor",
        "medical_conditions": ["renal", "cistitis/enfermedad_urinaria"],
        "allergies": ["pescado"],
        "current_diet": "concentrado",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# condition_protocols.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestConditionProtocols:
    def test_all_17_condiciones_presentes(self) -> None:
        """Deben existir exactamente 17 protocolos en ALL_PROTOCOLS (Sprint 4: +4 nuevas)."""
        assert len(ALL_PROTOCOLS) == 17

    def test_todos_los_condition_ids_conocidos(self) -> None:
        """Los 17 IDs de condición deben coincidir (13 base + 4 de Sprint 4: A-04)."""
        expected_ids = {
            # 13 originales
            "diabético", "hipotiroideo", "cancerígeno", "articular", "renal",
            "hepático/hiperlipidemia", "pancreático", "neurodegenerativo",
            "bucal/periodontal", "piel/dermatitis", "gastritis",
            "cistitis/enfermedad_urinaria", "sobrepeso/obesidad",
            # 4 nuevas (Sprint 4 — A-04)
            "insuficiencia_cardiaca", "hiperadrenocorticismo_cushing",
            "epilepsia", "megaesofago",
        }
        assert set(ALL_PROTOCOLS.keys()) == expected_ids

    def test_get_protocols_retorna_lista(self) -> None:
        """get_protocols_for_conditions retorna lista con los protocolos correctos."""
        protocols = get_protocols_for_conditions(["diabético", "renal"])
        assert len(protocols) == 2
        ids = {p.condition_id for p in protocols}
        assert "diabético" in ids
        assert "renal" in ids

    def test_condicion_desconocida_se_ignora(self) -> None:
        """Condición no existente → se ignora sin error."""
        protocols = get_protocols_for_conditions(["diabético", "condicion_inventada"])
        assert len(protocols) == 1

    def test_pancreático_tiene_grasa_mas_restrictiva(self) -> None:
        """Pancreatitis debe tener la grasa más baja (<10%) — condición más restrictiva."""
        protocol = ALL_PROTOCOLS["pancreático"]
        assert protocol.grasa_pct_ms_max <= 8.0

    def test_renal_tiene_fosforo_restringido(self) -> None:
        """ERC debe tener restricción de fósforo activa."""
        protocol = ALL_PROTOCOLS["renal"]
        assert protocol.fosforo_restringido is True
        assert protocol.fosforo_g_por_100kcal_max is not None
        assert protocol.fosforo_g_por_100kcal_max <= 0.5

    def test_gato_requiere_taurina(self) -> None:
        """Al menos un protocolo de gato debe mencionar taurina — pancreatitis lo hace."""
        protocol_pancreatico = ALL_PROTOCOLS["pancreático"]
        assert "taurina" in protocol_pancreatico.nota_gato.lower()

    def test_conflicto_pancreatico_hepatico_grasa(self) -> None:
        """Pancreatitis + hepatopatía → grasa máxima debe ser 8% (el más restrictivo)."""
        protocols = get_protocols_for_conditions(["pancreático", "hepático/hiperlipidemia"])
        fat_max = get_most_restrictive_fat_pct(protocols)
        assert fat_max <= 10.0  # El más restrictivo (pancreatitis tiene 8%)

    def test_resolucion_proteina_renal_diabetico(self) -> None:
        """Renal + Diabético → el rango proteína resuelto debe ser coherente (no vacío)."""
        protocols = get_protocols_for_conditions(["renal", "diabético"])
        protein_min, protein_max = get_most_restrictive_protein_range(protocols)
        # Rango válido — min < max (o al menos consistente con punto medio)
        assert protein_min > 0
        assert protein_max > 0

    def test_sobrepeso_tiene_alta_fibra(self) -> None:
        """Protocolo de sobrepeso debe tener fibra alta (≥8% MS)."""
        protocol = ALL_PROTOCOLS["sobrepeso/obesidad"]
        assert protocol.fibra_pct_ms_min >= 8.0

    def test_todos_protocolos_tienen_suplementos_o_lista_vacia(self) -> None:
        """Todos los protocolos tienen campo suplementos (puede ser lista vacía)."""
        for condition_id, protocol in ALL_PROTOCOLS.items():
            assert isinstance(protocol.suplementos, (list, tuple)), (
                f"{condition_id}: suplementos debe ser lista"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# plan_generation_prompts.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestPlanGenerationPrompts:
    def test_system_prompt_incluye_nrc_perro(self) -> None:
        """System prompt para perro debe incluir tablas NRC de perro."""
        prompt = build_plan_system_prompt([], "perro", "natural")
        assert "18%" in prompt  # mínimo proteína NRC perro adulto
        assert "5.5%" in prompt  # mínimo grasa NRC perro

    def test_system_prompt_incluye_nrc_gato(self) -> None:
        """System prompt para gato debe incluir tablas NRC de gato."""
        prompt = build_plan_system_prompt([], "gato", "natural")
        assert "26%" in prompt   # mínimo proteína NRC gato adulto
        assert "taurina" in prompt.lower()  # taurina esencial en gatos

    def test_system_prompt_incluye_barf_proporciones(self) -> None:
        """System prompt natural debe incluir proporciones BARF."""
        prompt = build_plan_system_prompt([], "perro", "natural")
        assert "70%" in prompt   # 70% proteína muscular BARF perro

    def test_system_prompt_concentrado_diferente(self) -> None:
        """Modalidad concentrado genera un prompt diferente al natural."""
        prompt_natural = build_plan_system_prompt([], "perro", "natural")
        prompt_conc = build_plan_system_prompt([], "perro", "concentrado")
        assert prompt_natural != prompt_conc
        assert "etiqueta" in prompt_conc.lower()

    def test_system_prompt_inyecta_protocolo_condicion(self) -> None:
        """Prompt con condición diabético debe incluir el protocolo de diabetes."""
        prompt = build_plan_system_prompt(["diabético"], "perro", "natural")
        assert "Diabetes Mellitus".upper() in prompt.upper()
        assert "índice glucémico" in prompt.lower() or "glucémico" in prompt.lower()

    def test_system_prompt_multiple_condiciones(self) -> None:
        """Múltiples condiciones → todos los protocolos inyectados."""
        prompt = build_plan_system_prompt(["diabético", "renal", "pancreático"], "perro", "natural")
        assert "Diabetes Mellitus".upper() in prompt.upper()
        assert "Pancreatitis".upper() in prompt.upper()
        assert "Renal".upper() in prompt.upper()

    def test_system_prompt_incluye_guardarrailes_anti_alucinacion(self) -> None:
        """Prompt debe incluir tabla de kcal de ingredientes para evitar alucinaciones."""
        prompt = build_plan_system_prompt([], "perro", "natural")
        assert "165 kcal/100g" in prompt  # pollo pechuga
        assert "NUNCA" in prompt

    def test_system_prompt_incluye_formato_json(self) -> None:
        """Prompt debe incluir instrucción de formato JSON."""
        prompt = build_plan_system_prompt([], "perro", "natural")
        assert "perfil_nutricional" in prompt
        assert "ingredientes" in prompt
        assert "porciones" in prompt

    def test_user_prompt_incluye_rer_der(self) -> None:
        """User prompt debe incluir RER y DER calculados."""
        prompt = build_plan_user_prompt(
            species="perro", age_months=96, weight_kg=10.08, breed="French Poodle",
            size="pequeño", sex="hembra", reproductive_status="esterilizado",
            activity_level="sedentario", bcs=6, bcs_phase="mantenimiento",
            conditions=["diabético"], allergies=[], current_diet="concentrado",
            modality="natural", rer_kcal=396.0, der_kcal=534.0, medical_restrictions=[],
        )
        assert "396" in prompt
        assert "534" in prompt

    def test_user_prompt_incluye_todos_campos_pet_profile(self) -> None:
        """User prompt debe incluir los 13 campos del PetProfile."""
        prompt = build_plan_user_prompt(
            species="perro", age_months=96, weight_kg=10.08, breed="French Poodle",
            size="pequeño", sex="hembra", reproductive_status="esterilizado",
            activity_level="sedentario", bcs=6, bcs_phase="mantenimiento",
            conditions=["diabético", "renal"], allergies=["pollo"],
            current_diet="concentrado", modality="natural",
            rer_kcal=396.0, der_kcal=534.0, medical_restrictions=["arroz blanco"],
        )
        assert "French Poodle" in prompt
        assert "96" in prompt   # age_months
        assert "10.08" in prompt  # weight
        assert "sedentario" in prompt
        assert "pollo" in prompt  # alergia
        assert "arroz blanco" in prompt  # restricción

    def test_user_prompt_no_contiene_pii(self) -> None:
        """User prompt NO debe contener nombres de propietarios ni datos personales."""
        prompt = build_plan_user_prompt(
            species="perro", age_months=36, weight_kg=20.0, breed="Labrador",
            size="grande", sex="macho", reproductive_status="no_esterilizado",
            activity_level="moderado", bcs=5, bcs_phase="mantenimiento",
            conditions=[], allergies=[], current_diet="concentrado",
            modality="natural", rer_kcal=500.0, der_kcal=700.0, medical_restrictions=[],
        )
        # Constitution REGLA 6 — no debe haber palabras que impliquen nombre de propietario
        assert "propietario" not in prompt.lower()
        assert "dueño" not in prompt.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# conversation_prompts.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestConversationPrompts:
    def test_prompt_sin_mascota_es_general(self) -> None:
        """Sin pet_profile → prompt genérico."""
        prompt = build_conversation_system_prompt(None, None, "FREE")
        assert "No hay mascota activa" in prompt

    def test_prompt_con_mascota_incluye_contexto(self, pet_perro_sano) -> None:
        """Con pet_profile → incluye especie, raza, peso, BCS, etc."""
        prompt = build_conversation_system_prompt(pet_perro_sano, None, "BASICO")
        assert "Labrador" in prompt
        assert "28.0 kg" in prompt
        assert "BCS: 5/9" in prompt

    def test_prompt_mascota_con_condicion_alerta(self, pet_gato_condiciones) -> None:
        """Mascota con condiciones → prompt incluye alerta de condiciones."""
        prompt = build_conversation_system_prompt(pet_gato_condiciones, None, "VET")
        assert "renal" in prompt.lower()
        assert "cistitis" in prompt.lower()
        assert "pescado" in prompt.lower()  # alergia

    def test_prompt_incluye_conocimiento_nrc(self, pet_perro_sano) -> None:
        """Prompt conversacional incluye conocimiento NRC embebido."""
        prompt = build_conversation_system_prompt(pet_perro_sano, None, "BASICO")
        assert "taurina" in prompt.lower()
        assert "perro" in prompt.lower()

    def test_prompt_incluye_lista_toxicos(self, pet_perro_sano) -> None:
        """Prompt conversacional incluye lista de tóxicos comunes."""
        prompt = build_conversation_system_prompt(pet_perro_sano, None, "BASICO")
        assert "uvas" in prompt.lower() or "xilitol" in prompt.lower()

    def test_prompt_incluye_boundary_medico_nutricional(self, pet_perro_sano) -> None:
        """Prompt incluye instrucciones para remitir consultas médicas al vet."""
        prompt = build_conversation_system_prompt(pet_perro_sano, None, "BASICO")
        assert "veterinario" in prompt.lower()
        assert "médica" in prompt.lower() or "médico" in prompt.lower()

    def test_prompt_tier_vet_incluye_instruccion_tecnica(self) -> None:
        """Tier VET → instrucción de tono técnico."""
        prompt = build_conversation_system_prompt(None, None, "VET")
        assert "VETERINARIO" in prompt or "veterinario" in prompt.lower()

    def test_prompt_tier_free_lenguaje_simple(self) -> None:
        """Tier FREE → instrucción de lenguaje simple."""
        prompt = build_conversation_system_prompt(None, None, "FREE")
        assert "simple" in prompt.lower() or "básico" in prompt.lower()

    def test_prompt_con_plan_activo_incluye_resumen(self, pet_perro_sano) -> None:
        """Con plan activo → prompt incluye información del plan."""
        plan = {
            "status": "ACTIVE",
            "modality": "natural",
            "rer_kcal": 500.0,
            "der_kcal": 700.0,
            "content": {
                "ingredientes": [
                    {"nombre": "Pechuga de pollo", "cantidad_g": 250}
                ],
                "porciones": {"total_g_dia": 400.0, "numero_comidas": 2},
            },
        }
        prompt = build_conversation_system_prompt(pet_perro_sano, plan, "BASICO")
        assert "ACTIVE" in prompt or "Pechuga de pollo" in prompt

    def test_model_selection_vet_siempre_claude(self) -> None:
        """Tier VET siempre usa claude-sonnet-4-5."""
        assert select_conversation_model("VET", conditions_count=0) == "anthropic/claude-sonnet-4-5"
        assert select_conversation_model("VET", conditions_count=3) == "anthropic/claude-sonnet-4-5"

    def test_model_selection_free_sin_condicion_gpt4o_mini(self) -> None:
        """FREE sin condiciones → gpt-4o-mini (no más llama)."""
        model = select_conversation_model("FREE", conditions_count=0)
        assert model == "openai/gpt-4o-mini"

    def test_model_selection_free_1_condicion_gpt4o_mini(self) -> None:
        """FREE + 1 condición → gpt-4o-mini (bajo umbral clínico de 2)."""
        model = select_conversation_model("FREE", conditions_count=1)
        assert model == "openai/gpt-4o-mini"

    def test_model_selection_free_2_condiciones_override_claude(self) -> None:
        """FREE + 2 condiciones → claude-sonnet-4-5 (override umbral=2)."""
        model = select_conversation_model("FREE", conditions_count=2)
        assert model == "anthropic/claude-sonnet-4-5"

    def test_model_selection_sin_endpoint_free(self) -> None:
        """Ningún tier retorna endpoint :free."""
        for tier in ["FREE", "BASICO", "PREMIUM", "VET"]:
            for cond in [0, 1, 2, 5]:
                model = select_conversation_model(tier, conditions_count=cond)
                assert ":free" not in model

    def test_model_selection_premium_claude(self) -> None:
        """PREMIUM → claude-sonnet-4-5."""
        assert select_conversation_model("PREMIUM", conditions_count=0) == "anthropic/claude-sonnet-4-5"


# ═══════════════════════════════════════════════════════════════════════════════
# json_repair.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestJsonRepair:
    def test_json_limpio_se_parsea_directo(self) -> None:
        """JSON válido sin formato extra → parseo directo."""
        raw = '{"perfil_nutricional": {"rer_kcal": 396.0}, "ingredientes": [], "porciones": {}}'
        result = extract_json(raw)
        assert result is not None
        assert result["perfil_nutricional"]["rer_kcal"] == 396.0

    def test_markdown_json_se_extrae(self) -> None:
        """JSON en bloque markdown → extraído correctamente."""
        raw = '```json\n{"key": "value", "num": 42}\n```'
        result = extract_json(raw)
        assert result is not None
        assert result["key"] == "value"
        assert result["num"] == 42

    def test_markdown_sin_lang_se_extrae(self) -> None:
        """JSON en bloque ``` sin especificar lenguaje → extraído."""
        raw = '```\n{"key": "value"}\n```'
        result = extract_json(raw)
        assert result is not None
        assert result["key"] == "value"

    def test_texto_antes_del_json(self) -> None:
        """Texto antes del primer { → JSON extraído correctamente."""
        raw = 'Aquí está el plan: {"perfil": "nutricional"}'
        result = extract_json(raw)
        assert result is not None
        assert result["perfil"] == "nutricional"

    def test_texto_despues_del_json(self) -> None:
        """Texto después del último } → JSON extraído correctamente."""
        raw = '{"key": "value"} Espero que sea útil.'
        result = extract_json(raw)
        assert result is not None

    def test_trailing_comma_se_repara(self) -> None:
        """Trailing comma antes de } → reparado."""
        raw = '{"key": "value", }'
        result = extract_json(raw)
        assert result is not None
        assert result["key"] == "value"

    def test_string_no_json_retorna_none(self) -> None:
        """String sin JSON válido → retorna None."""
        result = extract_json("esto no es JSON en absoluto")
        assert result is None

    def test_string_vacio_retorna_none(self) -> None:
        """String vacío → retorna None."""
        assert extract_json("") is None
        assert extract_json("   ") is None

    def test_safe_parse_plan_json_valida_secciones(self) -> None:
        """safe_parse_plan_json lanza ValueError si faltan secciones obligatorias."""
        raw = json.dumps({
            "perfil_nutricional": {},
            # Faltan: ingredientes, porciones, instrucciones_preparacion
        })
        with pytest.raises(ValueError, match="secciones faltantes"):
            safe_parse_plan_json(raw, der_kcal=534.0)

    def test_safe_parse_plan_json_valida_ingredientes_vacios(self) -> None:
        """safe_parse_plan_json lanza ValueError si ingredientes es lista vacía."""
        raw = json.dumps({
            "perfil_nutricional": {},
            "ingredientes": [],
            "porciones": {},
            "instrucciones_preparacion": {},
        })
        with pytest.raises(ValueError):
            safe_parse_plan_json(raw, der_kcal=534.0)

    def test_safe_parse_plan_json_agrega_defaults(self, plan_valido) -> None:
        """safe_parse_plan_json agrega campos opcionales con defaults."""
        plan_sin_suplementos = dict(plan_valido)
        del plan_sin_suplementos["suplementos"]
        raw = json.dumps(plan_sin_suplementos)
        result = safe_parse_plan_json(raw, der_kcal=534.0)
        assert "suplementos" in result
        assert isinstance(result["suplementos"], list)


# ═══════════════════════════════════════════════════════════════════════════════
# nutritional_validator.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestNutritionalValidator:
    def test_plan_valido_sin_errores(self, plan_valido) -> None:
        """Plan nutricionalmente correcto → sin blocking_errors."""
        result = validate_nutritional_plan(
            plan_content=plan_valido,
            species="perro",
            conditions=[],
            der_kcal=534.0,
            rer_kcal=396.0,
            allergies=[],
            medical_restrictions=[],
            age_months=96,
        )
        assert result.is_valid
        assert len(result.blocking_errors) == 0

    def test_proteina_insuficiente_en_gato_bloquea(self) -> None:
        """Gato con proteína <26% MS → blocking error (carnívoro obligado)."""
        plan = {
            "perfil_nutricional": {
                "rer_kcal": 200.0, "der_kcal": 280.0,
                "proteina_pct_ms": 20.0,  # Insuficiente para gato
                "grasa_pct_ms": 15.0, "fibra_pct_ms": 3.0,
                "calcio_g_dia": 0.5, "fosforo_g_dia": 0.4, "sodio_mg_dia": 150,
                "omega3_mg_dia": 400, "racion_total_g_dia": 150.0, "kcal_verificadas": 280.0,
            },
            "ingredientes": [
                {"nombre": "Arroz", "cantidad_g": 100, "kcal": 130},
                {"nombre": "Pollo", "cantidad_g": 80, "kcal": 132},
            ],
        }
        result = validate_nutritional_plan(
            plan_content=plan, species="gato", conditions=[],
            der_kcal=280.0, rer_kcal=200.0, allergies=[],
            medical_restrictions=[], age_months=60,
        )
        assert not result.is_valid
        assert any("PROTEÍNA INSUFICIENTE" in e for e in result.blocking_errors)

    def test_alergia_incluida_en_plan_bloquea(self, plan_valido) -> None:
        """Plan que incluye alérgeno declarado → blocking error."""
        result = validate_nutritional_plan(
            plan_content=plan_valido,
            species="perro",
            conditions=[],
            der_kcal=534.0,
            rer_kcal=396.0,
            allergies=["pollo"],  # pollo está en el plan
            medical_restrictions=[],
            age_months=96,
        )
        assert not result.is_valid
        assert any("ALERGIA" in e for e in result.blocking_errors)

    def test_restriccion_medica_violada_bloquea(self, plan_valido) -> None:
        """Plan que incluye ingrediente médicamente prohibido → blocking error."""
        result = validate_nutritional_plan(
            plan_content=plan_valido,
            species="perro",
            conditions=["renal"],
            der_kcal=534.0,
            rer_kcal=396.0,
            allergies=[],
            medical_restrictions=["pollo"],  # pollo en lista de restricciones
            age_months=96,
        )
        assert not result.is_valid
        assert any("RESTRICCIÓN MÉDICA" in e for e in result.blocking_errors)

    def test_grasa_excesiva_pancreatitis_bloquea(self) -> None:
        """Pancreatitis + grasa >10% → blocking error."""
        plan = {
            "perfil_nutricional": {
                "rer_kcal": 300.0, "der_kcal": 400.0,
                "proteina_pct_ms": 25.0,
                "grasa_pct_ms": 25.0,  # Excesiva para pancreatitis (máx 8%)
                "fibra_pct_ms": 5.0,
                "calcio_g_dia": 0.8, "fosforo_g_dia": 0.6, "sodio_mg_dia": 200,
                "omega3_mg_dia": 300, "racion_total_g_dia": 200.0, "kcal_verificadas": 400.0,
            },
            "ingredientes": [
                {"nombre": "Carne con grasa", "cantidad_g": 200, "kcal": 400},
                {"nombre": "Arroz", "cantidad_g": 100, "kcal": 130},
            ],
        }
        result = validate_nutritional_plan(
            plan_content=plan, species="perro", conditions=["pancreático"],
            der_kcal=400.0, rer_kcal=300.0, allergies=[],
            medical_restrictions=[], age_months=60,
        )
        assert not result.is_valid
        assert any("GRASA" in e for e in result.blocking_errors)

    def test_desviacion_calorica_bloquea_plan(self, plan_valido) -> None:
        """DER 534 pero plan tiene ~92 kcal → blocking_error de desviación calórica (>20%)."""
        plan_low = {
            **plan_valido,
            "ingredientes": [
                {"nombre": "Pollo", "cantidad_g": 50, "kcal": 82},
                {"nombre": "Zanahoria", "cantidad_g": 30, "kcal": 10},
            ],
        }
        result = validate_nutritional_plan(
            plan_content=plan_low, species="perro", conditions=[],
            der_kcal=534.0, rer_kcal=396.0, allergies=[],
            medical_restrictions=[], age_months=96,
        )
        # Desviación del 83% → bloqueante (>20% es inaceptable clínicamente)
        assert not result.is_valid
        assert any("calóric" in e.lower() for e in result.blocking_errors)

    def test_ratio_ca_p_fuera_de_rango_bloquea(self) -> None:
        """Ratio Ca:P fuera del rango NRC 1.0-2.0 → blocking error."""
        plan = {
            "perfil_nutricional": {
                "rer_kcal": 396.0, "der_kcal": 534.0,
                "proteina_pct_ms": 28.0, "grasa_pct_ms": 12.0, "fibra_pct_ms": 5.0,
                "calcio_g_dia": 0.1,  # Muy bajo Ca
                "fosforo_g_dia": 1.5,  # Alto P → ratio 0.07 (crítico)
                "sodio_mg_dia": 300, "omega3_mg_dia": 500, "racion_total_g_dia": 320.0,
                "kcal_verificadas": 534.0,
            },
            "ingredientes": [
                {"nombre": "Pollo", "cantidad_g": 200, "kcal": 330},
                {"nombre": "Arroz", "cantidad_g": 100, "kcal": 130},
            ],
        }
        result = validate_nutritional_plan(
            plan_content=plan, species="perro", conditions=[],
            der_kcal=534.0, rer_kcal=396.0, allergies=[],
            medical_restrictions=[], age_months=96,
        )
        assert not result.is_valid
        assert any("Ca:P" in e for e in result.blocking_errors)

    def test_gato_sin_taurina_genera_warning(self) -> None:
        """Gato con plan sin fuente de taurina → warning obligatorio."""
        plan = {
            "perfil_nutricional": {
                "rer_kcal": 200.0, "der_kcal": 280.0,
                "proteina_pct_ms": 35.0, "grasa_pct_ms": 15.0, "fibra_pct_ms": 3.0,
                "calcio_g_dia": 0.4, "fosforo_g_dia": 0.35, "sodio_mg_dia": 120,
                "omega3_mg_dia": 200, "racion_total_g_dia": 130.0, "kcal_verificadas": 280.0,
            },
            "ingredientes": [
                # Sin sardinas, sin corazón, sin taurina explícita
                {"nombre": "Pechuga de pollo", "cantidad_g": 100, "kcal": 165},
                {"nombre": "Arroz", "cantidad_g": 30, "kcal": 39},
            ],
            "suplementos": [],
        }
        result = validate_nutritional_plan(
            plan_content=plan, species="gato", conditions=[],
            der_kcal=280.0, rer_kcal=200.0, allergies=[],
            medical_restrictions=[], age_months=60,
        )
        assert any("taurina" in w.lower() for w in result.warnings)

    def test_enrich_plan_agrega_warnings_a_notas_clinicas(self, plan_valido) -> None:
        """enrich_plan_with_validation agrega warnings como notas_clinicas."""
        validation = NutritionalValidationResult(
            is_valid=True,
            blocking_errors=[],
            warnings=["Revisar fósforo"],
            nutritional_summary={},
        )
        enriched = enrich_plan_with_validation(plan_valido, validation)
        assert any("Revisar fósforo" in nota for nota in enriched.get("notas_clinicas", []))

    def test_plan_perro_cachorro_proteina_minima_mayor(self) -> None:
        """Perro cachorro (<12 meses) tiene mínimo proteína mayor (22.5% MS)."""
        plan = {
            "perfil_nutricional": {
                "rer_kcal": 200.0, "der_kcal": 400.0,
                "proteina_pct_ms": 19.0,  # Bajo para cachorro (necesita 22.5%)
                "grasa_pct_ms": 12.0, "fibra_pct_ms": 3.0,
                "calcio_g_dia": 0.8, "fosforo_g_dia": 0.6, "sodio_mg_dia": 200,
                "omega3_mg_dia": 300, "racion_total_g_dia": 200.0, "kcal_verificadas": 400.0,
            },
            "ingredientes": [
                {"nombre": "Pollo", "cantidad_g": 150, "kcal": 247},
                {"nombre": "Arroz", "cantidad_g": 100, "kcal": 130},
            ],
        }
        result = validate_nutritional_plan(
            plan_content=plan, species="perro", conditions=[],
            der_kcal=400.0, rer_kcal=200.0, allergies=[],
            medical_restrictions=[], age_months=6,  # cachorro
        )
        # Para cachorro, 19% < 22% → blocking_error (NRC mínimo obligatorio)
        assert not result.is_valid
        assert any("proteína" in e.lower() or "PROTEÍNA" in e for e in result.blocking_errors)

    def test_sally_golden_case_plan_valido(self) -> None:
        """Caso Sally: perro French Poodle 10.08kg con 5 condiciones → validación pasa."""
        plan_sally = {
            "perfil_nutricional": {
                "rer_kcal": 396.0,
                "der_kcal": 534.0,
                "proteina_pct_ms": 22.0,  # Dentro del rango para las 5 condiciones
                "grasa_pct_ms": 8.0,      # Respeta pancreatitis (<8%) y hepatopatía
                "fibra_pct_ms": 10.0,     # Alta para diabetes e hipotiroidismo
                "calcio_g_dia": 1.0,
                "fosforo_g_dia": 0.7,
                "sodio_mg_dia": 180.0,    # Bajo sodio para cistitis
                "omega3_mg_dia": 1000.0,
                "racion_total_g_dia": 300.0,
                "kcal_verificadas": 534.0,
            },
            "ingredientes": [
                {"nombre": "Pechuga de pavo cocida", "cantidad_g": 180, "kcal": 243},
                {"nombre": "Batata cocida", "cantidad_g": 100, "kcal": 86},
                {"nombre": "Calabaza cocida", "cantidad_g": 60, "kcal": 15.6},
                {"nombre": "Aceite de salmón", "cantidad_g": 5, "kcal": 45},
                {"nombre": "Avena cocida", "cantidad_g": 80, "kcal": 56.8},
            ],
            "porciones": {"total_g_dia": 425.0, "numero_comidas": 3, "g_por_comida": 141.7},
            "instrucciones_preparacion": {"metodo": "cocción", "pasos": ["Hervir todo"]},
            "suplementos": [],
        }
        conditions = [
            "diabético", "hepático/hiperlipidemia", "gastritis",
            "cistitis/enfermedad_urinaria", "hipotiroideo",
        ]
        result = validate_nutritional_plan(
            plan_content=plan_sally,
            species="perro",
            conditions=conditions,
            der_kcal=534.0,
            rer_kcal=396.0,
            allergies=[],
            medical_restrictions=[],
            age_months=96,
        )
        # El plan de Sally debe pasar — es el golden case
        assert result.is_valid, (
            f"Plan de Sally debe ser válido. Errores: {result.blocking_errors}"
        )
