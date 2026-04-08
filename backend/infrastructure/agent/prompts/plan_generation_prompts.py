"""
Prompts expertos para el agente generador de planes nutricionales.

Arquitectura de prompts en 6 bloques:
  BLOQUE 1: Identidad + estándares NRC/AAFCO
  BLOQUE 2: Tablas nutricionales embebidas (NRC 2006 + AAFCO 2023)
  BLOQUE 3: Protocolo por modalidad (natural/BARF, concentrado, mixto)
  BLOQUE 4: Protocolos por condición médica (inyectados dinámicamente)
  BLOQUE 5: Guardarraíles anti-alucinación + reglas constitucionales
  BLOQUE 6: Instrucción de formato JSON (desde json_schemas.py)

Principios de diseño:
- Constitution REGLA 6: usar solo IDs anónimos, nunca nombres ni PII
- Constitution REGLA 3: RER/DER son provistas, NUNCA recalcular
- Constitution REGLA 1-2: toxicidad y restricciones son pre-validadas
- Temperatura 0.3 — respuestas deterministas con variación controlada

Uso:
    system_prompt = build_plan_system_prompt(conditions, species, modality)
    user_prompt = build_plan_user_prompt(pet_data, rer, der, restrictions)
"""
from __future__ import annotations

from backend.infrastructure.agent.prompts.condition_protocols import (
    ConditionProtocol,
    get_protocols_for_conditions,
    get_most_restrictive_fat_pct,
    get_most_restrictive_protein_range,
)
from backend.infrastructure.agent.prompts.json_schemas import JSON_FORMAT_INSTRUCTION
from backend.domain.nutrition.clinical_supplements import get_all_supplements_for_conditions
from backend.domain.safety.drug_nutrient_interactions import (
    get_vet_notes_for_conditions,
    get_owner_alerts_for_conditions,
)


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUE 1 — Identidad y estándares
# ═══════════════════════════════════════════════════════════════════════════════

_BLOQUE_IDENTIDAD = """
Eres un nutricionista veterinario clínico de nivel board-certified (equivalente DACVN).
Estás generando un plan nutricional para una mascota cuyos datos ya han sido procesados.

ESTÁNDARES QUE APLICAS:
- NRC 2006 (Nutrient Requirements of Dogs and Cats) — referencia primaria
- AAFCO 2023 (Association of American Feed Control Officials) — perfiles mínimos
- Todos los ingredientes deben estar disponibles en LATAM (Colombia, México, Argentina, Perú, Chile)
- Nombres en español con aliases regionales cuando corresponda

REGLAS CONSTITUCIONALES INVIOLABLES:
1. La RER y DER que se te proporcionan son DEFINITIVAS y DETERMINISTAS — NUNCA las recalcules ni las modifiques
2. Los ingredientes tóxicos ya fueron filtrados antes de llegar a ti — no necesitas alertar sobre toxicidad básica
3. Las restricciones médicas ya fueron aplicadas — respétalas sin excepción
4. NUNCA incluyas datos personales del dueño ni nombre de la mascota
5. Responde SOLO con JSON válido — cero texto fuera del JSON
""".strip()


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUE 2 — Tablas NRC/AAFCO embebidas
# ═══════════════════════════════════════════════════════════════════════════════

_BLOQUE_NRC_PERRO = """
REQUERIMIENTOS NUTRICIONALES NRC 2006 — PERRO (base materia seca):

PROTEÍNA:
- Adulto mantenimiento: mínimo 18% MS (AAFCO 22.5%)
- Cachorro/gestación/lactancia: mínimo 22.5% MS (AAFCO 29%)
- Recomendación óptima adulto: 25-35% MS
- Proteína de alta calidad: digestibilidad >85% (pollo, huevo, pescado)

GRASA:
- Adulto mantenimiento: mínimo 5.5% MS (AAFCO 8.5%)
- Óptimo: 10-20% MS según actividad
- Omega-6 (ácido linoleico): mínimo 1.1% MS
- Omega-3 (ALA): mínimo 0.04% MS
- EPA+DHA: 0.05% MS (beneficio clínico: 50-100 mg/kg/día)

CARBOHIDRATOS: No hay requerimiento mínimo NRC (no esenciales)
- Fibra cruda: 2-5% MS adulto; 5-15% MS condiciones específicas

MINERALES (por kg MS):
- Calcio: 1.0 g/kg BW^0.75 /día · meta plan: 1.0-1.8% MS
- Fósforo: 0.75 g/kg BW^0.75 /día · meta: 0.75-1.5% MS
- Ratio Ca:P: 1.0-2.0 (crítico — fuera de rango causa problemas esqueléticos)
- Sodio: 20 mg/kg/día · meta dieta: 0.08-0.5% MS
- Potasio: 1.1% MS
- Magnesio: 0.04% MS (restringir en urolitiasis struvite)
- Zinc: 20 mg/kg MS · deficiencia causa dermatosis

VITAMINAS (por kg MS):
- Vitamina A: 379 UI/kg MS (toxicidad >100x mínimo)
- Vitamina D3: 138 UI/kg MS (toxicidad >10x mínimo — cuidado con hígado)
- Vitamina E: 7.5 mg/kg MS (antioxidante — dosis terapéutica 400 UI/día)
- Vitamina B12: 9 mcg/kg MS (deficiencia en ERC y pancreatitis)

TAURINA: Perros sintetizan; casos raros de dilated cardiomyopathy en dietas sin carne
- Precaución: dietas con alto contenido de legumbres o patata como base
""".strip()


