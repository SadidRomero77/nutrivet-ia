# ADR-016 — Sin Estado RECHAZADO en el Ciclo de Vida del Plan

**Estado**: Aceptado
**Fecha**: 2026-03
**Autores**: Sadid Romero (AI Engineer)

---

## Contexto

Durante el diseño del flujo HITL se propuso agregar un estado "RECHAZADO" para cuando el vet no está de acuerdo con el plan generado por el agente. Sin embargo, al analizar el flujo completo, el estado RECHAZADO crea un callejón sin salida: el plan está rechazado, ¿y ahora qué? ¿El owner tiene que generar uno nuevo manualmente? ¿El agente lo regenera automáticamente sin contexto del rechazo?

## Decisión

Eliminar el estado RECHAZADO del ciclo de vida del plan. En su lugar, el vet tiene exactamente dos opciones:

1. **Editar + Aprobar**: El vet modifica el plan (con justificación obligatoria) y lo aprueba → `ACTIVE`.
2. **Devolver con comentario**: El vet devuelve el plan al owner con una nota explicativa → plan regresa a `PENDING_VET` con el comentario visible. El owner actualiza el perfil de la mascota y el agente regenera.

```
PENDING_VET
    │
    ├── Vet edita + aprueba → ACTIVE ✅
    │
    └── Vet devuelve con comentario → PENDING_VET (con nota) ↩️
                                          │
                                    Owner actualiza perfil
                                          │
                                    Agente regenera plan
                                          │
                                      PENDING_VET (nuevo plan)
```

## Opciones Consideradas

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| Estado RECHAZADO | Explícito | Callejón sin salida — ¿qué hace el owner? |
| Solo editar+aprobar | Simple | Vet no puede devolver sin modificar |
| Editar+aprobar O devolver (elegida) | Siempre hay próximo paso | Más lógica de workflow |

## Consecuencias

**Positivas**:
- El owner siempre sabe qué hacer después (leer el comentario, actualizar el perfil).
- El vet no está obligado a editar si el problema está en el perfil del animal.
- El ciclo de vida del plan siempre tiene un next step — no hay estados terminales de error.

**Negativas**:
- El "devolver con comentario" requiere una UI adicional en el dashboard del vet.
- El comentario del vet debe ser obligatorio (no puede devolver sin explicar por qué).

**Estados finales del plan**: `ACTIVE` (aprobado) o `ARCHIVED` (reemplazado). RECHAZADO no existe.
