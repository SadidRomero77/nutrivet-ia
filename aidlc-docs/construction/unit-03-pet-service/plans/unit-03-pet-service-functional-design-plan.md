# Plan: Functional Design — Unit 03: pet-service

**Unidad**: unit-03-pet-service
**Fase AI-DLC**: C1 — Functional Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Definir la lógica de negocio del servicio de mascotas: CRUD del PetProfile (13 campos
obligatorios), wizard de 6 pasos, ClinicPet (creada por vet), claim code (TTL 30 días),
weight tracking (append-only) y límites por tier.

## PetProfile — 13 Campos Obligatorios

| # | Campo | Tipo | Reglas |
|---|-------|------|--------|
| 1 | `name` | Text | No vacío |
| 2 | `species` | Enum: perro/gato | Determina listas de tóxicos y actividad |
| 3 | `breed` | Text + selector | Búsqueda libre |
| 4 | `sex` | Enum: macho/hembra | Factor hormonal DER |
| 5 | `age` | Number (meses/años) | Factor DER etapa de vida |
| 6 | `weight_kg` | Decimal > 0 | Core del cálculo RER |
| 7 | `size` | Enum: mini_xs/pequeno_s/mediano_m/grande_l/gigante_xl | **Solo perros** |
| 8 | `reproductive_status` | Enum: esterilizado/no_esterilizado | Factor DER |
| 9 | `activity_level` | Enum (por especie) | Perros: sedentario/moderado/activo/muy_activo · Gatos: indoor/indoor_outdoor/outdoor |
| 10 | `bcs` | Int 1-9 | Fase del plan: reducción/mantenimiento/aumento |
| 11 | `medical_conditions` | Multi-select (13 + Ninguno) | Dispara HITL + LLM routing |
| 12 | `allergies` | Multi-select + texto libre | Filtro de ingredientes |
| 13 | `current_feeding` | Enum: concentrado/natural/mixto | Contexto para plan |

**Regla crítica**: `size` solo es obligatorio para perros — gatos no tienen este campo.

## Wizard de 6 Pasos (Owner)

```
Paso 1: nombre + especie + raza
Paso 2: sexo + edad + peso
Paso 3: talla (solo perros) + estado reproductivo
Paso 4: nivel de actividad + BCS (selector visual 1-9)
Paso 5: antecedentes médicos + alergias
Paso 6: alimentación actual (¿qué come hoy?)
```

**Draft en Hive**: el wizard guarda localmente hasta que los 13 campos se completan.
No existe "borrador" en el backend — solo se persiste cuando el wizard finaliza.

## ClinicPet (Creado por Vet)

Flujo paralelo para veterinarios que crean mascotas para sus pacientes sin app:

```
Vet crea ClinicPet con:
  - Los 13 campos del PetProfile
  - owner_name: str (nombre del dueño — no es cuenta en el sistema)
  - owner_phone: str (para contacto)

ClinicPet genera claim_code (8 chars alfanumérico, criptográficamente seguro)
TTL: 30 días desde creación, 1 solo uso
```

**Disponibilidad del ClinicPet**:
- Solo veterinarios con tier `vet` pueden crear ClinicPets.
- Limite: sin límite de ClinicPets para tier vet.

## Claim Code — Pet Claim Flow

```
Owner descarga app → ingresa claim_code
  → verificar: code válido + no expirado + no usado
  → convertir ClinicPet → AppPet (linked a owner_id)
  → marcar claim_code como usado
  → plan generado por vet permanece vinculado
```

**Invariantes del claim**:
- Código expira a los 30 días del TTL o al primer uso — lo que ocurra primero.
- Después del claim, el vet sigue viendo la mascota en su dashboard.

## Weight Tracking (Append-Only)

```
WeightRecord:
  - pet_id: UUID
  - weight_kg: Decimal
  - bcs: int (1-9, opcional)
  - recorded_at: datetime
  - recorded_by: user_id

Regla: solo INSERT — nunca UPDATE ni DELETE de registros de peso.
Historial: disponible para gráficos en dashboard.
```

## Límites por Tier

| Tier | Mascotas App | ClinicPets |
|------|-------------|-----------|
| Free | 1 | N/A |
| Básico | 1 | N/A |
| Premium | Hasta 3 | N/A |
| Vet | Ilimitadas (pacientes) | Ilimitadas |

**Regla de condición médica**: si owner agrega condición médica a mascota con plan
en estado `ACTIVE` → el plan vuelve a `PENDING_VET` automáticamente.

## Casos de Prueba Críticos

- [ ] Crear mascota válida con 13 campos → pet_id retornado
- [ ] Free tier no puede crear segunda mascota → 403
- [ ] `size` es requerido para perros, prohibido para gatos
- [ ] `activity_level` válido según especie (indoor solo para gatos)
- [ ] Weight record creado → solo INSERT, no UPDATE
- [ ] Vet crea ClinicPet con owner_name + owner_phone → claim_code generado
- [ ] Vet free tier no puede crear ClinicPet → 403
- [ ] Claim code expira después de 30 días → 410 Gone
- [ ] Claim code de un solo uso → segundo claim → 409 Conflict
- [ ] Claim convierte ClinicPet → AppPet con owner_id

## Referencias

- Spec: `aidlc-docs/inception/units/unit-03-pet-service.md`
- Domain: `aidlc-docs/construction/_shared/domain-entities.md`
- Unit 01: `unit-01-domain-core` (PetProfile aggregate)
