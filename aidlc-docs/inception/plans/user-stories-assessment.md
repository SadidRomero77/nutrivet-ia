# User Stories Assessment — NutriVet.IA

**Fase AI-DLC**: PASO 2 — User Stories
**Estado**: ✅ Completado
**Fecha**: 2026-03-10

---

## Resumen de Cobertura

- **Total User Stories**: 21
- **Épicas**: 9
- **Personas**: 3 (Valentina, Dr. Andrés, Carolina)
- **Cobertura de requisitos PRD**: 100% de features prioritarias

## Assessment por Épica

### Epic 1 — Gestión de Identidad (US-01 a US-03)
**Cobertura**: Completa
- US-01: Registro owner con email + contraseña → tier Free
- US-02: Registro vet con datos de clínica → tier Vet
- US-03: Login para ambos roles → JWT 15min + refresh
**Riesgo**: Bajo — flujo estándar

### Epic 2 — Perfil de Mascota (US-04, US-05)
**Cobertura**: Completa
- US-04: Wizard 6 pasos, 13 campos obligatorios, BCS visual, talla solo perros
- US-05: Registro de peso append-only con gráfica en dashboard
**Riesgo**: Medio — 13 campos + validaciones por especie + BCS visual

### Epic 3 — Generación de Plan (US-06, US-07, US-08)
**Cobertura**: Completa
- US-06: Plan mascota sana → ACTIVE directo (sin HITL)
- US-07: Plan con condición médica → PENDING_VET → firma vet → ACTIVE
- US-08: Ajuste ingrediente dentro del set pre-aprobado
**Riesgo**: ALTO — core del valor. LLM routing + validación post-LLM + async

### Epic 4 — Revisión Veterinaria HITL (US-09, US-10)
**Cobertura**: Completa
- US-09: Vet aprueba con review_date → ACTIVE
- US-10: Vet devuelve con comentario obligatorio → PENDING_VET
**Riesgo**: Medio — estado del plan, notificaciones, permisos

### Epic 5 — Agente Conversacional (US-11, US-12)
**Cobertura**: Completa
- US-11: Consulta nutricional respondida con contexto del perfil
- US-12: Detección de emergencia → mensaje de acción urgente sin consumir cuota
**Riesgo**: Alto — SSE streaming + clasificación nutricional/médica + límites freemium

### Epic 6 — Scanner OCR (US-13)
**Cobertura**: Completa
- US-13: Escanear tabla nutricional → semáforo + evaluación vs. perfil
**Riesgo**: Alto — GPT-4o vision + semáforo determinístico + Quality Gate G4 (85%)

### Epic 7 — Exportación (US-14, US-15)
**Cobertura**: Completa
- US-14: PDF con pre-signed URL 1 hora
- US-15: Share sheet nativo (WhatsApp/email/Telegram)
**Riesgo**: Bajo — WeasyPrint + R2, flujo sencillo

### Epic 8 — Dashboard (US-16, US-17)
**Cobertura**: Completa
- US-16: Dashboard owner — estado del plan + días activo
- US-17: Dashboard vet — todos sus pacientes con estado de plan
**Riesgo**: Bajo — queries SQL + fl_chart

### Epic 9 — Freemium (US-18, US-19)
**Cobertura**: Completa
- US-18: Gate Free → agota plan gratuito (mascota con condición) → upgrade
- US-19: Gate Free → agota 9 preguntas del agente → upgrade
**Riesgo**: Medio — gates en DB + UX modal de upgrade

### ClinicPet (US-20, US-21)
**Cobertura**: Completa
- US-20: Vet crea ClinicPet con owner_name + owner_phone
- US-21: Owner reclama ClinicPet con código TTL 30 días
**Riesgo**: Bajo — CRUD especializado con claim code

---

## Stories de Mayor Riesgo

1. **US-07** — Plan con condición médica: LLM routing + validación post-LLM + HITL = mayor complejidad
2. **US-13** — Scanner OCR: dependencia de GPT-4o vision + Quality Gate G4
3. **US-11/US-12** — Agente conversacional: SSE streaming + clasificación precisa + freemium gate

## Gaps Identificados

Ningún gap crítico. Todas las features del PRD v2.0 están cubiertas en las 21 stories.

## Alineación con Quality Gates

| Quality Gate | Stories Relacionadas |
|-------------|---------------------|
| G1: 0 tóxicos | US-06, US-07 |
| G2: 100% restricciones | US-07 |
| G3: 95% clasificación nut/med | US-11, US-12 |
| G4: 85% OCR | US-13 |
| G5: 80% cobertura domain | US-06, US-07 |
| G6: 18/20 aprobados Lady Carolina | US-06, US-07, US-09 |
| G7: Red-teaming | US-07, US-12 |
| G8: Golden case Sally | US-07 |
