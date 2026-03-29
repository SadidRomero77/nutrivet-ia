# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

**NutriVet.IA** — App móvil agéntica de planes nutricionales personalizados para perros y gatos.
Desarrollada por Sadid Romero (AI Engineer) y Lady Carolina Castañeda (MV, BAMPYSVET).

Validación clínica: Lady Carolina Castañeda (MV, BAMPYSVET) y estándares NRC/AAFCO.
Piloto inicial: BAMPYSVET, Bogotá — Dr. Andrés como primer veterinario adoptante.

## Tech Stack

- **Mobile**: Flutter (Dart) — iOS + Android
- **Backend**: Python + FastAPI — Clean Architecture / Hexagonal
- **Agente**: LangGraph — orquestador + 4 subgrafos especializados
- **Base de datos**: PostgreSQL + Alembic (migraciones)
- **Auth**: JWT (access 15min + refresh rotativo) + RBAC (roles: owner / vet)
- **LLM Texto + OCR**: OpenRouter (proveedor unificado) — routing por tier + override clínico (ver ADR-019)
  - Free → `openai/gpt-4o-mini` · Básico → `openai/gpt-4o-mini` · Premium/Vet → `anthropic/claude-sonnet-4-5`
  - Override: **2+** condiciones médicas → `anthropic/claude-sonnet-4-5` siempre, independiente del tier
  - OCR → `openai/gpt-4o` (vision) · Query classifier → `openai/gpt-4o-mini`
  - Sin endpoints `:free` — producción requiere SLA garantizado
- **Deployment**: Hetzner CPX31 (Ashburn VA) + Coolify — FastAPI en Docker, async jobs con ARQ (ver ADR-022)
- **Storage**: Cloudflare R2 (S3-compatible — imágenes OCR, PDFs exportados)
- **CI/CD**: GitHub Actions → Coolify webhook (deploy automático en staging, manual en prod)

## Comandos

```bash
# Backend desarrollo
uvicorn main:app --reload

# Tests con cobertura
pytest --cov=app tests/

# Lint + análisis de seguridad estático
ruff check . && bandit -r app/

# Escaneo de dependencias
safety check
```

> Actualizar cuando se inicialice el proyecto con rutas y configuraciones definitivas.

## Arquitectura

**Clean Architecture / Hexagonal** en backend. Flujo de dependencias: `Domain → Application → Infrastructure → Presentation`.

```
backend/
├── domain/          # Entidades, value objects, reglas NRC, toxicidad, restricciones (hard-coded)
├── application/     # Casos de uso, interfaces de repositorio
├── infrastructure/  # PostgreSQL, LLM clients (Ollama/Groq/GPT-4o), OCR, push notifications
└── presentation/    # FastAPI routers, Pydantic schemas, middleware JWT/RBAC
```

## Arquitectura del Agente LangGraph

**Un orquestador central con 4 subgrafos especializados.** Estado compartido `NutriVetState` accesible por todos.

```
Orquestador (clasifica intención)
  ├── Plan Generation Subgraph  → nutrition_calculator → food_toxicity_checker → LLM decide plan → hitl_router
  ├── Consultation Subgraph     → query_classifier → nutritional_responder / Referral Node
  ├── Scanner Subgraph          → image_validator → Qwen2.5-VL OCR → product_evaluator → semáforo
  └── Referral Node             → mensaje estructurado + contacto vet + acción urgente si emergencia
```

**LLM Routing:**
- 0 condiciones médicas → Ollama Qwen2.5-7B ($0, local)
- 1-2 condiciones → Groq Llama-70B ($0 free tier)
- 3+ condiciones → GPT-4o
- OCR → Qwen2.5-VL-7B ($0, local, siempre)

## Flujo Principal del Usuario

```
Registro → Login → Wizard de mascota (6 pasos, 13 campos)
  → Paso extra: ¿Qué come tu mascota HOY? (concentrado / natural / mixto)
  → Selección de modalidad:
      [A] Dieta Natural (BARF/casera) → Plan con ingredientes LATAM, porciones en gramos, preparación + transición 7 días si aplica
      [B] Concentrado comercial        → Perfil nutricional ideal + criterios de selección
  → Agente genera plan (LLM decide ingredientes y balance con guardarraíles deterministas)
  → Mascota SANA     → Plan ACTIVE directo (sin HITL) → exportable a PDF / compartir
  → Mascota con CONDICIÓN MÉDICA → PENDING_VET → firma vet → ACTIVE → exportable a PDF / compartir
  → Agente conversacional disponible antes, durante y después del plan
  → OCR Scanner (solo tabla nutricional o ingredientes) → evaluación vs perfil mascota
```

