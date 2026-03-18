# SHIPPING-CHECKLIST.md — NutriVet.IA v2
> Revisar antes de cada merge a `main` y antes de cada release.
> Basado en Playbook §8 + requisitos clínicos v2.

---

## Pre-Merge a `main` (cada PR)

### Calidad de Código
- [ ] `ruff check app/` pasa sin errores
- [ ] `mypy app/ --strict` pasa sin errores
- [ ] `pytest --cov=app --cov-fail-under=80 tests/` pasa
- [ ] Tests de evaluación críticos al 100%: `test_toxicity_block.py`, `test_vet_escalation.py`, `test_allergy_unknown_alert.py`
- [ ] Type hints en todas las funciones públicas
- [ ] Docstrings en español en todas las clases y métodos públicos nuevos

### Seguridad
- [ ] `bandit -r app/` — sin findings de severidad HIGH
- [ ] `safety check` — sin vulnerabilidades críticas en dependencias
- [ ] No hay secrets en el código (grep por `api_key=`, `password=`, `secret=`)
- [ ] Datos médicos nuevos siempre en columnas `_encrypted` (BYTEA)
- [ ] Nuevo endpoint tiene RBAC verificado en middleware
- [ ] Nuevo endpoint tiene validación Pydantic del input

### Lógica Clínica (verificar con veterinaria antes de merge)
- [ ] Cambios en `toxicity_db.py` revisados por Lady Carolina (MV)
- [ ] Cambios en `restrictions_db.py` revisados por Lady Carolina (MV)
- [ ] Cambios en `kcal_calculator.py` validados contra tabla NRC/AAFCO
- [ ] Factor de ajuste nuevo tiene test con caso de referencia real
- [ ] Lista de ingredientes prohibidos no fue reducida sin validación veterinaria

### OCR e Imparcialidad
- [ ] `product_scanner.py` sigue rechazando imágenes de marca/logo
- [ ] `image_type` validado antes de llamar GPT-4o Vision
- [ ] Resultado del OCR evaluado contra perfil completo del paciente

### Sponsors
- [ ] Nuevo sponsor requiere `verified_by_vet_id` no nulo para activarse
- [ ] Tag "Patrocinado" siempre visible en UI
- [ ] Sponsor no se muestra si su perfil no coincide con el paciente
- [ ] Máximo 3 sponsors por resultado validado en query

### Base de Datos
- [ ] Nuevas columnas tienen migración Alembic generada
- [ ] Migración tiene `upgrade()` y `downgrade()` implementados
- [ ] Migración probada en staging
- [ ] No hay `ALTER COLUMN` que cambie tipo sin migración de datos
- [ ] No hay `DROP COLUMN` sin periodo de deprecación

### Alergias y Responsabilidad
- [ ] Flujo "no sé" siempre muestra alerta antes de proceder
- [ ] `owner_accepted_risk` se guarda en base de datos
- [ ] Plan generado con `unknown_allergy_flag` incluye disclaimer visible

---

## Pre-Release a Producción

### Todas las verificaciones del Pre-Merge +

### Funcionalidad Clínica Completa
- [ ] Registro de usuario: nombre, email, ciudad, país funcionando
- [ ] Wizard de mascota: todos los pasos (BCS, antecedentes, alergias)
- [ ] BCS selector muestra imágenes correctas por especie (perro vs gato)
- [ ] Campo "ubicación del cáncer" se muestra solo cuando se selecciona "cancerígeno"
- [ ] Alerta de alergia "no sé" muestra disclaimer y requiere checkbox
- [ ] Selector de modalidad (natural vs concentrado) funciona
- [ ] Cálculo de kcal validado: Sally (9.6kg, esterilizada, senior, baja actividad) → 534 kcal ✓
- [ ] Ingredientes prohibidos aparecen en el plan según condición médica
- [ ] Snacks se generan correctamente
- [ ] Protocolo de transición de 7 días incluido en el plan
- [ ] Protocolo de emergencia digestiva incluido en el plan
- [ ] Disclaimer aparece en toda pantalla de plan (no se puede ocultar)
- [ ] Plan con condición médica → estado PENDING_VET
- [ ] Flujo de firma veterinaria funciona (ACTIVE) y rechazo (REJECTED)

### OCR
- [ ] Scanner rechaza imagen de frente de empaque con mensaje claro
- [ ] Scanner acepta tabla nutricional y extrae valores correctamente
- [ ] Semáforo (verde/amarillo/rojo) refleja evaluación vs perfil del paciente
- [ ] Imagen se sube a Cloudflare R2 con lifecycle rule de 90 días configurada

### Seguridad en Producción
- [ ] Variables de entorno configuradas en Coolify Dashboard (no en código ni .env commiteado)
- [ ] CORS configurado explícitamente (no wildcard)
- [ ] JWT expiración configurada (15 min access, 30 días refresh)
- [ ] Rate limiting activo (Cloudflare básico + RateLimitMiddleware en FastAPI)
- [ ] Logs no contienen PII ni datos médicos en texto plano
- [ ] Imagen Docker construida desde Dockerfile limpio (sin secretos, sin .env)

### Observabilidad
- [ ] Sentry configurado con alertas para: errores 5xx, tasa de toxicity_block, plan generation > 30s
- [ ] `agent_traces` registrando jobs correctamente
- [ ] Alertas de métricas clínicas configuradas

### Comunicación
- [ ] Email de verificación de cuenta funcionando
- [ ] Notificación al vet cuando plan queda PENDING_VET
- [ ] Notificación al owner cuando plan es firmado o rechazado

---

## Checklist OWASP Top 10 (por nuevo endpoint)

| # | Vulnerabilidad | Verificación |
|---|---------------|--------------|
| A01 | Broken Access Control | RBAC en middleware para el nuevo endpoint |
| A02 | Cryptographic Failures | Datos médicos nuevos cifrados AES-256 |
| A03 | Injection | Input validado con Pydantic. Queries con SQLAlchemy parameterizado |
| A04 | Insecure Design | Lógica de negocio en domain/use_cases (no en router) |
| A05 | Security Misconfiguration | debug=False en prod, headers seguros, sin secrets en código |
| A06 | Vulnerable Components | `safety check` en el PR |
| A07 | Auth Failures | Token validado, roles verificados, sin secrets en URL |
| A08 | Software Integrity | Docker image sin secretos, SHA pinning en Actions, `safety check` en PR |
| A09 | Logging Failures | structlog JSON sin PII, sin datos clínicos en texto |
| A10 | SSRF | Validar URLs externas si el endpoint las procesa |

---

## Regla de Oro — Antes de Cualquier Release

> Si alguno de los siguientes tests falla → **NO** hay release:
> 1. `test_toxicity_block.py` — 100% pass requerido
> 2. `test_vet_escalation.py` — 100% pass requerido
> 3. `test_allergy_unknown_alert.py` — 100% pass requerido
> 4. `test_kcal_calculator.py` con caso Sally (9.6 kg → 534 kcal) — 100% pass requerido
>
> Estos tests son los guardianes de la seguridad clínica del producto.
