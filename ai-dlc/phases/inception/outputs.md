# Outputs de Inception — NutriVet.IA Fase 1

Registro de artefactos producidos durante la fase Inception del proyecto.

---

## Completado ✅

### Documentación de Producto
| Artefacto | Ubicación | Estado |
|-----------|-----------|--------|
| PRD v2.0 (14 decisiones estratégicas) | `specs/prd.md` | ✅ Aprobado |
| Product Vision Board | `docs/research/pvb.md` | ✅ |
| ICP (3 segmentos) | `docs/research/icp.md` | ✅ |
| Análisis de mercado LATAM | `docs/research/mercado.md` | ✅ |
| Deep research nutrición vet + IA | `docs/research/overview.md` | ✅ |

### Especificaciones Técnicas
| Artefacto | Ubicación | Estado |
|-----------|-----------|--------|
| Backend Spec (FastAPI, endpoints, LangGraph) | `specs/backend.md` | ✅ |
| Database Spec (PostgreSQL schema completo) | `specs/database.md` | ✅ |
| Frontend Spec (Flutter, rutas, offline) | `specs/frontend.md` | ✅ |
| Deploy & Security Spec (Hetzner + Coolify, CI/CD) | `specs/deployment.md` | ✅ |
| SDD (Software Design Document) | `docs/SDD.md` | ✅ |

### Decisiones de Arquitectura (ADRs)
| ADR | Decisión | Estado |
|-----|---------|--------|
| ADR-001 | LangGraph como orquestador del agente | ✅ |
| ADR-002 | Toxicidad hard-coded en domain layer | ✅ |
| ~~ADR-003~~ | ~~AWS Lambda + API Gateway~~ | ⚠️ Superseeded por ADR-022 |
| ADR-004 | JWT access 15min + refresh rotativo | ✅ |
| ADR-005 | Flutter para mobile (iOS + Android) | ✅ |
| ADR-006 | PostgreSQL + Alembic | ✅ |
| ADR-007 | BCS escala 1-9 con selector visual | ✅ |
| ADR-008 | Dos modalidades de plan (Natural/Concentrado) | ✅ |
| ADR-009 | Sponsors con tag "Patrocinado" obligatorio | ✅ |
| ADR-010 | OCR solo tabla nutricional/ingredientes | ✅ |
| ADR-011 | Freemium (Free/Básico/Premium/Vet) | ✅ |
| ADR-012 | Base de datos LATAM-wide, no Colombia-first | ✅ |
| ADR-013 | LLM routing por condiciones médicas | ✅ |

### Tool Specs del Agente
| Tool | Ubicación | Estado |
|------|-----------|--------|
| nutrition_calculator | `specs/tool-specs/nutrition-calculator.md` | ✅ |
| food_toxicity_checker | `specs/tool-specs/food-toxicity-checker.md` | ✅ |
| plan_generator | `specs/tool-specs/plan-generator.md` | ✅ |
| product_scanner | `specs/tool-specs/product-scanner.md` | ✅ |
| concentrate_advisor | `specs/tool-specs/concentrate-advisor.md` | ✅ |

---

## Pendiente — Inception Restante

| Artefacto | Ubicación | Prioridad |
|-----------|-----------|-----------|
| DDD completo (ubiquitous language, bounded contexts, aggregates) | `domain/` | ALTA |
| Escenarios BDD / Gherkin (8 flujos críticos) | `behaviors/` | ALTA |
| User stories por rol (owner / vet) | `ai-dlc/phases/inception/user-stories/` | MEDIA |
| AI-DLC completo (esta estructura) | `ai-dlc/` | ALTA → EN PROGRESO |

---

## Golden Case de Referencia Clínica

**Caso Sally** — validado por Lady Carolina Castañeda (MV, BAMPYSVET):
```
French Poodle · 9.6 kg · 8 años · esterilizada · sedentaria · BCS 6/9
Condiciones: Diabetes + Hepatopatía + Hiperlipidemia + Gastritis + Cistitis
RER ≈ 396 kcal · DER ≈ 534 kcal/día · LLM: GPT-4o · Status: PENDING_VET
```
