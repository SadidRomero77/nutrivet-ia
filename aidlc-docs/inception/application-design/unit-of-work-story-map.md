# Unit of Work — Story Map

**Fecha**: 2026-03-16

Mapa de las User Stories cubiertas por cada unidad de trabajo.

---

## Cobertura por Unidad

| US | Título | U-01 | U-02 | U-03 | U-04 | U-05 | U-06 | U-07 | U-08 | U-09 |
|----|--------|------|------|------|------|------|------|------|------|------|
| US-01 | Registro owner | ◉ | ◉ | | | | | | | ◉ |
| US-02 | Registro vet | ◉ | ◉ | | | | | | | ◉ |
| US-03 | Login (owner/vet) | | ◉ | | | | | | | ◉ |
| US-04 | Wizard 13 campos | ◉ | | ◉ | | | | | | ◉ |
| US-05 | Registro peso/BCS | ◉ | | ◉ | | | | | | ◉ |
| US-06 | Plan mascota sana | ◉ | | | ◉ | ◉ | | | | ◉ |
| US-07 | Plan con condición → PENDING_VET | ◉ | | | ◉ | ◉ | | | | ◉ |
| US-08 | Ajuste ingrediente | ◉ | | | ◉ | | | | | ◉ |
| US-09 | Vet aprueba plan | ◉ | | | ◉ | ◉ | | | | ◉ |
| US-10 | Vet devuelve plan | ◉ | | | ◉ | | | | | ◉ |
| US-11 | Consulta nutricional | | | | | ◉ | | ◉ | | ◉ |
| US-12 | Detección emergencia | | | | | ◉ | | ◉ | | ◉ |
| US-13 | Scanner OCR + semáforo | | | | | ◉ | ◉ | | | ◉ |
| US-14 | Exportar PDF | | | | ◉ | | | | ◉ | ◉ |
| US-15 | Compartir PDF | | | | | | | | ◉ | ◉ |
| US-16 | Dashboard owner | | | ◉ | ◉ | | | | | ◉ |
| US-17 | Dashboard vet | | | ◉ | ◉ | | | | | ◉ |
| US-18 | Gate freemium plan | | ◉ | | ◉ | | | | | ◉ |
| US-19 | Gate freemium agente | | ◉ | | | | | ◉ | | ◉ |
| US-20 | Vet crea ClinicPet | | ◉ | ◉ | | | | | | ◉ |
| US-21 | Owner reclama ClinicPet | | | ◉ | | | | | | ◉ |

**Leyenda**: ◉ = unidad implementa esta story (puede ser parcial)

---

## Épicas vs Unidades

| Épica | Descripción | Unidades |
|-------|-------------|---------|
| Epic 1 | Gestión de identidad | U-02, U-09 |
| Epic 2 | Perfil de mascota | U-01, U-03, U-09 |
| Epic 3 | Generación de plan | U-01, U-04, U-05, U-09 |
| Epic 4 | Revisión veterinaria HITL | U-04, U-05, U-09 |
| Epic 5 | Agente conversacional | U-05, U-07, U-09 |
| Epic 6 | Scanner OCR | U-05, U-06, U-09 |
| Epic 7 | Exportación y compartir | U-08, U-09 |
| Epic 8 | Dashboard de seguimiento | U-03, U-04, U-09 |
| Epic 9 | Freemium y pagos | U-02, U-04, U-07, U-09 |

---

## Stories Críticas (Piloto BAMPYSVET)

Mínimo viable para el piloto con Dr. Andrés en BAMPYSVET:

| Priority | US | Descripción | Unidades |
|----------|----|-------------|---------|
| P0 | US-01, US-02, US-03 | Login/registro owner y vet | U-02, U-09 |
| P0 | US-04 | Wizard de mascota | U-01, U-03, U-09 |
| P0 | US-07 | Plan con condición → PENDING_VET | U-04, U-05, U-09 |
| P0 | US-09 | Vet aprueba plan (HITL) | U-04, U-09 |
| P1 | US-11, US-12 | Agente conversacional | U-05, U-07, U-09 |
| P1 | US-14, US-15 | Exportar y compartir PDF | U-08, U-09 |
| P2 | US-13 | Scanner OCR | U-06, U-09 |
| P2 | US-20, US-21 | ClinicPet + reclamación | U-03, U-09 |