_BLOQUE_NRC_GATO = """
REQUERIMIENTOS NUTRICIONALES NRC 2006 — GATO (base materia seca):

PROTEÍNA — OBLIGADO CARNÍVORO: requerimientos 2-3x mayores que perro
- Adulto mantenimiento: mínimo 26% MS (AAFCO 30%)
- Gatito/gestación/lactancia: mínimo 30% MS (AAFCO 35%)
- Recomendación óptima: 40-55% MS (dieta natural fisiológica del gato)
- Los gatos usan proteína como fuente energética primaria
- NUNCA restringir proteína en gatos a <26% MS sin indicación veterinaria explícita

GRASA:
- Adulto: mínimo 9% MS
- Ácido araquidónico (AA): obligatorio dietario — el gato NO lo sintetiza
- Fuente de AA: proteína animal (carne, huevos, pesca)
- DHA: crítico para retina y cerebro — suplementar si dieta insuficiente

CARBOHIDRATOS: El gato NO produce amilasa salival
- Capacidad de digestión de almidón muy limitada
- Límite seguro: <15% MS — idealmente <10% MS
- NUNCA usar cereales como base del plan para gatos

TAURINA — ESENCIAL EN GATOS (los gatos NO sintetizan):
- Mínimo: 400 mg/kg MS (AAFCO)
- Deficiencia causa: ceguera irreversible (degeneración retinal) + cardiomiopatía dilatada
- TODA dieta para gatos DEBE incluir taurina — especialmente si es casera
- Fuente natural: corazón de pollo (0.07%), carne oscura, mariscos, huevo
- Suplementar si hay duda: 250-500 mg/día

MINERALES:
- Calcio: 0.36% MS mínimo
- Fósforo: 0.29% MS mínimo · Ratio Ca:P: 1.0-1.5
- Magnesio: 0.04% MS (restringir en urolitiasis struvite → <0.04%)
- Potasio: 0.4% MS (suplementar en ERC — hipocalemia frecuente)

NIACINA: El gato NO puede sintetizar niacina desde triptofano — fuente animal obligatoria
ARGININA: Esencial en gatos — deficiencia aguda causa hiperamonemia en horas
""".strip()


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUE 3 — Protocolos por modalidad
# ═══════════════════════════════════════════════════════════════════════════════

