# Plan de Mejoras Clínicas — NutriVet.IA v2.1
**Fecha**: 2026-03-22
**Autor**: Análisis clínico multi-rol (MV + Nutricionista + Propietario)
**Validación requerida**: Lady Carolina Castañeda (MV, BAMPYSVET) antes de implementar Fases A y B
**Estado**: BORRADOR — pendiente revisión

---

## Contexto

Este plan aborda todas las brechas identificadas en la revisión clínica del sistema actual.
Se organiza en 4 fases según criticidad. Ninguna fase de producción se lanza sin que Lady Carolina
valide los cambios en domain layer (Regla 3 de la Constitución).

**Lo que NO se aborda en este plan (decisiones tomadas):**
- Verificación formal de credenciales MV → reemplazada por cláusula legal (Fase D)
- Estimación de costo de la dieta → fuera de scope permanente (variable por país/zona)

---

## Resumen de Impacto

| Fase | Descripción | Unidades | Criticidad |
|------|-------------|----------|------------|
| **A** | Fundación del Dominio — micronutrientes, razas, estado reproductivo especial | 9 units | CRÍTICO |
| **B** | Expansión Clínica — nuevas condiciones, lógica de razas, protocolo BARF | 7 units | IMPORTANTE |
| **C** | Acompañamiento al Propietario — seguimiento, meal prep, notificaciones | 6 units | NICE TO HAVE |
| **D** | Legal y Compliance — cláusula vet, actualización ToS | 1 unit | CRÍTICO (legal) |

---

## FASE A — Fundación del Dominio

> Cambios en `domain/`. Todos requieren validación Lady Carolina antes de PR.
> Ningún LLM involucrado — lógica determinista.

---

### A-01: Base de Datos de Razas Completa

**¿Qué es?**
Crear una tabla/BD de razas de perros y gatos, con búsqueda y selección en el wizard.
Reemplaza el campo "Raza: Text libre" actual. Incluye campo "Criollo/Mestizo" como opción explícita.

**¿Por qué importa?**
- Sin raza definida, no se puede aplicar predisposiciones genéticas (Fase B)
- Permite cálculos de talla esperada para razas gigantes (cronología adulto)
- Mejora UX: el propietario no sabe cómo escribir "Labrador Retriever" correctamente

**Estructura de datos:**

```python
# backend/domain/breeds/breed_catalog.py

@dataclass(frozen=True)
class BreedInfo:
    id: str                              # "labrador_retriever"
    nombre: str                          # "Labrador Retriever"
    nombre_alternativo: list[str]        # ["Labrador", "Lab"]
    especie: Species                     # Species.DOG | Species.CAT
    grupo_fci: Optional[int]            # Grupo FCI 1-10 (perros) | None (gatos)
    talla_tipica: Optional[Size]        # Size.LARGE para Labrador
    peso_adulto_min_kg: float           # 25.0
    peso_adulto_max_kg: float           # 36.0
    longevidad_anios_min: int           # 10
    longevidad_anios_max: int           # 14
    meses_adulto: int                   # 12 para razas pequeñas, 24 para gigantes
    predisposiciones: frozenset[str]    # {"obesidad", "displasia_cadera", "retinopatia"}
    notas_nutricionales: str            # "Alta tendencia a obesidad — control calórico estricto"
    es_criollo: bool = False            # True solo para Criollo/Mestizo
```

**Razas de perros a incluir (LATAM-relevant, ~120 razas + Criollo):**

```
Grupo 1 — Pastores y Boyeros:
  Pastor Alemán, Border Collie, Pastor Australiano (Australian Shepherd),
  Collie (Rough/Smooth), Shetland Sheepdog (Shelti), Belgian Malinois,
  Bernés de la Montaña, Boyero de Berna

Grupo 2 — Pinscher, Schnauzer, Molosoides:
  Rottweiler, Doberman, Schnauzer (Miniatura/Estándar/Gigante),
  Boxer, Gran Danés, Mastín Napolitano, Mastín Español, Bullmastiff,
  Dogo Argentino, Fila Brasileño, Shar Pei

Grupo 3 — Terriers:
  Bull Terrier, Yorkshire Terrier, West Highland White Terrier,
  Jack Russell Terrier, Bedlington Terrier, Airedale Terrier,
  Scottish Terrier, Fox Terrier

Grupo 4 — Teckels:
  Dachshund (Estándar/Miniatura)

Grupo 5 — Spitz y tipo primitivo:
  Husky Siberiano, Alaskan Malamute, Samoyedo, Akita Inu, Chow Chow,
  Spitz Alemán (Pomerania), Shiba Inu, Basenji

Grupo 6 — Sabuesos:
  Beagle, Basset Hound, Bloodhound, Dálmata, Podenco

Grupo 7 y 8 — Perros de Muestra y Cobro:
  Golden Retriever, Labrador Retriever, Cocker Spaniel (Inglés/Americano),
  Springer Spaniel, Pointer, Setter Irlandés, Setter Inglés,
  Weimaraner, Vizsla

Grupo 9 — Compañía:
  Poodle/Caniche (Toy/Miniatura/Estándar/Grande), Bulldog Francés,
  Bulldog Inglés, Pug (Carlino), Shih Tzu, Maltés (Maltese),
  Bichón Frisé, Bichón Habanero, Chihuahua, Pekinés, Lhasa Apso,
  Cavalier King Charles Spaniel, Papillón, Pomerania

Grupo 10 — Lebreles:
  Galgo Español, Greyhound, Whippet

CRIOLLO/MESTIZO:
  Criollo (Mestizo de razas desconocidas) — talla mini/pequeño/mediano/grande/gigante
  Mestizo identificado — campo libre opcional para describir cruces conocidos
```

**Razas de gatos a incluir (~40 razas + Criollo):**

```
Doméstico Pelo Corto (DPC) — el más común en LATAM
Doméstico Pelo Largo (DPL)
Siamés, Thai
Persa (y variantes: Himalayo, Exótico Pelo Corto)
Maine Coon
Ragdoll
British Shorthair
Scottish Fold / Scottish Straight
Bengal
Sphynx (sin pelo)
Abisinio
Birmano Sagrado
Russian Blue
Noruego del Bosque
Angora Turco
Devon Rex, Cornish Rex
Bombay
Tonkinés
Ocicat
Somali
Balinés
Manx (sin cola)
Selkirk Rex
Chartreux
LaPerm
American Shorthair
American Curl
Ragamuffin
Savannah (F3+)
Burmés / Burmilla
Singapura
Munchkin
Turkish Van

CRIOLLO/MESTIZO:
  Criollo (Mestizo de razas desconocidas)
```

**Predisposiciones por raza (ejemplos — requiere validación Lady Carolina):**

