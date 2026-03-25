"""
Tests RED — PDFGenerator con WeasyPrint (NUT-93 · Paso 3).

Verifica:
- PDF generado es bytes no vacíos.
- Disclaimer presente (REGLA 8).
- Sección 4 (protocolo de transición) solo si has_transition_protocol=True.
- Sección 5 (sustitutos) siempre presente.
- Nombre del vet si el plan fue aprobado.
"""
from __future__ import annotations

import pytest


_PLAN_DATA_BASE = {
    "plan_id": "plan-uuid-001",
    "rer_kcal": 396.0,
    "der_kcal": 534.0,
    # Variables nuevas del template (Sprint 7)
    "rer_kcal_display": 396.0,
    "der_kcal_display": 534.0,
    "modality": "natural",
    "plan_type": "temporal_medical",
    "llm_model_used": "anthropic/claude-sonnet-4-5",
    "weight_phase": "mantenimiento",
    "proteina_pct_ms": 28.0,
    "grasa_pct_ms": 12.0,
    "racion_total_g_dia": 420.0,
    "relacion_ca_p": None,
    "omega3_mg_dia": None,
    "objetivos_clinicos": ["Control glucémico", "Soporte hepático"],
    "ingredientes_prohibidos": ["Azúcar", "Cebolla"],
    "ingredientes": [
        {"nombre": "pollo cocido", "cantidad_g": 150, "kcal": 165, "proteina_g": 30, "grasa_g": 3.5, "fuente": "animal", "frecuencia": "diario", "notas": None, "especificacion_compra": None, "alternativas_equivalentes": []},
        {"nombre": "arroz blanco", "cantidad_g": 100, "kcal": 130, "proteina_g": 2.8, "grasa_g": 0.2, "fuente": "vegetal", "frecuencia": "diario", "notas": None, "especificacion_compra": None, "alternativas_equivalentes": ["quinoa cocida"]},
    ],
    "porciones": {
        "numero_comidas": 2,
        "total_g_dia": 400.0,
        "g_por_comida": 200.0,
        "distribucion_comidas": [
            {"horario": "08:00", "porcentaje": 50, "gramos": 200.0, "proteina_g": 40, "carbo_g": 30, "vegetal_g": 15},
            {"horario": "18:00", "porcentaje": 50, "gramos": 200.0, "proteina_g": 40, "carbo_g": 30, "vegetal_g": 15},
        ],
    },
    "suplementos": [
        {"nombre": "Omega-3", "dosis": "500 mg/día", "frecuencia": "diario", "forma": "cápsula", "justificacion": "antiinflamatorio"},
    ],
    "instrucciones_preparacion": {
        "metodo": "Cocción al vapor",
        "pasos": ["Lavar ingredientes", "Cocinar pollo 20 min"],
        "tiempo_preparacion_minutos": 30,
        "almacenamiento": "Refrigerado 3 días",
        "advertencias": ["No agregar sal"],
        "instrucciones_por_grupo": {"proteinas": ["Pollo: sin piel"], "carbohidratos": ["Arroz: sin sal"], "vegetales": []},
        "adiciones_permitidas": ["Aceite de salmón"],
    },
    "snacks_saludables": [
        {"nombre": "Zanahoria baby", "descripcion": "Bajo en calorías", "cantidad_g": 20, "frecuencia": "2 veces/semana"},
    ],
    "protocolo_digestivo": ["Vómito: reducir porción 20%", "Diarrea: ayuno 12h + arroz blanco"],
    "transicion_dieta": {
        "requiere_transicion": True,
        "duracion_dias": 7,
        "fases": [
            {"dias": "Días 1-2", "descripcion": "25% nuevo"},
            {"dias": "Días 5-7", "descripcion": "100% nuevo"},
        ],
        "senales_de_alerta": ["Diarrea persistente"],
    },
    "has_transicion": True,
    "alertas_propietario": ["Consulte con su vet sobre medicamentos."],
    "alertas_barf": [],
    "notas_clinicas": [],
    "approved_by_vet_name": None,
    "disclaimer": (
        "NutriVet.IA es asesoría nutricional digital — "
        "no reemplaza el diagnóstico médico veterinario."
    ),
}


class TestPDFGenerator:

    def test_pdf_generado_es_bytes(self) -> None:
        """generate() retorna bytes no vacíos."""
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        gen = PDFGenerator()
        pdf_bytes = gen.generate(_PLAN_DATA_BASE)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 100

    def test_pdf_es_formato_pdf_valido(self) -> None:
        """Los bytes generados comienzan con el magic number %PDF."""
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        gen = PDFGenerator()
        pdf_bytes = gen.generate(_PLAN_DATA_BASE)
        assert pdf_bytes[:4] == b"%PDF"

    def test_pdf_incluye_disclaimer(self) -> None:
        """El PDF contiene el texto del disclaimer (REGLA 8)."""
        import pypdf
        import io
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        gen = PDFGenerator()
        pdf_bytes = gen.generate(_PLAN_DATA_BASE)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        all_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        )
        assert "NutriVet" in all_text or "nutricional digital" in all_text.lower()

    def test_pdf_incluye_ingredientes_alternativas(self) -> None:
        """Las alternativas equivalentes de ingredientes aparecen en el PDF."""
        import pypdf
        import io
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        gen = PDFGenerator()
        pdf_bytes = gen.generate(_PLAN_DATA_BASE)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        all_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        ).lower()
        assert "quinoa" in all_text or "alternativa" in all_text

    def test_pdf_protocolo_transicion_si_flag(self) -> None:
        """Transición presente si has_transicion=True."""
        import pypdf
        import io
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        data = {**_PLAN_DATA_BASE, "has_transicion": True}
        gen = PDFGenerator()
        pdf_bytes = gen.generate(data)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        all_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        ).lower()
        assert "transici" in all_text

    def test_pdf_sin_protocolo_si_no_flag(self) -> None:
        """Sección de transición ausente si has_transicion=False."""
        import pypdf
        import io
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        data = {
            **_PLAN_DATA_BASE,
            "has_transicion": False,
            "transicion_dieta": {},
        }
        gen = PDFGenerator()
        pdf_bytes = gen.generate(data)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        all_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        ).lower()
        assert "protocolo de transici" not in all_text

    def test_pdf_incluye_nombre_vet_si_aprobado(self) -> None:
        """Nombre del vet aparece en el PDF si el plan fue aprobado."""
        import pypdf
        import io
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        data = {**_PLAN_DATA_BASE, "approved_by_vet_name": "Dra. Lady Carolina Castañeda"}
        gen = PDFGenerator()
        pdf_bytes = gen.generate(data)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        all_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        )
        assert "Lady Carolina" in all_text or "Castañeda" in all_text
