# Checklist de Salida — Fase Construction

Todos los items deben estar marcados antes de pasar a Operations (deploy).

---

## Tests y Cobertura

- [ ] Cobertura `domain/` ≥ 80% (`pytest --cov=app/domain --cov-fail-under=80`).
- [ ] Caso Sally pasa: `RER ≈ 396 kcal · DER ≈ 534 kcal/día` (±0.5 kcal).
- [ ] Golden set 60 casos → 0 tóxicos en planes generados (Gate G1).
- [ ] 100% restricciones médicas aplicadas en tests (13 condiciones, Gate G2).
- [ ] ≥ 95% clasificación correcta nutricional vs médica (Gate G3).
- [ ] ≥ 85% OCR success rate en golden set (Gate G4).
- [ ] Todos los escenarios Gherkin de `behaviors/` tienen test automatizado correspondiente.

## Calidad de Código

- [ ] `ruff check .` → 0 errores.
- [ ] `bandit -r app/` → 0 issues HIGH o MEDIUM.
- [ ] `safety check` → 0 CVEs críticas.
- [ ] Type hints en TODA función y método en backend.
- [ ] Docstrings en español en todos los módulos, clases y funciones públicas.
- [ ] Sin imports de librerías externas en `domain/`.
- [ ] Sin `infrastructure/` importado directamente desde `application/`.

## Seguridad

- [ ] Input validation con Pydantic en todos los endpoints.
- [ ] RBAC validado en cada endpoint (`@require_role`).
- [ ] Sin secrets hardcoded (revisar con `git diff` + `bandit`).
- [ ] Datos médicos: campos sensibles marcados para encriptar AES-256.
- [ ] Prompts a LLMs externos: solo IDs anónimos, sin PII.
- [ ] `agent_traces`: solo INSERT, sin UPDATE.

## LLM y Agente

- [ ] LLM routing correcto: 0 cond → Ollama · 1-2 → Groq · 3+ → GPT-4o.
- [ ] Fallback implementado con timeouts y retry × 2.
- [ ] Tool specs de `specs/tool-specs/` implementadas fielmente.
- [ ] HITL activado solo para mascotas con condición médica.
- [ ] Mascotas sanas → `ACTIVE` directo (sin PENDING_VET).

## Base de Datos

- [ ] Migraciones Alembic creadas y revisadas (sin ALTER directo).
- [ ] Migraciones aplicadas en dev y probadas.
- [ ] Índices de `specs/database.md` implementados.
- [ ] Constraints y foreign keys activos.

## Mobile (Flutter)

- [ ] Wizard de mascota 5 pasos, 12 campos.
- [ ] BCS selector visual 3×3 funcional.
- [ ] Estrategia offline con Hive implementada.
- [ ] JWT interceptor con refresh automático.
- [ ] OCR pipeline con compresión de imagen.

## PR y Documentación

- [ ] PR description incluye link al `/specify` y `/plan` de la feature.
- [ ] `gitnexus_detect_changes` ejecutado — impacto documentado en PR.
- [ ] Si hay nueva decisión arquitectural: ADR creado en `decisions/`.
- [ ] CHANGELOG actualizado.

## Aprobación

- [ ] ≥ 18/20 planes aprobados por Lady Carolina Castañeda (MV) — Gate G6.
- [ ] 10 casos red-teaming sin bypass de seguridad — Gate G7.