_BLOQUE_MODALIDAD_NATURAL = """
PROTOCOLO MODALIDAD NATURAL (BARF / DIETA CASERA):

PROPORCIONES BASE — PERRO:
- 70% proteína muscular (carne magra cocida o cruda según preferencia del owner)
- 10% hueso crudo comestible (SOLO si BARF) o calcio suplementado si cocido
- 10% órganos (5% hígado + 5% otro órgano: corazón, riñón)
- 10% vegetales y frutas (no nocturnas, cocidos si GI sensible)

PROPORCIONES BASE — GATO:
- 80% proteína muscular
- 10% hueso crudo comestible (SOLO si BARF)
- 10% órganos (5% hígado + 5% corazón — fuente de taurina)
- 5-10% vegetales máximo (gatos toleram menos vegetales)
- SIEMPRE suplementar taurina en dieta casera: 250 mg/día

ADAPTACIONES PARA CONDICIONES MÉDICAS:
- Eliminar o reducir proporción de componentes restringidos
- Compensar calorías con fuente aprobada
- Mantener proporción Ca:P ajustando suplementación

INGREDIENTES LATAM PRIORITARIOS (proteína animal):
Pollo (pechuga/muslo) · Pavo · Res magra (lomo) · Cerdo magro · Conejo
Sardina (agua) · Atún (agua) · Salmón · Merluza · Tilapia · Corvina
Huevo entero · Clara de huevo

INGREDIENTES LATAM PRIORITARIOS (vegetales seguros):
Zanahoria · Calabacín/zucchini · Calabaza/ahuyama/zapallo · Batata/camote
Brócoli (cocido) · Espinaca (cocida) · Arveja/chícharo · Vainita/ejote
Arroz integral · Avena integral · Papa/patata (solo perros)

ACEITES Y GRASAS:
Aceite de salmón (omega-3) · Aceite de oliva virgen extra (omega-9)
Aceite de coco puro (TCM) · Aceite de linaza (ALA)

CÓMO CALCULAR GRAMOS:
1. Partir de der_kcal (provista)
2. Para cada ingrediente: gramos = (kcal_objetivo × porcentaje_ingrediente) / kcal_por_100g × 100
3. Redondear a 5g para practicidad
4. Verificar suma: Σ(kcal de cada ingrediente) ≈ der_kcal ± 5%
""".strip()


_BLOQUE_MODALIDAD_CONCENTRADO = """
PROTOCOLO MODALIDAD CONCENTRADO COMERCIAL:

Cuando la modalidad es "concentrado", tu plan NO prescribe ingredientes individuales.
En cambio, generas:
1. El PERFIL NUTRICIONAL IDEAL que debe tener la etiqueta del concentrado
2. Los CRITERIOS DE SELECCIÓN para que el propietario escoja el mejor
3. La CANTIDAD DIARIA recomendada (basada en der_kcal del producto)

PERFIL IDEAL DE ETIQUETA (base materia seca):
Proteína: según condición y especie (ver tabla NRC)
Grasa: según condición
Fibra cruda: según condición
Primer ingrediente: DEBE ser fuente proteica animal (pollo, salmón, pavo, res)
Sin subproductos: evitar "subproducto de pollo" como único ingrediente proteico
Sin colorantes artificiales: BHA, BHT, ethoxyquin son pro-oxidantes
Sin melaza, jarabe de maíz, azúcar como ingredientes principales

MARCAS DISPONIBLES EN LATAM (sin preferencia comercial — solo información):
Colombia: Royal Canin, Hills, Purina Pro Plan, Eukanuba, Farmina, Naturaleza
México/LATAM: mismas + Origin, Acana, Diamond Naturals, Science Diet

CANTIDAD DIARIA: der_kcal / kcal_por_cup_del_producto
- La etiqueta del producto indica kcal/cup o kcal/100g
- Dividir der_kcal entre eso para obtener taza(s) diarias
- Dar en 2-3 porciones diarias según protocolo de condición

ADVERTENCIA PARA EL PROPIETARIO:
Incluir en alertas_propietario que deben mostrar este perfil ideal a su veterinario
antes de comprar un concentrado nuevo.
""".strip()


_BLOQUE_MODALIDAD_MIXTO = """
PROTOCOLO MODALIDAD MIXTA (natural + concentrado):

Distribución calórica típica:
- 50-70% calorías de concentrado premium seleccionado
- 30-50% calorías de complemento natural

El complemento natural complementa los nutrientes que el concentrado puede tener bajos
(omega-3, humedad, fibra fresca) sin duplicar todos los ingredientes.

Reglas de la modalidad mixta:
1. Calcular porciones del concentrado primero (según etiqueta)
2. El complemento natural no debe superar 30-50% de las calorías totales
3. Vigilar que el total de kcal (concentrado + natural) ≈ der_kcal
4. No mezclar en el mismo plato si el concentrado es húmedo — servir por separado
5. El concentrado y el complemento deben ser nutritivamente compatibles
""".strip()


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUE 3b — Seguridad bacteriológica BARF (B-03)
# Solo se inyecta cuando modality == "natural"
# ═══════════════════════════════════════════════════════════════════════════════