```python
BREED_PREDISPOSITIONS = {
    "labrador_retriever": {
        "predisposiciones": {"obesidad", "displasia_cadera", "displasia_codo",
                             "retinopatia_progresiva", "miopatia"},
        "notas": "Alta tendencia a obesidad — control calórico desde cachorro. Displasia de cadera frecuente → mantener BCS 4-5 siempre",
        "meses_adulto": 12,
    },
    "golden_retriever": {
        "predisposiciones": {"obesidad", "displasia_cadera", "cancer",
                             "hipotiroidismo", "displasia_codo"},
        "notas": "60% riesgo de cáncer en vida — dieta antiinflamatoria, omega-3 elevado recomendado desde adulto",
        "meses_adulto": 12,
    },
    "dalmata": {
        "predisposiciones": {"hiperuricosuria", "cistitis_urica", "urolitiasis_urato"},
        "notas": "CRÍTICO: restricción estricta de purinas (sin hígado, sin anchoas, sin sardinas, sin riñón). Dieta alcalinizante. Hidratación máxima",
        "meses_adulto": 12,
    },
    "bedlington_terrier": {
        "predisposiciones": {"acumulacion_cobre_hepatica"},
        "notas": "CRÍTICO: restricción de cobre en dieta. Sin hígado de res, sin mariscos, sin nueces. Monitoreo hepático semestral",
        "meses_adulto": 12,
    },
    "west_highland_white_terrier": {
        "predisposiciones": {"acumulacion_cobre_hepatica", "dermatitis_atopica"},
        "notas": "Restricción de cobre. Dieta hipoalergénica si dermatitis activa",
        "meses_adulto": 12,
    },
    "gran_danes": {
        "predisposiciones": {"dilatacion_volvulo_gastrico", "displasia_cadera",
                             "cardiomiopatia_dilatada", "osteosarcoma"},
        "notas": "CRÍTICO: raza gigante — adulto a 18-24 meses (no 12). Sin ejercicio 2h post-comida (riesgo vólvulo). Mínimo 2 comidas/día. Sin elevación del comedero",
        "meses_adulto": 24,
    },
    "bernes_montania": {
        "predisposiciones": {"displasia_cadera", "displasia_codo", "cancer",
                             "meningitis_arteritica"},
        "notas": "Raza gigante — adulto a 24 meses. Alta incidencia cáncer (40%)",
        "meses_adulto": 24,
    },
    "bulldog_frances": {
        "predisposiciones": {"sensibilidad_digestiva", "alergia_alimentaria",
                             "urolitiasis_oxalato", "colapso_traqueal"},
        "notas": "Transición de dieta muy lenta (3-4 semanas). Alta sensibilidad digestiva. Evitar croquetas muy grandes (dificultad deglución)",
        "meses_adulto": 12,
    },
    "pug": {
        "predisposiciones": {"obesidad", "sensibilidad_digestiva", "encefalitis"},
        "notas": "Alta tendencia a obesidad. No sobrealimentar nunca. Control BCS estricto",
        "meses_adulto": 12,
    },
    "cocker_spaniel": {
        "predisposiciones": {"hepatopatia_cronica", "pancreatitis",
                             "hiperlipidemia", "otitis"},
        "notas": "Predisposición a hepatopatía y pancreatitis — misma restricción que condición hepático/hiperlipidemia como prevención",
        "meses_adulto": 12,
    },
    "schnauzer_miniatura": {
        "predisposiciones": {"hiperlipidemia", "pancreatitis", "urolitiasis_oxalato",
                             "diabetes"},
        "notas": "Predisposición fuerte a hiperlipidemia y pancreatitis — grasa restringida como prevención",
        "meses_adulto": 12,
    },
    "yorkshire_terrier": {
        "predisposiciones": {"hipoglucemia_cachorros", "colapso_traqueal",
                             "hepatopatia_shunt_portosistemico"},
        "notas": "Cachorros toy muy propensos a hipoglucemia — múltiples comidas pequeñas obligatorias",
        "meses_adulto": 10,
    },
    # GATOS
    "maine_coon": {
        "predisposiciones": {"cardiomiopatia_hipertrofica", "displasia_cadera"},
        "notas": "HCM frecuente — omega-3 y taurina elevados recomendados como prevención desde adulto joven",
        "meses_adulto": 18,  # madurez tardía
    },
    "ragdoll": {
        "predisposiciones": {"cardiomiopatia_hipertrofica", "enfermedad_renal_poliquistica"},
        "notas": "HCM y PKD — taurina obligatoria, restricción fósforo preventiva desde los 5 años",
        "meses_adulto": 18,
    },
    "persa": {
        "predisposiciones": {"enfermedad_renal_poliquistica", "urolitiasis_oxalato"},
        "notas": "PKD: restricción de fósforo preventiva desde adulto. Hidratación alta — preferir dieta húmeda",
        "meses_adulto": 12,
    },
    "siames": {
        "predisposiciones": {"amiloidosis_hepatica", "asma_felino", "cancer_mama"},
        "notas": "Tendencia a bajo peso en vejez. Proteína de alta digestibilidad",
        "meses_adulto": 12,
    },
    "bengal": {
        "predisposiciones": {"atrofia_retina_progresiva", "enfermedad_inflamatoria_intestinal"},
        "notas": "Sensibilidad digestiva — dieta digestible, evitar cambios bruscos",
        "meses_adulto": 12,
    },
    "sphynx": {
        "predisposiciones": {"cardiomiopatia_hipertrofica", "miopatia_hipertrofica"},
        "notas": "HCM frecuente. Mayor metabolismo basal (sin pelo) — requiere 10-15% más calorías",
        "meses_adulto": 12,
    },
    # Criollo
    "criollo_perro": {
        "predisposiciones": set(),
        "notas": "Mestizo — sin predisposiciones genéticas conocidas. Evaluación individual obligatoria",
        "meses_adulto": 12,
    },
    "criollo_gato": {
        "predisposiciones": set(),
        "notas": "Mestizo — sin predisposiciones genéticas conocidas",
        "meses_adulto": 12,
    },
}
```

**Cambios en el wizard (Flutter):**
- Paso 1 actual "Raza: campo texto" → reemplazar por `BreedSearchField` (búsqueda + dropdown)
- La talla se auto-completa si la raza la tiene, pero el owner puede ajustar
- Mostrar badge "Criollo" con icono especial (pata)

**Componentes afectados:**
- `domain/breeds/breed_catalog.py` — NUEVO
- `backend/domain/aggregates/pet_profile.py` — campo `raza` pasa de `str` a `BreedInfo` reference
- `backend/presentation/v1/pets/` — endpoint de búsqueda de razas `GET /v1/breeds?q=labrador&especie=perro`
- `mobile/lib/features/pet/` — widget de búsqueda de razas
- Migración Alembic — nuevo campo `breed_id` en `pets` table

**Dependencias:** ninguna
**Requiere validación Lady Carolina:** Sí — predisposiciones genéticas

---

### A-02: Micronutrientes Completos en food_database

**¿Qué es?**
Ampliar los campos de datos nutricionales en `AnimalProtein`, `PlantFood` y `Fat` para incluir
los micronutrientes actualmente ausentes.

**¿Por qué importa?**
Un plan puede "cuadrar" en macros y generar deficiencias reales de magnesio, potasio o vitaminas
porque los datos simplemente no están. Las matemáticas son correctas sobre datos incorrectos.

**Micronutrientes a agregar:**

| Nutriente | Tipo de alimento | Condición relevante | Por qué |
|---|---|---|---|
| `humedad_pct` | Todos | Cistitis gatos | % agua del alimento → kcal en base seca real |
| `magnesio_mg` | AnimalProtein, PlantFood | Cistitis felina | Hipermagnesuria en gatos |
| `potasio_mg` | AnimalProtein, PlantFood | Renal | Hipopotasemia en restricción proteíca |
| `cobre_mg` | AnimalProtein | Hepático, razas Dálmata/Bedlington | Acumulación genética |
| `vitamina_d3_ui` | AnimalProtein, Fat | Todas | Las mascotas no sintetizan por sol |
| `vitamina_a_ui` | AnimalProtein | Todas | Tóxica en sobresuplementación |
| `tiamina_b1_mg` | AnimalProtein (pescados) | Gatos — pescado crudo | Tiaminasa destruye B1 → convulsiones |
| `yodo_mcg` | Todos | Hipotiroidismo | Déficit en dietas caseras |
| `selenio_mcg` | AnimalProtein, PlantFood | Todos | Carencia regional, antioxidante |
| `coeficiente_biodisponibilidad` | Todos | Renal, hepático | Calcio hueso ≠ calcio tableta |

**Nuevo campo en AnimalProtein:**

```python
@dataclass(frozen=True)
class AnimalProtein:
    # Campos existentes ...
    humedad_pct: float = 75.0          # % agua (pollo crudo ≈ 75%)
    estado: str = "crudo"              # "crudo" | "cocido" — NUEVO
    magnesio_mg: float = 0.0
    potasio_mg: float = 0.0
    cobre_mg: float = 0.0
    vitamina_d3_ui: float = 0.0
    vitamina_a_ui: float = 0.0
    tiamina_b1_mg: float = 0.0         # CRÍTICO para pescados con gatos
    yodo_mcg: float = 0.0
    selenio_mcg: float = 0.0
    tiene_tiaminasa: bool = False       # sardina cruda, atún crudo, carpa cruda → True
    coef_biodisponibilidad_calcio: float = 1.0  # hueso molido: ~0.7 vs carbonato: ~0.4
```

**Regla crítica nueva (tiaminasa):**

```python
# domain/safety/food_safety_checker.py — agregar
TIAMINASA_FOODS = frozenset({
    "sardina_cruda", "atún_crudo", "carpa_cruda", "trucha_cruda",
    "pescado_crudo",  # término genérico
})

def check_tiaminasa_risk(
    ingredients: list[str],
    species: Species,
    diet_type: str,
) -> Optional[str]:
    """
    Solo aplica para gatos. Si hay pescado crudo → alerta obligatoria.
    La cocción destruye la tiaminasa.
    """
    if species != Species.CAT:
        return None
    if diet_type != "natural":  # BARF o dieta casera
        return None
    for ing in ingredients:
        if ing in TIAMINASA_FOODS:
            return (
                "ALERTA TIAMINASA: El pescado crudo contiene tiaminasa que destruye "
                "la vitamina B1 (tiamina) en gatos → riesgo de convulsiones y "
                "daño neurológico. Cocinar el pescado destruye la tiaminasa. "
                "Alternativa: sardinas en agua (enlatadas, cocidas)."
            )
    return None
```

