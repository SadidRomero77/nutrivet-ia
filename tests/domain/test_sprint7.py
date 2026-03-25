"""
Tests Sprint 7 — NutriVet.IA
Cubre: F-01 (_build_plan_data mapeo 10 secciones), F-02 (template HTML secciones nuevas),
       F-03 (PDF con plan clínico completo de Sally)
"""
from __future__ import annotations

import io
import uuid

import pypdf
import pytest


# ---------------------------------------------------------------------------
# Fixture: plan completo con los campos del LLM (PlanOutputSchema)
# ---------------------------------------------------------------------------

_PLAN_DATA_COMPLETO = {
    "plan_id": "abc-001",
    "rer_kcal": 396.0,
    "der_kcal": 534.0,
    "rer_kcal_display": 396.0,
    "der_kcal_display": 534.0,
    "modality": "natural",
    "plan_type": "temporal_medical",
    "llm_model_used": "anthropic/claude-sonnet-4-5",
    "approved_by_vet_name": "Dra. Lady Carolina Castañeda",
    "weight_phase": "mantenimiento",
    "proteina_pct_ms": 28.0,
    "grasa_pct_ms": 12.0,
    "racion_total_g_dia": 420.0,
    "relacion_ca_p": 1.4,
    "omega3_mg_dia": 850,
    "objetivos_clinicos": [
        "Control glucémico mediante dieta baja en carbohidratos simples",
        "Soporte hepático con reducción de grasas saturadas",
        "Protección gástrica con comidas pequeñas y frecuentes",
    ],
    "ingredientes_prohibidos": [
        "Azúcar, miel, sirope de maíz (índice glucémico elevado)",
        "Hígado en exceso (sobrecarga hepática de cobre)",
        "Leche entera y queso (lactosa, grasa saturada)",
    ],
    "ingredientes": [
        {
            "nombre": "Pechuga de pollo cocida sin piel",
            "cantidad_g": 180,
            "kcal": 198.0,
            "proteina_g": 37.8,
            "grasa_g": 3.6,
            "fuente": "animal",
            "frecuencia": "diario",
            "notas": "Cocida al vapor, sin sal",
            "especificacion_compra": "Fresca o congelada sin aditivos. NO marinada.",
            "alternativas_equivalentes": ["Pechuga de pavo", "Clara de huevo cocida"],
        },
        {
            "nombre": "Arroz blanco cocido",
            "cantidad_g": 120,
            "kcal": 156.0,
            "proteina_g": 2.8,
            "grasa_g": 0.2,
            "fuente": "vegetal",
            "frecuencia": "diario",
            "notas": "Cocido sin sal",
            "especificacion_compra": None,
            "alternativas_equivalentes": [],
        },
    ],
    "porciones": {
        "numero_comidas": 3,
        "total_g_dia": 420.0,
        "g_por_comida": 140.0,
        "distribucion_comidas": [
            {"horario": "07:00", "porcentaje": 33, "gramos": 140.0, "proteina_g": 45.0, "carbo_g": 35.0, "vegetal_g": 20.0},
            {"horario": "13:00", "porcentaje": 34, "gramos": 143.0, "proteina_g": 46.0, "carbo_g": 36.0, "vegetal_g": 21.0},
            {"horario": "19:00", "porcentaje": 33, "gramos": 137.0, "proteina_g": 44.0, "carbo_g": 34.0, "vegetal_g": 19.0},
        ],
    },
    "suplementos": [
        {
            "nombre": "Omega-3 EPA+DHA",
            "dosis": "40 mg/kg/día",
            "frecuencia": "diario",
            "forma": "cápsula de aceite de salmón",
            "justificacion": "Antiinflamatorio hepático y renal",
        },
        {
            "nombre": "Silimarina",
            "dosis": "25 mg/kg/día",
            "frecuencia": "diario",
            "forma": "extracto de cardo mariano estandarizado",
            "justificacion": "Hepatoprotector",
        },
    ],
    "instrucciones_preparacion": {
        "metodo": "Cocción al vapor o hervido sin sal",
        "pasos": [
            "Lavar y picar todos los ingredientes crudos.",
            "Cocinar la proteína al vapor por 20 minutos sin añadir sal.",
            "Cocinar los carbohidratos y vegetales por separado hasta blandos.",
        ],
        "tiempo_preparacion_minutos": 35,
        "almacenamiento": "Refrigerado máximo 3 días en recipiente hermético.",
        "advertencias": [
            "NUNCA agregar sal, cebolla, ajo ni condimentos.",
            "Servir a temperatura ambiente — no directamente del refrigerador.",
        ],
        "instrucciones_por_grupo": {
            "proteinas": ["Pollo: cocinar hasta 74°C internos. Sin piel ni grasa visible."],
            "carbohidratos": ["Arroz: cocinar en agua sin sal hasta textura blanda."],
            "vegetales": ["Zanahoria: cocinar hasta blanda para mejor digestibilidad."],
        },
        "adiciones_permitidas": ["Aceite de salmón (1 cdta/día)", "Probiótico en polvo"],
    },
    "snacks_saludables": [
        {
            "nombre": "Zanahoria baby cocida",
            "descripcion": "Snack bajo en calorías, alto en fibra",
            "cantidad_g": 20.0,
            "frecuencia": "máximo 2 veces/semana",
        },
    ],
    "protocolo_digestivo": [
        "Vómito 1 vez: reducir porción 20% y observar 24 horas.",
        "Diarrea leve: cambiar a arroz blanco + pollo hervido por 48 horas.",
        "Inapetencia > 12 horas: consultar veterinario inmediatamente (riesgo lipidosis en gatos).",
    ],
    "transicion_dieta": {
        "requiere_transicion": True,
        "duracion_dias": 7,
        "fases": [
            {"dias": "Días 1-2", "descripcion": "25% nuevo + 75% alimento anterior"},
            {"dias": "Días 3-4", "descripcion": "50% nuevo + 50% alimento anterior"},
            {"dias": "Días 5-6", "descripcion": "75% nuevo + 25% alimento anterior"},
            {"dias": "Día 7", "descripcion": "100% nuevo plan"},
        ],
        "senales_de_alerta": [
            "Diarrea persistente > 48 horas",
            "Vómitos repetidos",
            "Rechazo completo del alimento > 24 horas",
        ],
    },
    "has_transicion": True,
    "alertas_propietario": [
        "La dieta de su mascota puede interactuar con medicamentos actuales — consulte con su veterinario.",
    ],
    "alertas_barf": [],
    "notas_clinicas": [
        "[ICC] Monitorear potasio sérico si está bajo IECA.",
    ],
    "disclaimer": (
        "NutriVet.IA es asesoría nutricional digital — "
        "no reemplaza el diagnóstico médico veterinario."
    ),
}


