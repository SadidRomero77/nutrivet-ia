# Plan: Functional Design — Unit 08: export-service

**Unidad**: unit-08-export-service
**Fase AI-DLC**: C1 — Functional Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Definir la lógica de negocio del servicio de exportación de planes: generación de PDF
(WeasyPrint), estructura de 5 secciones (ADR-020), pre-signed URL en Cloudflare R2
(TTL 1 hora), y reglas de acceso y disclaimer obligatorio.

## Reglas Fundamentales de Exportación

```
SOLO planes en estado ACTIVE son exportables.
PENDING_VET / UNDER_REVIEW / ARCHIVED → 422 Unprocessable Entity.

Quién puede exportar:
  - Owner del plan (owner_id == current_user.user_id)
  - Vet asignado al paciente (assigned_vet_id == current_user.user_id)

Disclaimer obligatorio: presente en CADA PÁGINA del PDF.
```

## Estructura del PDF — 5 Secciones (ADR-020)

```
Portada:
  - Nombre + especie + raza de la mascota
  - Fecha de generación
  - "Aprobado por: [nombre del vet]" (si plan fue revisado por vet)
  - Disclaimer

Sección 1: Resumen Nutricional
  - RER: [X] kcal/día
  - DER: [X] kcal/día
  - Macros objetivo: proteínas [X]%, grasas [X]%, carbohidratos [X]%
  - Fase: reducción / mantenimiento / aumento

Sección 2: Plan Semanal (Lun → Dom)
  - Por cada día: ingredientes + porciones en gramos
  - Total kcal/día

Sección 3: Instrucciones de Preparación
  - Pasos de preparación
  - Temperatura de servido
  - Frecuencia de comidas
  - Ayuno: nunca > 12 horas entre comidas

Sección 4: Protocolo de Transición (solo si has_transition_protocol=True)
  - 7 días de transición gradual
  - Porcentajes: Días 1-2: 25% nuevo/75% anterior, etc.

Sección 5: Sustitutos Aprobados
  - Lista de sustitutos pre-aprobados por ingrediente
  - Nota: sustitutos fuera de esta lista requieren revisión veterinaria

Pie de página (TODAS las páginas):
  "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario."
```

## Flujo de Generación y Almacenamiento

```
POST /v1/plans/{plan_id}/export
  → verificar plan ACTIVE + permisos
  → calcular content_hash del plan
  → buscar en R2: pdfs/{plan_id}/{content_hash}.pdf
      ↓ existe (cache) → generar pre-signed URL → retornar
      ↓ no existe → generar PDF (WeasyPrint) → upload R2 → generar pre-signed URL → retornar

Respuesta:
  { "url": "https://r2_presigned_url...", "expires_at": "ISO8601" }
  TTL: exactamente 1 hora (3600 segundos)
```

**Cache-friendly**: mismo plan sin cambios → mismo PDF en R2 (content_hash idéntico).
Si el plan se modifica (vet edita) → nuevo content_hash → nuevo PDF.

## Protocolo de Transición (Sección 4)

Solo incluida cuando `has_transition_protocol=True` en el plan:
```
Días 1-2: 25% plan nuevo + 75% alimentación anterior
Días 3-4: 50% plan nuevo + 50% alimentación anterior
Días 5-6: 75% plan nuevo + 25% alimentación anterior
Día 7:    100% plan nuevo
```

## Casos de Prueba Críticos

- [ ] Exportar plan ACTIVE → URL pre-signed retornada
- [ ] Exportar plan PENDING_VET → 422
- [ ] Exportar plan ARCHIVED → 422
- [ ] PDF incluye disclaimer en todas las páginas
- [ ] PDF incluye sustitutos aprobados (sección 5)
- [ ] PDF incluye protocolo de transición (sección 4) solo si `has_transition_protocol=True`
- [ ] Pre-signed URL expira en exactamente 1 hora
- [ ] Owner puede exportar su propio plan
- [ ] Vet puede exportar plan de su paciente
- [ ] Otro owner (no el dueño) → 403
- [ ] Mismo plan sin cambios → mismo PDF (cache hit en R2)
- [ ] Nombre del vet en portada si plan fue aprobado por vet

## Referencias

- Spec: `aidlc-docs/inception/units/unit-08-export-service.md`
- ADR-020: estructura 5 secciones del plan
- Constitution: REGLA 8 (disclaimer obligatorio)
- CLAUDE.md: "Exportación PDF: Solo planes en estado ACTIVE son exportables"