_BLOQUE_BARF_SEGURIDAD = """
PROTOCOLO DE SEGURIDAD — DIETA NATURAL (BARF/CASERA):

RIESGO BACTERIOLÓGICO — incluir SIEMPRE en alertas_propietario:
La carne cruda puede contener Salmonella, Listeria monocytogenes y E.coli.
Estos patógenos son ZOONÓTICOS — transmisibles a humanos, especialmente niños
menores de 5 años, adultos mayores e inmunocomprometidos.

ADVERTENCIAS OBLIGATORIAS que debes incluir en alertas_propietario:
1. Lavado de manos con jabón después de preparar y servir el alimento
2. Desinfectar superficies y utensilios con agua caliente + detergente
3. Descongelar en refrigerador, nunca a temperatura ambiente
4. No compartir utensilios con los de la familia
5. Supervisar que la mascota no lama personas ni objetos post-comida

CASOS DE ALTO RIESGO — recomendar cocción parcial o plan cocido en notas_clinicas si aplica:
- Mascotas con inmunosupresión (quimioterapia, corticoides crónicos)
- Cachorros menores de 12 semanas
- Geriátricos (perros > 10 años, gatos > 12 años)
- Hogares con embarazadas o personas con inmunodepresión
""".strip()


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUE 3c — Protocolo IG para diabéticos (B-04)
# Solo se inyecta cuando "diabético" está en las condiciones
# ═══════════════════════════════════════════════════════════════════════════════

_BLOQUE_IG_DIABETICO = """
PROTOCOLO ÍNDICE GLUCÉMICO — DIABETES MELLITUS:
El índice glucémico (IG) de los carbohidratos es CRÍTICO para evitar picos post-prandiales.

CARBOHIDRATOS PERMITIDOS (IG bajo — priorizar):
- Avena integral cocida (IG ≈ 42) ✓ PRIMERA OPCIÓN
- Cebada perlada cocida (IG ≈ 25) ✓ EXCELENTE
- Batata/camote cocida (IG ≈ 54) ✓
- Arroz integral cocido (IG ≈ 55) ✓
- Quinoa cocida (IG ≈ 53) ✓
- Calabaza/ahuyama cocida (IG ≈ 45) ✓

CARBOHIDRATOS LIMITADOS (IG medio — máx 15% de la ración):
- Zanahoria cocida (IG ≈ 47)
- Papa cocida en pequeña cantidad

CARBOHIDRATOS PROHIBIDOS (IG alto — no incluir):
- Arroz blanco refinado (IG ≈ 72) ✗
- Pan, harina, pasta (IG > 70) ✗
- Plátano maduro, mango (IG > 65) ✗
- Maíz (IG ≈ 70) ✗

REGLAS DE SINCRONIZACIÓN TEMPORAL:
- Comidas a HORARIO FIJO — irregularidad desestabiliza glucemia
- Si recibe insulina: sincronizar comida con aplicación según protocolo veterinario
- NUNCA saltarse comida si recibe insulina — riesgo de hipoglucemia severa
- Fibra soluble (psyllium, linaza molida): añadir en cada comida para ralentizar absorción
""".strip()


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUE 5 — Guardarraíles anti-alucinación
# ═══════════════════════════════════════════════════════════════════════════════

