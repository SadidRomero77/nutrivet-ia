# Services — NutriVet.IA

**Versión**: 1.0
**Fecha**: 2026-03-10

---

## Servicios Externos

### OpenRouter API
- **Tipo**: LLM gateway (texto + visión)
- **URL**: `https://openrouter.ai/api/v1`
- **Autenticación**: `OPENROUTER_API_KEY`
- **Modelos usados**: `meta-llama/llama-3.3-70b` · `openai/gpt-4o-mini` · `anthropic/claude-sonnet-4-5` · `openai/gpt-4o` (visión/OCR)
- **Timeout**: 55s (margen de 5s sobre el límite de 60s del producto)
- **Fallback**: Si el modelo primario falla → reintentar × 2 → registrar error en Sentry → devolver error controlado al cliente
- **Privacidad**: Solo IDs anónimos en prompts — nunca PII ni condiciones médicas en texto plano

### Cloudflare R2
- **Tipo**: Object storage (S3-compatible)
- **Uso**: Almacenamiento de PDFs generados + imágenes OCR + backups PostgreSQL
- **Configuración**: Pre-signed URLs con TTL 1h · Bucket privado · API idéntica a S3 (boto3 con endpoint personalizado)
- **Retención**: PDFs 1 año · imágenes OCR 90 días · lifecycle rules configuradas en R2

### Hetzner CPX31 + Coolify
- **Tipo**: VPS + PaaS self-hosted — reemplaza Lambda + API Gateway (ver ADR-022)
- **Configuración**: FastAPI + Uvicorn 2 workers (proceso persistente, sin cold starts) · ARQ worker para jobs async
- **Nota**: La generación de plan es async — FastAPI encola job en Redis (ARQ), el cliente hace polling a `/v1/jobs/{id}`

### Caddy (via Coolify)
- **Tipo**: Reverse proxy + SSL/TLS automático
- **Configuración**: Rutas `/v1/*` → FastAPI · CORS configurado explícitamente · Let's Encrypt automático
- **SSL**: Let's Encrypt — renovación automática vía Caddy

### Firebase Cloud Messaging (FCM)
- **Tipo**: Push notifications
- **Uso**: Notificaciones iOS + Android
- **Eventos MVP**: plan aprobado · plan próximo a expirar · marketing
- **Autenticación**: `FIREBASE_SERVICE_ACCOUNT_KEY`

### Resend (o SMTP propio)
- **Tipo**: Email transaccional
- **Uso**: Notificaciones por email (plan aprobado, próximo a expirar, marketing)
- **Nota**: MVP puede usar Resend free tier (3,000 emails/mes) — migrable a cualquier SMTP

### PayU
- **Tipo**: Procesador de pagos (v2)
- **SDK**: Flutter SDK nativo con tokenización en dispositivo
- **Nota**: No aplica en MVP — pagos manuales. Arquitectura preparada para integración en v2.

---

## Servicios Internos

### PostgreSQL 16 (Docker en Hetzner)
- **Tipo**: Base de datos relacional
- **Uso**: Todas las entidades del dominio + LangGraph checkpointer
- **Tablas principales**: `users` · `pets` · `nutrition_plans` · `plan_substitute_sets` · `agent_traces` (append-only) · `weight_records` · `pet_claim_codes` · `agent_checkpoints` (LangGraph)
- **Seguridad**: AES-256 en reposo · SSL en tránsito · datos médicos encriptados en columnas sensibles
- **Migraciones**: Alembic — nunca ALTER directo

### LangGraph (Python — in-process)
- **Tipo**: Orquestador de agente IA
- **Checkpointer**: PostgreSQL (tabla `agent_checkpoints`)
- **Estado compartido**: `NutriVetState` — pet_profile · active_plan · conversation_history · intent · agent_traces
- **Subgrafos**: Plan Generation · Consultation · Scanner · Referral Node

### WeasyPrint (Python — in-process)
- **Tipo**: Generador de PDF server-side
- **Uso**: Renderiza HTML → PDF para exportación de planes
- **Plantilla**: `templates/plan.html` con disclaimer obligatorio

### Hive (Flutter — on-device)
- **Tipo**: Base de datos local NoSQL para Flutter
- **Uso**: Caché offline — plan activo, historial de chat (solo lectura), peso/BCS pendientes de sync, perfil de mascota, dashboard
- **Sync strategy**: Unidireccional al reconectar — el servidor siempre gana en conflictos (MVP)

### Riverpod (Flutter — in-process)
- **Tipo**: State management para Flutter
- **Uso**: Providers async para todos los repositorios, gestión online/offline state, invalidación de caché

---

## Variables de Entorno Requeridas

```bash
# LLMs
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/nutrivet

# Cloudflare R2 (S3-compatible)
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET_NAME=nutrivet-storage-production
R2_ENDPOINT_URL=https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com

# Encryption AES-256
MEDICAL_DATA_ENCRYPTION_KEY=...  # openssl rand -hex 32

# Auth
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=15
JWT_REFRESH_EXPIRE_DAYS=30

# Notificaciones
FIREBASE_SERVICE_ACCOUNT_KEY=...
EMAIL_FROM=noreply@nutrivet.app
RESEND_API_KEY=...

# Observabilidad
SENTRY_DSN=...

# App
ENVIRONMENT=production|staging|development
```
