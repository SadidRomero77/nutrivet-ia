# ADR-022: Hetzner + Coolify como Infraestructura de Despliegue

**Fecha**: 2026-03-12
**Estado**: ACEPTADO
**Supercede a**: La arquitectura AWS multi-Lambda documentada en la primera versión de `aws-architecture.md`
**Autores**: Sadid Romero (AI Engineer)

---

## Contexto

El diseño inicial planteaba AWS con múltiples Lambda functions, API Gateway, RDS Multi-AZ, ElastiCache, SQS y otros servicios gestionados. Al analizar el costo (~$190-210/mes) frente a las necesidades reales del MVP (50-200 usuarios, piloto BAMPYSVET), se concluyó que esa arquitectura es prematura y costosa para la fase actual.

Se evaluaron tres opciones:
1. **AWS completo** — arquitectura original
2. **Hetzner VPS + Coolify** — VPS europeo con PaaS self-hosted
3. **Hostinger VPS** — alternativa más orientada a marketing

---

## Decisión

**Hetzner CPX31 + Coolify** como plataforma de despliegue para el MVP.

Stack de infraestructura completo:
- **Cómputo**: Hetzner CPX31 (4 vCPU AMD, 8GB RAM, 160GB SSD, Ashburn VA) — ~$13 USD/mes
- **PaaS**: Coolify (open-source, self-hosted) — gestiona deployments desde GitHub
- **Base de datos**: PostgreSQL 16 Docker (Coolify-managed) + backups a Cloudflare R2
- **Cache + Queue**: Redis 7 Docker (Coolify-managed) — usado por cache Y ARQ (async jobs)
- **Storage**: Cloudflare R2 — S3-compatible, 10GB gratis/mes
- **CDN + DNS + DDoS + SSL**: Cloudflare (plan gratuito)
- **Monitoring**: Sentry (plan gratuito) + Coolify built-in logs
- **Async jobs**: ARQ (async job queue sobre Redis) — reemplaza SQS

---

## Justificación

### Costo comparativo

| Stack | Costo/mes (sin LLM) |
|-------|---------------------|
| AWS completo | ~$175-180 |
| Hetzner + Coolify | ~$15-20 |
| Ahorro en MVP (12 meses) | ~$1.900 USD |

El costo de OpenRouter LLM (~$15-30/mes) es idéntico en ambos stacks.

### Por qué Hetzner sobre Hostinger
- Reputación técnica superior (usado por empresas de ingeniería serias)
- Datacenters en Ashburn VA (us-east-1 equivalente) — misma latencia a Colombia
- API completa para automatización
- SLA 99.9% histórico vs 99.5% de Hostinger
- Sin límites artificiales de CPU ni "CPU throttling"

### Por qué Coolify
- Conecta directamente con GitHub → webhooks de deploy automático
- SSL automático via Let's Encrypt (Caddy integrado)
- Gestiona variables de entorno de forma segura
- Rollback con 1 click
- Logs en tiempo real
- Gestiona PostgreSQL, Redis, y los contenedores de la app

### Por qué NO Lambda para este MVP
- Lambda + Mangum + API Gateway añade complejidad de packaging sin beneficio real a <500 usuarios
- Cold starts afectan la UX del chat conversacional
- El async job pattern con SQS se puede reemplazar con ARQ + Redis (ya tenemos Redis)
- FastAPI corriendo como proceso persistente en Docker es más simple de debuggear y operar
- La arquitectura Clean Architecture / Hexagonal NO cambia — solo cambia el adaptador de infraestructura

### Por qué ARQ sobre SQS
- ARQ es una librería Python de async job queue sobre Redis
- Ya tenemos Redis en el stack → sin servicio adicional
- API similar a Celery pero nativo async/await
- Sufficiente para el volumen del MVP

---

## Consecuencias

### Positivas
- $150+/mes de ahorro durante el MVP
- Curva de aprendizaje mucho más baja para primer deployment
- Debugging más simple (un servidor, logs centralizados en Coolify)
- Sin vendor lock-in severo de AWS
- FastAPI sin Mangum es más rápido (sin overhead del adapter)
- SSE streaming funciona nativamente en FastAPI sin necesidad de Lambda Function URLs

### Negativas
- Sin auto-scaling automático (se hace manualmente upgradeando el VPS)
- Sin Multi-AZ nativo (mitigado con backups automáticos a Cloudflare R2)
- Hetzner no tiene el ecosistema de servicios de AWS
- Operación del servidor requiere más responsabilidad (security patches, etc.)

### Mitigaciones
- **Sin Multi-AZ**: Backups diarios automáticos de PostgreSQL a Cloudflare R2 (Coolify lo gestiona). MTTR ante fallo de disco: <2h desde backup.
- **Sin auto-scaling**: Para el MVP, un VPS CPX31 maneja cómodamente 500-1000 usuarios concurrentes. Upgrade a CPX41 ($28/mes) si se necesita más.
- **Security patches**: Hetzner ofrece "Managed Security Updates" opcionales. Coolify se actualiza via Docker.

---

## Plan de Migración a Futuro

Cuando el producto supere 1.000 usuarios pagos y los ingresos lo justifiquen, migrar a AWS es posible sin cambiar código de dominio ni aplicación:
1. Reemplazar `ARQQueueClient` (adaptador) por `SQSQueueClient`
2. Reemplazar `CloudflareR2Client` por `AWSS3Client`
3. Agregar `Mangum` wrapper si se quiere ir a Lambda
4. Todo lo demás (domain, application, tests) permanece intacto

Tiempo estimado de migración: 2-3 días de trabajo de infraestructura.

---

## Decisores

- Sadid Romero — AI Engineer