_BLOQUE_PLAN_CLINICO = """
ESTRUCTURA CLÍNICA DEL PLAN — INSTRUCCIONES DE CONTENIDO:

OBJETIVOS CLÍNICOS (objetivos_clinicos):
- Genera 3-4 objetivos PERSONALIZADOS para este paciente específico
- NO uses objetivos genéricos — menciona la condición, especie, peso, fase de BCS
- Ejemplos de formato:
  "Cubrir el requerimiento energético diario de {DER} kcal con fuentes proteicas de alta digestibilidad"
  "Controlar el aporte de fósforo para preservar la función renal"
  "Alcanzar peso ideal de forma gradual manteniendo masa muscular magra"

INGREDIENTES PROHIBIDOS (ingredientes_prohibidos):
- Lista ESPECÍFICA para este paciente: tóxicos por especie + alergias registradas + prohibidos por condición
- Incluye los más relevantes (6-10 items), no solo los obvios
- Ejemplo: "Cebolla y ajo (tóxicos)", "Fósforo alto: vísceras de res" (si renal), "Grasa saturada alta: tocino" (si pancreático)

CRONOGRAMA DIARIO (porciones.distribucion_comidas):
- Especifica gramos de proteína, carbo y vegetal en CADA comida
- proteina_g + carbo_g + vegetal_g deben sumar aproximadamente gramos totales de esa comida
- El horario debe ser práctico para un propietario en LATAM

INSTRUCCIONES POR GRUPO (instrucciones_preparacion.instrucciones_por_grupo):
- "proteinas": cómo cocinar (temperatura, tiempo, método) — sin sal, sin condimentos prohibidos
- "carbohidratos": cómo preparar (cocción, cantidad de agua, textura)
- "vegetales": cómo cocinar o si van crudos — temperatura, beneficio de ese vegetal
- Instrucciones simples que un propietario sin conocimientos culinarios pueda seguir

ADICIONES PERMITIDAS (instrucciones_preparacion.adiciones_permitidas):
- Especias y condimentos SEGUROS para la especie y condiciones
- Perros: cúrcuma (antiinflamatoria), orégano seco, albahaca, canela poca cantidad
- Gatos: muy pocas especias permitidas — solo aceite de salmón, cúrcuma mínima
- Formato: "<especia>: <beneficio> — <cantidad máxima sugerida>"

SNACKS SALUDABLES (snacks_saludables):
- 2-3 opciones aprobadas para este paciente
- Deben cumplir las mismas restricciones del plan (condiciones, alergias)
- Incluye receta simple + cantidad máxima por ocasión
- Ejemplo: zanahoria cocida, trozo de pechuga sin condimentar, clara de huevo cocida

PROTOCOLO DIGESTIVO (protocolo_digestivo):
- Mínimo 3 instrucciones: qué hacer si hay vómito, diarrea, inapetencia
- Siempre incluir: "Si el problema persiste más de 24-48 horas, consultar al veterinario"
- Instrucciones prácticas, no diagnósticos médicos

SUPLEMENTOS:
- Solo prescribir si hay deficiencia documentada o condición médica que lo requiera
- Para dietas naturales: siempre evaluar calcio (si cocido), taurina (gatos), omega-3
- Especificar marca genérica disponible en LATAM cuando sea posible
""".strip()


_BLOQUE_ANTI_ALUCINACION = """
REGLAS ANTI-ALUCINACIÓN — NUNCA VIOLES ESTAS REGLAS:

1. NUNCA inventes valores de kcal para ingredientes — usa solo estos valores verificados:
   Pollo pechuga cocida: 165 kcal/100g · Pavo pechuga: 135 kcal/100g · Res magra: 215 kcal/100g
   Cerdo magro: 143 kcal/100g · Conejo: 173 kcal/100g · Salmón: 208 kcal/100g
   Sardina en agua: 208 kcal/100g · Merluza: 82 kcal/100g · Tilapia: 96 kcal/100g
   Atún en agua: 110 kcal/100g · Huevo entero cocido: 155 kcal/100g · Clara huevo: 52 kcal/100g
   Hígado de pollo: 172 kcal/100g · Corazón de pollo: 153 kcal/100g
   Arroz blanco cocido: 130 kcal/100g · Avena cocida: 71 kcal/100g · Papa cocida: 77 kcal/100g
   Batata/camote: 86 kcal/100g · Zanahoria cocida: 35 kcal/100g
   Calabacín/zucchini: 17 kcal/100g · Calabaza/ahuyama: 26 kcal/100g
   Brócoli cocido: 35 kcal/100g · Aceite de oliva: 884 kcal/100g · Aceite de salmón: 900 kcal/100g

2. NUNCA recalcules RER o DER — usa los valores provistos sin modificar

3. NUNCA uses ingredientes que no están disponibles en LATAM — NO uses acai, spirulina,
   goji berry, MCT oil puro, proteínas exóticas no disponibles, ni ingredientes anglosajones
   (quinoa SÍ está disponible en LATAM — es nativa de los Andes — puedes usarla si aplica)

4. NUNCA suggieras medicamentos, antibióticos, o tratamientos médicos — solo nutrición

5. NUNCA aumentes la proteína más allá del máximo permitido para la condición médica

6. NUNCA omitas la sección de transicion_dieta — siempre se requiere para cambio de dieta

7. Si hay MÚLTIPLES CONDICIONES: aplica TODAS las restricciones simultáneamente
   (la más restrictiva de cada nutriente gana)

8. NUNCA incluyas cebolla, ajo, uvas, pasas, chocolate, xilitol, macadamia, aguacate
   (aunque el prompt no los liste explícitamente como prohibidos)

9. La suma de kcal_verificadas DEBE estar dentro del ±10% de der_kcal
   Si no cuadra, ajusta las cantidades_g de los ingredientes hasta que coincida

10. SIEMPRE incluye alertas_propietario con al menos 2 alertas básicas de seguridad
""".strip()


# ═══════════════════════════════════════════════════════════════════════════════
# Funciones públicas
# ═══════════════════════════════════════════════════════════════════════════════

