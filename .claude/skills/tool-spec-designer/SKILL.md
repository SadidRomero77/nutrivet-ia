---
name: tool-spec-designer
description: Diseña y documenta Tool Specs completas para las tools del agente NutriVet.IA siguiendo el Playbook §5. Activar cuando se va a implementar una nueva tool del agente, modificar una existente, o cuando una tool genera errores inesperados en producción. Produce docs/tool-specs/[tool_name].md con schema estricto, ejemplos, errores accionables y límites.
tools: Read, Write
---

# Skill: tool-spec-designer
> Playbook ref: sección 5.1 y 5.2 — "Diseño de tools (agent-friendly)"
> Una tool bien diseñada tiene: nombre claro, propósito explícito, schemas estrictos, outputs estructurados, errores accionables, límites.

## Cuándo activarte
- Se va a implementar una nueva tool del agente LangGraph
- Se modifica el schema de inputs/outputs de una tool existente
- Una tool genera errores o comportamiento inesperado
- Se necesita documentar tools para onboarding del equipo

## Tools del agente NutriVet.IA (referencia)

Las 4 tools definidas en ARCH.md:
1. `nutrition_calculator` — calcula requerimientos nutricionales
2. `food_toxicity_checker` — valida alimentos contra lista de tóxicos
3. `plan_generator` — genera/ajusta plan en lenguaje natural
4. `product_scanner` — procesa OCR de etiqueta nutricional

## Plantilla Tool Spec (Playbook §5.2)

Para cada tool, generar `docs/tool-specs/{tool_name}.md`:

```markdown
# Tool Spec: {nombre_tool}

## Nombre
{nombre_exacto_en_código}

## Propósito
{Una frase: qué hace / qué NO hace}

## Cuándo usarla
- ✅ {caso de uso válido 1}
- ✅ {caso de uso válido 2}
- ❌ NO usar para: {caso fuera de scope}

## Inputs
{schema Pydantic o JSON Schema}

### Ejemplo de input válido
{JSON con valores reales}

## Outputs
{schema de respuesta}

### Ejemplo de output exitoso
{JSON con valores reales}

## Errores accionables
| Código | Mensaje | Acción del agente |
|--------|---------|-------------------|
| {ERR_001} | {mensaje} | {qué debe hacer el agente} |

## Side-effects
{qué cambia en el sistema: DB writes, API calls, cache updates}

## Permisos requeridos
{roles que pueden invocar esta tool}

## Límites
- Rate: {X calls/min}
- Timeout: {N segundos}
- Tamaño máximo de input: {bytes/chars}

## Observabilidad
- Métrica a loggear: {latencia, tokens si aplica, resultado}
- Alerta si: {condición}

## Pre-tool hook
{validaciones antes de ejecutar}

## Post-tool hook
{acciones después: caché, log, métricas}
```

## Proceso de diseño

### 1. Leer contexto
```
Lee: ARCH.md — sección "Arquitectura del Agente LangGraph"
Lee: docs/PRD.md — casos de uso y restricciones de negocio
```

### 2. Identificar la tool a diseñar
Confirmar con el usuario:
- Nombre exacto de la tool
- Job-to-be-done que resuelve
- Capa de la arquitectura (Domain / Application / Infrastructure)

### 3. Diseñar schema estricto (Pydantic)

Reglas:
- TODOS los campos tipados — nunca `Any` o `dict` genérico
- Validadores en campos críticos (ranges, enums, formatos)
- Mensaje de error descriptivo en cada validador

```python
# Ejemplo para nutrition_calculator
class NutritionCalculatorInput(BaseModel):
    pet_id: UUID
    species: Literal["dog", "cat"]
    breed: str = Field(..., min_length=2, max_length=100)
    weight_kg: float = Field(..., gt=0, lt=150, description="Peso en kg, mayor que 0")
    age_years: float = Field(..., ge=0, lt=30)
    medical_conditions: list[str] = Field(default_factory=list)
    activity_level: Literal["low", "medium", "high"] = "medium"

    @validator('weight_kg')
    def weight_realistic(cls, v, values):
        if values.get('species') == 'cat' and v > 20:
            raise ValueError('Peso inusualmente alto para gato — verificar unidad')
        return v
```

### 4. Definir errores accionables

Los errores deben decirle al agente QUÉ HACER, no solo qué salió mal:

```python
# MAL — error genérico
raise Exception("Error calculando nutrición")

# BIEN — error accionable
raise NutritionCalculatorError(
    code="PET_NOT_FOUND",
    message=f"Mascota {pet_id} no encontrada",
    agent_action="Solicitar al usuario que verifique el ID de la mascota o cree el perfil primero",
    recoverable=True
)
```

### 5. Especificar hooks (Playbook §5.4)

```python
# Pre-tool hook para nutrition_calculator
async def pre_nutrition_calculate(inputs: NutritionCalculatorInput):
    # 1. Validar que pet_id pertenece al usuario autenticado (RBAC)
    await rbac.verify_pet_ownership(inputs.pet_id, current_user)
    # 2. Log de invocación
    logger.info("nutrition_calculator called", pet_id=str(inputs.pet_id))

# Post-tool hook
async def post_nutrition_calculate(inputs, result: NutritionRequirements):
    # 1. Cachear resultado (los requerimientos no cambian si no cambia el perfil)
    await cache.set(f"nutrition_req:{inputs.pet_id}", result, ttl=3600)
    # 2. Métricas
    metrics.record("nutrition_calculator.latency", elapsed_ms)
    metrics.record("nutrition_calculator.success", 1)
```

### 6. Output final

Guardar en `docs/tool-specs/{tool_name}.md` siguiendo la plantilla.

Actualizar `docs/tool-specs/README.md` con la nueva tool en el índice.

## Reglas críticas

- Schemas ESTRICTOS — cualquier campo `Any` o `dict` sin tipado es un bug esperando pasar
- Errores ACCIONABLES — el agente debe saber qué hacer sin intervención humana
- `food_toxicity_checker` tiene permiso de solo LECTURA — nunca write
- `plan_generator` NO puede activar un plan — solo genera contenido. Activar es responsabilidad del use case
- Documentar side-effects explícitamente — el agente necesita saber si hay consecuencias irreversibles
