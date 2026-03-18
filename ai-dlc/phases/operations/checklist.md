# Checklist de Deploy — Fase Operations

Ejecutar antes de cada deploy a staging y producción.

---

## Pre-Deploy (Staging)

### Quality Gates (todos en verde)
- [ ] G1: 0 tóxicos en planes (golden set 60 casos)
- [ ] G2: 100% restricciones médicas aplicadas (13 condiciones)
- [ ] G3: ≥ 95% clasificación nutricional vs médica
- [ ] G4: ≥ 85% OCR success rate
- [ ] G5: ≥ 80% cobertura tests en domain layer
- [ ] G6: ≥ 18/20 planes aprobados por Lady Carolina
- [ ] G7: 10 casos red-teaming sin bypass de seguridad
- [ ] G8: Caso Sally reproduce output de referencia (±0.5 kcal)

### Seguridad
- [ ] `bandit -r app/` → 0 issues HIGH/MEDIUM
- [ ] `safety check` → 0 CVEs críticas
- [ ] Secrets en variables de entorno — no en código
- [ ] Variables de entorno de staging configuradas en Coolify Dashboard (no en código ni .env commiteado)

### Infraestructura
- [ ] Migraciones Alembic aplicadas en staging: `alembic upgrade head`
- [ ] Migración reversible verificada: `alembic downgrade -1` funciona
- [ ] Uvicorn workers configurados (default: 2 — ajustar en Coolify si carga > 80% CPU)
- [ ] CORS configurado explícitamente en FastAPI main.py (sin wildcard)

### Smoke Tests en Staging
- [ ] `POST /api/v1/auth/register` → 201
- [ ] `POST /api/v1/auth/login` → 200 + JWT válido
- [ ] `POST /api/v1/pets/` → 201 (wizard completo)
- [ ] `POST /api/v1/plans/generate` → 200 (mascota sana → ACTIVE)
- [ ] `POST /api/v1/plans/generate` → 200 (mascota con condición → PENDING_VET)
- [ ] Caso Sally: RER ≈ 396 kcal · DER ≈ 534 kcal (±0.5)
- [ ] `POST /api/v1/scanner/analyze` → 200 (imagen válida)
- [ ] `POST /api/v1/agent/query` → mensaje de referral para consulta médica

---

## Deploy a Producción

- [ ] Staging smoke tests todos en verde.
- [ ] Trigger Coolify deploy producción (aprobación manual en GitHub Actions environment "production").
- [ ] Coolify aplica: git pull → docker build → health check → swap containers (zero-downtime).
- [ ] Monitorear `toxic_food_bypass_rate` durante 15min — debe ser 0%.
- [ ] Monitorear `hitl_skip_rate` durante 15min — debe ser 0%.
- [ ] Si métricas normales: deploy completado. Coolify guarda el deploy anterior para rollback.

---

## Post-Deploy

- [ ] Métricas de p95 de latencia normales (< 30s plan generation).
- [ ] 0 errores 5xx en los primeros 30 minutos.
- [ ] Notificar a Lady Carolina: "Deploy exitoso — evals clínicos disponibles".
- [ ] Actualizar `ai-dlc/phases/operations/outputs.md` con versión desplegada.

---

## Rollback

Si cualquier métrica crítica falla post-deploy:
1. En Coolify Dashboard → Deployments → click en deploy anterior → "Rollback" (< 30 segundos).
2. Notificar a Sadid Romero.
3. Registrar incidente en `RUNBOOK.md`.
4. No reutilizar `prod-rollback` hasta investigar la causa raíz.