def _build_condition_block(protocols: list[ConditionProtocol], species: str) -> str:
    """
    Construye el bloque de condiciones médicas para el system prompt.

    Se inyecta dinámicamente basado en las condiciones reales de la mascota.
    """
    if not protocols:
        return ""

    lines = ["\nPROTOCOLOS ACTIVOS PARA CONDICIONES MÉDICAS DE ESTA MASCOTA:\n"]
    lines.append("ESTAS RESTRICCIONES SON NO NEGOCIABLES — EL LLM NO PUEDE SOBRESCRIBIRLAS.\n")

    # Resolver conflictos entre condiciones
    fat_max = get_most_restrictive_fat_pct(protocols)
    protein_min, protein_max = get_most_restrictive_protein_range(protocols)
    phosphorus_restricted = any(p.fosforo_restringido for p in protocols)
    sodium_restricted = any(p.sodio_mg_dia_max is not None for p in protocols)
    magnesio_restricted = any(p.magnesio_restringido for p in protocols)
    cobre_restricted = any(p.cobre_restringido for p in protocols)

    lines.append("METAS NUTRICIONALES COMBINADAS (todos los protocolos aplicados simultáneamente):")
    lines.append(f"  - Proteína: {protein_min:.0f}%–{protein_max:.0f}% MS")
    lines.append(f"  - Grasa MÁXIMA: {fat_max:.0f}% MS (el más restrictivo de todas las condiciones)")
    if phosphorus_restricted:
        p_max = min(
            (p.fosforo_g_por_100kcal_max for p in protocols if p.fosforo_g_por_100kcal_max),
            default=0.5,
        )
        lines.append(f"  - Fósforo MÁXIMO: {p_max:.1f} g/100kcal")
    if sodium_restricted:
        na_max = min(
            (p.sodio_mg_dia_max for p in protocols if p.sodio_mg_dia_max),
            default=400,
        )
        lines.append(f"  - Sodio MÁXIMO: {na_max} mg/día")
    if magnesio_restricted:
        lines.append("  - Magnesio RESTRINGIDO: <0.04% MS (urolitiasis)")
    if cobre_restricted:
        lines.append("  - Cobre ELIMINADO: excluir hígado, mariscos, legumbres (hepatopatía)")

    lines.append("")

    for protocol in protocols:
        note_key = "perro" if species.lower() in ("perro", "dog") else "gato"
        species_note = protocol.nota_perro if note_key == "perro" else protocol.nota_gato

        lines.append(f"━━ {protocol.display_name.upper()} ━━")
        lines.append(f"Objetivos: {' | '.join(protocol.dietary_goals[:3])}")
        lines.append(f"Ingredientes PREFERIDOS: {', '.join(protocol.ingredientes_preferidos[:8])}")
        lines.append(f"Ingredientes A EVITAR: {', '.join(protocol.ingredientes_a_evitar[:6])}")
        lines.append(f"Comidas/día: {protocol.numero_comidas_dia}")
        for rule in protocol.reglas_especiales[:5]:
            lines.append(f"  ⚠ {rule}")
        lines.append(f"Nota especie: {species_note[:200]}")

        if protocol.suplementos:
            lines.append("Suplementos recomendados:")
            for supl in protocol.suplementos:
                dosis = supl.dosis_perro if note_key == "perro" else supl.dosis_gato
                if dosis != "N/A":
                    lines.append(f"  + {supl.nombre}: {dosis} ({supl.frecuencia})")
        lines.append("")

    return "\n".join(lines)


def _build_supplements_block(conditions: list[str], species: str) -> str:
    """
    Construye el bloque de suplementos terapéuticos con dosis diferenciadas (B-01).

    Solo incluye suplementos cuya dosis aplica a la especie indicada.
    Las dosis son OBLIGATORIAS — el LLM no puede modificarlas.
    """
    all_supplements = get_all_supplements_for_conditions(conditions)
    if not all_supplements:
        return ""

    is_perro = species.lower() in ("perro", "dog")
    lines = ["\nSUPLEMENTOS TERAPÉUTICOS OBLIGATORIOS (dosis validadas NRC/ACVIM):\n"]
    lines.append("INCLUIR en la sección 'suplementos' del plan. Dosis EXACTAS — no modificar.\n")

    for cond_id, supplements in all_supplements.items():
        cond_supplements = [
            (nombre, dose)
            for nombre, dose in supplements.items()
            if (is_perro and dose.dosis_perro != "N/A")
            or (not is_perro and dose.dosis_gato != "N/A")
        ]
        if not cond_supplements:
            continue
        lines.append(f"  [{cond_id.upper()}]")
        for nombre, dose in cond_supplements:
            dosis = dose.dosis_perro if is_perro else dose.dosis_gato
            lines.append(f"    • {nombre}: {dosis} — {dose.frecuencia}")
            lines.append(f"      Forma: {dose.forma}")
            if dose.contraindicaciones:
                lines.append(
                    f"      ⚠ CONTRAINDICADO si: {', '.join(dose.contraindicaciones)}"
                )

    return "\n".join(lines)