## PetProfile — 13 Campos Obligatorios

| # | Campo | Tipo | Opciones |
|---|-------|------|---------|
| 1 | Nombre | Text | Libre |
| 2 | Especie | Enum | perro / gato |
| 3 | Raza | Text + selector | Búsqueda libre |
| 4 | Sexo | Enum | macho / hembra |
| 5 | Edad | Number | meses / años |
| 6 | Peso | Decimal (kg) | > 0 |
| 7 | Talla | Enum (solo perros) | mini XS (1-4kg) / pequeño S (4-9kg) / mediano M (9-14kg) / grande L (14-30kg) / gigante XL (+30kg) |
| 8 | Estado reproductivo | Enum | esterilizado / no esterilizado |
| 9 | Nivel de actividad | Enum (por especie) | Perros: sedentario/moderado/activo/muy_activo · Gatos: indoor/indoor_outdoor/outdoor |
| 10 | BCS | Selector visual | 1–9 (con imágenes de silueta por escala) |
| 11 | Antecedentes médicos | Multi-select | 13 condiciones + "Ninguno conocido" |
| 12 | Alergias / intolerancias | Multi-select + texto | Lista base + campo abierto |
| 13 | Alimentación actual | Enum | concentrado / natural / mixto |

**Fórmula NRC:**
```
RER = 70 × peso_kg^0.75
DER = RER × factor_edad × factor_reproductivo × factor_actividad × factor_bcs
```

## 13 Condiciones Médicas Soportadas

`diabético` · `hipotiroideo` · `cancerígeno` (+ campo: ubicación) · `articular` · `renal`
`hepático/hiperlipidemia` · `pancreático` · `neurodegenerativo` · `bucal/periodontal`
`piel/dermatitis` · `gastritis` · `cistitis/enfermedad_urinaria` · `sobrepeso/obesidad`

## Reglas Críticas del Agente — No Negociables

1. **TOXIC_DOGS / TOXIC_CATS** son hard-coded en domain layer — el LLM nunca decide toxicidad
2. **RESTRICTIONS_BY_CONDITION** son hard-coded para las 13 condiciones — el LLM no puede sobrescribir
3. **RER/DER** siempre Python determinista — nunca LLM
4. **HITL exclusivo para mascotas con condición médica** — mascotas sanas → ACTIVE directo; si owner agrega condición a plan ACTIVE → vuelve a PENDING_VET
5. **El LLM ES el decisor nutricional** (ingredientes, porciones, balance de macros) con guardarraíles deterministas que no puede sobrescribir
6. **Agente conversacional**: responde consultas nutricionales; ante consultas médicas (síntomas, medicamentos, diagnósticos) → remite al vet, nunca responde
7. **Alergias "no sabe"** → alerta obligatoria + recomendación de test alérgenos antes de proceder
8. **Disclaimer** en cada vista del plan: "NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario"
9. **Ayunos > 12 horas** deben evitarse (riesgo hepático/biliar/pancreático)
10. **BCS determina la fase del plan**: BCS ≥ 7 → reducción · BCS 4-6 → mantenimiento · BCS ≤ 3 → aumento

## Ciclo de Vida del Plan

**Tipos de plan:**
- `estándar` — mascota sana, sin expiración
- `temporal_medical` — condición médica activa, vet define `review_date` al firmar
- `life_stage` — cachorros/gatitos, milestones automáticos (3m · 6m · 12m · 18m)

**Weight Journey (fases por peso/BCS):**
- Reducción (BCS ≥ 7): `RER(peso ideal) × factor × 0.8` — RER sobre peso ideal estimado, no peso real
- Mantenimiento (BCS 4-6): `RER × factor` estándar
- Aumento (BCS ≤ 3): `RER × factor × 1.2`

**Status del plan:** `PENDING_VET` → `ACTIVE` → `UNDER_REVIEW` → `ARCHIVED`

