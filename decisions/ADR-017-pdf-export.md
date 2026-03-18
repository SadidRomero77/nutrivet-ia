# ADR-017 — Exportación PDF y Compartición Social de Planes

**Estado**: Aceptado
**Fecha**: 2026-03
**Autores**: Sadid Romero (AI Engineer)

---

## Contexto

Los owners necesitan compartir el plan nutricional aprobado con cuidadores, familiares, o llevarlo a consultas veterinarias. La app debe permitir exportación en formato profesional y compartición directa por canales de mensajería populares en LATAM (WhatsApp es el canal dominante en Colombia, México, y Argentina).

## Decisión

Implementar exportación PDF + compartición social con las siguientes restricciones:

**Solo planes en estado `ACTIVE` son exportables** — PENDING_VET, UNDER_REVIEW y ARCHIVED no se exportan al owner.

**Backend**: Endpoint `POST /api/v1/plans/{plan_id}/export` que genera PDF con WeasyPrint (librería Python, sin dependencias externas de cloud).

**Frontend (Flutter)**: Plugin `share_plus` para WhatsApp/Telegram/email + link temporal (72h) via deep link para "Copiar enlace".

**Contenido del PDF**:
- Primera página: Logo NutriVet.IA + Disclaimer obligatorio (INV-37)
- Perfil de la mascota (sin datos sensibles del owner — solo nombre de mascota)
- RER/DER calculado
- Plan completo (ingredientes, porciones, instrucciones)
- Firma del vet (si fue aprobado por HITL)
- Fecha de generación y fecha de aprobación

## Opciones Consideradas

| Opción | Ventaja | Desventaja |
|--------|---------|-----------|
| PDF con WeasyPrint (elegida) | Open source, Python nativo, sin cloud | Templates HTML/CSS adicionales |
| ReportLab | Más control de layout | API más compleja |
| PDF via servicio cloud (AWS Textract, etc.) | Sin mantenimiento de templates | Costo y privacidad |
| Solo compartir texto plano | Muy simple | No profesional, no imprimible |

## Consecuencias

**Positivas**:
- Aumenta adherencia al plan — tener el documento físico mejora el seguimiento.
- Profesionalismo: el PDF se ve como un informe veterinario real.
- WhatsApp es el canal de mayor alcance en LATAM — compartición directa reduce fricción.

**Negativas**:
- WeasyPrint requiere templates HTML/CSS bien diseñados.
- El link temporal (72h) requiere storage efímero (Redis o DynamoDB TTL).

**Seguridad**: El PDF no contiene PII del owner (email, nombre completo). Solo datos de la mascota y el plan. El link temporal expira a las 72h y no es reutilizable.

**INV-36**: Solo planes ACTIVE son exportables. Verificación en el endpoint con RBAC.
**INV-37**: Disclaimer obligatorio en primera página del PDF.
