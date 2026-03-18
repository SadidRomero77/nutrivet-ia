# Business Logic Model — unit-08-export-service
**Unidad**: unit-08-export-service
**Fase**: Construction — Functional Design
**Fecha**: 2026-03-16

## Flujos del Export Service

### Flujo 1: Exportar Plan a PDF

```
POST /plans/{plan_id}/export
  ↓
1. Verificar ownership: plan.owner_id == current_user.user_id
2. Verificar plan.status == ACTIVE
   → Si no ACTIVE: HTTP 422 "Solo planes activos pueden exportarse"
3. Cargar plan completo con secciones
4. Cargar PetProfile para obtener nombre de la mascota (visible en PDF)
5. Si plan.vet_id: cargar VetProfile para la firma
6. Construir PDFContent:
   {
     pet_name: pet.nombre,
     generated_date: date.today(),
     sections: plan.sections,  # las 5 secciones
     rer_kcal: plan.rer_kcal,
     der_kcal: plan.der_kcal,
     vet_signature: VetSignature(...) if plan.vet_id else None,
     disclaimer: PLAN_DISCLAIMER,  # inmutable
   }
7. Generar PDF: pdf_bytes = PDFGenerator.generate(pdf_content)
8. Generar export_id = uuid4()
9. Construir R2Key: exports/{owner_id}/{plan_id}/{export_id}.pdf
10. Subir PDF a Cloudflare R2: R2StorageClient.upload(r2_key, pdf_bytes)
11. Generar presigned URL (TTL 1 hora)
12. Crear ExportResult(export_id, plan_id, r2_key, presigned_url, url_expires_at)
13. Persistir ExportResult en PostgreSQL
14. Retornar { export_id, download_url, expires_at } + HTTP 201
```

### Flujo 2: Obtener Nueva URL de Descarga

```
GET /exports/{export_id}/url
  ↓
1. Verificar ownership
2. Cargar ExportResult de PostgreSQL
3. Si url_expires_at > now(): retornar presigned_url existente
4. Si expirada: generar nueva presigned URL (TTL 1 hora)
5. Actualizar ExportResult.presigned_url y url_expires_at
6. Retornar { download_url, expires_at } + HTTP 200
```

### Flujo 3: Listar Exportaciones del Plan

```
GET /plans/{plan_id}/exports
  ↓
1. Verificar ownership
2. SELECT * FROM export_results WHERE plan_id = ? ORDER BY created_at DESC
3. Retornar list[ExportResult] (sin bytes del PDF) + HTTP 200
```

### Flujo 4: Compartir desde Flutter

```
Flutter:
1. Llamar POST /plans/{plan_id}/export → { download_url }
2. Usar share_plus: Share.shareUri(Uri.parse(download_url))
3. El share sheet nativo del OS se abre con la URL
4. El usuario elige la app de destino (WhatsApp, Telegram, email, etc.)
5. El destinatario puede abrir la URL en un browser para descargar el PDF
```
