# NFR Requirements — unit-01-domain-core
**Unidad**: unit-01-domain-core
**Fase**: Construction — NFR Requirements
**Fecha**: 2026-03-16

## Requisitos No Funcionales del Domain Core

### NFR-01: Cobertura de Tests — 80% Mínimo (Quality Gate G5)
- Cobertura mínima: **80%** en toda la capa `domain/`.
- Cobertura obligatoria **100%** en `domain/safety/` (toxicidad y restricciones médicas).
- El CI falla si la cobertura está por debajo del umbral.
- Comando: `pytest --cov=app/domain tests/domain/ --cov-fail-under=80`

### NFR-02: Golden Case Sally — Tolerancia ±0.5 kcal (Quality Gate G8)
- El cálculo NRC para Sally debe producir: RER ≈ 396 kcal, DER ≈ 534 kcal.
- Tolerancia: ±0.5 kcal en ambos valores.
- Este test corre en cada PR y en el pipeline de CI pre-deploy.

### NFR-03: Cero Dependencias Externas
- El módulo `domain/` NO importa ninguna librería de terceros.
- Verificado en CI con `pipdeptree` o análisis estático de imports.
- Garantiza que el dominio es testeable de forma aislada sin contenedor.

### NFR-04: 0% Tóxicos en Planes (Quality Gate G1)
- El `FoodSafetyChecker` tiene **0% tolerancia** a falsos negativos.
- Golden set de 60 casos debe producir 0 ingredientes tóxicos en planes.
- Cualquier ingrediente tóxico en un plan generado es un P0 inmediato.

### NFR-05: 100% Restricciones Médicas Aplicadas (Quality Gate G2)
- El `MedicalRestrictionEngine` debe aplicar el 100% de las restricciones hard-coded.
- Verificado con test matrix: 13 condiciones × ingredientes prohibidos.

### NFR-06: ≥95% Clasificación Nutricional vs. Médica (Quality Gate G3)
- El `QueryClassifier` debe clasificar correctamente ≥95% de consultas.
- Evaluado sobre dataset de 100 consultas anotadas (nutricionales vs. médicas).

### NFR-07: Precisión Numérica con Decimal
- Todos los cálculos calóricos usan `Decimal`, no `float`.
- Previene errores de punto flotante que podrían alterar el resultado de Sally.

### NFR-08: Inmutabilidad de Trazas
- `AgentTrace` es append-only en el dominio.
- No existe método `update()` ni `delete()` en el port `AgentTraceRepositoryPort`.
- Verificado por ausencia de UPDATE SQL en cualquier repositorio de trazas.

### NFR-09: Stateless
- Los servicios de dominio (NRCCalculator, FoodSafetyChecker, etc.) son stateless.
- Sin estado mutable en runtime en instancias de servicio.
- Permite instanciación segura en contextos concurrentes (workers ARQ, Uvicorn).

### NFR-10: Rendimiento de Cálculos
- `NRCCalculator.calculate()` debe completar en < 1ms.
- `FoodSafetyChecker.check()` debe completar en < 1ms.
- `MedicalRestrictionEngine.check_all()` debe completar en < 5ms (para 13 condiciones).
- No hay I/O en el dominio — todo debe ser ultra-rápido.
