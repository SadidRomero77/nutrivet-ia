# Requisito — Plan Nutricional Visual Interactivo

**ID**: REQ-010
**Fecha**: 2026-03-11
**Estado**: Aprobado
**ADR asociado**: [ADR-020](../../../decisions/ADR-020-interactive-plan-presentation.md)

---

## Problema

El plan nutricional contiene información heterogénea: alertas de seguridad, protocolo de transición,
cuidados especiales y menú diario. Presentarlo en formato plano (texto o PDF simple) hace que el
owner pierda información crítica o no pueda consultar rápidamente lo que necesita.

## Motivación Clínica

Lady Carolina identificó que la mayor fuente de errores en propietarios que siguen planes BARF o
dietas caseras es:
1. Olvidar qué alimentos están prohibidos para su mascota específica.
2. No seguir el protocolo de transición gradual (cambian de golpe y causan gastritis).
3. No recordar los cuidados especiales que aplican a la condición médica de su mascota.

Una presentación visual por secciones, con la sección de alimentos prohibidos siempre visible,
mitiga directamente estos tres problemas.

## Criterios de Aceptación

```gherkin
Feature: Plan nutricional visual interactivo

  Scenario: Owner abre plan y ve sección de prohibidos inmediatamente
    Given el owner tiene un plan ACTIVE para "Luna"
    When abre la pantalla del plan
    Then ve la Sección 1 "Alimentos Prohibidos" expandida sin necesidad de scroll
    And la lista incluye al menos los tóxicos de TOXIC_DOGS
    And las restricciones por condición médica de Luna

  Scenario: Owner navega por días del plan
    Given el owner está en la Sección 4 "Plan por Días"
    When selecciona el tab "Miércoles"
    Then ve las comidas del miércoles: desayuno, almuerzo, cena, snack
    And cada comida muestra ingrediente + gramos + kcal
    And el total del día suma ≈ DER de Luna (tolerancia ±5%)

  Scenario: Plan PENDING_VET es solo lectura
    Given el plan de "Rocky" está en estado PENDING_VET
    When el owner abre el plan
    Then ve un banner "Pendiente de revisión veterinaria"
    And todas las secciones son visibles pero no editables

  Scenario: Exportación PDF respeta el layout de secciones
    Given el plan de "Luna" está en estado ACTIVE
    When el owner toca "Exportar PDF"
    Then el PDF generado tiene las mismas 5 secciones en el mismo orden
    And el disclaimer aparece en cada página del PDF

  Scenario: Sección de transición activa en plan nuevo
    Given se acaba de activar un plan para "Rocky"
    When el owner abre el plan
    Then la Sección 2 "Protocolo de Transición" está expandida
    And muestra el día actual de transición resaltado
    And el porcentaje nuevo/anterior para hoy es visible
```

## Estructura de Datos Requerida (PlanResponse)

El endpoint `GET /v1/plans/{plan_id}` debe retornar:

```json
{
  "plan_id": "uuid",
  "pet_name": "Luna",
  "status": "ACTIVE",
  "der_kcal": 534,
  "disclaimer": "NutriVet.IA es asesoría nutricional digital...",
  "sections": {
    "prohibited": {
      "toxic_foods": ["chocolate", "uvas", "cebolla"],
      "condition_restrictions": {
        "diabetico": ["azúcar", "miel", "harina refinada"],
        "gastritis": ["alimentos grasos", "condimentos"]
      }
    },
    "transition": {
      "total_days": 7,
      "current_day": 3,
      "schedule": [
        {"day": 1, "pct_new": 25, "pct_old": 75},
        {"day": 2, "pct_new": 25, "pct_old": 75},
        {"day": 3, "pct_new": 50, "pct_old": 50},
        {"day": 7, "pct_new": 100, "pct_old": 0}
      ]
    },
    "health_care": {
      "per_condition": {
        "diabetico": "Mantener horarios fijos de alimentación...",
        "gastritis": "Dividir en 3-4 porciones pequeñas al día..."
      },
      "warning_signs": ["letargo mayor a 24h", "vómito persistente"],
      "hydration_ml_day": 480
    },
    "daily_plan": {
      "monday": {
        "breakfast": [{"ingredient": "pollo", "grams": 120, "kcal": 198, "prep": "cocido sin sal"}],
        "lunch": [...],
        "dinner": [...],
        "snack": [...],
        "total_kcal": 534
      }
    },
    "nutritional_summary": {
      "protein_pct": 28,
      "fat_pct": 12,
      "carbs_pct": 45,
      "fiber_pct": 5,
      "nrc_compliance": {"protein": 0.95, "fat": 1.02, "calcium": 0.88}
    }
  }
}
```

## Dependencias

- Depende de: U-04 plan-service (estructura PlanResponse)
- Afecta: U-08 export-service (PDF por secciones), U-09 mobile-app (PlanDetailScreen)