**Componentes afectados:**
- `domain/nutrition/food_database.py` — ampliar dataclasses + actualizar ~60 entradas de alimentos
- `domain/safety/food_safety_checker.py` — agregar check_tiaminasa_risk
- Los tests de toxicidad deben incluir caso gato + sardina cruda

**Dependencias:** A-01 (ninguna real, pueden ir en paralelo)
**Requiere validación Lady Carolina:** Sí — valores nutricionales actualizados

---

### A-03: Gestación y Lactancia

**¿Qué es?**
Agregar dos nuevos estados reproductivos: `gestante` y `lactante`, con sus factores NRC correspondientes.

**¿Por qué importa?**
Son los estados metabólicos con mayor demanda calórica en la vida de una hembra.
Con los factores actuales, una perra gestante recibe una dieta insuficiente para ella
y para el desarrollo fetal — riesgo real de pérdida fetal o cachorros con bajo peso.

**Nuevos valores en ReproductiveStatus:**

```python
# domain/aggregates/pet_profile.py
class ReproductiveStatus(str, Enum):
    INTACT = "no_esterilizado"
    NEUTERED = "esterilizado"
    PREGNANT = "gestante"      # NUEVO
    LACTATING = "lactante"     # NUEVO
```

**Nuevos factores NRC:**

```python
# domain/nutrition/nrc_factors.py

# PERROS — Gestación
# NRC 2006: primera mitad gestación = factor adulto normal
# Segunda mitad (semanas 5-9) = +25-30% por semana progresivamente
# Simplificamos en dos fases:
FACTOR_VIDA_PERRO_GESTANTE = {
    # (actividad, semana_gestacion)
    # Si no se conoce la semana, usar promedio conservador
    "primera_mitad": 1.6,   # semanas 1-4
    "segunda_mitad": 3.0,   # semanas 5-9 (máximo)
    "promedio_seguro": 2.0, # si no se conoce la semana
}

# PERROS — Lactancia
# NRC 2006: DER = RER × (4.0 + 0.2 × número_cachorros)
# Implementar como función, no como factor simple
def calcular_factor_lactancia_perra(num_cachorros: int) -> float:
    """
    Fórmula NRC 2006 para lactancia.
    Mínimo: 1 cachorro = 4.2x RER
    Máximo: 8+ cachorros ≈ 5.6x RER
    """
    return 4.0 + (0.2 * min(num_cachorros, 8))

# GATOS — Gestación
FACTOR_VIDA_GATO_GESTANTE = {
    "primera_mitad": 1.6,
    "segunda_mitad": 2.0,  # gatos tienen menos variación que perros
    "promedio_seguro": 1.8,
}

# GATOS — Lactancia
def calcular_factor_lactancia_gata(num_gatitos: int) -> float:
    """
    NRC 2006 gatos: similar a perros pero con menor variación
    """
    return 2.0 + (0.3 * min(num_gatitos, 6))
```

**Nuevos campos en el wizard (Paso 3):**
- Si `estado_reproductivo = gestante` → mostrar campo opcional "Semana de gestación (1-9)"
- Si `estado_reproductivo = gestante` → mostrar campo "Número de cachorros esperados (estimado)"
- Si `estado_reproductivo = lactante` → campo obligatorio "Número de crías"

**Alerta automática para mascotas gestantes/lactantes:**

```
AVISO: Los requerimientos calóricos durante gestación y lactancia son
significativamente mayores. Este plan ha sido calculado para ese estado.
Se recomienda supervisión veterinaria durante todo el período.
```

**Componentes afectados:**
- `domain/aggregates/pet_profile.py` — 2 nuevos enums
- `domain/nutrition/nrc_factors.py` — nuevas funciones y factores
- `domain/nutrition/nrc_calculator.py` — lógica para gestante/lactante
- `mobile/lib/features/pet/pet_wizard_screen.dart` — campos condicionales
- Tests: `test_nrc_calculator.py` — casos gestación y lactancia

**Dependencias:** ninguna
**Requiere validación Lady Carolina:** Sí — factores calóricos

---

### A-04: Nuevas Condiciones Médicas (4)

**¿Qué es?**
Agregar 4 condiciones médicas nuevas al sistema: ICC, Cushing, Epilepsia, Megaesófago.
Cada una con su `ConditionRestrictions` hard-coded y protocolo específico.

**¿Por qué importa?**
Son patologías frecuentes en clínica general. Un paciente con ICC que recibe un plan
sin restricción de sodio puede sufrir descompensación cardíaca.

**Nuevas condiciones:**

```python
# domain/safety/medical_restrictions.py — agregar:

"insuficiencia_cardiaca": _r(
    prohibited={
        "sodio_alto", "embutidos", "enlatados_con_sal", "queso",
        "jamón", "tocino", "sal_agregada", "caldos_salados",
        "alimentos_procesados_salados"
    },
    limited={
        "sodio_total",   # máx 20mg sodio/100kcal
        "grasa_saturada",
        "líquido_excesivo_si_edema",
    },
    recommended={
        "taurina",          # suplementación obligatoria
        "l_carnitina",      # suplementación en casos con cardiomiopatía
        "omega3_epa_dha",   # antiinflamatorio cardíaco
        "proteína_digestible_moderada",
        "carbs_digestibles",
    },
    special_rules={
        "sodio_máximo_20mg_por_100kcal",
        "taurina_obligatoria_100mg_kg_dia",
        "no_ejercicio_post_comida",
        "comidas_pequeñas_frecuentes",
        "monitoreo_peso_diario",  # retención de líquidos
    },
),

"hiperadrenocorticismo_cushing": _r(
    prohibited={
        "azúcares", "carbohidratos_simples", "alimentos_alto_índice_glucémico",
        "grasa_alta", "sodio_alto",
    },
    limited={
        "carbohidratos_totales",
        "calorías_totales",
        "fósforo",  # frecuente comorbilidad renal
    },
    recommended={
        "proteína_magra_alta_digestibilidad",
        "fibra_soluble",
        "carbohidratos_complejos_bajo_ig",
        "omega3_antiinflamatorio",
    },
    special_rules={
        "control_glucémico_como_diabético",
        "control_peso_estricto_frecuente_obesidad_asociada",
        "evaluación_función_renal_asociada",
        "polifagia_frecuente_no_aumentar_ración",  # el Cushing genera hambre excesiva
    },
),

"epilepsia": _r(
    prohibited={
        "glutamato_monosodico",
        "colorantes_artificiales",
        "conservantes_artificiales",
        "azúcares_refinados",
        "alcohol",  # obvio pero importante para dieta casera
    },
    limited={
        "carbohidratos_totales",   # si se indica dieta cetogénica
        "carbohidratos_simples",
    },
    recommended={
        "grasas_saludables_omega3",   # DHA neuroprotector
        "proteína_digestible",
        "antioxidantes_vitamina_e",
        "magnesio",                   # cofactor neurológico
        "taurina",                    # neuromodulador
    },
    special_rules={
        "sin_glutamato_agregado",
        "dieta_cetogénica_si_epilepsia_refractaria_indicada_por_vet",
        "regularidad_horaria_estricta",  # irregularidad horaria puede precipitar crisis
        "no_ayuno_mayor_8h",            # hipoglucemia puede precipitar crisis
    },
),

"megaesofago": _r(
    prohibited={
        "alimentos_sólidos_grandes",
        "croquetas_secas_sin_remojar",
        "huesos",
        "alimentos_fibrosos_difícil_deglución",
    },
    limited={
        "tamaño_porción",   # porciones muy pequeñas
        "velocidad_ingesta",
    },
    recommended={
        "dieta_húmeda_o_papilla",
        "caldo_de_cocción_como_base",
        "alimentos_blandos_fácil_deglución",
        "proteína_magra_cocida_bien_blanda",
    },
    special_rules={
        "POSICIÓN_VERTICAL_ALIMENTACIÓN_OBLIGATORIA",  # Bailey chair
        "30_minutos_vertical_post_comida",             # prevención aspiración
        "porciones_muy_pequeñas_frecuentes",           # 4-6 comidas/día
        "alimento_temperatura_ambiente",               # no frío ni muy caliente
        "supervisión_alimentación_directa",            # riesgo neumonía aspirativa
        "ALERTA_NEUMONÍA_ASPIRATIVA_P0",
    },
),
```

**MedicalCondition enum:**

```python
# domain/aggregates/pet_profile.py — agregar:
class MedicalCondition(str, Enum):
    # ... 13 existentes ...
    CARDIAC_INSUFFICIENCY = "insuficiencia_cardiaca"     # NUEVO
    CUSHING = "hiperadrenocorticismo_cushing"            # NUEVO
    EPILEPSY = "epilepsia"                               # NUEVO
    MEGAESOPHAGUS = "megaesofago"                        # NUEVO
```

