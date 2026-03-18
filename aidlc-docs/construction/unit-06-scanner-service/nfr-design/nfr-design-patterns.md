# NFR Design Patterns — unit-06-scanner-service
**Unidad**: unit-06-scanner-service
**Fase**: Construction — NFR Design
**Fecha**: 2026-03-16

## Patrones NFR del Scanner Service

### Patrón 1: Modelo OCR Fijo (gpt-4o siempre)
El modelo OCR es una constante, no una variable de configuración del tier.
```python
OCR_MODEL: Final[str] = "openai/gpt-4o"  # nunca cambiar
```
La calidad del OCR es crítica para la seguridad — un modelo inferior podría no detectar un ingrediente tóxico si lo transcribe mal.

### Patrón 2: Determinismo para Semáforo
El semáforo NUNCA lo decide el LLM. La lógica es:
```python
def calculate_semaphore(findings: list[EvaluationFinding]) -> SemaphoreColor:
    if any(f.severity == "critical" for f in findings):
        return SemaphoreColor.RED
    if any(f.severity == "warning" for f in findings):
        return SemaphoreColor.YELLOW
    return SemaphoreColor.GREEN
```
El LLM genera el texto de recomendación DESPUÉS de que el semáforo ya fue calculado.

### Patrón 3: Separación de Almacenamiento (R2) y Metadata (PostgreSQL)
- Imagen binaria → Cloudflare R2 (objeto S3)
- Metadata + resultado → PostgreSQL
- Esta separación reduce el tamaño de la base de datos y permite CDN para las imágenes.
- Un escaneo en PostgreSQL pesa < 5KB (solo texto y JSON).

### Patrón 4: Presigned URLs para Acceso a Imágenes
Las imágenes en R2 no son públicas. Se generan presigned URLs con TTL 1 hora:
```python
url = r2_client.get_presigned_url(scan.r2_image_key, expires_in=3600)
```
El cliente Flutter usa esta URL temporal para mostrar la imagen en la UI.

### Patrón 5: Fail Early en Validación de Imagen
La validación de imagen (ImageValidator) es el primer paso, antes del OCR de extracción.
- Ahorra el costo de un OCR completo (gpt-4o es el modelo más caro) si la imagen es inválida.
- La validación usa gpt-4o con un prompt corto → más barato que el OCR completo.

### Patrón 6: JSON-Structured OCR Output
El prompt de OCR pide respuesta en JSON estructurado, no texto libre.
```python
response_format={"type": "json_object"}
```
- Parseo más confiable que extraer de texto libre.
- Fallos de parseo son detectados inmediatamente (JSONDecodeError → ScanStatus.FAILED).

### Patrón 7: Pipeline de Guardarraíles Antes de LLM
El orden es crítico:
1. Toxicidad (determinista) → si RED, el LLM igual genera recomendación pero el semáforo ya es RED.
2. Restricciones médicas (determinista).
3. Alergias (determinista).
4. Solo entonces → LLM para texto de recomendación.
El LLM nunca "override" el semáforo — solo explica por qué es RED/YELLOW/GREEN.
