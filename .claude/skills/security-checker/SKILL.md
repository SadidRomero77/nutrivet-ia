# Skill: Security Checker

## Propósito
Ejecutar revisión de seguridad completa sobre el código de NutriVet.IA antes de cada PR siguiendo DevSecOps y OWASP Top 10.

## Cuándo activar
- Antes de cada Pull Request
- Cuando se agregue una nueva dependencia
- Cuando se modifique lógica de autenticación o autorización

## Proceso

### Paso 1 — Análisis estático (SAST)
```bash
# Análisis de seguridad Python
bandit -r app/ -f json -o reports/bandit-report.json

# Verificar dependencias vulnerables
safety check --json > reports/safety-report.json

# Lint general
ruff check .
```

### Paso 2 — Búsqueda de secrets
Verificar que no existan en el código:
- API keys hardcodeadas
- Passwords en texto plano
- Tokens de acceso
- Connection strings con credenciales
- Archivos .env commiteados

Comandos:
```bash
# Buscar patrones de secrets
grep -r "password\s*=" app/ --include="*.py"
grep -r "api_key\s*=" app/ --include="*.py"
grep -r "secret\s*=" app/ --include="*.py"
```

### Paso 3 — OWASP Top 10 Checklist
Verificar para cada endpoint nuevo:
- [ ] A01 — Broken Access Control: ¿RBAC implementado?
- [ ] A02 — Cryptographic Failures: ¿Datos sensibles encriptados?
- [ ] A03 — Injection: ¿Queries parametrizadas? ¿Input validado con Pydantic?
- [ ] A04 — Insecure Design: ¿Reglas de negocio en capa Domain?
- [ ] A05 — Security Misconfiguration: ¿CORS configurado? ¿Debug desactivado en prod?
- [ ] A06 — Vulnerable Components: ¿Dependencias actualizadas?
- [ ] A07 — Auth Failures: ¿JWT con expiración corta? ¿Refresh tokens?
- [ ] A09 — Logging: ¿Logs sin datos sensibles?

### Paso 4 — Generar reporte
Crear `reports/security-report.md` con:
- Fecha del análisis
- Hallazgos críticos (bloqueantes para merge)
- Hallazgos medios (a resolver en próximo sprint)
- Hallazgos bajos (mejoras recomendadas)
- Estado del checklist OWASP
- Veredicto: ✅ Aprobado / ❌ Bloqueado

## Reglas
- Hallazgo CRÍTICO = no merge hasta resolver
- Secrets encontrados = bloqueo inmediato
- Reporte siempre en `reports/security-report.md`