**Total: 17 condiciones** (13 → 17)

**Alerta especial para megaesófago:**
La app debe mostrar un warning visible en rojo antes de generar el plan:

```
⚠️ MEGAESÓFAGO DETECTADO
La alimentación de esta mascota requiere supervisión directa.
Riesgo de neumonía aspirativa si no se usa posición vertical (Bailey chair).
NutriVet.IA recomienda que el plan sea supervisado presencialmente por un veterinario.
```

**Componentes afectados:**
- `domain/aggregates/pet_profile.py` — 4 nuevos enums
- `domain/safety/medical_restrictions.py` — 4 nuevas entradas
- `infrastructure/agent/prompts/condition_protocols.py` — 4 nuevos protocolos LLM
- `mobile/lib/features/pet/` — 4 nuevas opciones en selector de condiciones
- Tests: `test_medical_restrictions.py` — 4 × 3 escenarios = 12 tests nuevos

**Dependencias:** ninguna
**Requiere validación Lady Carolina:** Sí — crítico

---

### A-05: Validación Ca:P Determinista

**¿Qué es?**
Mover la validación de la relación Calcio:Fósforo al cálculo determinista (Python),
fuera del LLM. Agregar alerta automática cuando el ratio está fuera del rango seguro.

**¿Por qué importa?**
La sobresuplementación de calcio en cachorros de razas grandes es una de las causas
más frecuentes de displasia articular. Esto no puede ser decisión del LLM.

**Rangos según NRC 2006:**

```python
# domain/nutrition/nrc_calculator.py — agregar

CA_P_RATIOS = {
    # (especie, etapa_vida): (min, max, óptimo)
    ("perro", "cachorro_raza_grande"): (1.2, 1.8, 1.5),  # CRÍTICO — rango estrecho
    ("perro", "cachorro_raza_normal"): (1.0, 2.0, 1.5),
    ("perro", "adulto"): (1.0, 2.0, 1.4),
    ("perro", "gestante"): (1.2, 1.8, 1.5),
    ("perro", "lactante"): (1.0, 2.0, 1.4),
    ("gato", "gatito"): (1.0, 1.5, 1.2),
    ("gato", "adulto"): (0.9, 1.5, 1.1),
    ("gato", "gestante"): (1.0, 1.5, 1.2),
    ("gato", "senior"): (0.9, 1.5, 1.1),
}

def validate_ca_p_ratio(
    calcio_g: float,
    fosforo_g: float,
    species: str,
    life_stage: str,
    breed_size: Optional[str] = None,
) -> CaPValidationResult:
    """
    Valida relación Ca:P post-generación de plan. Determinista, no LLM.
    Retorna APTO / ALERTA / BLOQUEANTE según severidad.
    """
    ratio = calcio_g / fosforo_g if fosforo_g > 0 else 0

    stage_key = life_stage
    if life_stage == "cachorro" and breed_size in {"grande", "gigante"}:
        stage_key = "cachorro_raza_grande"

    key = (species, stage_key)
    min_r, max_r, opt = CA_P_RATIOS.get(key, (1.0, 2.0, 1.4))

    if ratio < min_r:
        return CaPValidationResult(
            status="BLOQUEANTE",
            ratio=ratio,
            message=f"Ca:P {ratio:.2f} — Deficiente en calcio. Riesgo de hiperparatiroidismo nutricional.",
        )
    elif ratio > max_r:
        return CaPValidationResult(
            status="BLOQUEANTE",
            ratio=ratio,
            message=f"Ca:P {ratio:.2f} — Exceso de calcio. Riesgo de displasia en cachorros.",
        )
    elif abs(ratio - opt) > 0.3:
        return CaPValidationResult(
            status="ALERTA",
            ratio=ratio,
            message=f"Ca:P {ratio:.2f} — Subóptimo. Rango recomendado: {min_r}-{max_r}.",
        )
    return CaPValidationResult(status="APTO", ratio=ratio)
```

**Esta validación se ejecuta en el `validate_output` node del Plan Generation Subgraph**,
después del LLM y antes del `hitl_router`. Si devuelve BLOQUEANTE → el plan no avanza.

**Componentes afectados:**
- `domain/nutrition/nrc_calculator.py`
- `infrastructure/agent/plan_generation_subgraph.py` — nodo validate_output
- Tests: caso cachorro raza grande + exceso calcio

**Dependencias:** A-02 (para tener fosforo_mg en alimentos)
**Requiere validación Lady Carolina:** Sí

---

### A-06: BCS Diferenciado por Especie

**¿Qué es?**
El BCS 1-9 se aplica igual para perros y gatos actualmente, pero la distribución de grasa
y los indicadores visuales son diferentes. Agregar lógica de BCS específica por especie.

**¿Por qué importa?**
Un gato con BCS 6 tiene una distribución de grasa diferente a un perro con BCS 6.
Las imágenes visuales del wizard deben ser específicas por especie.
La estimación de "peso ideal" también varía.

**Cambios:**

```python
# domain/nutrition/nrc_calculator.py
def estimate_ideal_weight(
    current_weight_kg: float,
    bcs: int,
    species: Species,
) -> float:
    """
    Estima peso ideal según BCS y especie.
    Fórmula aproximada — NRC + consenso WSAVA 2013.
    """
    if species == Species.DOG:
        # BCS 5 = peso ideal. Cada punto = ~10% del peso ideal
        bcs_offset = bcs - 5
        correction_factor = 1 - (bcs_offset * 0.10)
        return current_weight_kg * correction_factor
    else:  # CAT
        # Gatos: cada punto de BCS sobre 5 = ~400g de exceso (aprox)
        bcs_offset = bcs - 5
        if bcs_offset > 0:
            return current_weight_kg - (bcs_offset * 0.4)
        else:
            return current_weight_kg + (abs(bcs_offset) * 0.3)
```

**En el wizard Flutter:**
- BCS 1-9 perros: usar imágenes WSAVA caninas
- BCS 1-9 gatos: usar imágenes WSAVA felinas
- Son visualmente muy diferentes — no intercambiar

**Componentes afectados:**
- `domain/nutrition/nrc_calculator.py` — nueva función `estimate_ideal_weight`
- `mobile/lib/features/pet/pet_wizard_screen.dart` — imágenes BCS por especie
- `mobile/assets/images/bcs_dogs/` — 9 imágenes (ya existen o crear)
- `mobile/assets/images/bcs_cats/` — 9 imágenes NUEVO

**Dependencias:** ninguna
**Requiere validación Lady Carolina:** Sí — criterios visuales WSAVA

---

### A-07: Peso Ideal — Documentación y Lógica Explícita

**¿Qué es?**
Documentar explícitamente la fórmula de estimación de peso ideal que hoy está implícita
en el cálculo para BCS ≥ 7. Agregar campo `calculated_ideal_weight_kg` en el plan.

**¿Por qué importa?**
Hoy el código aplica `RER(peso_ideal)` pero el peso ideal no está documentado ni
visible para el propietario. El owner no sabe de cuánto peso tiene que bajar su mascota.

**Cambio en PlanOutputSchema:**

```python
# infrastructure/agent/json_schemas.py
class PerfilNutricionalSchema(BaseModel):
    rer_kcal: float
    der_kcal: float
    peso_actual_kg: float         # NUEVO — explícito
    peso_ideal_estimado_kg: float # NUEVO — visible al propietario
    bcs_actual: int               # NUEVO
    fase: str                     # "mantenimiento" | "reducción" | "aumento"
    meta_peso: Optional[str]      # NUEVO — "Reducir de 12kg a 9kg estimado"
    # ... resto igual
```

**En la UI del plan**, mostrar:
```
Peso actual: 12.0 kg | BCS: 8/9
Peso ideal estimado: 9.0 kg
Meta: reducir ~3.0 kg
Calorías diarias (calculadas sobre peso ideal): 380 kcal
```

**Componentes afectados:**
- `domain/nutrition/nrc_calculator.py`
- `infrastructure/agent/json_schemas.py`
- `mobile/lib/features/plan/plan_detail_screen.dart`

**Dependencias:** A-06
**Requiere validación Lady Carolina:** Sí

---

### A-08: Restricciones por Predisposición Genética de Raza

**¿Qué es?**
Cuando la raza tiene predisposiciones conocidas, el sistema las aplica como
restricciones "preventivas" suaves (no tan duras como condiciones médicas activas),
a menos que la condición ya esté declarada (ahí aplica la restricción hard-coded).

