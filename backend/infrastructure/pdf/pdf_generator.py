"""
PDFGenerator — Implementación WeasyPrint del IPDFGenerator.

Genera PDFs de planes nutricionales con 5 secciones (ADR-020).
Disclaimer obligatorio en todas las páginas via CSS @bottom-center (REGLA 8).
"""
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.application.interfaces.pdf_generator import IPDFGenerator

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_DISCLAIMER = (
    "NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario."
)


class PDFGenerator(IPDFGenerator):
    """
    Generador de PDF usando WeasyPrint + Jinja2.

    El disclaimer aparece en todas las páginas via CSS @bottom-center
    y también en el cuerpo del documento (REGLA 8 doble garantía).
    """

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )

    def generate(self, plan_data: dict) -> bytes:
        """
        Genera el PDF del plan nutricional.

        Args:
            plan_data: Diccionario con secciones 1-5, flags y metadata del plan.

        Returns:
            Bytes del PDF generado (comienza con %PDF).
        """
        from weasyprint import HTML, CSS

        # Asegurar disclaimer presente
        if "disclaimer" not in plan_data:
            plan_data = {**plan_data, "disclaimer": _DISCLAIMER}

        template = self._env.get_template("plan_template.html")
        html_str = template.render(**plan_data)

        css_path = _TEMPLATES_DIR / "assets" / "style.css"

        pdf_bytes: bytes = HTML(string=html_str, base_url=str(_TEMPLATES_DIR)).write_pdf(
            stylesheets=[CSS(filename=str(css_path))] if css_path.exists() else None,
        )

        return pdf_bytes