## Base de Datos de Alimentos

**LATAM-wide en español con aliases regionales.** NO Colombia-específica.
El pollo es pollo en Colombia, México, Ecuador, Argentina.
Aliases: ahuyama (CO) = zapallo (AR/PE) = calabaza (MX)
"Colombia-first" es estrategia GTM — no restricción del producto.

## OCR — Regla Crítica

Solo se acepta imagen de la tabla nutricional o la lista de ingredientes.
**NUNCA** imagen de marca, logo o empaque frontal — imparcialidad y cautela.
El resultado se evalúa contra el perfil completo de la mascota.

## Modelo Freemium

| Tier | Precio | Mascotas | Planes | Agente Conversacional |
|------|--------|----------|--------|-----------------------|
| Free | $0 | 1 | 1 plan total (puede incluir 1 con condición médica) | 3 preguntas/día × 3 días → upgrade obligatorio |
| Básico | $29.900 COP/mes | 1 | 1 nuevo/mes | Ilimitado |
| Premium | $59.900 COP/mes | Hasta 3 | Ilimitados | Ilimitado |
| Vet | $89.000 COP/mes | Ilimitadas (pacientes) | Ilimitados + dashboard clínico | Ilimitado + asistente vet (modo guía) |

Gate de mayor conversión: Gate 3 — mascota con condición médica agota plan gratuito (urgencia clínica real).
Gate secundario: Free agota 9 preguntas (3×3 días) → bloqueo del agente → conversión a Básico.

**Estado RECHAZADO**: No existe. Vet tiene dos opciones: editar+aprobar, o devolver con comentario obligatorio → plan regresa a PENDING_VET.
**Estado BORRADOR**: No existe. El wizard guarda localmente (Hive) hasta que los 13 campos se completan.
**Exportación PDF**: Solo planes en estado ACTIVE son exportables y compartibles (WhatsApp/Telegram/email).

## Roles de Usuario

- `owner` — registro de mascotas, interacción con agente, consultas conversacionales, ajuste de plan
- `vet` — revisión y firma de planes (`PENDING_VET`), trazabilidad completa, edición con justificación

## Convenciones de Código

- **Python**: PEP8, type hints obligatorios en toda función y método, docstrings en español
- **Dart/Flutter**: Effective Dart style
- **Git**: Conventional Commits — `feat/fix/docs/chore/security`
- **Tests**: pytest, cobertura mínima 80% (obligatorio en domain layer antes de lanzar)
- **Idioma**: código en inglés, comentarios y documentación en español
- **PRs**: no merge a `main` sin tests pasando y revisión de seguridad (bandit + safety)

## Seguridad (obligatorio desde día 0)

- **Secrets**: nunca en código — solo variables de entorno
- **JWT**: access tokens 15 min + refresh tokens rotativos
- **RBAC**: validación de rol en cada endpoint — nunca omitir
- **Input validation**: Pydantic models obligatorio en todos los endpoints
- **Logs**: JSON estructurado, sin datos sensibles (PII ni condiciones médicas en texto plano)
- **CORS**: configurado explícitamente, nunca wildcard en producción
- **HTTPS**: obligatorio en todos los entornos expuestos
- **Datos médicos**: encriptar AES-256 en reposo en PostgreSQL
- **Prompts a LLMs externos**: usar IDs anónimos, nunca nombres ni datos de propietario
- **agent_traces**: inmutables post-generación — sin UPDATE permitido sobre trazas existentes
- **CI/CD**:
  - SAST con `bandit` en cada PR
  - Dependency scanning con `safety` en cada PR
  - OWASP Top 10 como checklist en cada nueva feature

## Quality Gates de Lanzamiento

No se lanza hasta que todos estén en verde:

| Gate | Criterio |
|------|----------|
| G1 | 0 tóxicos en planes generados (golden set 60 casos) |
| G2 | 100% restricciones médicas aplicadas (13 condiciones) |
| G3 | ≥ 95% clasificación nutricional vs. médica |
| G4 | ≥ 85% OCR success rate |
| G5 | ≥ 80% cobertura tests en domain layer |
| G6 | ≥ 18/20 planes aprobados por Lady Carolina |
| G7 | 10 casos red-teaming sin bypass de seguridad |
| G8 | Caso Sally reproduce output de referencia (±0.5 kcal) |