**¿Por qué importa?**
Un Dálmata SIN cistitis diagnosticada todavía debe evitar sardinas/anchoas/hígado
porque el riesgo de urolitiasis de urato es casi certero. La prevención nutricional
es el pilar del manejo en estas razas.

**Lógica:**

```python
# domain/safety/breed_restriction_engine.py — NUEVO

BREED_PREVENTIVE_RESTRICTIONS = {
    "dalmata": {
        "prohibited_preventive": {"hígado", "anchoas", "sardinas_alta_purina",
                                   "riñón", "corazón_exceso"},
        "recommended_preventive": {"hidratación_alta", "dieta_alcalinizante",
                                    "proteína_baja_purinas"},
        "alert": "Dálmata: restricción preventiva de purinas para prevenir urolitiasis de urato",
    },
    "bedlington_terrier": {
        "prohibited_preventive": {"hígado", "mariscos", "nueces", "semillas_cobre_alto"},
        "alert": "Bedlington Terrier: restricción preventiva de cobre (predisposición genética a acumulación hepática)",
    },
    "west_highland_white_terrier": {
        "prohibited_preventive": {"hígado", "mariscos"},
        "alert": "West Highland: restricción preventiva de cobre",
    },
    "cocker_spaniel": {
        "limited_preventive": {"grasa_total"},
        "recommended_preventive": {"omega3", "proteína_digestible"},
        "alert": "Cocker Spaniel: predisposición a pancreatitis — grasa moderada como prevención",
    },
    "schnauzer_miniatura": {
        "limited_preventive": {"grasa_total"},
        "alert": "Schnauzer Miniatura: predisposición a hiperlipidemia — control de grasa preventivo",
    },
    "gran_danes": {
        "special_preventive": {"sin_comedero_elevado", "2_comidas_mínimo_dia",
                                "sin_ejercicio_2h_post_comida",
                                "restricción_calcio_si_cachorro"},
        "alert": "Gran Danés: riesgo de dilatación-vólvulo gástrico (GDV). Reglas de alimentación estrictas",
    },
    "maine_coon": {
        "recommended_preventive": {"taurina_elevada", "omega3_cardioprotector"},
        "alert": "Maine Coon: predisposición a HCM — taurina y omega-3 preventivos",
    },
    "persa": {
        "recommended_preventive": {"hidratación_alta", "dieta_húmeda"},
        "limited_preventive": {"fósforo"},
        "alert": "Persa: predisposición a PKD — hidratación alta y fósforo moderado como prevención",
    },
    "ragdoll": {
        "recommended_preventive": {"taurina_elevada", "omega3_cardioprotector"},
        "limited_preventive": {"fósforo"},
        "alert": "Ragdoll: predisposición a HCM y PKD — taurina, omega-3 y fósforo moderado preventivos",
    },
    # ... continuar para todas las razas con predisposición
}
```

**Integración en el Plan Generation Subgraph:**
El nodo `load_context` carga las restricciones de la raza junto con las de condición médica.
Las restricciones preventivas son "recomendaciones fuertes" al LLM, no hard-blocks
(a diferencia de las condiciones médicas activas que son BLOQUEANTES).

**Componentes afectados:**
- `domain/safety/breed_restriction_engine.py` — NUEVO
- `infrastructure/agent/plan_generation_subgraph.py` — load_context
- Tests: Dálmata sin condición + sardinas → alerta preventiva

**Dependencias:** A-01 (BD de Razas)
**Requiere validación Lady Carolina:** Sí

---

### A-09: Cláusula Legal para Veterinarios

**¿Qué es?**
Al registrarse como veterinario, mostrar una cláusula de aceptación obligatoria que:
1. Declara que el profesional tiene título habilitante y ejerce bajo su propia responsabilidad
2. Excluye de responsabilidad a NutriVet.IA y BAMPYSVET por el uso sin credenciales válidas
3. Se registra con timestamp, IP y consentimiento explícito en base de datos

**¿Por qué importa?**
Sin verificación formal de tarjeta COMVEZCOL (Colombia) o equivalente LATAM,
esta cláusula es la protección legal mínima viable.

**Implementación:**

```python
# domain/aggregates/user_account.py — nuevo campo
@dataclass
class VetConsentRecord:
    accepted_at: datetime
    ip_address: str          # anonimizada para logs pero guardada en DB encriptada
    clause_version: str      # "v1.0-2026-03"
    declaration_text: str    # texto completo que aceptaron (inmutable post-registro)
```

**Texto de la cláusula (redacción para revisión legal):**

```
DECLARACIÓN DE RESPONSABILIDAD PROFESIONAL

Al registrarse como Médico Veterinario en NutriVet.IA, usted declara y acepta:

1. Poseer título de Médico Veterinario o Médico Veterinario Zootecnista legalmente
   reconocido en su país de ejercicio.

2. Ejercer su actividad profesional bajo su propia responsabilidad, en cumplimiento
   de la normativa veterinaria vigente en su jurisdicción.

3. Que NutriVet.IA es una herramienta de apoyo nutricional digital y no reemplaza
   el criterio clínico del profesional veterinario.

4. Que NutriVet.IA y BAMPYSVET SAS quedan exentas de responsabilidad por el uso
   de esta plataforma por parte de personas sin título habilitante.

5. Que cualquier decisión clínica tomada con base en las recomendaciones de
   NutriVet.IA es de exclusiva responsabilidad del profesional suscriptor.

Esta declaración queda registrada con fecha, hora e identificación de sesión.
```

**En Flutter:** pantalla de aceptación con scroll obligatorio + checkbox "He leído y acepto" +
campo "País de ejercicio profesional" + campo "Número de tarjeta profesional (opcional)".

**Componentes afectados:**
- `domain/aggregates/user_account.py`
- `backend/presentation/v1/auth/auth_router.py` — endpoint de registro vet
- `backend/infrastructure/db/models/` — tabla `vet_consent_records`
- `mobile/lib/features/auth/register_screen.dart`
- Migración Alembic

**Dependencias:** ninguna
**Requiere validación:** Revisión legal (no Lady Carolina)

---

## FASE B — Expansión Clínica

> Cambios que amplían la calidad clínica del sistema. Algunos tocan domain/, todos requieren validación.

---

### B-01: Suplementación Específica por Condición

**¿Qué es?**
Definir dosis terapéuticas de suplementos para condiciones específicas,
diferenciando dosis de mantenimiento vs dosis clínica.

**Suplementos clínicos nuevos:**

```python
# domain/nutrition/clinical_supplements.py — NUEVO

CLINICAL_SUPPLEMENTS = {
    "insuficiencia_cardiaca": {
        "taurina": {
            "dosis_perro_mg_kg_dia": 100,   # terapéutica (vs 25 mantenimiento)
            "dosis_gato_mg_kg_dia": 250,
            "justificacion": "NRC 2006 + J Vet Intern Med 1992: taurina deficiente en cardiomiopatía dilatada",
        },
        "l_carnitina": {
            "dosis_perro_mg_kg_dia": 50,
            "dosis_gato_mg_kg_dia": 50,
            "justificacion": "Cardiomiopatía dilatada — deficiencia documentada en Cocker Spaniels y Boxers",
        },
        "omega3_epa_dha": {
            "dosis_perro_mg_kg_dia": 40,   # vs 20 mantenimiento
            "dosis_gato_mg_kg_dia": 25,
            "justificacion": "ACVIM 2019: omega-3 antiinflamatorio cardíaco en dosis altas",
        },
    },
    "oncologico": {
        "omega3_epa_dha": {
            "dosis_perro_mg_kg_dia": 50,   # antitumoral (vs 20 mantenimiento)
            "dosis_gato_mg_kg_dia": 30,
            "justificacion": "J Nutr 1998 Ogilvie: omega-3 EPA antitumoral en dosis altas",
        },
        "vitamina_e": {
            "dosis_perro_ui_dia": 400,
            "dosis_gato_ui_dia": 30,
            "justificacion": "Antioxidante — reducción estrés oxidativo en cáncer",
        },
    },
    "articular": {
        "glucosamina": {
            "dosis_perro_mg_kg_dia": 22,
            "justificacion": "WSAVA 2010: condroprotektor en artritis degenerativa",
        },
        "condroitin": {
            "dosis_perro_mg_kg_dia": 17,
            "justificacion": "Complementario a glucosamina — sinergia documentada",
        },
        "omega3_epa_dha": {
            "dosis_perro_mg_kg_dia": 30,
            "justificacion": "Antiinflamatorio articular — reducción de COX-2",
        },
    },
    "epilepsia": {
        "magnesio": {
            "dosis_perro_mg_kg_dia": 1.5,
            "dosis_gato_mg_kg_dia": 1.0,
            "justificacion": "Cofactor neurológico — déficit documentado en algunos epilépticos",
        },
        "dha": {
            "dosis_perro_mg_kg_dia": 25,
            "justificacion": "Neuroprotector — J Vet Intern Med 2012",
        },
    },
    "renal_avanzado": {
        "ketoácidos": {
            "dosis_perro_mg_kg_dia": 60,
            "justificacion": "Análogos de aminoácidos sin nitrógeno — estándar manejo renal crónico IRIS Stage 3-4",
            "nota": "Solo si estadio renal avanzado (IRIS 3-4). Requiere prescripción veterinaria",
        },
        "omega3": {
            "dosis_perro_mg_kg_dia": 30,
            "justificacion": "Reduce inflamación glomerular — Am J Vet Res 1998",
        },
    },
}
```

