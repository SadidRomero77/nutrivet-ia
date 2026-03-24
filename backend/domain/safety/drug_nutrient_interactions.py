"""
Alertas de interacción medicamento-nutriente — NutriVet.IA (B-06)

Alcance REDUCIDO y deliberado: solo las interacciones más críticas y frecuentes
en clínica veterinaria de pequeños animales. El agente NO especifica medicamentos
ni diagnostica — usa la condición como proxy del tratamiento probable.

Principio de diseño:
- El agente NUNCA menciona medicamentos por nombre al propietario
- Las alertas van en notas_clinicas (para el vet revisor)
- Al propietario se le dice: "consulte con su veterinario sobre posibles
  interacciones entre el medicamento actual y la dieta"

Fuentes: Plumb's Veterinary Drug Handbook 10th Ed., Merck Vet Manual 2023,
         Small Animal Clinical Nutrition 5th Ed.
Validado por Lady Carolina Castañeda (MV, BAMPYSVET).
NUNCA modificar sin confirmación veterinaria.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DrugNutrientAlert:
    """
    Alerta de interacción medicamento-nutriente.

    condicion:          Condición médica que genera el contexto del fármaco probable.
    farmaco_probable:   Fármaco o clase terapéutica típicamente usada (INTERNO — no mostrar al owner).
    alerta_vet:         Texto técnico para el veterinario revisor (en notas_clinicas).
    alerta_propietario: Texto simplificado para el propietario (genérico, sin nombrar fármaco).
    nutrientes_afectados: Nutrientes cuya absorción o nivel sérico se modifica.
    accion_recomendada: Qué hacer con la dieta para mitigar la interacción.
    """

    condicion: str
    farmaco_probable: str
    alerta_vet: str
    alerta_propietario: str
    nutrientes_afectados: list[str] = field(default_factory=list)
    accion_recomendada: str = ""


# ---------------------------------------------------------------------------
# Base de interacciones — indexada por condition_id
# Cada condición puede tener múltiples alertas (una por fármaco probable)
# ---------------------------------------------------------------------------

DRUG_NUTRIENT_INTERACTIONS: dict[str, list[DrugNutrientAlert]] = {

    "epilepsia": [
        DrugNutrientAlert(
            condicion="epilepsia",
            farmaco_probable="fenobarbital (anticonvulsivante más común en perros)",
            alerta_vet=(
                "Fenobarbital: induce enzimas hepáticas CYP → acelera catabolismo de "
                "vitamina D, folato y vitamina B12. Monitorear niveles séricos. "
                "Considerar suplementación preventiva de B-complex y vitamina D3 "
                "(dosis perro: 100-400 UI/día D3; 1 comprimido B-complex/día)."
            ),
            alerta_propietario=(
                "Si su mascota recibe medicamento anticonvulsivante, "
                "consulte a su veterinario sobre posibles necesidades nutricionales adicionales."
            ),
            nutrientes_afectados=["vitamina_d3", "folato", "vitamina_b12", "tiamina_b1"],
            accion_recomendada=(
                "Incluir fuentes de vitamina D en el plan (yema de huevo, salmón cocido). "
                "Considerar suplemento B-complex. Evitar alimentos que compitan con "
                "absorción de anticonvulsivantes (alto contenido proteico puede reducir absorción)."
            ),
        ),
        DrugNutrientAlert(
            condicion="epilepsia",
            farmaco_probable="bromuro de potasio (anticonvulsivante coadyuvante)",
            alerta_vet=(
                "Bromuro de potasio: el cloro dietético COMPITE con la absorción de bromuro. "
                "Dietas altas en sal (NaCl) pueden reducir eficacia del KBr y precipitar crisis. "
                "Mantener NaCl constante en la dieta — no cambiar abruptamente el nivel de sal."
            ),
            alerta_propietario=(
                "Es importante mantener el nivel de sal en la dieta estable. "
                "Consulte a su veterinario antes de cambiar la dieta si su mascota "
                "toma medicamento para las convulsiones."
            ),
            nutrientes_afectados=["cloro", "sodio"],
            accion_recomendada=(
                "Mantener sodio dietético constante. No agregar sal de mesa ni caldos salados. "
                "Avisar al veterinario de cualquier cambio de dieta."
            ),
        ),
    ],

    "insuficiencia_cardiaca": [
        DrugNutrientAlert(
            condicion="insuficiencia_cardiaca",
            farmaco_probable="IECA (enalapril, benazepril, ramipril) — estándar ICC",
            alerta_vet=(
                "IECA inhiben degradación de bradiquinina y reducen excreción de potasio. "
                "Riesgo de HIPERPOTASEMIA si se suplementa potasio o se usan dietas "
                "muy ricas en potasio (plátano, papa, tomate). "
                "NO suplementar potasio sin monitoreo de ionograma."
            ),
            alerta_propietario=(
                "Con el tratamiento cardíaco actual, es importante no agregar "
                "suplementos de potasio sin consultar al veterinario."
            ),
            nutrientes_afectados=["potasio"],
            accion_recomendada=(
                "Evitar fuentes muy concentradas de potasio (plátano, papa en exceso). "
                "Si aparece debilidad muscular o arritmia → ionograma urgente."
            ),
        ),
        DrugNutrientAlert(
            condicion="insuficiencia_cardiaca",
            farmaco_probable="furosemida (diurético de asa — frecuente en ICC)",
            alerta_vet=(
                "Furosemida causa pérdida urinaria de potasio, magnesio y vitaminas B hidrosolubles. "
                "Monitorear electrolitos (K+, Mg2+) cada 4-8 semanas. "
                "Puede ser necesario suplementar magnesio (glicinato 1-2 mg/kg/día) "
                "y potasio si hay hipopotasemia confirmada."
            ),
            alerta_propietario=(
                "El medicamento para el corazón puede afectar los niveles de minerales. "
                "Siga las indicaciones del veterinario sobre controles periódicos."
            ),
            nutrientes_afectados=["potasio", "magnesio", "tiamina_b1", "vitaminas_b"],
            accion_recomendada=(
                "Incluir fuentes de magnesio en el plan (semillas de chía, avena). "
                "Si ionograma muestra K+ < 3.5 mEq/L → suplementar bajo supervisión vet."
            ),
        ),
    ],

    "hipotiroideo": [
        DrugNutrientAlert(
            condicion="hipotiroideo",
            farmaco_probable="levotiroxina sódica (T4 sintética — tratamiento estándar)",
            alerta_vet=(
                "Calcio, hierro y fibra soluble reducen absorción intestinal de levotiroxina. "
                "Administrar el medicamento con el estómago vacío, 30-60 minutos antes de comer. "
                "NO dar junto con suplementos de calcio o comidas ricas en calcio."
            ),
            alerta_propietario=(
                "El medicamento para la tiroides debe darse según las instrucciones del veterinario "
                "— generalmente separado de las comidas para mejor absorción."
            ),
            nutrientes_afectados=["calcio", "hierro", "fibra_soluble"],
            accion_recomendada=(
                "Sincronizar administración de levotiroxina ANTES de las comidas (30-60 min). "
                "No suplementar calcio en las horas próximas a la dosis."
            ),
        ),
    ],

    "cancerígeno": [
        DrugNutrientAlert(
            condicion="cancerígeno",
            farmaco_probable="quimioterapia (agentes alquilantes, antraciclinas, vincristina)",
            alerta_vet=(
                "Vitamina C en dosis altas puede REDUCIR eficacia de algunos agentes alquilantes "
                "(ciclofosfamida, melfalán) — efecto antioxidante protege células tumorales. "
                "Suspender suplementación de vitamina C ≥ 500 mg/día durante quimioterapia. "
                "Hierro libre puede generar radicales libres que dañan tejidos sanos."
            ),
            alerta_propietario=(
                "Durante el tratamiento oncológico, no administre suplementos vitamínicos "
                "sin consultar al veterinario oncólogo — algunos pueden interferir."
            ),
            nutrientes_afectados=["vitamina_c", "hierro", "antioxidantes_dosis_alta"],
            accion_recomendada=(
                "Evitar suplementos vitamínicos antioxidantes en dosis altas durante quimioterapia. "
                "Priorizar palatabilidad y densidad calórica — caquexia neoplásica es el riesgo principal."
            ),
        ),
    ],

    "renal": [
        DrugNutrientAlert(
            condicion="renal",
            farmaco_probable="quelantes de fósforo (hidróxido de aluminio, carbonato de calcio)",
            alerta_vet=(
                "Quelantes de fósforo deben darse CON las comidas para ser efectivos. "
                "Carbonato de calcio como quelante puede causar hipercalcemia si se combina "
                "con suplementación de calcio o dieta alta en calcio — monitorear calcio sérico."
            ),
            alerta_propietario=(
                "El medicamento para el riñón debe administrarse junto con las comidas. "
                "Consulte al veterinario antes de agregar suplementos."
            ),
            nutrientes_afectados=["fosforo", "calcio"],
            accion_recomendada=(
                "Dar quelante de fósforo mezclado en el alimento. "
                "Si usa carbonato de calcio como quelante, no añadir suplemento de calcio adicional."
            ),
        ),
    ],

    "hiperadrenocorticismo_cushing": [
        DrugNutrientAlert(
            condicion="hiperadrenocorticismo_cushing",
            farmaco_probable="trilostano o mitotano (tratamiento médico de Cushing)",
            alerta_vet=(
                "Trilostano/mitotano pueden causar hipoadrenocorticismo iatrogénico. "
                "El estrés metabólico (ayuno, cambio brusco de dieta) puede precipitar "
                "crisis de Addison. Mantener horarios de comida ESTRICTAMENTE fijos "
                "y no hacer cambios de dieta sin supervisión veterinaria."
            ),
            alerta_propietario=(
                "Con el tratamiento para el Cushing, mantener los horarios de comida "
                "exactamente iguales todos los días. Ante vómito o inapetencia, "
                "contactar al veterinario ese mismo día."
            ),
            nutrientes_afectados=["sodio", "potasio", "glucosa"],
            accion_recomendada=(
                "Horarios fijos de alimentación — NUNCA saltarse comidas. "
                "Si hay vómito o inapetencia → consulta veterinaria urgente (riesgo Addison)."
            ),
        ),
    ],
}


def get_drug_nutrient_alerts(condition_id: str) -> list[DrugNutrientAlert]:
    """
    Retorna las alertas de interacción medicamento-nutriente para una condición.

    Args:
        condition_id: ID de la condición médica.

    Returns:
        Lista de DrugNutrientAlert. Lista vacía si no hay alertas para esa condición.
    """
    return DRUG_NUTRIENT_INTERACTIONS.get(condition_id, [])


def get_vet_notes_for_conditions(conditions: list[str]) -> list[str]:
    """
    Genera notas clínicas de interacciones para el veterinario revisor.

    Args:
        conditions: Lista de condition_ids activos.

    Returns:
        Lista de strings con las alertas técnicas (para notas_clinicas del plan).
    """
    notes: list[str] = []
    for cond in conditions:
        for alert in get_drug_nutrient_alerts(cond):
            notes.append(
                f"[INTERACCIÓN FÁRMACO-NUTRIENTE — {cond.upper()}] "
                f"Fármaco probable: {alert.farmaco_probable}. "
                f"{alert.alerta_vet}"
            )
    return notes


def get_owner_alerts_for_conditions(conditions: list[str]) -> list[str]:
    """
    Genera alertas simplificadas para el propietario (sin mencionar fármacos).

    Args:
        conditions: Lista de condition_ids activos.

    Returns:
        Lista de strings deduplicadas con las alertas para el propietario.
    """
    seen: set[str] = set()
    alerts: list[str] = []
    for cond in conditions:
        for alert in get_drug_nutrient_alerts(cond):
            msg = alert.alerta_propietario
            if msg not in seen:
                seen.add(msg)
                alerts.append(msg)
    return alerts