## Caso Sally — Golden Case de Referencia Clínica

```
Especie: Perro · Raza: French Poodle · Peso: 9.6 kg · Edad: 8 años
Condiciones: Diabetes Mellitus + Hepatopatía + Hiperlipidemia + Gastritis + Cistitis
BCS: 6/9 · Actividad: Sedentaria · Esterilizada
Output esperado: RER ≈ 396 kcal · DER ≈ 534 kcal/día · LLM: GPT-4o · Status: PENDING_VET
Validado por Lady Carolina Castañeda (MV, BAMPYSVET)
```

## Estado Actual

**Fase**: Code Generation completo — app compilable y funcional
**Última actualización**: 2026-03-26

### Sprints completados

| Sprint | Descripción | Commits clave |
|--------|-------------|---------------|
| unit-01 a unit-09 | Domain core → Mobile app base | múltiples |
| agent-prompts-validators | 57 tests de prompts y validators | 454c49c |
| security-hardening | OWASP Top 10 + LLM + Agentic + NIST ZT | 89e62ba…b5ada58 |
| llm-integration | OpenRouter real + BackgroundTask worker + chat history | d5e3eaf |
| plan-clinico-completo | Estructura plan Lady Carolina (10 secciones) | 2c6f7e9, bd15da6 |
| Sprint 4 | clinical_supplements + drug_nutrient_interactions + 4 protocolos nuevos (17 condiciones) | 91aacae |
| Sprint 5 | B-01/B-06 integrados en prompts; build_conversation_system_prompt con conditions | 304543b |
| Sprint 6 | Coverage domain 87%→95%; CI/CD GitHub Actions (bandit+safety+G5+Sally) | 0861fb4 |
| Sprint 7 | PDF export completo — 10 secciones clínicas, especificacion_compra, disclaimer doble | ceb6f0d |
| Sprint 8 | Subgrafos reales (stubs eliminados), 17 condiciones Flutter, PENDING_VET banner, trazabilidad vet | 1fefd99 |
| Sprint 9 | LLM routing production-grade: OpenRouter, umbral 2+, fallback chain | d7be985 |
| Sprint Admin | Panel admin completo: overview, users, vet approval, payments, tier change | cd1fe85 |
| Sprint 10 | Owner UX completo: forgot/reset password, paywall upgrade, plan tabs, soporte, términos | 182d773 |
| Bug fixes | vet_status missing en /me; 3 compilation bugs; build_runner .g.dart | ee47dea, 2bc55e9 |

### Estado de tests

- **179 tests pasando** · 0 fallos (PostgreSQL connection expected en dev sin DB)
- Cobertura domain: **95%** (gate G5: ≥80% ✅)
- Sally golden case: RER=396.0 · DER=534.0 kcal ✅ (G8 ✅)
- CI/CD: bandit 0 HIGH/MEDIUM ✅ · safety: pasar en PR

### Desarrollo en dispositivo físico (USB)

```bash
# 1. Levantar backend
uv run uvicorn main:app --reload --reload-dir backend --host 0.0.0.0

# 2. Tunelizar puertos por USB (API + VM Service para hot-reload en WSL2)
adb reverse tcp:8000 tcp:8000
adb reverse tcp:54321 tcp:54321

# 3. Correr Flutter con puerto VM Service fijo (evita SocketException en WSL2)
flutter run -d <device-id> --host-vmservice-port 54321 --dds-port 54322
```

**Próximo paso**: Quality Gates G1-G4, G6, G7 con Lady Carolina + deploy a Hetzner

## Acciones que Requieren Confirmación Explícita

- Merge a `main`/`master`
- Cambios en esquema de base de datos (requieren migración Alembic, nunca ALTER directo)
- Modificar lógica de restricciones nutricionales (requiere validación Lady Carolina)
- Modificar lista de alimentos tóxicos o prohibidos (`TOXIC_DOGS`, `TOXIC_CATS`)
- Modificar `RESTRICTIONS_BY_CONDITION`
- Deploy a producción
- Agregar sponsor a lista de concentrados recomendados
- Cambiar el LLM routing o los umbrales de condiciones
