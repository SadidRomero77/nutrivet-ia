# Domain Entities — unit-08-export-service
**Unidad**: unit-08-export-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Entidades del Export Service

### ExportResult
Resultado de una exportación de plan a PDF.
- `export_id: UUID`
- `plan_id: UUID` — FK a NutritionPlan (debe ser status=ACTIVE)
- `pet_id: UUID`
- `owner_id: UUID`
- `r2_key: R2Key` — clave del PDF en Cloudflare R2
- `presigned_url: str` — URL temporal para descargar/compartir
- `url_expires_at: datetime` — TTL 1 hora
- `file_size_bytes: int`
- `created_at: datetime`

### PDFContent
Contenido estructurado del PDF generado (5 secciones del plan + metadata).
- `content_id: UUID`
- `plan_id: UUID`
- `pet_name: str` — nombre de la mascota (solo aparece en el PDF, nunca en prompts LLM)
- `generated_date: date`
- `sections: list[PlanSection]` — 5 secciones del NutritionPlan
- `rer_kcal: Decimal`
- `der_kcal: Decimal`
- `vet_signature: VetSignature | None` — solo si plan fue firmado por vet
- `disclaimer: str` — fijo: "NutriVet.IA es asesoría nutricional digital..."
- `nutrivet_logo: bool` — siempre True (branding)

### VetSignature
Información del vet que firmó el plan, incluida en el PDF.
- `vet_name: str`
- `tarjeta_profesional: str | None`
- `clinica: str | None`
- `signed_at: datetime`

### R2Key (Value Object)
```python
@dataclass(frozen=True)
class R2Key:
    value: str  # exports/{owner_id}/{plan_id}/{export_id}.pdf

    @classmethod
    def generate(cls, owner_id: UUID, plan_id: UUID, export_id: UUID) -> "R2Key":
        return cls(f"exports/{owner_id}/{plan_id}/{export_id}.pdf")
```

## Constantes del Export Service

### DISCLAIMER (Inmutable)
```python
PLAN_DISCLAIMER: Final[str] = (
    "NutriVet.IA es asesoría nutricional digital — "
    "no reemplaza el diagnóstico médico veterinario. "
    "Este plan fue generado con base en los datos proporcionados y "
    "validado según estándares NRC/AAFCO. "
    "Consulta a tu veterinario ante cualquier duda clínica."
)
```

### PDF_SECTIONS_ORDER
```python
PDF_SECTIONS_ORDER: Final[list[str]] = [
    "Resumen nutricional",
    "Ingredientes y porciones por día",
    "Instrucciones de preparación",
    "Protocolo de transición",
    "Advertencias y consideraciones especiales",
]
```