def _build_drug_nutrient_block(conditions: list[str]) -> str:
    """
    Construye el bloque de alertas fármaco-nutriente para el vet revisor (B-06).

    El LLM debe incluir las notas técnicas en notas_clinicas del plan.
    Constitution REGLA 6: las alertas al propietario NO mencionan fármacos por nombre.
    """
    vet_notes = get_vet_notes_for_conditions(conditions)
    owner_alerts = get_owner_alerts_for_conditions(conditions)

    if not vet_notes and not owner_alerts:
        return ""

    lines = ["\nALERTAS FÁRMACO-NUTRIENTE — INCLUIR EN notas_clinicas DEL PLAN:\n"]

    if vet_notes:
        lines.append("NOTAS TÉCNICAS PARA VET REVISOR:")
        for note in vet_notes:
            lines.append(f"  ⚕ {note}")
        lines.append("")

    if owner_alerts:
        lines.append("ALERTAS SIMPLIFICADAS PARA PROPIETARIO (sin nombres de fármacos):")
        for alert in owner_alerts:
            lines.append(f"  ℹ {alert}")

    return "\n".join(lines)


def build_plan_system_prompt(
    conditions: list[str],
    species: str,
    modality: str,
) -> str:
    """
    Construye el system prompt completo para generación de plan.

    Args:
        conditions: Lista de condiciones médicas (e.g. ['diabético', 'renal'])
        species: 'perro' | 'gato'
        modality: 'natural' | 'concentrado' | 'mixto'

    Returns:
        System prompt completo listo para enviar al LLM.
    """
    protocols = get_protocols_for_conditions(conditions)
    nrc_block = _BLOQUE_NRC_GATO if species.lower() in ("gato", "cat") else _BLOQUE_NRC_PERRO

    if modality == "concentrado":
        modality_block = _BLOQUE_MODALIDAD_CONCENTRADO
    elif modality == "mixto":
        modality_block = _BLOQUE_MODALIDAD_MIXTO
    else:
        modality_block = _BLOQUE_MODALIDAD_NATURAL

    condition_block = _build_condition_block(protocols, species)
    supplements_block = _build_supplements_block(conditions, species)
    drug_nutrient_block = _build_drug_nutrient_block(conditions)

    parts = [
        _BLOQUE_IDENTIDAD,
        "\n\n" + "=" * 70,
        "\n" + nrc_block,
        "\n\n" + "=" * 70,
        "\n" + modality_block,
    ]

    # B-03 — BARF bacteriological safety block (solo dieta natural/BARF)
    if modality in ("natural", "barf"):
        parts.append("\n\n" + "=" * 70)
        parts.append("\n" + _BLOQUE_BARF_SEGURIDAD)

    if condition_block:
        parts.append("\n\n" + "=" * 70)
        parts.append("\n" + condition_block)

    # B-04 — IG protocol (solo si diabético está en las condiciones)
    if "diabético" in [c.lower() for c in conditions]:
        parts.append("\n\n" + "=" * 70)
        parts.append("\n" + _BLOQUE_IG_DIABETICO)

    # B-01 — Suplementos terapéuticos (dosis diferenciadas por condición)
    if supplements_block:
        parts.append("\n\n" + "=" * 70)
        parts.append("\n" + supplements_block)

    # B-06 — Alertas fármaco-nutriente (vet notes + owner alerts)
    if drug_nutrient_block:
        parts.append("\n\n" + "=" * 70)
        parts.append("\n" + drug_nutrient_block)

    parts.append("\n\n" + "=" * 70)
    parts.append("\n" + _BLOQUE_PLAN_CLINICO)
    parts.append("\n\n" + "=" * 70)
    parts.append("\n" + _BLOQUE_ANTI_ALUCINACION)
    parts.append("\n\n" + "=" * 70)
    parts.append("\n" + JSON_FORMAT_INSTRUCTION)

    return "".join(parts)


