# Plan: Functional Design — Unit 02: auth-service

**Unidad**: unit-02-auth-service
**Fase AI-DLC**: C1 — Functional Design
**Estado**: ⬜ Pendiente
**Fecha**: 2026-03-16

---

## Objetivo

Definir la lógica de negocio del servicio de autenticación: JWT auth flow, RBAC,
límites del modelo freemium y el aggregate UserAccount.

## Flujo JWT (Access + Refresh Rotativo)

```
Login (email + password)
  → validar credenciales (bcrypt verify)
  → emitir access_token (JWT, 15 min)
  → emitir refresh_token (opaque, 30 días, rotativo)
  → almacenar refresh_token_hash en DB

Solicitud autenticada:
  → Authorization: Bearer <access_token>
  → validar JWT (HS256, expiración, firma)
  → extraer user_id + role del payload

Refresh:
  → POST /v1/auth/refresh { refresh_token }
  → verificar hash en DB, validar no expirado, no usado
  → invalidar refresh_token anterior (rotación)
  → emitir nuevo par access_token + refresh_token

Logout:
  → invalidar refresh_token activo en DB
```

## RBAC — Roles y Permisos

| Rol | Descripción | Accesos |
|-----|-------------|---------|
| `owner` | Dueño de mascotas | Registro de mascotas, planes propios, agente conversacional, OCR, exportar |
| `vet` | Veterinario | Dashboard clínico, revisar PENDING_VET, firmar/devolver planes, crear ClinicPet |

**Regla**: cada endpoint valida el rol — nunca omitir la verificación de RBAC.

## Límites del Modelo Freemium

| Tier | Mascotas | Planes | Agente Conversacional |
|------|----------|--------|-----------------------|
| Free | 1 | 1 plan total (lifetime) | 3 preguntas/día × 3 días → upgrade |
| Básico | 1 | 1 nuevo plan/mes | Ilimitado |
| Premium | Hasta 3 | Ilimitados | Ilimitado |
| Vet | Ilimitadas (pacientes) | Ilimitados + dashboard clínico | Ilimitado + asistente vet |

**Validación**: los límites se verifican en `application/use_cases/` consultando el `subscription_tier` del UserAccount.

## UserAccount Aggregate

**Campos**:
- `user_id: UUID`
- `email: EmailAddress` (value object)
- `password_hash: str` (bcrypt)
- `role: Literal["owner", "vet"]`
- `subscription_tier: Literal["free", "basico", "premium", "vet"]`
- `is_active: bool`
- `created_at: datetime`

**Invariantes**:
- Email único en sistema.
- `role == "vet"` implica `subscription_tier == "vet"`.
- Solo `owner` puede tener tiers free/básico/premium.
- Password mínimo 8 caracteres antes de hashear.

**Eventos de dominio emitidos**:
- `UserRegistered`
- `UserLoggedIn`
- `UserTierUpgraded`

## Casos de Prueba Críticos

- [ ] Login exitoso retorna access_token (15 min) + refresh_token
- [ ] Login con password incorrecto → 401
- [ ] Refresh con token válido → nuevo par de tokens, token anterior invalidado
- [ ] Access token expirado → 401 (no confundir con 403)
- [ ] Endpoint de owner con rol vet → 403
- [ ] Endpoint de vet con rol owner → 403
- [ ] Free tier intenta crear segunda mascota → 403 con mensaje claro
- [ ] Vet role tiene subscription_tier "vet" automáticamente

## Referencias

- Spec: `aidlc-docs/inception/units/unit-02-auth-service.md`
- ADR-004: JWT access + refresh rotativo
- ADR-011: RBAC implementation
- Constitution: REGLA 6 (seguridad de datos)