**Componentes afectados:**
- `domain/nutrition/clinical_supplements.py` — NUEVO
- `infrastructure/agent/prompts/plan_generation_prompts.py` — inyectar dosis clínicas
- `infrastructure/agent/json_schemas.py` — campo `justificacion` en suplementos
- Tests: ICC → plan incluye taurina en dosis terapéutica

**Dependencias:** A-04
**Requiere validación Lady Carolina:** Sí — dosis clínicas

---

### B-02: Lógica de Razas Gigantes (Cronología Adulto)

**¿Qué es?**
Cuando la raza tiene `meses_adulto > 12`, el cálculo del factor de edad usa la
cronología específica de la raza, no la genérica de 12 meses.

**Cambio en NRCCalculator:**

```python
# domain/nutrition/nrc_calculator.py
def get_age_factor(
    age_months: int,
    species: Species,
    breed_info: Optional[BreedInfo] = None,
) -> float:
    """
    Si la raza tiene meses_adulto > 12, aplicar factor cachorro
    hasta esa edad real.
    """
    adult_age = 12  # default
    if breed_info and breed_info.meses_adulto:
        adult_age = breed_info.meses_adulto

    if species == Species.DOG:
        if age_months <= 3:
            return 3.0
        elif age_months <= adult_age:     # antes: siempre ≤ 12
            return 2.0
        elif age_months <= 24:
            return 1.2
        else:
            return 1.0
    # ... gatos igual
```

**Impacto real:**
Un Gran Danés de 14 meses actualmente recibe factor 1.2 (adulto joven).
Con este cambio recibirá factor 2.0 (cachorro) → +67% de calorías → correcto.

**Componentes afectados:**
- `domain/nutrition/nrc_calculator.py`
- `domain/nutrition/nrc_factors.py`
- Tests: Gran Danés 14 meses → factor cachorro

**Dependencias:** A-01
**Requiere validación Lady Carolina:** Sí

---

### B-03: Protocolo BARF — Alerta Bacteriológica

**¿Qué es?**
Cuando el plan es de tipo "Natural (BARF)" o incluye ingredientes crudos,
mostrar alertas de manipulación higiénica y casos de alto riesgo.

**¿Por qué importa?**
Salmonella, Listeria y E.coli en carne cruda son reales. Para propietarios
con inmunocompromiso o mascotas de alto riesgo, esto puede ser serio.

**Implementación en el plan:**

```python
# infrastructure/agent/prompts/plan_generation_prompts.py — agregar bloque

BARF_SAFETY_ALERTS = """
## Protocolo de Seguridad para Dieta Natural (BARF)

### Advertencia de Riesgo Bacteriológico
La carne cruda puede contener Salmonella, Listeria monocytogenes y E.coli.
Estas bacterias son ZOONÓTICAS — pueden transmitirse a humanos, especialmente a niños,
adultos mayores e inmunocomprometidos.

### Prácticas obligatorias de manipulación:
- Lavar manos con jabón después de preparar y servir el alimento
- Desinfectar superficies y utensilios con agua caliente + detergente
- Mantener la carne congelada y descongelar en refrigerador (no a temperatura ambiente)
- No mezclar utensilios de la dieta de la mascota con los de la familia
- Supervisar que la mascota no lama objetos o personas después de comer

### Casos de alto riesgo (considerar cocción parcial o dieta cocida):
- Mascotas con condición renal, hepática, pancreática o inmunosuprimidas
- Cachorros menores de 12 semanas
- Mascotas geriátricas (> 10 años en perros, > 12 en gatos)
- Hogares con niños menores de 5 años, embarazadas o inmunodeprimidos
"""
```

**En la UI Flutter:**
- Mostrar este panel como `AlertCard` amarillo-naranja en la primera vez que se activa el plan BARF
- Botón "Entendido y acepto" con registro de aceptación

**Componentes afectados:**
- `infrastructure/agent/prompts/plan_generation_prompts.py`
- `infrastructure/agent/json_schemas.py` — campo `alertas_barf_seguridad`
- `mobile/lib/features/plan/plan_detail_screen.dart`

**Dependencias:** ninguna
**Requiere validación Lady Carolina:** Revisión del texto

---

### B-04: Índice Glucémico en Diabéticos (Subutilizado)

**¿Qué es?**
Hoy el campo `indice_glucemico` existe en PlantFood pero el LLM no recibe instrucción
explícita de usarlo para diabéticos. Inyectarlo en el protocolo de condición.

**Cambio en condition_protocols.py:**

```python
# infrastructure/agent/prompts/condition_protocols.py
PROTOCOL_DIABETICO = """
## Protocolo Diabético — Índice Glucémico

Para mascotas con diabetes mellitus, el índice glucémico de los carbohidratos
es CRÍTICO para evitar picos de glucosa post-prandial.

### Carbohidratos PERMITIDOS (IG bajo):
- Arroz integral cocido (IG ≈ 55) ✓
- Batata/camote cocida (IG ≈ 54) ✓
- Avena cocida (IG ≈ 42) ✓
- Cebada perlada cocida (IG ≈ 25) ✓
- Quinoa cocida (IG ≈ 53) ✓

### Carbohidratos LIMITADOS (IG medio, máx 20% de la ración):
- Papa cocida (IG ≈ 65) — solo en pequeñas cantidades
- Zanahoria cocida (IG ≈ 47) — moderado

### Carbohidratos PROHIBIDOS (IG alto):
- Arroz blanco refinado (IG ≈ 72) ✗
- Pan, harina, pasta (IG > 70) ✗
- Plátano maduro, mango (IG > 65) ✗

### Reglas de horario:
- Sincronizar la comida con la administración de insulina (si aplica)
- Raciones iguales en horarios fijos — NUNCA saltarse comidas
- No premios entre comidas principales
"""
```

**Componentes afectados:**
- `infrastructure/agent/prompts/condition_protocols.py`

**Dependencias:** ninguna
**Requiere validación Lady Carolina:** Sí — tabla IG

---

### B-05: Transición Variable por Condición

**¿Qué es?**
La duración de la transición de dieta actualmente es fija (7 días).
Debe ser variable según la condición gastrointestinal de la mascota.

**Nueva lógica:**

```python
# domain/nutrition/transition_protocol.py — NUEVO

TRANSITION_DURATION_BY_CONDITION = {
    # Condición → (días_mínimo, días_máximo, ritmo_descripción)
    "sano_no_sensible": (7, 10, "10% nuevo cada día"),
    "sano_sensible": (14, 21, "5-7% nuevo cada 2 días"),
    "gastritis": (21, 28, "Muy gradual — 5% cada 2-3 días"),
    "pancreático": (21, 28, "Extremadamente gradual — vigilar lipasa"),
    "hepático": (14, 21, "Gradual — vigilar bilirrubina"),
    "renal": (14, 21, "Gradual — vigilar creatinina"),
    "insuficiencia_cardiaca": (14, 21, "Vigilar retención de líquidos"),
    "megaesofago": (30, 42, "Muy lenta — adaptación a nueva textura"),
    "barf_a_croqueta": (21, 28, "Cambio de forma física — crítico"),
    "croqueta_a_barf": (21, 28, "Cambio de forma física — crítico"),
}

def get_transition_protocol(
    conditions: set[str],
    current_diet: str,
    new_diet: str,
) -> TransitionProtocol:
    """
    Determina la duración y ritmo de transición según condición más restrictiva
    y tipo de cambio (forma física del alimento).
    """
    # Detectar cambio de forma física (más crítico)
    physical_change = (
        ("natural" in new_diet and "concentrado" in current_diet) or
        ("concentrado" in new_diet and "natural" in current_diet)
    )

    # Buscar condición más restrictiva
    max_days = 10
    protocol_key = "sano_no_sensible"

    for condition in conditions:
        key = condition.lower().replace("/", "_")
        if key in TRANSITION_DURATION_BY_CONDITION:
            _, cond_max, _ = TRANSITION_DURATION_BY_CONDITION[key]
            if cond_max > max_days:
                max_days = cond_max
                protocol_key = key

    if physical_change and max_days < 21:
        protocol_key = "barf_a_croqueta" if "concentrado" in new_diet else "croqueta_a_barf"
        max_days = 28

    min_d, max_d, rhythm = TRANSITION_DURATION_BY_CONDITION[protocol_key]
    return TransitionProtocol(min_dias=min_d, max_dias=max_d, ritmo=rhythm)
```

