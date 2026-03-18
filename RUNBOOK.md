# RUNBOOK.md — Operación NutriVet.IA v2
> Documento de operación, incidentes y mantenimiento.
> Mantener actualizado con cada release significativo.

---

## Servicios y URLs

| Entorno | API URL | Status |
|---------|---------|--------|
| Dev | http://localhost:8000 | Local uvicorn |
| Staging | https://staging.api.nutrivet.app | Coolify — Hetzner CPX31 (staging) |
| Producción | https://api.nutrivet.app | Coolify — Hetzner CPX31 (prod) |

---

## Comandos de Arranque

```bash
# Desarrollo local
cd backend/
cp .env.example .env             # Configurar variables
docker-compose up -d             # Levantar PostgreSQL local
uvicorn app.main:app --reload    # API con hot-reload

# Tests
pytest --cov=app tests/ -v
pytest tests/evals/ -v           # Evaluaciones del agente (más lentas)

# Calidad
ruff check app/
mypy app/ --strict
bandit -r app/ -f json
safety check

# Migraciones
alembic upgrade head             # Aplicar migraciones pendientes
alembic revision --autogenerate -m "descripción del cambio"
```

---

## Incidentes — Prioridades y Respuesta

### P0 — Crítico (respuesta inmediata, < 15 min)

**Plan con ingrediente tóxico generado y entregado al usuario**
```
1. Identificar el plan_id y pet_id afectados
2. Cambiar status del plan a BLOCKED inmediatamente
   UPDATE nutrition_plans SET status='BLOCKED',
   block_reason='Toxicity incident — P0'
   WHERE id = '{plan_id}';
3. Notificar al owner vía email/push: no implementar el plan
4. Notificar al vet asignado (si existe)
5. Crear entrada en plan_changes con tipo 'emergency_block'
6. Investigar cómo se generó el alimento tóxico
7. Post-mortem obligatorio dentro de 48h
```

**OCR aceptó imagen de marca (violación de imparcialidad)**
```
1. Identificar el scan_id
2. Marcar el scan como inválido
3. Notificar al usuario que repita el escaneo con imagen de tabla nutricional
4. Revisar la lógica de validación de image_type en product_scanner.py
```

### P1 — Alto (respuesta < 1 hora)

**Plan generado sin aplicar restricciones de condición médica**
```
1. Identificar planes afectados del día
2. Cambiar status a PENDING_VET para revisión manual
3. Notificar a veterinarios de los pacientes afectados
4. Fix en restrictions_db.py + deploy urgente
```

**Cálculo de kcal incorrecto (factor erróneo)**
```
1. Consultar agent_traces para identificar el rango de tiempo afectado
2. Recalcular RER/DER para planes del período
3. Si diferencia > 15%: regenerar el plan automáticamente
4. Si diferencia < 15%: marcar para revisión en próximo control
```

**Sponsor mostrado sin verificación veterinaria**
```
1. Desactivar el sponsor inmediatamente:
   UPDATE sponsors SET is_active=FALSE WHERE id='{sponsor_id}';
2. Los planes que lo mostraron quedan sin cambios (el sponsor ya no aparece en nuevas consultas)
3. Investigar cómo se activó sin verified_by_vet_id
```

### P2 — Medio (respuesta < 4 horas)

- OCR devuelve confianza < 0.70 de forma sistemática
- Latencia de generación de plan > 60 segundos
- Tasa de error 5xx > 1% en 15 minutos

### P3 — Bajo (respuesta < 24 horas)

- Fallo en envío de emails de verificación
- Métricas de observabilidad no llegando a Sentry / Coolify logs
- Warnings de bandit en PRs pendientes

---

## Métricas Clave

### Salud del Sistema
| Métrica | Umbral Normal | Alerta |
|---------|--------------|--------|
| Latencia API (p95) | < 500ms | > 2s |
| Latencia generación plan (p95) | < 30s | > 60s |
| Latencia OCR (p95) | < 10s | > 20s |
| Tasa de error 5xx | < 0.1% | > 1% |
| Disponibilidad | > 99.5% | < 99% |

### Calidad Clínica
| Métrica | Umbral Normal | Alerta |
|---------|--------------|--------|
| % planes BLOCKED por toxicidad | < 0.5% (falsos positivos) | > 2% |
| % planes REJECTED por vet | < 30% | > 50% |
| Confianza promedio OCR | > 0.80 | < 0.70 |
| % planes con alerta de alergia "no sé" aceptada | Monitorear | — |

### Negocio
| Métrica | Objetivo Mes 6 |
|---------|---------------|
| Planes generados/mes | 500 |
| Usuarios activos/mes | 1,000 |
| Vets activos | 10 |
| Tasa conversión registro→plan | 60% |

---

## Logs y Observabilidad

```bash
# Ver logs del backend en tiempo real (Coolify Dashboard → App → Logs)
# O via SSH al servidor Hetzner:
docker logs nutrivet-backend --follow --tail 100

# Buscar errores de toxicidad en los últimos 30 minutos (Sentry)
# → Sentry Dashboard → Issues → filtrar por "toxicity_check"
# O directo en DB:

# Ver trazas del agente con latencia > 30s
SELECT * FROM agent_traces
WHERE latency_ms > 30000
ORDER BY created_at DESC
LIMIT 20;

# Ver planes BLOCKED en las últimas 24h
SELECT np.id, np.block_reason, p.name, u.email
FROM nutrition_plans np
JOIN pets p ON np.pet_id = p.id
JOIN users u ON p.owner_id = u.id
WHERE np.status = 'BLOCKED'
AND np.updated_at > NOW() - INTERVAL '24 hours';
```

---

## Mantenimiento Rutinario

### Diario (automatizado)
- Health check via Coolify (GET /health cada 30s — alerta automática si falla)
- Verificar rate limit OpenRouter no superado
- Revisar tasa de error 5xx en Sentry

### Semanal
- Revisar safety check de dependencias
- Revisar planes PENDING_VET con más de 72h sin firma
- Revisar métricas de calidad de OCR

### Mensual
- Actualizar lista de tóxicos si hay nuevas publicaciones NRC/AAFCO
- Revisar factores de ajuste de kcal con veterinaria validadora
- Revisar sponsors activos: vigencia y perfil nutricional actualizado
- Verificar lifecycle rule R2 para imágenes OCR > 90 días (Cloudflare R2 Dashboard → Lifecycle Rules)

---

## Acciones que Requieren Confirmación Explícita

Nunca ejecutar en producción sin aprobación del equipo:
- Cambio en `TOXIC_DOGS` o `TOXIC_CATS` (domain layer)
- Cambio en `RESTRICTIONS_BY_CONDITION`
- Cambio en `FACTOR_TABLE` o `BCS_ADJUSTMENTS` del calculador de kcal
- Agregar o activar un sponsor
- `ALTER TABLE` en producción (usar Alembic)
- Eliminar datos de usuarios o mascotas
- Reset de contraseña masivo

---

## Contactos de Emergencia

| Rol | Nombre | Contacto |
|-----|--------|---------|
| AI Engineer | Sadid Romero | — |
| Veterinaria validadora | Lady Carolina Castañeda | BAMPYSVET |
| Veterinaria validadora nutricional | Lady Carolina Castañeda | BAMPYSVET |
