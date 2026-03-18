# Specs — NutriVet.IA

Especificaciones técnicas del proyecto. Esta carpeta es la fuente de verdad para implementación.

---

## Índice

| Archivo | Descripción | Actualizar cuando... |
|---------|-------------|----------------------|
| [`prd.md`](./prd.md) | Product Requirements Document completo v2.0 | Cambia un requisito de negocio |
| [`backend.md`](./backend.md) | Estructura FastAPI, endpoints, capas, pyproject.toml | Cambia la estructura del backend |
| [`database.md`](./database.md) | Esquema PostgreSQL completo, índices, constraints | Cambia el esquema de BD (siempre con migración Alembic) |
| [`frontend.md`](./frontend.md) | Estructura Flutter, pantallas, pubspec.yaml | Cambia la estructura del mobile app |
| [`deployment.md`](./deployment.md) | Hetzner + Coolify, GitHub Actions, OWASP (ver ADR-022) | Cambia la infraestructura o pipeline CI/CD |
| [`tool-specs/`](./tool-specs/) | Specs de tools del agente LangGraph | Se implementa o modifica una tool del agente |

## Relación con Otros Documentos

- **¿Por qué?** → [`specs/prd.md`](./prd.md)
- **¿Qué decisión arquitectural?** → [`decisions/`](../decisions/README.md) (ADRs)
- **¿Cómo implementar?** → Este directorio (`specs/`)
- **¿Cuáles son las unidades?** → [`aidlc-docs/inception/units/`](../aidlc-docs/inception/units/)
- **¿Qué comportamientos debe tener?** → [`behaviors/`](../behaviors/)

## Nota sobre database.md

`database.md` es un snapshot aprobado del esquema. La fuente de verdad en código es
`backend/migrations/versions/`. Actualizar este archivo siempre junto con la migración Alembic.