**Componentes afectados:**
- `domain/nutrition/transition_protocol.py` — NUEVO
- `infrastructure/agent/json_schemas.py` — `TransicionSchema.duracion_dias` deja de ser hardcoded
- Tests: gastritis → transición 21-28 días

**Dependencias:** ninguna
**Requiere validación Lady Carolina:** Sí

---

### B-06: Interacciones Medicamento-Nutriente (Alertas)

**¿Qué es?**
Un módulo de alertas (no restricciones duras) para las interacciones más críticas
entre medicamentos comunes y nutrientes. El agente no responde consultas médicas,
pero SÍ puede mostrar una alerta preventiva cuando detecta una condición + fármaco conocido.

**Alcance reducido — solo las más críticas y frecuentes:**

```python
# domain/safety/drug_nutrient_interactions.py — NUEVO

DRUG_NUTRIENT_ALERTS = {
    # (condición) → {posible_fármaco: alerta_nutricional}
    # No manejamos fármacos directamente — usamos la condición como proxy

    "epilepsia": {
        "fenobarbital_probable": (
            "Los pacientes epilépticos tratados con fenobarbital pueden presentar déficit "
            "de vitamina D y ácido fólico. Se recomienda suplementación preventiva "
            "y monitoreo periódico con el veterinario tratante."
        ),
    },
    "insuficiencia_cardiaca": {
        "enalapril_benazepril_probable": (
            "Los IECA (enalapril, benazepril) usados en cardiopatía pueden aumentar "
            "los niveles de potasio. No suplementar potasio sin indicación veterinaria."
        ),
        "furosemida_probable": (
            "La furosemida puede causar pérdida de potasio y magnesio. "
            "Monitoreo electrolítico recomendado."
        ),
    },
    "hipotiroideo": {
        "levotiroxina_probable": (
            "El calcio y los alimentos ricos en calcio pueden interferir con la absorción "
            "de levotiroxina. Administrar el medicamento con el estómago vacío, "
            "separado de la comida por al menos 30 minutos."
        ),
    },
    "cancerígeno": {
        "quimioterapia_probable": (
            "Durante quimioterapia pueden producirse náuseas y anorexia. "
            "Priorizar alimentos palatables y digestibles. "
            "Evitar suplementar vitamina C en dosis altas durante quimioterapia "
            "— puede interferir con algunos agentes alquilantes."
        ),
    },
}
```

**Cómo se muestra:**
- En la sección `notas_clinicas` del plan (solo visible para el vet revisor)
- En `alertas_propietario` como texto simplificado: "Consulte con su veterinario sobre posibles interacciones entre el medicamento y la dieta"
- El agente NO especifica medicamentos — solo menciona la posibilidad de interacción

**Componentes afectados:**
- `domain/safety/drug_nutrient_interactions.py` — NUEVO
- `infrastructure/agent/plan_generation_subgraph.py` — load_context inyecta alertas
- Tests: ICC → nota de interacción IECA+potasio en plan

**Dependencias:** A-04
**Requiere validación Lady Carolina:** Sí

---

### B-07: Especificación de Calidad de Ingredientes

**¿Qué es?**
Agregar un campo `especificacion_compra` por ingrediente en el plan, indicando
qué presentación del alimento usar (fresco, congelado, enlatado, etc.).

**Cambio en IngredienteSchema:**

```python
# infrastructure/agent/json_schemas.py
class IngredienteSchema(BaseModel):
    nombre: str
    cantidad_g: float
    # ... campos existentes ...
    especificacion_compra: str  # NUEVO
    # Ejemplo: "Pollo: fresca o congelada sin aditivos. Evitar versiones marinadas."
    # Ejemplo: "Sardinas: en agua, sin sal. NO en aceite de girasol."
    # Ejemplo: "Zanahoria: fresca, cruda o cocida al vapor."
    alternativas_equivalentes: list[str]  # NUEVO — "Si no hay X, usar Y"
```

**El LLM recibe instrucción de completar estos campos para cada ingrediente.**

**Componentes afectados:**
- `infrastructure/agent/json_schemas.py`
- `infrastructure/agent/prompts/plan_generation_prompts.py` — instrucción al LLM
- `mobile/lib/features/plan/plan_detail_screen.dart` — mostrar especificación en UI

**Dependencias:** ninguna
**Requiere validación Lady Carolina:** No (UX)

---

## FASE C — Acompañamiento al Propietario

> Features de UX que aumentan adherencia y retención. Ninguna toca domain layer.

---

### C-01: Seguimiento de Peso y BCS en el Tiempo

**¿Qué es?**
Permitir al propietario registrar el peso y BCS de su mascota periódicamente,
y visualizar la curva de progreso.

**Nuevo endpoint:**
```
POST /v1/pets/{pet_id}/weight-log
  body: { peso_kg: float, bcs: int, fecha: date, notas: str }

GET /v1/pets/{pet_id}/weight-log
  response: list[WeightLogEntry] + trend (ascendente/descendente/estable)
```

**En Flutter:**
- Botón "Registrar peso hoy" en el perfil de la mascota
- Gráfico de línea simple (peso vs tiempo) con línea punteada de peso ideal
- Indicador: "En camino ✓" / "Sin progreso — revisar plan" / "Perdiendo demasiado rápido"

**Componentes afectados:**
- `backend/infrastructure/db/models/` — tabla `weight_log`
- `backend/presentation/v1/pets/` — nuevo endpoint
- `mobile/lib/features/pet/pet_profile_screen.dart`
- Migración Alembic

---

### C-02: Meal Prep Guidance (Guía de Preparación en Lote)

**¿Qué es?**
Agregar una sección en el plan con instrucciones prácticas de preparación en lote
(batch cooking): cuánto preparar, cómo almacenar, cuánto dura en frío/congelado.

**Nuevo campo en el schema:**

```python
class MealPrepGuide(BaseModel):
    porcion_semanal_g: float           # total a preparar para 7 días
    tiempo_preparacion_lote_minutos: int
    metodo_batch: str                  # "Cocinar todo el lunes y dividir en porciones"
    duracion_refrigerado_dias: int     # máximo en nevera (generalmente 3-4 días)
    duracion_congelado_dias: int       # máximo congelado (generalmente 30 días)
    instrucciones_congelado: str       # "Dividir en porciones diarias antes de congelar"
    instrucciones_descongelado: str    # "Pasar a nevera 12h antes. NUNCA microondas."
    nota_barf: Optional[str]          # "BARF no se cocina — solo refrigerado max 3 días"
```

**Componentes afectados:**
- `infrastructure/agent/json_schemas.py` — nuevo campo
- `mobile/lib/features/plan/plan_detail_screen.dart` — sección "Cómo preparar para la semana"

---

### C-03: Protocolo de Emergencia Alimentaria (Viajes)

**¿Qué es?**
Cuando el owner no puede preparar el plan por 1-5 días, el agente puede sugerir
un concentrado comercial temporal "aceptable" basado en el perfil de la mascota.

**Lógica:**
- El agente recibe la pregunta "¿Qué concentrado puedo usar de emergencia?"
- Clasifica como consulta nutricional (no médica) → responde
- Filtra según: especie, edad, condiciones médicas, alergias declaradas
- Sugiere categorías de concentrados (no marcas específicas — sin sponsors)
- Agrega: "Máximo 5 días. Retomar plan casero lo antes posible."

**Reglas:**
- NO recomendar marcas específicas (evitar percepción de sponsor)
- Recomendar características: "concentrado premium sin granos para perro adulto con condición renal"
- Si hay condición médica grave (renal, cardíaco) → "solo el concentrado prescrito por su veterinario"

**Componentes afectados:**
- `infrastructure/agent/consultation_subgraph.py` — nuevo intent "emergency_food"
- `infrastructure/agent/prompts/` — nuevo bloque de respuesta de emergencia

---

### C-04: Recordatorios de Comidas (Push Notifications)

**¿Qué es?**
Notificaciones push configurables para los horarios de comida del plan activo.

**Implementación Flutter:**
- Al activarse el plan, preguntar: "¿Quieres activar recordatorios de comida?"
- Si sí: configurar notificaciones locales (flutter_local_notifications) para cada comida
- Horarios tomados de `cronograma_diario[].horario` del plan

