# ADR-018 — Vet como Creador de Planes y Modelo ClinicPet

**Estado**: Aceptado
**Fecha**: 2026-03-10
**Autores**: Sadid Romero (AI Engineer)
**Revisores**: Lady Carolina Castañeda (MV, BAMPYSVET)

---

## Contexto

El modelo inicial asumía que el vet solo actúa como revisor (HITL) de planes generados por owners. Sin embargo, existen pacientes cuyos propietarios no tienen smartphone o no quieren descargar la app. El vet necesita poder gestionar estos pacientes directamente desde la plataforma, generar planes y compartir el PDF como canal de entrega.

## Decisión

Introducir dos tipos de mascota en el sistema y ampliar el rol del vet a creador de planes:

### Dos tipos de mascota

```python
class PetOrigin(str, Enum):
    APP_PET = "app_pet"        # Creada por owner con cuenta activa
    CLINIC_PET = "clinic_pet"  # Creada por vet para paciente sin app
```

### Flujo ClinicPet

```
Vet dashboard → "Nuevo Paciente"
  → Vet ingresa 13 campos del wizard
  → Agente genera plan (LLM routing normal)
  → Plan va DIRECTO a aprobación del vet (no PENDING_VET)
  → Vet aprueba/edita → status = ACTIVE
  → Vet comparte PDF por WhatsApp/email/link
  → Opcional: Vet envía link de reclamación al propietario
```

### Reclamación de mascota

Si el propietario descarga la app después:
1. Vet genera código de reclamación desde su dashboard
2. Propietario crea cuenta y usa el código
3. `clinic_pet` → `app_pet` con historial completo preservado
4. El vet sigue vinculado como vet asignado de la mascota

### Regla HITL actualizada

```
Owner crea plan + condición médica  → PENDING_VET (vet externo revisa)
Vet crea plan directamente          → ACTIVE directo (vet es creador Y aprobador)
Owner crea plan sin condición       → ACTIVE directo
```

### Modelo de suscripción del vet

| Tier | Costo | Capacidades |
|------|-------|-------------|
| Vet FREE | $0 | Revisar planes de owners (máx 10/mes). Sin ClinicPets. |
| Vet BÁSICO | $89.000 COP/mes | Revisiones ilimitadas + ClinicPets ilimitados + dashboard + PDF + invitaciones |
| Vet CLÍNICA | A negociar | Multi-vet + facturación unificada + vista consolidada |

### Vet de plataforma (safety net)

Lady Carolina (MVP) actúa como vet de plataforma:
- Recibe todos los planes sin vet asignado
- Recibe overflow de vets FREE que superan límite mensual
- Recibe planes de vets que cancelaron suscripción

## Opciones Consideradas

| Opción | Descartada porque |
|--------|------------------|
| Solo HITL (vet como revisor) | No cubre pacientes sin app — limita adopción veterinaria |
| Vet crea plan y va a PENDING_VET de otro vet | Sin sentido clínico — el vet no necesita revisión de otro vet para su propio trabajo |
| Modelo elegido (ClinicPet + aprobación directa) | Cubre todos los casos, respeta responsabilidad clínica del vet |

## Consecuencias

**Positivas**:
- El vet adopta la plataforma como herramienta de trabajo diario — no solo como revisor ocasional
- Canal de adquisición orgánica: el vet trae propietarios a la app vía link de reclamación
- El PDF como canal de entrega elimina la barrera de "el dueño no tiene smartphone"
- Refuerza el valor del tier Vet BÁSICO ($89k/mes)

**Negativas**:
- Complejidad adicional: dos tipos de mascota en el modelo de datos
- El código de reclamación requiere lógica adicional para la transferencia de ownership

**Impacto en DB**: Nueva columna `pet_origin` en tabla `pets`. Nueva tabla `pet_claim_codes` con TTL de 30 días.
**Impacto en RBAC**: Nuevo permiso `vet:create_plan` además del existente `vet:approve_plan`.
