# Business Rules — unit-08-export-service
**Unidad**: unit-08-export-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Reglas de Negocio del Export Service

### BR-EXPORT-01: Solo Planes ACTIVE son Exportables
- Solo planes con `status == ACTIVE` pueden exportarse a PDF.
- Si el plan está en `PENDING_VET`, `UNDER_REVIEW`, o `ARCHIVED` → HTTP 422 con mensaje claro.
- El export service verifica el status antes de iniciar la generación del PDF.

### BR-EXPORT-02: Disclaimer Obligatorio en el PDF
- El disclaimer DEBE aparecer en el PDF, nunca se puede omitir.
- Texto fijo: "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."
- Se coloca en el footer de todas las páginas del PDF.
- No es configurable por el usuario.

### BR-EXPORT-03: Presigned URL TTL 1 Hora
- La URL de descarga es una presigned URL de Cloudflare R2 con TTL de 1 hora.
- Después de 1 hora → la URL expira y el usuario debe solicitar una nueva.
- El PDF en R2 permanece — solo la URL expira.
- El endpoint `GET /exports/{export_id}/url` genera una nueva presigned URL si la anterior expiró.

### BR-EXPORT-04: Exportación Gratuita para Todos los Tiers
- La exportación a PDF NO tiene costo adicional ni restricción por tier.
- Todos los tiers (free, básico, premium, vet) pueden exportar planes ACTIVE.
- Esto es un diferenciador de valor: el plan es utilizable offline.

### BR-EXPORT-05: PDF Incluye 5 Secciones del Plan
- El PDF contiene exactamente las 5 secciones del NutritionPlan en orden.
- Además incluye: header con nombre del pet (no el owner), fecha de generación, RER/DER, firma del vet (si aplica), disclaimer en footer.

### BR-EXPORT-06: Branding NutriVet.IA
- El PDF incluye el logo y branding de NutriVet.IA en el header.
- El nombre del producto es visible pero no invasivo.
- El PDF es el "producto tangible" que el owner recibe y puede compartir.

### BR-EXPORT-07: Un Export por Plan
- Se puede exportar el mismo plan múltiples veces.
- Cada exportación genera un nuevo PDF (con fecha actualizada) y un nuevo `ExportResult`.
- No hay límite de exportaciones por plan.

### BR-EXPORT-08: Compartir via WhatsApp/Telegram/Email
- El endpoint devuelve la presigned URL.
- Flutter usa `share_plus` para abrir el share sheet nativo con la URL.
- El usuario elige cómo compartir (WhatsApp, Telegram, email, etc.).
- NutriVet.IA no gestiona el canal de compartición — solo provee la URL.

### BR-EXPORT-09: Firma del Vet en el PDF
- Si el plan tiene `vet_id != None`, el PDF incluye la sección de firma del vet.
- Información incluida: nombre del vet, clínica (si aplica), fecha de firma.
- Aumenta la credibilidad y valor del documento para el dueño.
