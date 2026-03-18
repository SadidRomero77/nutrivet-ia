# NFR Design Patterns — unit-08-export-service
**Unidad**: unit-08-export-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Patrones NFR del Export Service

### Patrón 1: Server-Side PDF Generation
El PDF se genera en el servidor (WeasyPrint), no en el cliente (Flutter).
- Garantiza que el PDF siempre tenga el mismo aspecto independientemente del dispositivo.
- El disclaimer y el branding están en el template del servidor — no modificables por el cliente.
- El PDF generado es el documento oficial, con firma del vet incluida.

### Patrón 2: Disclaimer Hardcoded en Template
El disclaimer está hardcoded en el template HTML del servidor.
```html
<!-- template: siempre presente, no configurable -->
<footer>
  <p class="disclaimer">{{ disclaimer }}</p>  {# valor fijo desde constante Python #}
</footer>
```
- El usuario no puede pedir un PDF sin disclaimer.
- El template usa la constante `PLAN_DISCLAIMER` — cualquier cambio requiere deploy.

### Patrón 3: Presigned URL (Seguridad + Simplicidad)
El PDF no es público. Se usa presigned URL de R2 con TTL 1 hora:
- El PDF está protegido — solo quien tiene la URL puede descargarlo.
- La URL expira → un enlace robado tiene vida útil limitada.
- Compartir via WhatsApp/Telegram: el receptor puede descargar durante 1 hora.
- Si el receptor necesita más tiempo → el owner solicita nueva URL.

### Patrón 4: One-Time Render (No Caché del PDF)
Cada solicitud de export genera un nuevo PDF en lugar de servir uno cacheado.
- Razón: el plan puede haber sido editado por el vet entre exportaciones.
- Trade-off: mayor CPU por exportación, pero siempre datos actualizados.
- Post-MVP: si el plan no ha cambiado desde el último export → reusar R2 key existente.

### Patrón 5: Jinja2 con autoescape
El template usa `autoescape=True` para prevenir XSS.
- El contenido del plan es generado por LLM — aunque se valida, buena práctica defensiva.
- `{{ section.content }}` con autoescape escapa caracteres HTML potencialmente maliciosos.

### Patrón 6: upload_then_presign (Orden Correcto)
El orden de operaciones es:
1. Generar PDF bytes (CPU local)
2. Upload a R2 (I/O externo)
3. Generar presigned URL (I/O mínimo)
4. Persistir en PostgreSQL
5. Retornar al cliente

Si R2 upload falla → no se persiste en PostgreSQL → el cliente recibe error y puede reintentar.
No se puede tener un ExportResult en DB sin el PDF correspondiente en R2.

### Patrón 7: Retry en Upload R2
El upload a R2 usa retry × 2 con backoff (boto3 retry config):
```python
config = Config(
    retries={"max_attempts": 3, "mode": "standard"},
    connect_timeout=5,
    read_timeout=30,
)
```
Los PDFs pueden ser grandes (1-3MB) — el timeout debe ser generoso.