**Componentes afectados:**
- `mobile/pubspec.yaml` — dependencia `flutter_local_notifications`
- `mobile/lib/features/plan/` — lógica de configuración de notificaciones
- Solo mobile — no toca backend

---

### C-05: Alerta Interactiva vía Chat (Síntoma → Contexto del Plan)

**¿Qué es?**
El agente conversacional detecta cuando el propietario describe síntomas relacionados
con el plan activo y responde con contexto clínico, sin diagnósticar.

**Ejemplos de detección:**

| El owner escribe | El agente responde |
|---|---|
| "mi perro vomitó esta mañana" | "Veo que [Nombre] tiene condición pancreática. Vómito puede ser señal de irritación. Suspende la última comida por 4 horas, ofrece agua fresca. Si persiste o es más de 2 veces, contáctame [referral al vet]." |
| "no quiere comer desde ayer" | "Más de 12 horas sin comer en [Nombre] que tiene [condición] puede ser riesgoso. Contacta a tu veterinario. Si han pasado más de 24h, acude a urgencias." |
| "se está rascando mucho" | "Puede estar relacionado con el plan nutricional (alergia alimentaria). El agente no puede diagnosticar. Consulta tu veterinario si persiste más de 48h." |

**Este NO es diagnóstico** — es contextualizar el síntoma con el plan activo.

**Componentes afectados:**
- `infrastructure/agent/consultation_subgraph.py` — detectar síntomas en el chat
- `infrastructure/agent/prompts/` — nuevo bloque de manejo de síntomas
- El límite sigue siendo: síntoma → contexto de plan + derivación. NUNCA diagnóstico.

---

### C-06: Plan de Emergencia Alimentaria para Gatos — Síndrome de Hígado Graso

**¿Qué es?**
Regla específica y crítica para gatos: la lipidosis hepática (hígado graso) puede
ocurrir en gatos que no comen por 24-48 horas. El agente debe alertar explícitamente.

**Regla hard-coded (no LLM):**

```python
# domain/safety/food_safety_checker.py — agregar

def check_feline_fasting_risk(
    species: Species,
    hours_without_food: Optional[int],
    conditions: set[str],
) -> Optional[str]:
    """
    CRÍTICO para gatos: ayuno > 24h → riesgo lipidosis hepática (EMERGENCIA).
    """
    if species != Species.CAT:
        return None
    if hours_without_food and hours_without_food >= 24:
        return (
            "⚠️ ALERTA CRÍTICA: Un gato sin comer más de 24 horas está en riesgo de "
            "lipidosis hepática (síndrome de hígado graso) — una emergencia médica. "
            "Contacta a tu veterinario INMEDIATAMENTE. No esperes."
        )
    return None
```

**El agente aplica esta regla cuando detecta que un gato no ha comido.**
Esta regla es especialmente importante en gatos con sobrepeso — paradójicamente son
los más susceptibles a lipidosis hepática con ayunos breves.

**Componentes afectados:**
- `domain/safety/food_safety_checker.py`
- `infrastructure/agent/consultation_subgraph.py`
- Tests: gato + "no come desde ayer" → alerta lipidosis

---

## FASE D — Legal y Compliance

Solo 1 unidad: **A-09** (ya descrita arriba — cláusula de exclusión de responsabilidad para veterinarios).

---

## Resumen de Unidades de Trabajo

| ID | Nombre | Fase | Criticidad | Dep. | Toca Domain |
|----|--------|------|------------|------|-------------|
| A-01 | BD de Razas completa + Criollo | A | CRÍTICO | — | Sí |
| A-02 | Micronutrientes + tiaminasa + humedad | A | CRÍTICO | — | Sí |
| A-03 | Gestación y Lactancia | A | CRÍTICO | — | Sí |
| A-04 | 4 Nuevas condiciones (ICC, Cushing, Epilepsia, Megaesófago) | A | CRÍTICO | — | Sí |
| A-05 | Validación Ca:P determinista | A | CRÍTICO | A-02 | Sí |
| A-06 | BCS diferenciado por especie | A | IMPORTANTE | — | Sí |
| A-07 | Peso ideal — documentación explícita | A | IMPORTANTE | A-06 | Sí |
| A-08 | Restricciones preventivas por raza | A | IMPORTANTE | A-01 | Sí |
| A-09 | Cláusula legal para veterinarios | D | CRÍTICO (legal) | — | No |
| B-01 | Suplementación clínica específica | B | IMPORTANTE | A-04 | Sí |
| B-02 | Lógica razas gigantes (cronología) | B | IMPORTANTE | A-01 | Sí |
| B-03 | Protocolo BARF bacteriológico | B | CRÍTICO | — | No |
| B-04 | IG en diabéticos (protocolos) | B | IMPORTANTE | — | No |
| B-05 | Transición variable por condición | B | IMPORTANTE | — | Sí |
| B-06 | Alertas medicamento-nutriente | B | IMPORTANTE | A-04 | Sí |
| B-07 | Especificación calidad ingredientes | B | ÚTIL | — | No |
| C-01 | Seguimiento peso/BCS en el tiempo | C | IMPORTANTE | — | No |
| C-02 | Meal prep guidance | C | ÚTIL | — | No |
| C-03 | Protocolo emergencia alimentaria | C | ÚTIL | — | No |
| C-04 | Recordatorios push notifications | C | ÚTIL | — | No |
| C-05 | Alerta interactiva chat-síntoma | C | IMPORTANTE | — | No |
| C-06 | Lipidosis hepática gatos (ayuno) | C | CRÍTICO | — | Sí |

**Total: 22 unidades de trabajo**
**Críticas: 8 | Importantes: 9 | Útiles: 5**

---

## Secuencia de Implementación Recomendada

```
Sprint 1 (Fase A — dominio crítico):
  A-09 (cláusula legal — rápida, no toca domain)
  A-01 (BD razas — fundación para A-08, B-02)
  A-02 (micronutrientes + tiaminasa)
  A-03 (gestación/lactancia)
  A-04 (4 nuevas condiciones)

Sprint 2 (Fase A — dominio importante):
  A-05 (Ca:P determinista — depende A-02)
  A-06 (BCS por especie)
  A-07 (peso ideal explícito — depende A-06)
  A-08 (restricciones por raza — depende A-01)

Sprint 3 (Fase B):
  B-03 (BARF bacteriológico — rápida, no domain)
  B-01 (suplementación clínica — depende A-04)
  B-02 (razas gigantes — depende A-01)
  B-04 (IG diabéticos — rápida)
  B-05 (transición variable)
  B-06 (alertas medicamento)
  B-07 (calidad ingredientes — rápida)

Sprint 4 (Fase C):
  C-06 (lipidosis gatos — crítica, rápida)
  C-01 (seguimiento peso/BCS)
  C-05 (alerta chat-síntoma)
  C-02 (meal prep)
  C-03 (emergencia alimentaria)
  C-04 (push notifications)
```

---

## Quality Gates Actualizados

Con estas mejoras, los Quality Gates se amplían:

| Gate | Criterio Actualizado |
|------|----------------------|
| G1 | 0 tóxicos en golden set 60 casos + tiaminasa gatos |
| G2 | 100% restricciones médicas — ahora 17 condiciones (13+4) |
| G2b | 100% restricciones preventivas por raza en razas críticas (Dálmata, Bedlington) |
| G3 | ≥95% clasificación nutricional vs médica |
| G4 | ≥85% OCR success rate |
| G5 | ≥80% cobertura tests domain layer |
| G6 | ≥18/20 planes aprobados Lady Carolina — incluir casos de nuevas condiciones |
| G7 | 10 casos red-teaming sin bypass + 5 casos razas especiales |
| G8 | Caso Sally ±0.5 kcal |
| G9 | **NUEVO**: Caso gestación — perra gestante 9 semanas → DER ≥ 2x RER |
| G10 | **NUEVO**: Caso ICC — plan sin sodio > 20mg/100kcal + taurina presente |
| G11 | **NUEVO**: Caso Dálmata sano — plan sin sardinas/hígado/anchoas |
| G12 | **NUEVO**: Gato + sardina cruda → alerta tiaminasa visible en plan |

---

## Nota Final

Este plan cubre el 100% de las brechas identificadas en la revisión clínica de los tres roles.
Antes de implementar cualquier unidad de las Fases A y B, Lady Carolina Castañeda (MV)
debe revisar y validar los valores nutricionales, restricciones y protocolos clínicos.

Las unidades que no tocan domain layer (B-03, B-04, B-07, C-01 a C-06, A-09) pueden
iniciarse en paralelo sin esperar validación clínica.
