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
    "pet_name": "Luna",
    "species": "perro",
    "breed": "French Poodle",
    "weight_kg": 9.6,
    "rer_kcal": 396.0,
    "der_kcal": 534.0,
    "modality": "natural",
    "seccion_1_perfil": {
        "especie": "perro",
        "raza": "French Poodle",
        "peso_kg": 9.6,
        "edad_anios": 8,
        "bcs": 6,
        "condiciones": ["diabetes", "hepatico"],
    },
    "seccion_2_calorias": {
        "rer_kcal": 396.0,
        "der_kcal": 534.0,
        "peso_objetivo_kg": 9.6,
        "fase": "mantenimiento",
    },
    "seccion_3_ingredientes": [
        {"nombre": "pollo cocido", "gramos": 150, "proteinas_g": 30},
        {"nombre": "arroz blanco", "gramos": 100, "proteinas_g": 3},
    ],
    "seccion_4_transicion": {
        "dias": 7,
        "fases": ["25% nuevo día 1-2", "50% nuevo día 3-4", "100% nuevo día 5-7"],
    },
    "seccion_5_sustitutos": [
        {"original": "pollo", "alternativa": "pavo", "razon": "disponibilidad"},
    ],
    "has_transition_protocol": True,
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

    def test_pdf_incluye_sustitutos(self) -> None:
        """Sección 5 (sustitutos) siempre presente en el PDF."""
        import pypdf
        import io
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        gen = PDFGenerator()
        pdf_bytes = gen.generate(_PLAN_DATA_BASE)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        all_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        ).lower()
        assert "pavo" in all_text or "sustit" in all_text

    def test_pdf_protocolo_transicion_si_flag(self) -> None:
        """Sección 4 presente si has_transition_protocol=True."""
        import pypdf
        import io
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        data = {**_PLAN_DATA_BASE, "has_transition_protocol": True}
        gen = PDFGenerator()
        pdf_bytes = gen.generate(data)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        all_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        ).lower()
        assert "transici" in all_text

    def test_pdf_sin_protocolo_si_no_flag(self) -> None:
        """Sección 4 ausente si has_transition_protocol=False."""
        import pypdf
        import io
        from backend.infrastructure.pdf.pdf_generator import PDFGenerator

        data = {
            **_PLAN_DATA_BASE,
            "has_transition_protocol": False,
            "seccion_4_transicion": None,
        }
        gen = PDFGenerator()
        pdf_bytes = gen.generate(data)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        all_text = " ".join(
            page.extract_text() or "" for page in reader.pages
        ).lower()
        # "protocolo de transición" no debe aparecer como sección
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