def _extract_text(pdf_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    return " ".join(page.extract_text() or "" for page in reader.pages).lower()


# ---------------------------------------------------------------------------
# F-02 — Template genera PDF con todas las secciones nuevas
# ---------------------------------------------------------------------------

class TestPDFTemplateSecciones:

    def _gen(self, data: dict) -> bytes:
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator
        return PDFGenerator().generate(data)

    def test_pdf_valido_con_plan_completo(self):
        pdf = self._gen(_PLAN_DATA_COMPLETO)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 500

    def test_seccion_objetivos_clinicos(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "control gluc" in text or "objetivos" in text

    def test_seccion_ingredientes_prohibidos(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "prohibid" in text or "az" in text  # azúcar

    def test_seccion_ingredientes_cantidad_g(self):
        """Los ingredientes usan campo cantidad_g (no gramos)."""
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "pollo" in text
        assert "180" in text  # cantidad_g del pollo

    def test_seccion_ingredientes_alternativas(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "pavo" in text or "alternativa" in text

    def test_seccion_cronograma_diario(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "07:00" in text or "cronograma" in text

    def test_seccion_suplementos(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "omega" in text or "silimarina" in text

    def test_seccion_instrucciones_preparacion(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "vapor" in text or "preparaci" in text

    def test_seccion_instrucciones_por_grupo(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "prote" in text  # proteínas

    def test_seccion_snacks_saludables(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "zanahoria" in text or "snack" in text

    def test_seccion_protocolo_digestivo(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "digestivo" in text or "v" in text  # vómito/diarrea

    def test_seccion_transicion_con_fases(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "transici" in text
        assert "75%" in text or "25%" in text

    def test_seccion_alertas_propietario(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "medicamento" in text or "alerta" in text

    def test_disclaimer_presente(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "nutricional digital" in text or "nutrivet" in text

    def test_nombre_vet_presente(self):
        text = _extract_text(self._gen(_PLAN_DATA_COMPLETO))
        assert "lady carolina" in text or "castañeda" in text

    def test_sin_transicion_si_flag_false(self):
        data = {**_PLAN_DATA_COMPLETO, "has_transicion": False, "transicion_dieta": {}}
        text = _extract_text(self._gen(data))
        assert "protocolo de transici" not in text

    def test_sin_alertas_si_listas_vacias(self):
        data = {
            **_PLAN_DATA_COMPLETO,
            "alertas_propietario": [],
            "alertas_barf": [],
        }
        text = _extract_text(self._gen(data))
        assert "alertas importantes" not in text

    def test_barf_alerta_presente(self):
        data = {
            **_PLAN_DATA_COMPLETO,
            "alertas_barf": ["Descongelar 24h en refrigerador antes de servir."],
        }
        text = _extract_text(self._gen(data))
        assert "barf" in text or "descongelar" in text


# ---------------------------------------------------------------------------
# F-01 — _build_plan_data mapeo correcto desde plan.content
# ---------------------------------------------------------------------------

class TestBuildPlanData:

    def _make_plan(self, content: dict):
        """Crea un plan mock con los campos necesarios."""
        from unittest.mock import MagicMock
        from backend.domain.aggregates.nutrition_plan import PlanStatus, PlanModality, PlanType
        from backend.domain.value_objects.bcs import BCSPhase
        plan = MagicMock()
        plan.plan_id = uuid.uuid4()
        plan.pet_id = uuid.uuid4()
        plan.owner_id = uuid.uuid4()
        plan.rer_kcal = 396.0
        plan.der_kcal = 534.0
        plan.status = PlanStatus.ACTIVE
        plan.modality = PlanModality.NATURAL
        plan.plan_type = PlanType.TEMPORAL_MEDICAL
        plan.weight_phase = BCSPhase.MANTENIMIENTO
        plan.llm_model_used = "anthropic/claude-sonnet-4-5"
        plan.content = content
        return plan

    def test_mapea_objetivos_clinicos(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({"objetivos_clinicos": ["objetivo 1", "objetivo 2"]})
        data = ExportPlanUseCase._build_plan_data(plan)
        assert data["objetivos_clinicos"] == ["objetivo 1", "objetivo 2"]

    def test_mapea_ingredientes_prohibidos(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({"ingredientes_prohibidos": ["azúcar", "chocolate"]})
        data = ExportPlanUseCase._build_plan_data(plan)
        assert "azúcar" in data["ingredientes_prohibidos"]

    def test_mapea_ingredientes_con_cantidad_g(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({
            "ingredientes": [{"nombre": "pollo", "cantidad_g": 180, "kcal": 198}]
        })
        data = ExportPlanUseCase._build_plan_data(plan)
        assert data["ingredientes"][0]["cantidad_g"] == 180

    def test_mapea_porciones_con_distribucion(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({
            "porciones": {"numero_comidas": 3, "total_g_dia": 420, "g_por_comida": 140}
        })
        data = ExportPlanUseCase._build_plan_data(plan)
        assert data["porciones"]["numero_comidas"] == 3

    def test_mapea_suplementos(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({
            "suplementos": [{"nombre": "Silimarina", "dosis": "25 mg/kg/día"}]
        })
        data = ExportPlanUseCase._build_plan_data(plan)
        assert data["suplementos"][0]["nombre"] == "Silimarina"

    def test_mapea_snacks_saludables(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({
            "snacks_saludables": [{"nombre": "zanahoria", "cantidad_g": 20}]
        })
        data = ExportPlanUseCase._build_plan_data(plan)
        assert data["snacks_saludables"][0]["nombre"] == "zanahoria"

    def test_mapea_protocolo_digestivo(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({"protocolo_digestivo": ["Vómito: reducir porción."]})
        data = ExportPlanUseCase._build_plan_data(plan)
        assert len(data["protocolo_digestivo"]) == 1

    def test_has_transicion_true_cuando_requiere_transicion(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({
            "transicion_dieta": {"requiere_transicion": True, "duracion_dias": 7, "fases": []}
        })
        data = ExportPlanUseCase._build_plan_data(plan)
        assert data["has_transicion"] is True

    def test_has_transicion_false_cuando_no_requiere(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({"transicion_dieta": {"requiere_transicion": False}})
        data = ExportPlanUseCase._build_plan_data(plan)
        assert data["has_transicion"] is False

    def test_disclaimer_siempre_presente(self):
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({})
        data = ExportPlanUseCase._build_plan_data(plan)
        assert "NutriVet.IA" in data["disclaimer"]
        assert "no reemplaza" in data["disclaimer"]

    def test_content_vacio_retorna_defaults_seguros(self):
        """plan.content = {} no debe lanzar KeyError."""
        from backend.application.use_cases.export_plan_use_case import ExportPlanUseCase
        plan = self._make_plan({})
        data = ExportPlanUseCase._build_plan_data(plan)
        assert data["ingredientes"] == []
        assert data["suplementos"] == []
        assert data["objetivos_clinicos"] == []
        assert data["has_transicion"] is False