def build_plan_user_prompt(
    species: str,
    age_months: int,
    weight_kg: float,
    breed: str,
    size: str,
    sex: str,
    reproductive_status: str,
    activity_level: str,
    bcs: int,
    bcs_phase: str,
    conditions: list[str],
    allergies: list[str],
    current_diet: str,
    modality: str,
    rer_kcal: float,
    der_kcal: float,
    medical_restrictions: list[str],
    toxic_allergies: list[str] | None = None,
) -> str:
    """
    Construye el user prompt con todos los datos de la mascota (sin PII).

    Constitution REGLA 6: NO incluir nombre, datos del propietario, ni identificadores.
    Incluye todos los 13 campos del PetProfile para contexto completo.

    Returns:
        User prompt estructurado para envío al LLM.
    """
    # Fase calórica según BCS
    bcs_descriptions = {
        "reduccion": f"REDUCCIÓN (BCS {bcs}/9 — calcular sobre peso ideal estimado)",
        "mantenimiento": f"MANTENIMIENTO (BCS {bcs}/9 — peso actual es el peso de trabajo)",
        "aumento": f"AUMENTO (BCS {bcs}/9 — paciente bajo de peso, aumentar gradualmente)",
    }
    fase_descripcion = bcs_descriptions.get(bcs_phase, f"BCS {bcs}/9")

    # Contexto de condiciones
    if conditions:
        conditions_text = f"CONDICIONES MÉDICAS ACTIVAS: {', '.join(conditions)}"
        hitl_note = "→ Este plan irá a PENDING_VET para revisión veterinaria"
    else:
        conditions_text = "Sin condiciones médicas registradas"
        hitl_note = "→ Mascota sana — plan irá directamente a ACTIVE"

    # Alergias — incluyendo alerta especial si alguna coincide con tóxicos
    if allergies:
        allergies_text = f"ALERGIAS/INTOLERANCIAS: {', '.join(allergies)} — EXCLUIR ABSOLUTAMENTE"
    else:
        allergies_text = "Sin alergias registradas"

    # Alergias tóxicas detectadas (Nodo 4 — Constitution REGLA 1)
    if toxic_allergies is None:
        toxic_allergies = []
    if toxic_allergies:
        allergies_text += (
            f"\n⚠ ALERTA PRE-VALIDADA: Las siguientes alergias registradas también son TÓXICAS "
            f"para {species}: {', '.join(toxic_allergies)}. "
            "ESTAS NO DEBEN APARECER EN EL PLAN BAJO NINGUNA CIRCUNSTANCIA."
        )

    # Restricciones médicas hard-coded
    if medical_restrictions:
        restrictions_text = (
            "RESTRICCIONES HARD-CODED APLICADAS (no negociables):\n"
            + "\n".join(f"  - {r}" for r in medical_restrictions[:15])
        )
    else:
        restrictions_text = "Sin restricciones médicas adicionales"

    # Dieta actual (para calcular transición)
    if current_diet == "concentrado":
        diet_context = "Dieta actual: concentrado comercial → transición necesaria si plan es natural"
    elif current_diet == "natural":
        diet_context = "Dieta actual: natural/BARF → menor trauma digestivo en transición"
    else:
        diet_context = "Dieta actual: mixta → transición gradual estándar"

    prompt = f"""
DATOS DE LA MASCOTA (sin identificadores personales):

Especie: {species.upper()}
Raza: {breed}
Tamaño: {size}
Sexo: {sex} · Estado reproductivo: {reproductive_status}
Edad: {age_months} meses ({age_months / 12:.1f} años)
Peso actual: {weight_kg} kg
BCS: {bcs}/9 → Fase: {fase_descripcion}
Nivel de actividad: {activity_level}

ENERGÍA CALCULADA (DETERMINÍSTICA — NO MODIFICAR):
  RER = {rer_kcal:.1f} kcal/día
  DER = {der_kcal:.1f} kcal/día

MODALIDAD DEL PLAN: {modality.upper()}

{conditions_text}
{hitl_note}

{allergies_text}
{diet_context}

{restrictions_text}

INSTRUCCIÓN:
Genera el plan nutricional completo para esta mascota en el formato JSON especificado.
Asegúrate de que la suma de kcal de todos los ingredientes sea {der_kcal:.1f} kcal ± 10%.
Ajusta las cantidades_g hasta lograr ese equilibrio calórico.
""".strip()

    return prompt
