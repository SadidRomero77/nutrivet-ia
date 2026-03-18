# Plan: NFR Requirements — Unit 07: conversation-service

**Unidad**: unit-07-conversation-service
**Fase AI-DLC**: C2 — NFR Requirements
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Requerimientos No Funcionales del conversation-service

### Performance

| Operación | SLA | Justificación |
|-----------|-----|--------------|
| SSE: primer token visible | < 1s | UX crítico — usuario ve respuesta comenzando rápido |
| QueryClassifier (determinar tipo) | < 300ms | LLM call con clasificación binaria |
| FreemiumGateChecker (verificar cuota) | < 20ms | DB lookup atómico |
| GET /v1/agent/chat/history | < 100ms | Lista paginada de conversaciones |
| Emergency detection | < 1ms | Frozenset determinístico — ya implementado en unit-05 |

### Quality Gate G3

```
≥ 95% de precisión en clasificación nutricional vs. médica
Medido: consultas médicas correctamente remitidas / total consultas médicas
Testear con conjunto de 100 casos etiquetados (50 nutricional, 50 médica)
```

**Nunca aceptar < 95%** antes de lanzar (Quality Gate G3).

### Seguridad

**Free tier — cuota atómica**:
- Cuota persistida en tabla `agent_quotas` — no en sesión ni en cookie.
- Decremento atómico en DB (SELECT FOR UPDATE o atomic UPDATE).
- No se puede "hacer trampa" limpiando cookies o cambiando dispositivo.
- Emergencias: bypass incondicional — no decrementar cuota, no bloquear.

**Disclaimer obligatorio**:
- Presente en TODA respuesta del agente (Constitution REGLA 8).
- Incluido en el evento final del SSE stream (`done: true`).
- Incluido también en mensajes de remisión al vet.
- Test: verificar que NINGUNA respuesta del agente omite el disclaimer.

**Datos en system prompt**:
- Solo `pet_id` UUID para trazabilidad — no nombre en texto plano en traces.
- El system prompt usa el nombre del pet (para UX) pero las trazas registran solo el ID.

**Historial en contexto LLM**:
- Los mensajes del historial pasan al LLM — NO deben contener condiciones médicas
  en texto plano (solo referencias por ID si es necesario).

### Confiabilidad

- Si QueryClassifier falla → default a `NUTRITIONAL` → responde con disclaimer (comportamiento seguro).
- Si LLM stream se interrumpe → SSE envía evento de error al cliente.
- Si `agent_quotas` no existe para un user → crear registro con cuota inicial.

### Mantenibilidad

- Cobertura mínima: **80%** en conversation-service modules.
- Type hints obligatorios. Docstrings en español.
- Ruff + bandit: 0 errores antes de PR.

## Checklist NFR conversation-service

- [ ] SSE primer token < 1s (test con timer en integration test)
- [ ] G3: ≥ 95% clasificación nutricional vs médica (test set 100 casos)
- [ ] Disclaimer presente en TODA respuesta (test automatizado en cada response)
- [ ] Emergencias bypass cuota (test con Free tier + emergency query)
- [ ] Cuota Free: 3/día + 9 total — atómico, no bypasseable vía sesión
- [ ] Historial 10 mensajes en contexto LLM (verificar en integration test)
- [ ] Cobertura ≥ 80%
- [ ] Ruff + bandit sin errores

## Referencias

- Global: `_shared/nfr-requirements.md`
- Unit spec: `inception/units/unit-07-conversation-service.md`
- ADR-021: SSE streaming
- Constitution: REGLA 8 (disclaimer), REGLA 9 (límite nutricional/médico)
- Quality Gates: G3
