"""
Protocolos nutricionales clínicos para las 13 condiciones médicas soportadas.

Cada ConditionProtocol define:
- Objetivos dietéticos clínicos
- Metas numéricas de macronutrientes (% materia seca)
- Ingredientes preferidos y prohibidos (adicionales a los hard-coded en domain/)
- Reglas especiales por especie
- Suplementos recomendados con dosis
- Frecuencia de comidas
- Parámetros de monitoreo veterinario

Fuente: NRC 2006 + AAFCO 2023 + literatura veterinaria clínica peer-reviewed.
Validado clínicamente por Lady Carolina Castañeda (MV, BAMPYSVET).

IMPORTANTE: Este módulo solo define protocolos. La lista definitiva de
ingredientes tóxicos y restricciones hard-coded reside en domain/safety/.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SupplementoRecomendado:
    """Suplemento con dosificación por especie."""

    nombre: str
    dosis_perro: str          # Dosis para perros
    dosis_gato: str           # Dosis para gatos ("N/A" si no aplica)
    frecuencia: str
    forma: str                # Presentación preferida
    justificacion_clinica: str
    contraindicaciones: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ConditionProtocol:
    """
    Protocolo nutricional completo para una condición médica.

    Todos los porcentajes son sobre base de materia seca (MS) a menos que se indique.
    """

    condition_id: str
    display_name: str

    # ── Objetivos dietéticos ──────────────────────────────────────────────────
    dietary_goals: list[str]

    # ── Metas macronutrientes (% MS) ─────────────────────────────────────────
    proteina_pct_ms_min: float      # Mínimo % proteína sobre MS
    proteina_pct_ms_max: float      # Máximo % proteína sobre MS
    grasa_pct_ms_max: float         # Máximo % grasa sobre MS
    fibra_pct_ms_min: float         # Mínimo % fibra cruda sobre MS
    fibra_pct_ms_max: float         # Máximo % fibra cruda sobre MS

    # ── Restricciones minerales ───────────────────────────────────────────────
    fosforo_restringido: bool
    fosforo_g_por_100kcal_max: float | None   # None = sin restricción específica
    sodio_mg_dia_max: int | None              # None = sin restricción
    magnesio_restringido: bool                # Para cistitis/struvite
    cobre_restringido: bool                   # Para hepatopatía

    # ── Ingredientes preferidos (LATAM, en español) ───────────────────────────
    ingredientes_preferidos: list[str]

    # ── Ingredientes a evitar (ADICIONALES a domain/safety/) ─────────────────
    ingredientes_a_evitar: list[str]

    # ── Reglas especiales ─────────────────────────────────────────────────────
    numero_comidas_dia: int
    reglas_especiales: list[str]

    # ── Diferencias por especie ───────────────────────────────────────────────
    nota_perro: str
    nota_gato: str

    # ── Suplementos recomendados ──────────────────────────────────────────────
    suplementos: list[SupplementoRecomendado]

    # ── Monitoreo veterinario ─────────────────────="────────────────────────────
    parametros_monitoreo: list[str]

    # ── Justificación clínica ─────────────────────────────────────────────────
    justificacion: str


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOLOS — 13 CONDICIONES
# ═══════════════════════════════════════════════════════════════════════════════

PROTOCOL_DIABETICO = ConditionProtocol(
    condition_id="diabético",
    display_name="Diabetes Mellitus",
    dietary_goals=[
        "Estabilizar glucemia con carbohidratos de bajo índice glucémico",
        "Mantener peso corporal ideal (BCS 4-5/9)",
        "Alta fibra soluble para modular absorción de glucosa",
        "Comidas a horario fijo para sincronizar con insulina",
    ],
    proteina_pct_ms_min=28.0,
    proteina_pct_ms_max=35.0,
    grasa_pct_ms_max=15.0,
    fibra_pct_ms_min=8.0,
    fibra_pct_ms_max=18.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo cocida sin piel",
        "Pechuga de pavo cocida",
        "Clara de huevo cocida",
        "Atún en agua sin sal",
        "Sardinas en agua",
        "Avena integral cocida",
        "Batata/camote cocida sin piel",
        "Zanahoria cocida",
        "Brócoli cocido",
        "Vainitas/ejotes cocidos",
        "Calabacín/zucchini cocido",
        "Calabaza/ahuyama cocida",
        "Linaza molida (fibra soluble)",
        "Psyllium (fibra soluble — suplemento)",
    ],
    ingredientes_a_evitar=[
        "Arroz blanco (alto IG)",
        "Papa/patata cocida (alto IG)",
        "Maíz (alto IG)",
        "Pan, harinas refinadas",
        "Frutas altas en azúcar (mango, banano maduro, uvas)",
        "Miel, azúcar, jarabes",
        "Alimentos ultra-procesados con maíz o trigo",
        "Ingredientes fritos",
        "Hígado en exceso (alto en colesterol)",
    ],
    numero_comidas_dia=3,
    reglas_especiales=[
        "OBLIGATORIO: comidas a horario FIJO cada 8 horas — sincronizar con insulina",
        "NUNCA saltarse comida si recibe insulina — riesgo de hipoglucemia",
        "Pesar ración en gramos, nunca a ojo — control glucémico requiere consistencia",
        "Si el paciente recibe insulina NPH: dar comida JUSTO antes de la inyección",
        "Textura: preferir cocido y suave — mejor digestibilidad y absorción controlada",
        "Calcular calorías sobre PESO IDEAL si hay sobrepeso concurrente",
        "Fibra soluble: añadir psyllium 1 tsp/10kg/día mezclado en la comida",
        "Gatos: frecuencia 2-3 comidas/día — gatos toleran mejor libre acceso a alimento seco bajo IG",
    ],
    nota_perro=(
        "Diabetes tipo 2 es rara en perros — generalmente tipo 1 (dependiente de insulina). "
        "Alta fibra (10-18% MS) es MUY efectiva en perros. Usar avena integral y linaza. "
        "DER sobre peso ideal, no peso actual si hay obesidad."
    ),
    nota_gato=(
        "Diabetes tipo 2 en gatos: alta proteína + MUY bajos carbohidratos (<10% MS) "
        "puede llevar a remisión diabética. Priorizar proteína animal sobre fibra. "
        "Dieta húmeda/natural muy superior a seca para control glucémico en gatos. "
        "Algunos gatos en remisión con <12% carbohidratos MS."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Cromo picolinato",
            dosis_perro="200 mcg/día",
            dosis_gato="100 mcg/día",
            frecuencia="diario",
            forma="polvo o cápsula mezclada en alimento",
            justificacion_clinica="Mejora sensibilidad a la insulina",
            contraindicaciones=["Insuficiencia renal severa"],
        ),
        SupplementoRecomendado(
            nombre="Omega-3 (EPA+DHA)",
            dosis_perro="50 mg/kg/día",
            dosis_gato="50 mg/kg/día",
            frecuencia="diario",
            forma="aceite de salmón o cápsulas",
            justificacion_clinica="Reduce inflamación, mejora perfil lipídico",
            contraindicaciones=[],
        ),
    ],
    parametros_monitoreo=[
        "Glucemia en ayunas (meta: 100-250 mg/dL en perros tratados)",
        "Fructosamina cada 60-90 días",
        "Peso corporal semanal",
        "BCS cada 30 días",
        "Signos de hipoglucemia: temblores, debilidad, desorientación",
    ],
    justificacion=(
        "La diabetes mellitus requiere control glucémico estricto mediante dieta. "
        "Alta proteína preserva masa muscular y soporta sensibilidad insulínica. "
        "Alta fibra soluble retrasa absorción de glucosa (efecto prebiótico). "
        "Carbohidratos de bajo IG evitan picos postprandiales. "
        "La consistencia de ración y horario es tan importante como la composición."
    ),
)


PROTOCOL_HIPOTIROIDEO = ConditionProtocol(
    condition_id="hipotiroideo",
    display_name="Hipotiroidismo",
    dietary_goals=[
        "Mantener peso ideal (hipotiroidismo causa aumento de peso)",
        "Evitar ingredientes que interfieran con absorción de levotiroxina",
        "Aportar L-carnitina para mejorar metabolismo de grasas",
        "Restringir iodo a niveles normales (no suplementar en exceso)",
    ],
    proteina_pct_ms_min=25.0,
    proteina_pct_ms_max=35.0,
    grasa_pct_ms_max=20.0,
    fibra_pct_ms_min=5.0,
    fibra_pct_ms_max=12.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo cocida",
        "Pechuga de pavo cocida",
        "Conejo cocido",
        "Huevo entero cocido (fuente de L-carnitina)",
        "Res magra cocida (90% carne)",
        "Batata/camote cocida",
        "Zanahoria cocida",
        "Espinaca cocida (pequeñas cantidades)",
        "Arroz integral cocido",
        "Calabaza/ahuyama cocida",
    ],
    ingredientes_a_evitar=[
        "Soya y productos de soya (inhiben absorción de hormona tiroidea)",
        "Algas marinas y kelp (exceso de iodo — 50-800 mcg/100g)",
        "Harina de pescado o pescado de agua de mar en exceso (alto iodo)",
        "Maíz en exceso",
        "Col cruda, brócoli crudo, repollo crudo (bociógenos — seguros cocidos)",
        "Nabo crudo, rábano crudo",
        "Glutén de trigo en exceso",
    ],
    numero_comidas_dia=2,
    reglas_especiales=[
        "Si recibe levotiroxina: dar la medicación 30-60 min ANTES de comer para máxima absorción",
        "NUNCA dar soya ni algas con la medicación",
        "Col, brócoli y repollo son seguros SI ESTÁN COCIDOS (destruye bociógenos)",
        "L-carnitina: suplementar 50-100 mg/kg/día — mejora metabolismo lipídico",
        "Control estricto de calorías — tasa metabólica reducida en 20-40%",
        "Calcular DER con factor de actividad REDUCIDO (sedentario aunque el perro sea 'activo')",
        "Pesar a la mascota CADA SEMANA durante el primer mes de tratamiento",
    ],
    nota_perro=(
        "Hipotiroidismo es común en perros medianos-grandes (Golden Retriever, Doberman, Beagle). "
        "La restricción calórica es crítica — el metabolismo basal está reducido. "
        "L-carnitina 50-100 mg/kg/día mejora movilización de grasa. "
        "El tratamiento con levotiroxina requiere dieta consistente para estabilizar la dosis."
    ),
    nota_gato=(
        "Hipotiroidismo es RARO en gatos (más frecuente hipertiroidismo). "
        "Si es post-tratamiento por hipertiroidismo: las mismas pautas aplican. "
        "Gatos toleran menos restricción calórica — riesgo de lipidosis hepática."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="L-carnitina",
            dosis_perro="50-100 mg/kg/día (máx 2g/día)",
            dosis_gato="250-500 mg/día",
            frecuencia="diario",
            forma="polvo o líquido mezclado en alimento",
            justificacion_clinica="Mejora oxidación de ácidos grasos, reduce acumulación grasa",
            contraindicaciones=["Insuficiencia renal severa"],
        ),
        SupplementoRecomendado(
            nombre="Omega-3 (EPA+DHA)",
            dosis_perro="50 mg/kg/día",
            dosis_gato="N/A — hipertiroidismo es más común",
            frecuencia="diario",
            forma="aceite de salmón",
            justificacion_clinica="Mejora perfil lipídico (hipotiroidismo causa hiperlipemia)",
            contraindicaciones=[],
        ),
    ],
    parametros_monitoreo=[
        "TSH y T4 libre cada 60-90 días hasta estabilizar, luego cada 6 meses",
        "Perfil lipídico (colesterol, triglicéridos) — frecuente hiperlipemia asociada",
        "Peso corporal mensual",
        "BCS cada 30 días",
        "Signos dermatológicos: alopecia bilateral simétrica, piel engrosada",
    ],
    justificacion=(
        "El hipotiroidismo reduce el metabolismo basal en 20-40%, causando obesidad y dislipidemia. "
        "La dieta debe restringir calorías ajustando factores de actividad a la baja. "
        "L-carnitina es el suplemento más respaldado clínicamente para esta condición. "
        "Evitar ingredientes bociógenos y los que interfieren con la levotiroxina es crítico "
        "para que el tratamiento médico funcione correctamente."
    ),
)


PROTOCOL_CANCERIGENO = ConditionProtocol(
    condition_id="cancerígeno",
    display_name="Cáncer / Neoplasia",
    dietary_goals=[
        "Reducir sustrato energético para células tumorales (glucosa)",
        "Alta grasa y proteína como fuente calórica principal (efecto ketogénico moderado)",
        "Omega-3 EPA+DHA anti-inflamatorio y anti-tumoral",
        "Preservar masa muscular ante catabolismo tumoral",
        "Alta digestibilidad para mascotas con apetito reducido por quimioterapia",
    ],
    proteina_pct_ms_min=30.0,
    proteina_pct_ms_max=45.0,
    grasa_pct_ms_max=50.0,   # Alta grasa como fuente calórica preferida
    fibra_pct_ms_min=2.0,
    fibra_pct_ms_max=8.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Sardinas en agua (omega-3 alto)",
        "Salmón cocido sin espinas",
        "Caballa cocida",
        "Pechuga de pollo cocida",
        "Huevo entero cocido",
        "Res magra cocida",
        "Aceite de salmón (suplemento de omega-3)",
        "Aceite de coco (TCM — tricialglicéridos de cadena media)",
        "Brócoli cocido (sulforafano — anti-tumoral)",
        "Espinaca cocida",
        "Arándanos (pequeñas cantidades — antioxidantes)",
        "Zanahoria cocida",
    ],
    ingredientes_a_evitar=[
        "Arroz blanco, papa, maíz (carbohidratos simples — sustrato tumoral)",
        "Azúcar, miel, frutas dulces en exceso",
        "Alimentos procesados con conservantes",
        "Aceites vegetales altos en omega-6 (maíz, soya, girasol) — pro-inflamatorios",
        "Hígado en exceso durante quimioterapia (sobrecarla hepática)",
    ],
    numero_comidas_dia=3,
    reglas_especiales=[
        "Si recibe quimioterapia: reducir fibra y grasa durante días de tratamiento (GI sensible)",
        "Si hay anorexia: aumentar palatabilidad con aceite de salmón — no con ingredientes dañinos",
        "Tumores gastrointestinales: alta digestibilidad, comidas pequeñas y frecuentes (4-5/día)",
        "Tumores orales: textura suave o licuada si hay dificultad masticatoria",
        "Carbohidratos: NO eliminar completamente — reducir a <15% MS y usar complejos (no simples)",
        "Omega-3: dosis terapéutica 100-200 mg/kg/día de EPA+DHA (doble de la dosis estándar)",
        "Aceite de coco (TCM): 1 ml/kg/día — fuente de energía alternativa a glucosa para el huésped",
        "Ayuno superior a 12h CONTRAINDICADO absolutamente (REGLA 10)",
    ],
    nota_perro=(
        "Histiocitoma, linfoma y osteosarcoma son más comunes en perros grandes. "
        "La caquexia tumoral es una emergencia nutricional — priorizar calorías y proteína. "
        "Omega-3 EPA a 100-150 mg/kg/día tiene evidencia para linfoma canino."
    ),
    nota_gato=(
        "Linfoma y carcinoma mamario son más frecuentes en gatos. "
        "Los gatos son obligados carnívoros — naturalmente bajo en carbohidratos, "
        "hacer la 'dieta anticáncer' es más fisiológica en gatos. "
        "Alta proteína es crítica — nunca reducir por debajo de 26% MS."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Omega-3 EPA+DHA (dosis terapéutica)",
            dosis_perro="100-200 mg/kg/día de EPA+DHA combinado",
            dosis_gato="100 mg/kg/día de EPA+DHA",
            frecuencia="diario",
            forma="aceite de salmón o cápsulas de concentrado marino",
            justificacion_clinica=(
                "EPA inhibe eicosanoides pro-tumorales, modula caquexia, "
                "mejora respuesta a quimioterapia en linfoma"
            ),
            contraindicaciones=["Pancreatitis activa", "Coagulopatías"],
        ),
        SupplementoRecomendado(
            nombre="Antioxidantes (Vitamina E + Vitamina C)",
            dosis_perro="Vit E: 400 UI/día · Vit C: 500 mg/día",
            dosis_gato="Vit E: 100 UI/día · Vit C: 125 mg/día",
            frecuencia="diario",
            forma="cápsulas mezcladas en alimento",
            justificacion_clinica="Reducen estrés oxidativo generado por tumor y quimioterapia",
            contraindicaciones=["NO usar durante radioterapia — puede interferir con eficacia"],
        ),
    ],
    parametros_monitoreo=[
        "Peso y BCS semanal (pérdida >5% en 30 días = emergencia nutricional)",
        "Albumina sérica (meta: >2.5 g/dL)",
        "Perfil hepático si recibe quimioterapia",
        "Apetito y vómitos (diario por el propietario)",
        "Masa muscular — evaluación del músculo epaxial",
    ],
    justificacion=(
        "Las células tumorales dependen principalmente de glucosa (efecto Warburg). "
        "Reducir carbohidratos disponibles mientras se aportan grasas de calidad "
        "favorece al huésped sobre el tumor. El omega-3 EPA tiene evidencia en linfoma canino "
        "para reducir producción de eicosanoides pro-tumorales y mejorar la respuesta "
        "a quimioterapia. La caquexia tumoral es la causa de muerte en 30-40% de casos — "
        "preservar masa muscular es prioridad absoluta."
    ),
)


PROTOCOL_ARTICULAR = ConditionProtocol(
    condition_id="articular",
    display_name="Enfermedad Articular / Osteoartritis",
    dietary_goals=[
        "Control de peso — reducir carga articular (cada kg extra = 4kg de presión articular)",
        "Anti-inflamatorio mediante omega-3 EPA+DHA",
        "Preservar masa muscular para soporte articular",
        "Suplementar glucosamina y condroitina",
    ],
    proteina_pct_ms_min=22.0,
    proteina_pct_ms_max=30.0,
    grasa_pct_ms_max=20.0,
    fibra_pct_ms_min=5.0,
    fibra_pct_ms_max=12.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Sardinas en agua (omega-3 + calcio natural)",
        "Salmón cocido sin espinas",
        "Pechuga de pollo cocida",
        "Pechuga de pavo cocida",
        "Huevo entero cocido",
        "Mejillón de labio verde (Perna canaliculus — omega-3 + glucosamina natural)",
        "Zanahoria cocida",
        "Calabacín/zucchini cocido",
        "Batata/camote cocida",
        "Arándanos (pequeñas cantidades — antioxidantes articulares)",
        "Jengibre (antiinflamatorio natural — pequeñas cantidades cocido)",
        "Cúrcuma (curcumina antiinflamatoria — con pimienta negra)",
    ],
    ingredientes_a_evitar=[
        "Aceites vegetales ricos en omega-6 (girasol, maíz, soya) en exceso — pro-inflamatorios",
        "Alimentos ultra-procesados",
        "Alimentos altos en grasa saturada en exceso",
        "Nachtschatten vegetables en exceso: tomate, berenjena, pimiento (potencial pro-inflamatorio en algunos pacientes)",
    ],
    numero_comidas_dia=2,
    reglas_especiales=[
        "Si hay sobrepeso (BCS ≥7): calcular sobre PESO IDEAL con factor 0.8 — pérdida de peso es la intervención más efectiva",
        "Omega-3 a dosis terapéutica: 75-100 mg EPA+DHA/kg/día",
        "Glucosamina HCl: 15-20 mg/kg/día — efecto a las 4-8 semanas",
        "Condroitín sulfato: 15 mg/kg/día — complementario a glucosamina",
        "Aceite de krill superior a aceite de salmón por mejor biodisponibilidad",
        "Cúrcuma: 15-20 mg/kg/día con pimienta negra (mejora absorción 20x)",
        "Evitar ejercicio de alto impacto — preferir natación o caminata suave",
        "Enriquecer con antioxidantes (Vit E) para reducir radicales libres articulares",
    ],
    nota_perro=(
        "Razas grandes (Labrador, Golden, Pastor) con displasia de cadera/codo. "
        "Control de peso es la intervención NÚMERO UNO — más efectiva que cualquier suplemento. "
        "Piscina/hidroterapia recomendada como ejercicio complementario."
    ),
    nota_gato=(
        "Osteoartritis en gatos está subdiagnosticada (>60% gatos >6 años tienen signos radiológicos). "
        "Los gatos no muestran cojera obvia — observar dificultad para subir, acicalarse la espalda, saltar. "
        "Omega-3 EPA a 50-75 mg/kg/día es bien tolerado en gatos."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Omega-3 EPA+DHA",
            dosis_perro="75-100 mg/kg/día de EPA+DHA",
            dosis_gato="50-75 mg/kg/día de EPA+DHA",
            frecuencia="diario",
            forma="aceite de salmón o krill",
            justificacion_clinica=(
                "Inhibe mediadores inflamatorios (IL-1, PGE2), reduce dolor articular "
                "demostrado en estudios controlados"
            ),
            contraindicaciones=["Pancreatitis activa"],
        ),
        SupplementoRecomendado(
            nombre="Glucosamina HCl + Condroitín sulfato",
            dosis_perro="Glucosamina: 15-20 mg/kg/día · Condroitín: 15 mg/kg/día",
            dosis_gato="Glucosamina: 125 mg/día · Condroitín: 50 mg/día",
            frecuencia="diario",
            forma="comprimidos o polvo mezclado en alimento",
            justificacion_clinica="Protegen cartílago articular, reducen degradación",
            contraindicaciones=["Diabetes (glucosamina puede afectar glucemia — monitorear)"],
        ),
        SupplementoRecomendado(
            nombre="Curcumina (Cúrcuma)",
            dosis_perro="15-20 mg/kg/día con pimienta negra (piperina)",
            dosis_gato="N/A — metabolismo diferente del curcuminoides",
            frecuencia="diario",
            forma="polvo de cúrcuma con pizca de pimienta negra mezclado en comida",
            justificacion_clinica="Anti-inflamatorio COX-2, respaldo en osteoartritis canina",
            contraindicaciones=["Cálculos biliares", "Uso con anticoagulantes"],
        ),
    ],
    parametros_monitoreo=[
        "Peso y BCS mensual",
        "Evaluación de dolor (escala CBPI — dolor crónico en perros)",
        "Movilidad: capacidad de subir escaleras, saltar, levantarse",
        "Radiografías articulares cada 12 meses en estadios avanzados",
    ],
    justificacion=(
        "La osteoartritis es irreversible pero manejable con dieta. "
        "El control de peso reduce la carga mecánica articular dramáticamente — "
        "perder 6-8% del peso reduce el dolor articular de forma comparable a AINEs. "
        "El omega-3 EPA tiene la mayor evidencia en medicina veterinaria para dolor articular. "
        "Glucosamina y condroitín sulfato protegen el cartílago existente y pueden ralentizar progresión."
    ),
)


PROTOCOL_RENAL = ConditionProtocol(
    condition_id="renal",
    display_name="Enfermedad Renal Crónica (ERC)",
    dietary_goals=[
        "Reducir carga de fosfatos (retrasa progresión de ERC)",
        "Proteína de alta calidad a dosis reducida (minimizar uremia)",
        "Alta humedad para mantener hidratación y dilución de orina",
        "Potasio suplementado si hipocalemia (común en gatos con ERC)",
        "Omega-3 para nefroprotección",
    ],
    proteina_pct_ms_min=14.0,    # Estadio 2-3. Estadio 4: hasta 10% MS
    proteina_pct_ms_max=20.0,    # No exceder — genera uremia
    grasa_pct_ms_max=25.0,       # Grasa como fuente calórica alternativa
    fibra_pct_ms_min=3.0,
    fibra_pct_ms_max=8.0,
    fosforo_restringido=True,
    fosforo_g_por_100kcal_max=0.5,   # IRIS estadio 2: <0.5g/100kcal; estadio 3: <0.4
    sodio_mg_dia_max=300,             # Restricción moderada — no severa
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Clara de huevo cocida (proteína de máxima calidad, MUY bajo fósforo)",
        "Pechuga de pollo cocida (bajo fósforo vs otras proteínas)",
        "Pechuga de pavo cocida",
        "Conejo cocido (bajo fósforo)",
        "Arroz blanco cocido (bajo fósforo, alta digestibilidad)",
        "Pasta cocida sin sal (bajo fósforo)",
        "Papa/patata hervida sin piel (bajo fósforo cuando moderada)",
        "Batata/camote cocida",
        "Zanahoria cocida",
        "Calabacín/zucchini cocido",
        "Calabaza/ahuyama cocida",
        "Aceite de oliva (calorías sin fósforo)",
        "Aceite de coco (TCM — calorías sin fósforo)",
    ],
    ingredientes_a_evitar=[
        "Hueso (hueso crudo o cocido — muy alto fósforo)",
        "Hígado, riñón, corazón (altísimo fósforo)",
        "Sardinas/atún en lata con espinas (alto fósforo)",
        "Carne roja oscura en exceso (alto fósforo y purinas)",
        "Legumbres (alto fósforo)",
        "Productos lácteos altos en fósforo (queso, leche)",
        "Alimentos procesados con fosfatos aditivos (leer etiqueta)",
        "Sal en cualquier cantidad",
    ],
    numero_comidas_dia=3,
    reglas_especiales=[
        "ESTADIO IRIS 1: restricción moderada de fósforo (<0.6g/100kcal). Proteína normal.",
        "ESTADIO IRIS 2: fósforo <0.5g/100kcal. Proteína 14-20% MS. Hidratación crítica.",
        "ESTADIO IRIS 3: fósforo <0.4g/100kcal. Proteína 12-16% MS. Considerar quelante de fósforo.",
        "ESTADIO IRIS 4: fósforo <0.3g/100kcal. Proteína 10-14% MS. Manejo paliativo.",
        "HIDRATACIÓN: dieta húmeda/natural es prioritaria — agua libre siempre disponible",
        "Quelantes de fósforo si la dieta no logra meta: hidróxido de aluminio o carbonato de lantano (bajo supervisión vet)",
        "Potasio: gatos con ERC frecuentemente tienen hipocalemia — suplementar con gluconato de potasio",
        "NaHCO3 si acidosis metabólica (pH <7.2 o bicarbonato <18) — bajo supervisión vet",
        "Enriquecer con aceites para aportar calorías sin aumentar proteína ni fósforo",
        "NUNCA reducir proteína a menos del mínimo NRC — riesgo de desnutrición proteica",
    ],
    nota_perro=(
        "ERC estadio 2-3 es manejable años con dieta. "
        "Clara de huevo + arroz blanco es la combinación clásica 'low phosphorus'. "
        "Omega-3: 75 mg/kg/día de EPA — nefroprotector demostrado. "
        "Vigilar presión arterial — hipertensión en ERC es común y empeora progresión."
    ),
    nota_gato=(
        "ERC es la causa de muerte más frecuente en gatos >12 años. "
        "GATOS con ERC: hipocalemia frecuente → suplementar potasio (gluconato de K). "
        "Hipertiroidismo puede enmascarar ERC — tratar hipertiroidismo primero. "
        "Dieta húmeda es ESENCIAL — gatos no beben suficiente agua con dieta seca. "
        "Restricción proteica agresiva NO recomendada en estadio 1-2 (riesgo desnutrición)."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Omega-3 EPA+DHA",
            dosis_perro="75-100 mg/kg/día de EPA+DHA",
            dosis_gato="50-75 mg/kg/día",
            frecuencia="diario",
            forma="aceite de salmón",
            justificacion_clinica=(
                "Reduce inflamación glomerular, disminuye proteinuria, "
                "nefroprotección demostrada en ERC estadio 2-3"
            ),
            contraindicaciones=[],
        ),
        SupplementoRecomendado(
            nombre="Gluconato de potasio (solo si hipocalemia)",
            dosis_perro="N/A — raro en perros",
            dosis_gato="2-6 mEq/día según kalemia",
            frecuencia="diario",
            forma="polvo mezclado en alimento",
            justificacion_clinica=(
                "Hipocalemia en gatos con ERC causa debilidad, ventroflexión cervical y deterioro renal"
            ),
            contraindicaciones=["Hipercalemia", "Obstrucción urinaria activa"],
        ),
        SupplementoRecomendado(
            nombre="B-complex vitamínico",
            dosis_perro="1 ampolla/semana o según laboratorio",
            dosis_gato="1 ampolla/semana",
            frecuencia="semanal",
            forma="inyectable SC (supervisión vet) o tableta oral",
            justificacion_clinica=(
                "ERC causa pérdida de vitaminas hidrosolubles (B1, B6, B12) por diuresis compensatoria"
            ),
            contraindicaciones=[],
        ),
    ],
    parametros_monitoreo=[
        "BUN y creatinina sérica cada 60-90 días (meta: creatinina estable o en descenso)",
        "Fósforo sérico (meta: <4.5 mg/dL estadio 2; <5.0 mg/dL estadio 3)",
        "Potasio sérico (meta: 3.5-5.5 mEq/L)",
        "Presión arterial (meta: <160/100 mmHg)",
        "UPC (proteína/creatinina urinaria — meta: <0.2 en perros, <0.4 en gatos)",
        "Peso y condición muscular mensual",
        "Estadio IRIS actualizado en cada control",
    ],
    justificacion=(
        "La restricción de fósforo es la intervención nutricional más respaldada en ERC — "
        "reduce la hiperfosfatemia que acelera la mineralización renal y la progresión de la enfermedad. "
        "La proteína se reduce para disminuir la producción de uremia (BUN), pero NUNCA por debajo del "
        "mínimo NRC — la malnutrición proteica empeora el pronóstico. "
        "La hidratación mediante dieta húmeda mantiene la dilución urinaria y flujo glomerular."
    ),
)


PROTOCOL_HEPATICO = ConditionProtocol(
    condition_id="hepático/hiperlipidemia",
    display_name="Hepatopatía / Hiperlipidemia",
    dietary_goals=[
        "Reducir carga de trabajo hepático con proteína moderada y de alta calidad",
        "Grasa MUY restringida (<10% MS) si hay hiperlipidemia",
        "Alta digestibilidad para maximizar absorción con función hepática reducida",
        "Zinc y vitamina E como hepatoprotectores",
        "Fibra soluble para atrapar amoniaco y reducir encefalopatía hepática",
    ],
    proteina_pct_ms_min=18.0,    # No demasiado baja — el hígado necesita AAs para regenerarse
    proteina_pct_ms_max=25.0,
    grasa_pct_ms_max=10.0,       # MUY bajo si hay hiperlipidemia o lipidosis
    fibra_pct_ms_min=5.0,
    fibra_pct_ms_max=12.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=200,         # Restricción si hay ascitis
    magnesio_restringido=False,
    cobre_restringido=True,       # Hígado acumula cobre en hepatopatía crónica
    ingredientes_preferidos=[
        "Clara de huevo cocida (aminoácidos de cadena ramificada, bajo cobre)",
        "Pechuga de pollo cocida sin piel (bajo cobre)",
        "Pechuga de pavo cocida (bajo cobre)",
        "Requesón/cottage cheese bajo en grasa (aminoácidos ramificados — PERROS)",
        "Tofu firme cocido (aminoácidos ramificados, bajo cobre)",
        "Arroz blanco cocido (alta digestibilidad)",
        "Pasta cocida sin sal",
        "Batata/camote cocida",
        "Calabaza/ahuyama cocida",
        "Espinaca cocida (folato, antioxidante)",
        "Zanahoria cocida",
        "Avena cocida (fibra soluble — captura amoniaco)",
    ],
    ingredientes_a_evitar=[
        "Hígado, riñón (altísimo en cobre — 2-12 mg Cu/100g)",
        "Mariscos y moluscos (ostras, mejillones — muy alto cobre)",
        "Nueces y legumbres (alto cobre)",
        "Alimentos fermentados o curados (salchichas, embutidos)",
        "Grasas animales visibles (manteca, tocino, piel de pollo)",
        "Aceites en exceso si hay hiperlipidemia",
        "Alimentos altos en grasa saturada",
        "Sal y condimentos",
        "Alimentos con additivos artificiales",
    ],
    numero_comidas_dia=3,
    reglas_especiales=[
        "Si hay ENCEFALOPATÍA HEPÁTICA: reducir proteína a mínimo tolerable + fibra fermentable alta",
        "Proteína preferida: VEGETAL (tofu, requesón) o aminoácidos ramificados — menos amoniaco",
        "SAM-e (S-adenosilmetionina): 20 mg/kg/día en perros — hepatoprotector demostrado",
        "UDCA (ácido ursodesoxicólico): hepatoprotector — bajo supervisión vet",
        "Zinc: 3-5 mg/kg/día en perros — hepatoprotector, reduce acumulación de cobre",
        "Si hay ASCITIS: restricción sódica severa + proteína moderada",
        "Si hay LIPIDOSIS en gato: forzar alimentación (sonda si es necesario) — ayuno >12h es peligroso",
        "GATOS: lipidosis hepática idiopática es emergencia — alimentación mínima de 60 kcal/kg/día es crítica",
        "Vitamina E: 400 UI/día en perros — antioxidante hepático",
        "Comidas pequeñas y frecuentes para no saturar el metabolismo hepático",
    ],
    nota_perro=(
        "Hepatitis crónica y shunt portosistémico son más frecuentes. "
        "Razas con predisposición a acumulación de cobre: Bedlington Terrier, Labrador, Dálmata, Doberman. "
        "Encefalopatía hepática: reducir proteína y aumentar fibra fermentable (lactulose + dieta). "
        "SAM-e 20 mg/kg/día y UDCA 10-15 mg/kg/día son el estándar en hepatopatía crónica canina."
    ),
    nota_gato=(
        "LIPIDOSIS HEPÁTICA es emergencia — puede ocurrir con solo 24-48h de ayuno en gatos obesos. "
        "NUNCA restringir calorías agresivamente en gatos — reducir 20-30% máximo. "
        "Si el gato no come: nutrición enteral (sonda NE o NG) es preferible a ayuno. "
        "Taurina ESENCIAL en gatos — suplementar 250 mg/día si dieta alterada."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="SAM-e (S-adenosilmetionina)",
            dosis_perro="20 mg/kg/día (máx 400 mg/día)",
            dosis_gato="90 mg/día",
            frecuencia="diario en ayunas",
            forma="tabletas entéricas (no masticar)",
            justificacion_clinica=(
                "Principal antioxidante hepático endógeno. Mejora función hepática "
                "y reduce fibrogénesis en hepatopatía crónica"
            ),
            contraindicaciones=["Epilepsia", "Uso con inhibidores MAO"],
        ),
        SupplementoRecomendado(
            nombre="Vitamina E",
            dosis_perro="400 UI/día",
            dosis_gato="100 UI/día",
            frecuencia="diario",
            forma="cápsulas de tocoferol",
            justificacion_clinica="Antioxidante hepático que reduce daño oxidativo por inflamación",
            contraindicaciones=["Coagulopatía severa (Vit E puede inhibir plaquetas)"],
        ),
        SupplementoRecomendado(
            nombre="Zinc (gluconato o acetato)",
            dosis_perro="3-5 mg/kg/día elemental",
            dosis_gato="2-3 mg/kg/día elemental",
            frecuencia="diario con comida",
            forma="tabletas o polvo",
            justificacion_clinica=(
                "Antagoniza absorción de cobre, cofactor enzimático hepático, "
                "reduce acumulación de cobre en hepatopatía"
            ),
            contraindicaciones=["Insuficiencia renal severa", "Exceso causa toxicidad en gatos"],
        ),
    ],
    parametros_monitoreo=[
        "ALT, AST, GGT, fosfatasa alcalina cada 30-60 días inicialmente",
        "Albumina sérica (indicador de función hepática — meta: >2.0 g/dL)",
        "Colesterol y triglicéridos (si hay hiperlipidemia)",
        "BUN y amoniaco si sospecha encefalopatía",
        "Bilirrubina total",
        "Peso y BCS mensual",
        "Signos neurológicos (encefalopatía): desorientación, convulsiones, presión de cabeza",
    ],
    justificacion=(
        "La hepatopatía requiere reducir la carga metabólica del hígado mientras se proveen "
        "los nutrientes necesarios para la regeneración hepatocelular. "
        "La grasa se restringe severamente en hiperlipidemia (triglicéridos >500 mg/dL). "
        "El cobre se elimina de la dieta porque el hígado dañado lo acumula. "
        "SAM-e y vitamina E tienen la mayor evidencia como hepatoprotectores nutricionales."
    ),
)


PROTOCOL_PANCREATICO = ConditionProtocol(
    condition_id="pancreático",
    display_name="Pancreatitis",
    dietary_goals=[
        "GRASA MUY BAJA para no estimular secreción de lipasa pancreática",
        "Alta digestibilidad para minimizar trabajo pancreático",
        "Comidas pequeñas y muy frecuentes",
        "Rehidratación — la pancreatitis causa vómitos y deshidratación",
    ],
    proteina_pct_ms_min=18.0,
    proteina_pct_ms_max=25.0,
    grasa_pct_ms_max=8.0,        # MÁXIMO 8% MS — el menor de todas las condiciones
    fibra_pct_ms_min=3.0,
    fibra_pct_ms_max=8.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo hervida sin piel (grasa <1%)",
        "Pechuga de pavo hervida sin piel",
        "Pescado blanco hervido (merluza, corvina, tilapia — grasa <2%)",
        "Clara de huevo cocida",
        "Arroz blanco hervido (BIEN cocido — alta digestibilidad)",
        "Papa hervida sin piel (sin yema ni mantequilla)",
        "Batata/camote hervida sin piel",
        "Calabaza/ahuyama hervida",
        "Zanahoria hervida",
        "Calabacín/zucchini hervido",
        "Pasta cocida sin aceite",
    ],
    ingredientes_a_evitar=[
        "Cualquier ingrediente frito",
        "Grasas visibles: manteca, aceite de coco, aceite de oliva en exceso",
        "Piel de pollo (37% grasa)",
        "Carne de cerdo y cortes grasos de res",
        "Embutidos, salchichas, quesos grasos",
        "Productos lácteos altos en grasa (mantequilla, crema, leche entera)",
        "Huevo completo (yema — 30% grasa)",
        "Aguacate/palta (alto en grasa)",
        "Nueces y maníes",
        "Alimentos comerciales altos en grasa (>15% en etiqueta)",
    ],
    numero_comidas_dia=4,
    reglas_especiales=[
        "FASE AGUDA: ayuno inicial solo bajo supervisión vet (max 12h) luego reintroducir",
        "REINTRODUCCIÓN: iniciar con agua, luego arroz con caldo sin grasa, luego proteína magra",
        "Calcular grasa total del plan: no debe superar 8g/día por cada 10kg de peso",
        "Vitamina B12 (cobalamina): suplementar si hay insuficiencia pancreática exocrina",
        "Enzimas pancreáticas: bajo supervisión vet en IPE (insuficiencia pancreática exocrina)",
        "NO usar aceite de coco ni aceite de oliva durante pancreatitis activa",
        "PANCREATITIS CRÓNICA: misma restricción de grasa permanente",
        "Fracasar en reducir grasa es la causa más común de recaída — CERO excepciones",
        "Calcular el contenido de grasa de CADA ingrediente y sumar — no estimar",
    ],
    nota_perro=(
        "Pancreatitis más frecuente en perros de mediana edad obesos con dieta alta en grasa. "
        "Schnauzer miniatura tiene predisposición genética a hipertrigliceridemia y pancreatitis. "
        "Yorkies y Cocker Spaniels también predispuestos. "
        "La restricción de grasa debe ser PERMANENTE en pancreatitis crónica."
    ),
    nota_gato=(
        "Pancreatitis felina frecuentemente se presenta como 'triaditis' — junto con EII y colangitis. "
        "Los gatos son más sutiles en síntomas: letargo, anorexia, pérdida de peso. "
        "Taurina CRÍTICA en gatos con pancreatitis — suplementar 250 mg/día. "
        "Gatos no toleran bien la restricción de proteína — mantener >26% MS."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Vitamina B12 (cobalamina)",
            dosis_perro="250-1000 mcg/semana SC (o 250 mcg oral diario)",
            dosis_gato="250 mcg/semana SC o 250 mcg oral diario",
            frecuencia="semanal (inyectable) o diario (oral)",
            forma="inyectable SC o tabletas",
            justificacion_clinica=(
                "Deficiencia de cobalamina común en pancreatitis e IPE por absorción en íleon. "
                "La deficiencia empeora pronóstico — suplementar agresivamente"
            ),
            contraindicaciones=[],
        ),
    ],
    parametros_monitoreo=[
        "Lipasa pancreática específica (PLI) — cPLI en perros, fPLI en gatos",
        "Triglicéridos séricos (meta: <500 mg/dL, ideal <150 mg/dL)",
        "Colesterol sérico",
        "Peso y apetito semanal durante fase activa",
        "Signos de dolor abdominal (postura de ruego, vocalización)",
        "Cobalamina sérica (vitamina B12) — si IPE sospechado",
    ],
    justificacion=(
        "La pancreatitis se desencadena y perpetúa por estimulación con grasa — "
        "la lipasa pancreática se activa prematuramente en respuesta a alto contenido lipídico. "
        "La restricción de grasa al <8% MS es el pilar del tratamiento nutricional. "
        "Las comidas frecuentes y pequeñas reducen el pico de secreción pancreática postprandial. "
        "La hiperlipidemia (especialmente triglicéridos >500 mg/dL) puede CAUSAR pancreatitis."
    ),
)


PROTOCOL_NEURODEGENERATIVO = ConditionProtocol(
    condition_id="neurodegenerativo",
    display_name="Síndrome de Disfunción Cognitiva",
    dietary_goals=[
        "Antioxidantes para reducir estrés oxidativo cerebral",
        "Omega-3 DHA para estructura y función neuronal",
        "TCM (triglicéridos de cadena media) como fuente alternativa de energía cerebral",
        "Vitamina E y C sinérgicas como neuroprotectores",
    ],
    proteina_pct_ms_min=22.0,
    proteina_pct_ms_max=32.0,
    grasa_pct_ms_max=20.0,
    fibra_pct_ms_min=3.0,
    fibra_pct_ms_max=10.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Sardinas en agua (DHA alto)",
        "Salmón cocido (DHA alto)",
        "Huevo entero cocido (colina — esencial para membrana neuronal)",
        "Pechuga de pollo cocida",
        "Arándanos (antocianinas — antioxidantes neuroprotectores)",
        "Espinaca cocida (folato, luteína)",
        "Zanahoria cocida (beta-caroteno)",
        "Aceite de coco puro (TCM — ketogénico cerebral)",
        "Calabaza/ahuyama (antioxidantes, fibra)",
    ],
    ingredientes_a_evitar=[
        "Aceites vegetales ricos en omega-6 en exceso (pro-oxidantes competidores de DHA)",
        "Alimentos ultra-procesados con conservantes sintéticos (BHA, BHT)",
        "Exceso de cobre (pro-oxidante en cerebro)",
        "Alimentos con colorantes sintéticos",
    ],
    numero_comidas_dia=2,
    reglas_especiales=[
        "Aceite de coco: 1 ml/kg/día — fuente de TCM que el cerebro envejecido puede usar directamente",
        "Omega-3 DHA específico (no solo EPA): 50-100 mg/kg/día de DHA para cerebro",
        "Vitamina E: 400 UI/día en perros — antioxidante liposoluble en membranas neuronales",
        "Vitamina C: 250-500 mg/día en perros (aunque sintetizan — suplementar es beneficioso)",
        "Colina: huevo entero es la mejor fuente natural — 1 huevo/10kg/día",
        "L-carnitina: 50-100 mg/kg/día mejora metabolismo energético neuronal",
        "Enriquecimiento ambiental es complementario a la dieta — no solo nutricional",
        "Fosfatidilserina: 25-75 mg/día (suplemento — mejora transmisión sináptica)",
    ],
    nota_perro=(
        "SDC afecta al 50% de perros >11 años. Signos: desorientación, cambios en ciclo sueño/vigilia, "
        "pérdida de entrenamiento, cambios de personalidad. "
        "El aceite de coco (TCM) tiene evidencia emergente — comenzar con 0.5 ml/kg para evitar diarrea. "
        "Selegilina (Anipryl) y antioxidantes dietéticos son complementarios."
    ),
    nota_gato=(
        "SDC en gatos similar pero aún más subdiagnosticado. "
        "Maullido nocturno y desorientación son signos clave. "
        "Los gatos NO metabolizan bien el aceite de coco en exceso — limitarlo a 0.5 ml/día máx. "
        "Omega-3 DHA es seguro y beneficioso en gatos adultos mayores."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Omega-3 DHA (enfocado en DHA, no EPA)",
            dosis_perro="50-100 mg DHA/kg/día",
            dosis_gato="50 mg DHA/kg/día",
            frecuencia="diario",
            forma="aceite de salmón o cápsulas específicas de DHA",
            justificacion_clinica=(
                "DHA es componente estructural de membranas neuronales (40% de grasas del cerebro). "
                "Suplementación mejora función cognitiva en perros mayores"
            ),
            contraindicaciones=[],
        ),
        SupplementoRecomendado(
            nombre="Vitamina E + Vitamina C (combinación antioxidante)",
            dosis_perro="Vit E: 400 UI · Vit C: 250-500 mg diario",
            dosis_gato="Vit E: 100 UI · Vit C: 125 mg diario",
            frecuencia="diario",
            forma="cápsulas",
            justificacion_clinica=(
                "Sinergia antioxidante — Vit C recicla Vit E. "
                "Reducen oxidación de lípidos en membranas neuronales"
            ),
            contraindicaciones=["No exceder Vit E >800 UI — efecto pro-oxidante"],
        ),
    ],
    parametros_monitoreo=[
        "Escala cognitiva CCDR (Canine Cognitive Dysfunction Rating) mensual",
        "Calidad de sueño (propietario registra interrupciones nocturnas)",
        "Orientación y navegación en el hogar",
        "Reconocimiento de personas familiares",
        "Apetito y peso mensual",
    ],
    justificacion=(
        "El síndrome de disfunción cognitiva es el 'Alzheimer' veterinario — "
        "acumulación de beta-amiloide y radicales libres en cerebro envejecido. "
        "Los antioxidantes reducen la carga oxidativa cerebral. "
        "El DHA es structural para las membranas neuronales. "
        "Los TCM del aceite de coco proporcionan cetonas como combustible alternativo "
        "para neuronas que no metabolizan eficientemente la glucosa."
    ),
)


PROTOCOL_BUCAL = ConditionProtocol(
    condition_id="bucal/periodontal",
    display_name="Enfermedad Periodontal / Bucal",
    dietary_goals=[
        "Adaptar textura si hay dolor dental severo",
        "Zinc y vitamina C para salud periodontal",
        "Omega-3 anti-inflamatorio gingival",
        "Evitar alimentos adherentes que favorezcan placa dental",
    ],
    proteina_pct_ms_min=22.0,
    proteina_pct_ms_max=35.0,
    grasa_pct_ms_max=25.0,
    fibra_pct_ms_min=2.0,
    fibra_pct_ms_max=10.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo cocida (textura suave si enfermedad severa)",
        "Pescado cocido (fácil masticación)",
        "Huevo cocido",
        "Zanahoria cruda (efecto raspado dental — si tolerado)",
        "Manzana sin semillas (crujiente natural — con tolerancia dental)",
        "Sardinas en agua (omega-3 anti-gingival)",
    ],
    ingredientes_a_evitar=[
        "Alimentos pegajosos o gomosos (miel, platano muy maduro)",
        "Azúcar — favorece placa bacteriana",
        "Galletitas muy azucaradas",
        "Alimentos que se adhieren a los dientes",
    ],
    numero_comidas_dia=2,
    reglas_especiales=[
        "GRADO 1-2 de enfermedad periodontal: textura normal o ligeramente suave",
        "GRADO 3-4: textura muy suave o licuada hasta resolución post-cirugía dental",
        "Post-cirugía oral: dieta BLANDA obligatoria por 7-14 días",
        "Dieta natural puede ayudar mecánicamente SI hay consistencia adecuada (no papilla)",
        "Cepillado dental complementario es MÁS IMPORTANTE que la dieta en enfermedad periodontal",
        "Zinc: 3-5 mg/kg/día — bacteriostático y promotor de cicatrización gingival",
        "Vitamina C: 250 mg/día — esencial para síntesis de colágeno periodontal",
    ],
    nota_perro=(
        "85% de perros >3 años tienen algún grado de enfermedad periodontal. "
        "La dieta sola no controla la enfermedad — el cepillado diario es fundamental. "
        "Razas braquicéfalas (Bulldog, Pug) tienen mayor riesgo por hacinamiento dental. "
        "Dieta natural con textura apropiada puede reducir cálculo dental."
    ),
    nota_gato=(
        "Gatos frecuentemente desarrollan resorción odontoclástica felina (FORL) — "
        "lesiones que no están relacionadas con placa y requieren extracción. "
        "Textura suave esencial si hay FORL o gingivoestomatitis crónica felina. "
        "Dieta húmeda reduce carga bacteriana y favorece hidratación."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Vitamina C",
            dosis_perro="250-500 mg/día",
            dosis_gato="125 mg/día",
            frecuencia="diario",
            forma="tabletas o polvo en alimento",
            justificacion_clinica="Síntesis de colágeno periodontal, cicatrización gingival",
            contraindicaciones=["Urolitiasis por oxalato (Vit C puede aumentar oxalato urinario)"],
        ),
    ],
    parametros_monitoreo=[
        "Grado de enfermedad periodontal (1-4) en examen veterinario cada 6 meses",
        "Halitosis (propietario registra cambios)",
        "Apetito y capacidad de masticación",
        "Signos de dolor: salivación excesiva, preferencia por un lado al masticar",
    ],
    justificacion=(
        "La enfermedad periodontal afecta al 85% de mascotas adultas. "
        "El manejo nutricional adapta la textura al grado de compromiso oral "
        "y aporta nutrientes que soportan la salud gingival. "
        "El cepillado dental supera en eficacia a cualquier intervención dietética."
    ),
)


PROTOCOL_PIEL = ConditionProtocol(
    condition_id="piel/dermatitis",
    display_name="Dermopatía / Dermatitis Atópica",
    dietary_goals=[
        "Omega-3 EPA+DHA para modulación inmune y anti-inflamatorio dérmico",
        "Zinc como cofactor enzimático cutáneo",
        "Proteína de alta calidad para regeneración cutánea",
        "Eliminar alérgenos alimentarios si hay componente alérgico",
        "Vitamina E como antioxidante dérmico",
    ],
    proteina_pct_ms_min=25.0,
    proteina_pct_ms_max=35.0,
    grasa_pct_ms_max=20.0,
    fibra_pct_ms_min=3.0,
    fibra_pct_ms_max=10.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Sardinas en agua (omega-3 más alto por g de proteína)",
        "Salmón cocido (EPA+DHA)",
        "Caballa cocida",
        "Pechuga de pollo cocida (si no hay alergia a pollo)",
        "Conejo cocido (NOVEL PROTEIN si alergia a proteínas comunes)",
        "Venado cocido (novel protein)",
        "Canguro (si disponible — novel protein extrema)",
        "Huevo entero cocido (biotina, zinc)",
        "Aceite de salmón (omega-3 concentrado)",
        "Aceite de cáñamo/hemp (omega-3 + omega-6 balanceado)",
        "Avena cocida (avenantramidas — anti-inflamatorio cutáneo)",
        "Zanahoria cocida (beta-caroteno)",
        "Brócoli cocido (antioxidantes)",
    ],
    ingredientes_a_evitar=[
        "Proteínas a las que hay alergia confirmada (individualizado por paciente)",
        "Trigo y gluten si hay hipersensibilidad",
        "Aditivos artificiales: colorantes, conservantes BHA/BHT",
        "Aceites de maíz y soya en exceso (omega-6 pro-inflamatorio)",
        "Alimentos con alto omega-6:omega-3 ratio (>10:1)",
    ],
    numero_comidas_dia=2,
    reglas_especiales=[
        "Si hay ALERGIA ALIMENTARIA SOSPECHADA: dieta de eliminación 8-12 semanas con proteína NOVEL",
        "Proteína novel LATAM: conejo, cordero, venado — verificar disponibilidad regional",
        "Durante dieta de eliminación: CERO otros alimentos, premios o suplementos saborizados",
        "Omega-3 a dosis terapéutica: 100-200 mg EPA+DHA/kg/día (el doble del estándar)",
        "Ratio omega-6:omega-3 objetivo: <5:1 (muchas dietas comerciales tienen >15:1)",
        "Zinc: 3-5 mg/kg/día — especialmente en Siberian Husky, Malamute (predisposición a dermatosis responsive al zinc)",
        "Biotina: 200-500 mcg/día — cofactor para síntesis de ácidos grasos cutáneos",
        "Reintroducción de alimentos tras dieta de eliminación: de uno en uno, 2 semanas cada uno",
        "Biopsia cutánea + perfil de alérgenos antes de concluir causa alimentaria",
    ],
    nota_perro=(
        "Dermatitis atópica canina: razas predispuestas — Bulldog, West Highland, Golden, Labrador, Boxer. "
        "Solo 15-30% de las dermatitis tienen causa alimentaria — las demás son ambientales. "
        "Dieta de eliminación diagnostica pero NO trata la atopia ambiental. "
        "Omega-3 a dosis terapéutica mejora significativamente la calidad de la piel."
    ),
    nota_gato=(
        "Complejo eosinofílico felino y alergia miliar: causas incluyen pulgas, atopia y alimentos. "
        "Proteínas más alergénicas en gatos: pescado, leche de vaca, carne de res. "
        "Dieta de hidrolizado de proteína es opción cuando no hay novel protein disponible. "
        "Taurina: mantener >250 mg/día incluso durante dieta de eliminación."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Omega-3 EPA+DHA (dosis terapéutica)",
            dosis_perro="100-200 mg EPA+DHA/kg/día",
            dosis_gato="100 mg EPA+DHA/kg/día",
            frecuencia="diario",
            forma="aceite de salmón o cápsulas",
            justificacion_clinica=(
                "Modula respuesta inmune Th2, reduce producción de leucotrienos pro-inflamatorios, "
                "mejora barrera cutánea"
            ),
            contraindicaciones=["Pancreatitis activa"],
        ),
        SupplementoRecomendado(
            nombre="Zinc quelado (bisglicinato de zinc)",
            dosis_perro="3-5 mg/kg/día elemental",
            dosis_gato="2-4 mg/kg/día elemental",
            frecuencia="diario con comida",
            forma="tabletas o polvo",
            justificacion_clinica=(
                "Cofactor en >200 enzimas de reparación cutánea. "
                "Deficiencia causa dermatosis hiperqueratótica"
            ),
            contraindicaciones=["Exceso (>10 mg/kg/día) causa toxicidad hemolítica"],
        ),
        SupplementoRecomendado(
            nombre="Biotina (Vitamina B7)",
            dosis_perro="200-500 mcg/día",
            dosis_gato="200 mcg/día",
            frecuencia="diario",
            forma="polvo o tabletas",
            justificacion_clinica="Cofactor de síntesis de ácidos grasos cutáneos y queratina",
            contraindicaciones=[],
        ),
    ],
    parametros_monitoreo=[
        "Puntuación CADESI-4 (Canine Atopic Dermatitis Extent and Severity Index) mensual",
        "Área afectada y tipo de lesión (eritema, excoriación, liquenificación)",
        "Prurito (escala PVAS 0-10, propietario)",
        "Calidad del pelo y de la piel",
        "IgE sérica si se realiza prueba de alergia",
    ],
    justificacion=(
        "La dermatitis tiene componente inflamatorio sistémico que responde a omega-3. "
        "Zinc y biotina son cofactores enzimáticos esenciales para la barrera cutánea. "
        "Si hay componente alérgico alimentario, la dieta de eliminación es el gold standard diagnóstico. "
        "La nutrición dermatológica es adyuvante — el tratamiento médico (apoquel, ciclosporina) "
        "sigue siendo el pilar del control en atopia severa."
    ),
)


PROTOCOL_GASTRITIS = ConditionProtocol(
    condition_id="gastritis",
    display_name="Gastritis / Enfermedad Inflamatoria Intestinal",
    dietary_goals=[
        "Alta digestibilidad para reducir carga gástrica",
        "Baja grasa en fase aguda",
        "Fibra moderada y soluble para restaurar microbiota intestinal",
        "Comidas pequeñas y frecuentes",
        "Eliminar alérgenos si hay componente inmune (EII)",
    ],
    proteina_pct_ms_min=20.0,
    proteina_pct_ms_max=30.0,
    grasa_pct_ms_max=15.0,
    fibra_pct_ms_min=3.0,
    fibra_pct_ms_max=10.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo hervida sin piel",
        "Pavo hervido",
        "Arroz blanco hervido (BIEN cocido, suave)",
        "Papa hervida sin piel",
        "Calabaza/ahuyama hervida",
        "Zanahoria hervida (fibra soluble — restaura microbiota)",
        "Linaza cocida (fibra soluble prebiótica)",
        "Avena cocida (fibra soluble — efecto gastroprotector)",
        "Caldo de pollo sin sal, sin cebolla, sin ajo",
    ],
    ingredientes_a_evitar=[
        "Alimentos altos en grasa (causa retraso del vaciamiento gástrico)",
        "Especias, condimentos, sal",
        "Cebolla y ajo (irritantes gástricos + tóxicos)",
        "Alimentos ácidos: tomate, naranja, limón",
        "Lácteos en animales con intolerancia a lactosa",
        "Alimentos ultra-procesados con conservantes",
        "Alimentos fríos directamente del refrigerador",
        "Agua con gas o carbonatada",
    ],
    numero_comidas_dia=4,
    reglas_especiales=[
        "GASTRITIS AGUDA: dieta en blanco 12-24h (solo agua) → reintroducir gradual bajo supervisión vet",
        "Comenzar con arroz + pollo sin piel en ratio 2:1 por primeras 48-72h",
        "GASTRITIS CRÓNICA: dieta controlada permanente, no solo en crisis",
        "EII (Enfermedad Inflamatoria Intestinal): considerar proteína hidrolizada o novel",
        "Probióticos: Lactobacillus + Bifidobacterium — restauran microbiota comprometida",
        "Prebióticos (FOS, inulina): 1g/10kg/día — alimentan microbiota beneficiosa",
        "Temperatura del alimento: tibio o a temperatura ambiente, NUNCA frío del fridge",
        "Agua disponible siempre — gastritis causa deshidratación",
        "Glutamina: 500mg/10kg/día — combustible principal de enterocitos para reparación",
    ],
    nota_perro=(
        "Gastritis crónica vs EII (Enfermedad Inflamatoria Intestinal) requiere diferenciación por biopsia. "
        "Gastroenteritis hemorrágica aguda: emergencia — IV fluidos primero, dieta segundo. "
        "Helicobacter pylori: tratamiento antibiótico es el pilar, la dieta es adyuvante."
    ),
    nota_gato=(
        "Triaditis felina: pancreatitis + colangitis + EII simultáneamente — frecuente. "
        "EII felina: linfocítica-plasmocítica más común. Proteína hidrolizada o novel. "
        "Gatos con gastritis frecuentemente rechazas el alimento bruscamente — "
        "ofrecer pequeñas cantidades de alta palatabilidad y temperatura correcta."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Probióticos (Lactobacillus + Bifidobacterium)",
            dosis_perro="1-5 × 10^9 UFC/día",
            dosis_gato="1 × 10^9 UFC/día",
            frecuencia="diario",
            forma="polvo mezclado en alimento o cápsulas",
            justificacion_clinica=(
                "Restauran microbiota intestinal, compiten con patógenos, "
                "mejoran barrera mucosa intestinal"
            ),
            contraindicaciones=["Inmunosupresión severa"],
        ),
        SupplementoRecomendado(
            nombre="L-glutamina",
            dosis_perro="500 mg/10kg/día",
            dosis_gato="250 mg/día",
            frecuencia="diario",
            forma="polvo mezclado en alimento",
            justificacion_clinica=(
                "Principal combustible de enterocitos (células intestinales). "
                "Acelera regeneración de la mucosa gastrointestinal"
            ),
            contraindicaciones=["Insuficiencia hepática severa con encefalopatía"],
        ),
    ],
    parametros_monitoreo=[
        "Frecuencia y características del vómito (propietario — diario en fase aguda)",
        "Consistencia y frecuencia de defecación (escala Purina fecal)",
        "Peso mensual",
        "Proteínas séricas (albumina/globulina) si EII severa",
        "Cobalamina (B12) — malabsorción es común en EII",
        "Endoscopia con biopsia si no hay respuesta a 4-6 semanas de dieta controlada",
    ],
    justificacion=(
        "La gastritis e EII requieren reducir el trabajo gástrico-intestinal "
        "con alimentos de alta digestibilidad y baja carga fermentativa. "
        "Las comidas frecuentes evitan el vaciamiento gástrico ácido prolongado. "
        "Probióticos y prebióticos restauran la microbiota dañada por la inflamación. "
        "La eliminación de irritantes (grasa, especias, alérgenos) reduce la inflamación crónica."
    ),
)


PROTOCOL_CISTITIS = ConditionProtocol(
    condition_id="cistitis/enfermedad_urinaria",
    display_name="Cistitis / Enfermedad Urinaria",
    dietary_goals=[
        "ALTA HUMEDAD para diluir orina y reducir cristalización",
        "pH urinario óptimo según tipo de cálculo",
        "Restricción de minerales litogénicos según tipo",
        "Reducir concentración urinaria general",
    ],
    proteina_pct_ms_min=22.0,
    proteina_pct_ms_max=35.0,
    grasa_pct_ms_max=20.0,
    fibra_pct_ms_min=3.0,
    fibra_pct_ms_max=10.0,
    fosforo_restringido=True,
    fosforo_g_por_100kcal_max=0.6,   # Moderar fósforo para struvite
    sodio_mg_dia_max=400,            # Moderado — exceso aumenta calcio urinario
    magnesio_restringido=True,       # CRÍTICO para urolitiasis por struvite
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo cocida (bajo Mg)",
        "Pechuga de pavo cocida (bajo Mg)",
        "Huevo entero cocido",
        "Atún en agua sin sal",
        "Arroz blanco cocido",
        "Pasta cocida sin sal",
        "Zanahoria cocida",
        "Calabacín/zucchini cocido",
        "Agua adicional mezclada en el alimento (aumentar humedad)",
    ],
    ingredientes_a_evitar=[
        "Sal y alimentos salados (aumentan excreción de calcio urinario)",
        "Espinaca, acelga, remolacha (alto en oxalato — para urolitiasis oxalato)",
        "Riñón e hígado (alto en purinas — para urolitiasis urato)",
        "Anchoas y sardinas en exceso (alto en purinas)",
        "Queso y leche en exceso (alto en calcio)",
        "Hueso crudo (alto en calcio y fósforo)",
        "Alimentos secos/croquetas como fuente principal (muy bajo en humedad — gatos)",
    ],
    numero_comidas_dia=3,
    reglas_especiales=[
        "TIPO DE CÁLCULO DETERMINA LA DIETA — consultar con vet antes de diseñar plan",
        "STRUVITE (MgNH4PO4): dieta acidificante, bajo Mg (<0.04% MS), bajo P, bajo NH4",
        "OXALATO DE CALCIO: dieta alcalinizante, bajo Ca, EVITAR oxalatos (espinaca, remolacha)",
        "URATO: dieta alcalinizante, muy bajo en purinas, vegetariana preferiblemente en dálmatas",
        "CISTINA: dieta alcalinizante, bajo en metionina y cisteína (proteína moderada)",
        "GATOS: dieta HÚMEDA/NATURAL es obligatoria — gatos con dieta seca tienen riesgo 4x mayor",
        "META DE HUMEDAD: >70% del contenido total del plan (equivale a dieta húmeda)",
        "Añadir agua a la comida: 50-100ml/kg de peso/día adicional más allá de la comida",
        "Objetivo de densidad urinaria (USG): <1.030 perros, <1.035 gatos",
        "Fuentes múltiples de agua (fontanas de agua en gatos mejoran consumo 50%)",
        "Cistitis idiopática felina (FIC): manejo ambiental + dieta húmeda son el tratamiento",
    ],
    nota_perro=(
        "Urolitiasis es más frecuente en perros: Struvite en hembras, Oxalato en Schnauzer/Bichón. "
        "Dálmata: metabolismo de purinas alterado genéticamente → dieta baja en purinas. "
        "Cistitis bacteriana: antibiótico es el tratamiento, dieta es adyuvante."
    ),
    nota_gato=(
        "FLUTD (Feline Lower Urinary Tract Disease) — 60% son cistitis idiopática felina (estrés). "
        "OBSTRUCCIÓN URETRAL en gatos machos: emergencia veterinaria, no nutricional. "
        "Post-obstrucción: dieta húmeda permanente + manejo de estrés + fontana de agua. "
        "Struvite en gatos: generalmente por infección, tratar infección + dieta acidificante."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="D-manosa (para cistitis bacteriana)",
            dosis_perro="500 mg/25kg/día",
            dosis_gato="N/A — evidencia limitada en gatos",
            frecuencia="diario durante infección activa",
            forma="polvo mezclado en agua o alimento",
            justificacion_clinica=(
                "Inhibe adherencia de E. coli al uroepitelio — "
                "coadyuvante a antibióticos en cistitis bacteriana"
            ),
            contraindicaciones=[],
        ),
    ],
    parametros_monitoreo=[
        "Urianálisis con sedimento urinario cada 30-90 días",
        "Densidad urinaria (USG — meta: <1.030 perros, <1.035 gatos)",
        "pH urinario (struvite meta: 6.0-6.5; oxalato meta: 6.5-7.5)",
        "Radiografías o ecografía abdominal para seguimiento de cálculos",
        "Signos de disuria, hematuria, polaquiuria (propietario diario en fase activa)",
        "Cultivo urinario si hay infección confirmada — seguimiento a 7 días post-antibiótico",
    ],
    justificacion=(
        "La enfermedad urinaria inferior requiere fundamentalmente dilución de orina. "
        "Una dieta húmeda en gatos reduce el riesgo de urolitiasis en 3-4x comparada con dieta seca. "
        "El manejo de minerales (Mg, Ca, P, purinas) depende del tipo de cristal/cálculo — "
        "no existe una sola 'dieta urinaria' universal. "
        "El tipo de cálculo debe confirmarse por análisis de laboratorio antes de prescribir la dieta."
    ),
)


PROTOCOL_SOBREPESO = ConditionProtocol(
    condition_id="sobrepeso/obesidad",
    display_name="Sobrepeso / Obesidad",
    dietary_goals=[
        "Restricción calórica calculada sobre PESO IDEAL (no peso actual)",
        "Alta proteína para preservar masa muscular durante pérdida de peso",
        "Alta fibra para saciedad y efecto prebiótico",
        "Monitoreo riguroso — meta: 1-2% de pérdida de peso semanal",
    ],
    proteina_pct_ms_min=30.0,
    proteina_pct_ms_max=40.0,
    grasa_pct_ms_max=15.0,
    fibra_pct_ms_min=8.0,
    fibra_pct_ms_max=18.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo hervida sin piel (bajísimo en grasa)",
        "Pechuga de pavo hervida (bajísimo en grasa)",
        "Merluza o tilapia cocida (muy bajo en grasa)",
        "Clara de huevo cocida",
        "Zanahoria cruda (alta fibra, baja caloría)",
        "Brócoli cocido (baja densidad calórica, alta fibra)",
        "Calabacín/zucchini cocido (prácticamente 0 calorías)",
        "Vainitas/ejotes hervidas",
        "Pepino crudo (90% agua, 0 calorías)",
        "Lechuga romana (relleno de volumen sin calorías)",
        "Psyllium (fibra soluble — saciedad)",
        "Avena integral cocida (fibra soluble)",
    ],
    ingredientes_a_evitar=[
        "Ningún ingrediente frito",
        "Aceites en más de 5ml/día",
        "Alimentos ultra-procesados",
        "Snacks, galletitas, premios altos en calorías",
        "Arroz blanco, pasta blanca en exceso (densidad calórica)",
        "Frutas altas en azúcar (mango, banano, uvas, cerezas)",
    ],
    numero_comidas_dia=3,
    reglas_especiales=[
        "CALCULAR SIEMPRE sobre PESO IDEAL estimado, no sobre peso actual",
        "PESO IDEAL: calculado con BCS-score: 5/9 es el objetivo para la mayoría",
        "DER PARA PÉRDIDA: RER(peso ideal) × factor × 0.8 — nunca menos de 1.0 × RER",
        "VELOCIDAD DE PÉRDIDA: 1-2% del peso corporal por semana — más rápido causa catabolismo muscular",
        "NO reducir por debajo de 1.0 × RER — riesgo de déficit nutricional grave",
        "Distribuir calorías en 3-4 comidas pequeñas para maximizar saciedad",
        "Verduras de baja densidad calórica como 'relleno de volumen': zanahoria, zucchini, brócoli",
        "EJERCICIO: incrementar actividad física gradualmente — 10 min/día más cada semana",
        "GATOS: NO restringir calorías >30% del mantenimiento — lipidosis hepática en gatos obesos",
        "Meta de pérdida en gatos: 0.5-1% semanal máximo",
        "L-carnitina: mejora movilización de grasa preservando músculo",
        "Pesar a la mascota CADA 2 SEMANAS — ajustar plan si no hay progreso",
        "Si no hay pérdida en 4 semanas: revisar errores de medición y posibles fuentes ocultas de calorías",
    ],
    nota_perro=(
        "55% de los perros en LATAM tienen sobrepeso u obesidad. "
        "Labrador, Beagle, Cocker, Basset son razas más predispuestas. "
        "El peso ideal en perros: BCS 5/9 para razas 'normales'. "
        "Una pérdida del 5-10% del peso mejora marcadores de salud articular, glucemia y presión arterial."
    ),
    nota_gato=(
        "60% de los gatos adultos en hogares son obesos o con sobrepeso. "
        "Gatos castrados tienen riesgo 3x mayor de obesidad. "
        "NUNCA ayunar a un gato obeso bruscamente — riesgo alto de lipidosis hepática. "
        "Transición gradual a dieta alta proteína/baja carbohidrato puede lograr pérdida sin restricción calórica severa."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="L-carnitina",
            dosis_perro="50-100 mg/kg/día (máx 2g/día)",
            dosis_gato="250-500 mg/día",
            frecuencia="diario",
            forma="polvo o líquido mezclado en alimento",
            justificacion_clinica=(
                "Transporta ácidos grasos a la mitocondria para oxidación. "
                "Preserva masa muscular durante restricción calórica. "
                "Mejora composición corporal (↓ grasa, ↑ músculo)"
            ),
            contraindicaciones=["Insuficiencia renal severa"],
        ),
    ],
    parametros_monitoreo=[
        "Peso corporal cada 2 semanas",
        "BCS (Escala 1-9) cada 30 días",
        "Evaluación de masa muscular (escala MCS)",
        "Registro de todo lo que come (propietario — diario)",
        "Meta: 1-2% pérdida/semana en perros, 0.5-1% en gatos",
        "Glucemia si hay diabetes concurrente",
    ],
    justificacion=(
        "La obesidad es la enfermedad nutricional más prevalente en mascotas — "
        "causa o agrava diabetes, osteoartritis, enfermedades respiratorias, dermatopatías y cáncer. "
        "La restricción calórica sobre peso ideal evita que el animal 'meta' su metabolismo basal. "
        "La alta proteína preserva la masa muscular que de otro modo se catabolizaría junto con la grasa. "
        "La alta fibra aumenta el volumen del bolo alimenticio sin aumentar calorías — efecto saciante."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# PROTOCOLOS — 4 CONDICIONES NUEVAS (A-04)
# ═══════════════════════════════════════════════════════════════════════════════

PROTOCOL_ICC = ConditionProtocol(
    condition_id="insuficiencia_cardiaca",
    display_name="Insuficiencia Cardíaca Congestiva (ICC)",
    dietary_goals=[
        "Restricción estricta de sodio (< 20 mg/100 kcal) para reducir retención de líquidos",
        "Suplementación terapéutica de taurina (100 mg/kg/día) y L-carnitina",
        "Omega-3 EPA+DHA en dosis alta antiinflamatoria cardíaca (40 mg/kg/día)",
        "Mantener masa muscular con proteína digestible moderada",
        "Prevenir caquexia cardíaca — densidad calórica adecuada en pocas porciones",
    ],
    proteina_pct_ms_min=22.0,
    proteina_pct_ms_max=30.0,
    grasa_pct_ms_max=15.0,
    fibra_pct_ms_min=3.0,
    fibra_pct_ms_max=8.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=50,       # < 20 mg/100 kcal → aprox 50 mg/día para mascota ~10kg
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo cocida sin piel",
        "Pechuga de pavo cocida",
        "Sardinas en agua sin sal",
        "Clara de huevo cocida",
        "Arroz blanco o integral cocido (sin sal)",
        "Batata/camote cocida",
        "Zanahoria cocida",
        "Calabaza/ahuyama cocida",
        "Aceite de salmón (omega-3)",
    ],
    ingredientes_a_evitar=[
        "Sal de mesa, salsa de soya, caldos salados",
        "Embutidos, jamón, tocino, queso",
        "Enlatados con sal (usar solo sin sal añadida)",
        "Snacks salados comerciales",
        "Alimentos procesados con sodio > 100 mg/100g",
    ],
    numero_comidas_dia=3,
    reglas_especiales=[
        "CRÍTICO: sodio máximo 20 mg/100 kcal — pesar y calcular cada ingrediente",
        "Taurina OBLIGATORIA 100 mg/kg/día — suplementar siempre",
        "Comidas pequeñas y frecuentes — evitar sobrecarga post-prandial",
        "Monitorear peso diario — aumento súbito indica retención de líquidos",
        "Sin ejercicio intenso post-comida",
        "Si hay edema: restricción adicional de líquidos según criterio veterinario",
    ],
    nota_perro=(
        "Razas predispuestas a DCM (Cocker Spaniel, Boxer, Doberman, Golden Retriever, "
        "Dálmata, Labrador): suplementar L-carnitina además de taurina. "
        "ACVIM 2019: no esperar deficiencia confirmada — suplementar preventivamente."
    ),
    nota_gato=(
        "Cardiomiopatía hipertrófica (HCM) en gatos: taurina 250 mg/kg/día obligatoria. "
        "Maine Coon y Ragdoll: predisposición genética — comenzar suplementación a los 2 años. "
        "Gatos: menor necesidad de restricción de sodio que perros con HCM."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Taurina",
            dosis_perro="100 mg/kg/día",
            dosis_gato="250 mg/kg/día",
            frecuencia="diario",
            forma="polvo mezclado en alimento o cápsula abierta",
            justificacion_clinica="Obligatoria en ICC — deficiencia documentada en DCM (NRC 2006, ACVIM 2019)",
        ),
        SupplementoRecomendado(
            nombre="L-Carnitina",
            dosis_perro="50 mg/kg/día",
            dosis_gato="50 mg/kg/día",
            frecuencia="diario",
            forma="polvo o cápsula",
            justificacion_clinica="Cardiomiopatía dilatada — deficiencia en Cocker Spaniel y Boxer (ACVIM 2019)",
        ),
        SupplementoRecomendado(
            nombre="Omega-3 EPA+DHA",
            dosis_perro="40 mg/kg/día",
            dosis_gato="25 mg/kg/día",
            frecuencia="diario",
            forma="aceite de salmón o cápsulas omega-3 marino",
            justificacion_clinica="Antiinflamatorio cardíaco en dosis alta — ACVIM 2019",
        ),
    ],
    parametros_monitoreo=[
        "Peso diario en casa (balanza)",
        "Circunferencia abdominal semanal (ascitis)",
        "Frecuencia cardíaca y respiratoria en reposo",
        "Ionograma (K+, Na+, Mg2+) cada 4-8 semanas",
        "Ecocardiograma cada 3-6 meses según evolución",
    ],
    justificacion=(
        "ICC requiere manejo nutricional multimodal: restricción de sodio para reducir precarga, "
        "suplementación de taurina/L-carnitina para soporte miocárdico, y omega-3 antiinflamatorio. "
        "El manejo dietético complementa — no reemplaza — el tratamiento farmacológico."
    ),
)


PROTOCOL_CUSHING = ConditionProtocol(
    condition_id="hiperadrenocorticismo_cushing",
    display_name="Hiperadrenocorticismo (Síndrome de Cushing)",
    dietary_goals=[
        "Control glucémico estricto — similar a diabético (resistencia a insulina frecuente)",
        "Control calórico estricto — polifagia del Cushing NO justifica aumentar ración",
        "Proteína magra de alta digestibilidad para preservar masa muscular",
        "Fibra soluble para control de peso y modulación glucémica",
        "Evaluar función renal — comorbilidad frecuente (restricción de fósforo si aplica)",
    ],
    proteina_pct_ms_min=25.0,
    proteina_pct_ms_max=35.0,
    grasa_pct_ms_max=12.0,
    fibra_pct_ms_min=8.0,
    fibra_pct_ms_max=18.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo cocida sin piel",
        "Pechuga de pavo cocida",
        "Clara de huevo cocida",
        "Avena integral cocida (IG bajo, fibra soluble)",
        "Batata/camote cocida (IG moderado)",
        "Brócoli cocido",
        "Zanahoria cocida",
        "Calabaza/ahuyama cocida",
        "Linaza molida (fibra soluble)",
    ],
    ingredientes_a_evitar=[
        "Azúcares simples, miel, glucosa",
        "Alimentos de alto IG (arroz blanco en exceso, pan, papa)",
        "Grasas saturadas en exceso",
        "Snacks hipercalóricos",
        "Alimentos ultraprocesados",
    ],
    numero_comidas_dia=3,
    reglas_especiales=[
        "POLIFAGIA: el Cushing causa hambre excesiva — NUNCA aumentar ración por esta razón",
        "Control de peso estricto — la obesidad empeora la resistencia a insulina",
        "Horarios fijos de alimentación como en diabético",
        "Si hay diabetes concurrente: aplicar restricciones de ambas condiciones",
        "Evaluar función renal antes y durante el tratamiento — ajustar fósforo si aplica",
        "Si recibe trilostano/mitotano: mantener horarios de comida fijos — riesgo crisis Addison",
    ],
    nota_perro=(
        "Cushing en perros: casi siempre hipófiso-dependiente (85%). "
        "Distribución abdominal de grasa característica. "
        "Alto riesgo de diabetes mellitus concurrente — monitoreo glucémico rutinario."
    ),
    nota_gato=(
        "Cushing felino es raro — frecuentemente asociado a diabetes mellitus resistente a insulina. "
        "Tratar diabetes primero; el manejo dietético es el del diabético felino."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Omega-3 EPA+DHA",
            dosis_perro="30 mg/kg/día",
            dosis_gato="20 mg/kg/día",
            frecuencia="diario",
            forma="aceite de salmón o cápsulas",
            justificacion_clinica="Antiinflamatorio sistémico — reduce inflamación por exceso de cortisol",
        ),
    ],
    parametros_monitoreo=[
        "Peso semanal",
        "Glucemia en ayunas si hay diabetes concurrente",
        "Ionograma (riesgo hiperpotasemia con trilostano)",
        "Cortisol (ACTH estimulación) según protocolo veterinario",
        "Función renal (BUN, creatinina) semestral",
    ],
    justificacion=(
        "El Cushing genera un estado metabólico complejo con resistencia a insulina, "
        "catabolismo muscular y redistribución grasa. El manejo nutricional replica "
        "el del diabético con énfasis adicional en control calórico — la polifagia "
        "es una trampa frecuente de sobrealimentación."
    ),
)


PROTOCOL_EPILEPSIA = ConditionProtocol(
    condition_id="epilepsia",
    display_name="Epilepsia",
    dietary_goals=[
        "Eliminar posibles desencadenantes dietéticos (glutamato, colorantes artificiales)",
        "DHA neuroprotector en dosis terapéutica (25 mg/kg/día)",
        "Regularidad horaria estricta — la irregularidad puede precipitar crisis",
        "Evitar hipoglucemia — no ayunos > 8 horas",
        "Si indicado por veterinario: dieta cetogénica (alta grasa, mínimos carbohidratos)",
    ],
    proteina_pct_ms_min=25.0,
    proteina_pct_ms_max=35.0,
    grasa_pct_ms_max=20.0,
    fibra_pct_ms_min=3.0,
    fibra_pct_ms_max=10.0,
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Pechuga de pollo cocida sin piel (sin aditivos)",
        "Salmón cocido (omega-3 DHA elevado)",
        "Huevo entero cocido",
        "Arroz blanco cocido (sin sal, sin condimentos)",
        "Batata/camote cocida",
        "Brócoli cocido",
        "Espinaca cocida (magnesio)",
        "Semillas de calabaza (magnesio — molidas)",
    ],
    ingredientes_a_evitar=[
        "Glutamato monosódico (MSG) — potencial desencadenante",
        "Colorantes artificiales (tartrazina, rojo 40, amarillo 5)",
        "Conservantes artificiales (BHA, BHT, etoxiquina)",
        "Azúcares refinados — pueden causar hipoglucemia reactiva",
        "Alimentos ultraprocesados con aditivos",
        "Alcohol etílico — obvio pero importante en preparaciones caseras",
    ],
    numero_comidas_dia=3,
    reglas_especiales=[
        "HORARIO FIJO OBLIGATORIO — irregularidad puede precipitar crisis epiléptica",
        "NUNCA ayuno > 8 horas — hipoglucemia es desencadenante de crisis",
        "Sin glutamato agregado en NINGÚN ingrediente del plan",
        "Solo ingredientes naturales sin aditivos artificiales",
        "Si bromuro de potasio: mantener nivel de sal CONSTANTE (variación precipita crisis)",
        "Dieta cetogénica SOLO si indicada explícitamente por veterinario neurólogo",
    ],
    nota_perro=(
        "Epilepsia idiopática en perros: frecuente en Border Collie, Labrador, Golden, Beagle. "
        "El manejo dietético es adyuvante — no reemplaza anticonvulsivantes. "
        "Fenobarbital induce catabolismo de vitaminas B y D — suplementar."
    ),
    nota_gato=(
        "Epilepsia en gatos: menos frecuente que en perros, frecuentemente sintomática. "
        "Descartar toxicidad (lilium, permetrina) antes de diagnóstico de epilepsia idiopática. "
        "Dieta natural sin aditivos es especialmente relevante para gatos."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Omega-3 DHA",
            dosis_perro="25 mg/kg/día",
            dosis_gato="15 mg/kg/día",
            frecuencia="diario",
            forma="aceite de salmón (alto DHA) o aceite de krill",
            justificacion_clinica="DHA neuroprotector — J Vet Intern Med 2012: reduce frecuencia de crisis",
        ),
        SupplementoRecomendado(
            nombre="Magnesio (glicinato)",
            dosis_perro="1.5 mg/kg/día",
            dosis_gato="1.0 mg/kg/día",
            frecuencia="diario",
            forma="glicinato de magnesio o citrato (NOT óxido)",
            justificacion_clinica="Cofactor neurológico — modulador NMDA, déficit documentado en epilépticos",
            contraindicaciones=["Insuficiencia renal"],
        ),
    ],
    parametros_monitoreo=[
        "Registro de crisis (fecha, duración, tipo) — diario idealmente",
        "Nivel sérico de anticonvulsivante cada 6 meses",
        "Función hepática (fenobarbital es hepatotóxico a largo plazo) cada 6 meses",
        "Vitamina D sérica si recibe fenobarbital > 6 meses",
    ],
    justificacion=(
        "El manejo nutricional en epilepsia busca eliminar desencadenantes dietéticos, "
        "proveer soporte neuroprotector (DHA, magnesio) y garantizar regularidad glucémica. "
        "La regularidad horaria es tan importante como la composición del plan."
    ),
)


PROTOCOL_MEGAESOFAGO = ConditionProtocol(
    condition_id="megaesofago",
    display_name="Megaesófago",
    dietary_goals=[
        "Textura adaptada para facilitar deglución y tránsito esofágico",
        "Prevenir regurgitación y neumonía aspirativa (emergencia P0)",
        "Posición vertical OBLIGATORIA durante y post-comida (Bailey chair)",
        "Porciones pequeñas y frecuentes — nunca volúmenes grandes",
        "Mantener estado nutricional adecuado pese a pérdidas por regurgitación",
    ],
    proteina_pct_ms_min=25.0,
    proteina_pct_ms_max=35.0,
    grasa_pct_ms_max=20.0,
    fibra_pct_ms_min=1.0,
    fibra_pct_ms_max=5.0,      # Fibra baja — facilita tránsito
    fosforo_restringido=False,
    fosforo_g_por_100kcal_max=None,
    sodio_mg_dia_max=None,
    magnesio_restringido=False,
    cobre_restringido=False,
    ingredientes_preferidos=[
        "Caldo de cocción suave (sin sal) como base líquida",
        "Pechuga de pollo muy bien cocida y desmenuzada en papilla",
        "Huevo pochado o revuelto blando",
        "Arroz blanco muy cocido (consistencia papilla)",
        "Batata/camote cocida en puré",
        "Calabaza/ahuyama cocida en puré",
        "Zanahoria cocida en puré",
    ],
    ingredientes_a_evitar=[
        "Croquetas secas sin remojar",
        "Alimentos sólidos de tamaño grande",
        "Huesos o cartílagos",
        "Alimentos fibrosos duros (zanahoria cruda, apio crudo)",
        "Alimentos fríos directamente del refrigerador",
        "Trozos grandes de carne sin desmenuzar",
    ],
    numero_comidas_dia=4,      # Mínimo 4 comidas al día
    reglas_especiales=[
        "⚠️ POSICIÓN VERTICAL OBLIGATORIA (Bailey chair o similar) durante TODA la comida",
        "⚠️ Mantener vertical 30 MINUTOS post-comida — previene neumonía aspirativa",
        "⚠️ ALERTA NEUMONÍA ASPIRATIVA — cualquier signo respiratorio → urgencias",
        "Porciones muy pequeñas (50-100g máximo por comida en perros medianos)",
        "Consistencia: papilla o semilíquido — NUNCA sólidos sin licuar",
        "Temperatura: a temperatura ambiente o tibia — nunca fría ni muy caliente",
        "Supervisión directa en CADA comida — no dejar comer solo",
        "Si el paciente regurgita > 3 veces/día → revisión veterinaria urgente",
    ],
    nota_perro=(
        "Megaesófago en perros: frecuente en Setter Irlandés, Gran Danés, Labrador, "
        "Schnauzer Gigante. Puede ser congénito (cachorros) o adquirido (adultos — "
        "frecuentemente asociado a miastenia gravis, hipotiroidismo, Addison). "
        "Tratar la causa subyacente es fundamental para mejorar el manejo."
    ),
    nota_gato=(
        "Megaesófago en gatos es poco frecuente — descartar cuerpo extraño, "
        "estrechez esofágica o neoplasia. El manejo dietético es igual al canino."
    ),
    suplementos=[
        SupplementoRecomendado(
            nombre="Vitamina B12 (cianocobalamina)",
            dosis_perro="250-500 mcg/semana (subcutáneo) o 1000 mcg/día oral",
            dosis_gato="250 mcg/semana",
            frecuencia="semanal (SC) o diario (oral)",
            forma="Inyectable SC preferido — mejor absorción. Oral si no es posible",
            justificacion_clinica=(
                "Absorción intestinal frecuentemente comprometida en megaesófago "
                "con dismotilidad — suplementar vía parenteral es más confiable."
            ),
        ),
    ],
    parametros_monitoreo=[
        "Frecuencia de regurgitación (registro diario)",
        "Peso semanal — pérdida indica nutrición insuficiente",
        "Temperatura y frecuencia respiratoria (alerta neumonía aspirativa)",
        "Radiografía torácica mensual si hay sospecha de aspiración",
        "Causa subyacente: AChR-Ab para miastenia gravis, T4 para hipotiroidismo",
    ],
    justificacion=(
        "El megaesófago requiere el mayor nivel de adaptación de manejo alimentario. "
        "La neumonía aspirativa es la complicación más grave y frecuente causa de muerte. "
        "La posición vertical y las porciones pequeñas son tan críticas como la composición del plan."
    ),
)


# ═══════════════════════════════════════════════════════════════════════════════
# ÍNDICE — diccionario por condition_id para lookup rápido
# ═══════════════════════════════════════════════════════════════════════════════

ALL_PROTOCOLS: dict[str, ConditionProtocol] = {
    p.condition_id: p
    for p in [
        PROTOCOL_DIABETICO,
        PROTOCOL_HIPOTIROIDEO,
        PROTOCOL_CANCERIGENO,
        PROTOCOL_ARTICULAR,
        PROTOCOL_RENAL,
        PROTOCOL_HEPATICO,
        PROTOCOL_PANCREATICO,
        PROTOCOL_NEURODEGENERATIVO,
        PROTOCOL_BUCAL,
        PROTOCOL_PIEL,
        PROTOCOL_GASTRITIS,
        PROTOCOL_CISTITIS,
        PROTOCOL_SOBREPESO,
        # ── 4 condiciones nuevas (A-04) ───────────────────────────────────
        PROTOCOL_ICC,
        PROTOCOL_CUSHING,
        PROTOCOL_EPILEPSIA,
        PROTOCOL_MEGAESOFAGO,
    ]
}


def get_protocols_for_conditions(conditions: list[str]) -> list[ConditionProtocol]:
    """
    Retorna los protocolos para una lista de condiciones.

    Args:
        conditions: Lista de condition_ids (e.g. ['diabético', 'renal'])

    Returns:
        Lista de ConditionProtocol correspondientes (ignorando condiciones no encontradas).
    """
    protocols = []
    for cond in conditions:
        protocol = ALL_PROTOCOLS.get(cond)
        if protocol:
            protocols.append(protocol)
    return protocols


def get_most_restrictive_fat_pct(protocols: list[ConditionProtocol]) -> float:
    """Retorna el límite de grasa más restrictivo entre todos los protocolos activos."""
    if not protocols:
        return 30.0  # Máximo estándar NRC
    return min(p.grasa_pct_ms_max for p in protocols)


def get_most_restrictive_protein_range(
    protocols: list[ConditionProtocol],
) -> tuple[float, float]:
    """
    Resuelve el rango de proteína cuando hay múltiples condiciones.

    Regla: el mínimo más alto gana (garantiza el requisito más estricto),
    el máximo más bajo gana (no sobrepasa el límite más restrictivo).
    """
    if not protocols:
        return (18.0, 35.0)  # Rango estándar NRC adulto
    min_protein = max(p.proteina_pct_ms_min for p in protocols)
    max_protein = min(p.proteina_pct_ms_max for p in protocols)
    # Si el resultado es un rango inválido (conflicto extremo), usar punto medio
    if min_protein > max_protein:
        midpoint = (min_protein + max_protein) / 2
        return (midpoint - 2, midpoint + 2)
    return (min_protein, max_protein)
