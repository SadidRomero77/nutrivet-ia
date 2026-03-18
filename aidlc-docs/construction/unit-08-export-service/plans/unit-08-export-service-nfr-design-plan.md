# Plan: NFR Design — Unit 08: export-service

**Unidad**: unit-08-export-service
**Fase AI-DLC**: C3b — NFR Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Patrones NFR Aplicados a export-service

### Patrón: Content-Hash Key (Cache-Friendly, No Duplicados)

**Contexto**: El mismo plan exportado múltiples veces no debe generar múltiples PDFs
en R2. El content-hash garantiza idempotencia.

**Diseño**:
```python
# application/use_cases/export_plan_use_case.py
import hashlib, json

def compute_content_hash(plan_data: dict) -> str:
    """Hash determinístico del contenido del plan. Mismo plan = mismo hash."""
    canonical = json.dumps(plan_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]

async def export_plan(self, plan_id: UUID, user_id: UUID) -> ExportResult:
    plan = await self.plan_repo.find_by_id(plan_id)

    # Verificar status y permisos
    if plan.status != "ACTIVE":
        raise PlanNotExportableError(f"Plan en estado {plan.status} no es exportable")
    if plan.owner_id != user_id and plan.assigned_vet_id != user_id:
        raise UnauthorizedExportError()

    # Construir datos y calcular hash
    plan_data = self._build_plan_data(plan)
    content_hash = compute_content_hash(plan_data)
    r2_key = f"pdfs/{plan_id}/{content_hash}.pdf"

    # Cache check
    if await self.storage_client.exists(r2_key):
        url = self.storage_client.generate_presigned_url(r2_key, expires_in=3600)
        return ExportResult(url=url, cached=True)

    # Generar y subir
    pdf_bytes = await self.pdf_generator.generate(plan_data)
    await self.storage_client.upload(r2_key, pdf_bytes, content_type="application/pdf")
    url = self.storage_client.generate_presigned_url(r2_key, expires_in=3600)
    return ExportResult(url=url, cached=False)
```

### Patrón: On-Demand Generation (Sin Pre-generación)

**Contexto**: Los PDFs solo se generan cuando el usuario lo solicita.
No hay job de pre-generación en background.

**Justificación**: Los planes cambian (vet puede editar antes de aprobar).
Pre-generar significaría invalidar y re-generar con cada cambio.
On-demand + content-hash cache es más simple y correcto.

### Patrón: Disclaimer-Every-Page (Template Base con Footer)

**Contexto**: El disclaimer debe aparecer en CADA PÁGINA del PDF, no solo en la
portada o en la última página (Constitution REGLA 8).

**Diseño** (Jinja2 + WeasyPrint CSS):
```html
<!-- base_layout.html -->
<!DOCTYPE html>
<html>
<head>
<style>
  @page {
    margin-bottom: 2cm;
    @bottom-center {
      content: "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario.";
      font-size: 8pt;
      color: #666;
      font-style: italic;
    }
  }
</style>
</head>
<body>
  {% block content %}{% endblock %}
</body>
</html>
```

El `@bottom-center` de CSS Paged Media hace que el disclaimer aparezca automáticamente
en el footer de CADA página generada por WeasyPrint.

### Patrón: Pre-Signed URL TTL Hardcoded

**Contexto**: El TTL de la URL pre-signed debe ser exactamente 1 hora — sin excepción.

**Diseño**:
```python
# infrastructure/storage/r2_client.py
PRESIGNED_URL_TTL_SECONDS = 3600  # 1 hora — no configurable via env var

class R2StorageClient(IStorageClient):
    def generate_presigned_url(self, key: str) -> str:
        """Genera URL pre-signed. TTL fijo en 3600s. No configurable."""
        return self._s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=PRESIGNED_URL_TTL_SECONDS
        )
```

**Test de contrato**:
```python
def test_presigned_url_ttl_es_exactamente_3600():
    """Verificar que el TTL es siempre 3600s — no menos, no más."""
    with patch.object(r2_client._s3, "generate_presigned_url") as mock:
        r2_client.generate_presigned_url("pdfs/test/abc.pdf")
        mock.assert_called_once_with(
            "get_object",
            Params={"Bucket": ANY, "Key": "pdfs/test/abc.pdf"},
            ExpiresIn=3600
        )
```

## Cobertura de Tests Requerida

| Módulo | Cobertura Mínima | Tipo de Test |
|--------|-----------------|--------------|
| `application/use_cases/export_plan_use_case.py` | 90% | Unit tests |
| `infrastructure/pdf/pdf_generator.py` | 80% | Integration tests |
| `infrastructure/storage/r2_client.py` | 90% | Unit tests con mocks |
| `presentation/routers/export_router.py` | 80% | Integration tests |

## Referencias

- Global: `_shared/nfr-design-patterns.md`
- ADR-020: estructura 5 secciones del plan
- Constitution: REGLA 8 (disclaimer obligatorio en toda vista del plan)
