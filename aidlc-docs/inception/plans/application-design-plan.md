# Plan: Application Design — Inception

**Fase AI-DLC**: PASO 4 — Application Design
**Estado**: ✅ Completado
**Fecha**: 2026-03-10

---

## Objetivo

Diseñar la arquitectura de la aplicación: componentes, métodos, servicios externos y dependencias.
Aplicable a NutriVet.IA completa (backend FastAPI + mobile Flutter + agente LangGraph).

## Artefactos Producidos

| Artefacto | Ubicación | Estado |
|-----------|-----------|--------|
| Lista de componentes | `inception/application-design/components.md` | ✅ |
| Métodos por componente | `inception/application-design/component-methods.md` | ✅ |
| Servicios externos e internos | `inception/application-design/services.md` | ✅ |
| Diagrama de dependencias (Mermaid) | `inception/application-design/component-dependency.md` | ✅ |
| Documento consolidado | `inception/application-design/application-design.md` | ✅ |

## Principios Arquitecturales Aplicados

1. **Clean Architecture / Hexagonal**: dependencias solo hacia adentro (domain ← application ← infrastructure ← presentation)
2. **Domain-Driven Design**: bounded contexts, aggregates, value objects, domain events
3. **Port + Adapter**: interfaces en application/, implementaciones en infrastructure/
4. **Determinismo en seguridad**: toxicidad y restricciones médicas en código, nunca en DB ni LLM
5. **Async by default**: generación de planes via ARQ (Redis), SSE streaming para chat

## Decisiones Clave Tomadas

| Decisión | Justificación | ADR |
|---------|--------------|-----|
| LangGraph como orquestador | Grafo stateful con subgrafos especializados | ADR-001 |
| Toxicidad hard-coded | Seguridad clínica no puede depender de red/DB | ADR-002 |
| JWT 15min + refresh rotativo | Balance seguridad/UX | ADR-004 |
| Flutter para mobile | iOS + Android desde un codebase | ADR-005 |
| PostgreSQL + Alembic | ACID, migraciones controladas | ADR-006 |
| Hetzner + Coolify | Costo, control, SSE nativo | ADR-022 |
| OpenRouter | Proveedor LLM unificado con routing por tier | ADR-019 |

## Restricciones

- Domain layer: CERO imports externos (Python stdlib only)
- LLM externo: solo IDs anónimos (UUID), nunca PII
- agent_traces: INSERT only, nunca UPDATE
