"""
Base de datos nutricional de ingredientes — NutriVet.IA

Fuentes:
- USDA FoodData Central (FDC) 2024
- NRC 2006 Nutrient Requirements of Dogs and Cats
- Small Animal Clinical Nutrition 5th Ed. (Hand et al.)
- AAFCO 2023 Official Publication
- Tablas de composición de alimentos ICBF Colombia 2015
- FAO LATINFOODS

Todos los valores son por 100g de peso en crudo, salvo donde se indica (cocido).
Unidades: kcal, g, mg según columna.

NUNCA modificar los valores de TOXIC_GRAY_ZONE sin validación de Lady Carolina Castañeda (MV).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AnimalProtein:
    """Perfil nutricional de proteína animal por 100g crudo."""
    nombre: str
    aliases: list[str]
    kcal: float
    proteina_g: float
    grasa_g: float
    carbohidratos_g: float
    calcio_mg: float
    fosforo_mg: float
    zinc_mg: float
    hierro_mg: float
    taurina_mg: Optional[float]       # None = no aplica o sin dato confiable
    omega3_epa_dha_mg: Optional[float]  # EPA+DHA combinados
    notas: str = ""


@dataclass(frozen=True)
class PlantFood:
    """Perfil nutricional de vegetal, cereal o fruta por 100g crudo (o cocido si se indica)."""
    nombre: str
    aliases: list[str]
    estado: str                        # "crudo" | "cocido"
    kcal: float
    proteina_g: float
    carbohidratos_g: float
    fibra_g: float
    calcio_mg: float
    fosforo_mg: float
    indice_glucemico: Optional[int]    # None = sin dato validado
    notas: str = ""


@dataclass(frozen=True)
class Fat:
    """Perfil nutricional de grasa/aceite por 100 ml (líquidos) o 100g (sólidos)."""
    nombre: str
    aliases: list[str]
    unidad: str                        # "100ml" | "100g"
    kcal: float
    grasa_total_g: float
    saturada_g: float
    omega3_g: float
    omega6_g: float
    omega9_g: float
    notas: str = ""


@dataclass(frozen=True)
class Supplement:
    """Suplemento de uso veterinario común en LATAM."""
    nombre: str
    aliases: list[str]
    funcion: str
    dosis_perro_mg_kg_dia: str         # rango como string p.ej. "50-100"
    dosis_gato_mg_kg_dia: str
    contraindicaciones: list[str]
    notas: str = ""


@dataclass(frozen=True)
class DangerousFood:
    """Alimento peligroso — zona gris y tóxicos confirmados."""
    nombre: str
    aliases: list[str]
    nivel_riesgo: str                  # "LETAL" | "ALTO" | "MODERADO" | "BAJO"
    especie_afectada: str              # "perros" | "gatos" | "ambos"
    mecanismo: str
    dosis_toxica: str
    que_hacer: str
    notas: str = ""


# ---------------------------------------------------------------------------
# TABLA 1 — PROTEÍNAS ANIMALES
# Fuentes: USDA FDC, Tabela TACO Brasil, ICBF Colombia
# ---------------------------------------------------------------------------

PROTEINAS_ANIMALES: list[AnimalProtein] = [

    # ── AVES ────────────────────────────────────────────────────────────────

    AnimalProtein(
        nombre="Pechuga de pollo sin piel",
        aliases=["pollo pechuga", "pecho de pollo", "filete de pollo"],
        kcal=110.0,
        proteina_g=23.1,
        grasa_g=1.2,
        carbohidratos_g=0.0,
        calcio_mg=11.0,
        fosforo_mg=220.0,
        zinc_mg=0.9,
        hierro_mg=0.7,
        taurina_mg=62.0,
        omega3_epa_dha_mg=30.0,
        notas="Fuente magra estándar. Relación Ca:P ≈ 1:20 — requiere suplemento de calcio en BARF.",
    ),

    AnimalProtein(
        nombre="Muslo de pollo sin piel",
        aliases=["contra-muslo pollo", "pierna pollo sin piel"],
        kcal=170.0,
        proteina_g=19.7,
        grasa_g=9.7,
        carbohidratos_g=0.0,
        calcio_mg=11.0,
        fosforo_mg=196.0,
        zinc_mg=2.1,
        hierro_mg=1.1,
        taurina_mg=83.0,
        omega3_epa_dha_mg=80.0,
        notas="Mayor contenido graso que pechuga. Más palatabilidad. Buena fuente de zinc.",
    ),

    AnimalProtein(
        nombre="Muslo de pollo con piel",
        aliases=["pierna pollo con piel"],
        kcal=215.0,
        proteina_g=18.6,
        grasa_g=15.3,
        carbohidratos_g=0.0,
        calcio_mg=11.0,
        fosforo_mg=179.0,
        zinc_mg=1.9,
        hierro_mg=1.0,
        taurina_mg=80.0,
        omega3_epa_dha_mg=75.0,
        notas="Alta densidad calórica. Evitar en sobrepeso/obesidad o pancreático.",
    ),

    AnimalProtein(
        nombre="Pechuga de pollo con piel",
        aliases=["pecho de pollo con piel"],
        kcal=172.0,
        proteina_g=20.8,
        grasa_g=9.3,
        carbohidratos_g=0.0,
        calcio_mg=11.0,
        fosforo_mg=210.0,
        zinc_mg=1.0,
        hierro_mg=0.7,
        taurina_mg=65.0,
        omega3_epa_dha_mg=35.0,
        notas="Intermedia entre pechuga magra y muslo. Moderada en grasa.",
    ),

    AnimalProtein(
        nombre="Corazón de pollo",
        aliases=["corazones de pollo"],
        kcal=185.0,
        proteina_g=16.3,
        grasa_g=13.0,
        carbohidratos_g=0.1,
        calcio_mg=11.0,
        fosforo_mg=194.0,
        zinc_mg=6.3,
        hierro_mg=5.9,
        taurina_mg=681.0,
        omega3_epa_dha_mg=90.0,
        notas=(
            "FUENTE PRIMARIA de taurina en dietas BARF — crítico para gatos. "
            "No superar 15% del plan (alta grasa y hierro)."
        ),
    ),

    AnimalProtein(
        nombre="Hígado de pollo",
        aliases=["higaditos de pollo", "hígado de ave"],
        kcal=119.0,
        proteina_g=16.9,
        grasa_g=4.8,
        carbohidratos_g=0.9,
        calcio_mg=8.0,
        fosforo_mg=297.0,
        zinc_mg=3.9,
        hierro_mg=9.0,
        taurina_mg=110.0,
        omega3_epa_dha_mg=50.0,
        notas=(
            "Víscera de alta densidad nutricional. "
            "Limitar a 5-10% del plan — exceso de vitamina A causa hipervitaminosis. "
            "Alto en fósforo: restringir en enfermedad renal."
        ),
    ),

    AnimalProtein(
        nombre="Molleja de pollo",
        aliases=["mollejas", "ventrículo de pollo"],
        kcal=94.0,
        proteina_g=17.7,
        grasa_g=2.1,
        carbohidratos_g=0.0,
        calcio_mg=10.0,
        fosforo_mg=163.0,
        zinc_mg=3.0,
        hierro_mg=2.5,
        taurina_mg=130.0,
        omega3_epa_dha_mg=20.0,
        notas="Músculo liso. Magra y rica en taurina. Buena textura para masticación.",
    ),

    AnimalProtein(
        nombre="Pechuga de pavo",
        aliases=["pavo pechuga", "filete de pavo"],
        kcal=104.0,
        proteina_g=22.4,
        grasa_g=1.0,
        carbohidratos_g=0.0,
        calcio_mg=12.0,
        fosforo_mg=218.0,
        zinc_mg=1.5,
        hierro_mg=1.1,
        taurina_mg=55.0,
        omega3_epa_dha_mg=25.0,
        notas="Alternativa hipoalergénica al pollo. Perfil muy similar a pechuga de pollo.",
    ),

    AnimalProtein(
        nombre="Pato (pechuga)",
        aliases=["pechuga de pato", "duck breast"],
        kcal=201.0,
        proteina_g=18.3,
        grasa_g=14.0,
        carbohidratos_g=0.0,
        calcio_mg=11.0,
        fosforo_mg=203.0,
        zinc_mg=2.2,
        hierro_mg=2.7,
        taurina_mg=75.0,
        omega3_epa_dha_mg=120.0,
        notas="Alta en grasa y hierro. Proteína novel para casos de alergia al pollo.",
    ),

    AnimalProtein(
        nombre="Huevo entero crudo",
        aliases=["huevo de gallina", "huevo fresco"],
        kcal=143.0,
        proteina_g=12.6,
        grasa_g=9.5,
        carbohidratos_g=0.7,
        calcio_mg=56.0,
        fosforo_mg=198.0,
        zinc_mg=1.3,
        hierro_mg=1.8,
        taurina_mg=60.0,
        omega3_epa_dha_mg=30.0,
        notas=(
            "Proteína de referencia biológica (BV=100). "
            "Clara cruda contiene avidina (inhibe biotina) — preferir cocida o limitar a 2-3/semana crudos. "
            "Yema cruda es segura."
        ),
    ),

    AnimalProtein(
        nombre="Clara de huevo",
        aliases=["albúmina de huevo", "blanco de huevo"],
        kcal=52.0,
        proteina_g=10.9,
        grasa_g=0.2,
        carbohidratos_g=0.7,
        calcio_mg=7.0,
        fosforo_mg=15.0,
        zinc_mg=0.0,
        hierro_mg=0.1,
        taurina_mg=0.0,
        omega3_epa_dha_mg=0.0,
        notas="Cruda: contiene avidina que bloquea biotina. Cocida: segura y excelente fuente de proteína magra.",
    ),

    AnimalProtein(
        nombre="Yema de huevo",
        aliases=["yema", "yolk"],
        kcal=322.0,
        proteina_g=15.9,
        grasa_g=26.5,
        carbohidratos_g=3.6,
        calcio_mg=129.0,
        fosforo_mg=390.0,
        zinc_mg=2.9,
        hierro_mg=2.7,
        taurina_mg=150.0,
        omega3_epa_dha_mg=150.0,
        notas="Alta densidad calórica y nutricional. Fuente de colina y luteína. Limitar en hiperlipidemia.",
    ),

    # ── RES/VACUNO ───────────────────────────────────────────────────────────

    AnimalProtein(
        nombre="Carne magra de res",
        aliases=["lomo de res", "falda magra", "carne de vacuno magra", "carne molida magra"],
        kcal=143.0,
        proteina_g=21.4,
        grasa_g=5.9,
        carbohidratos_g=0.0,
        calcio_mg=9.0,
        fosforo_mg=198.0,
        zinc_mg=4.5,
        hierro_mg=2.1,
        taurina_mg=38.0,
        omega3_epa_dha_mg=15.0,
        notas="Buena fuente de zinc y hierro hemo. Perfil estándar para planes adultos.",
    ),

    AnimalProtein(
        nombre="Carne grasa de res",
        aliases=["costilla de res", "carne de res con grasa", "asado de tira"],
        kcal=291.0,
        proteina_g=17.5,
        grasa_g=24.5,
        carbohidratos_g=0.0,
        calcio_mg=9.0,
        fosforo_mg=162.0,
        zinc_mg=3.8,
        hierro_mg=1.8,
        taurina_mg=32.0,
        omega3_epa_dha_mg=30.0,
        notas="Alta en calorías. Evitar en pancreático, hepático/hiperlipidemia y sobrepeso.",
    ),

    AnimalProtein(
        nombre="Corazón de res",
        aliases=["corazón vacuno", "bofe de res"],
        kcal=112.0,
        proteina_g=17.7,
        grasa_g=3.9,
        carbohidratos_g=0.1,
        calcio_mg=8.0,
        fosforo_mg=212.0,
        zinc_mg=1.8,
        hierro_mg=4.3,
        taurina_mg=862.0,
        omega3_epa_dha_mg=65.0,
        notas=(
            "Mayor concentración de taurina en carnes rojas. "
            "Músculo cardíaco magro — excelente para planes BARF. "
            "Hasta 20% del plan."
        ),
    ),

    AnimalProtein(
        nombre="Hígado de res",
        aliases=["hígado bovino", "hígado vacuno", "bofe de res — diferente al hígado"],
        kcal=135.0,
        proteina_g=20.4,
        grasa_g=3.6,
        carbohidratos_g=3.9,
        calcio_mg=5.0,
        fosforo_mg=387.0,
        zinc_mg=4.0,
        hierro_mg=6.5,
        taurina_mg=40.0,
        omega3_epa_dha_mg=0.0,
        notas=(
            "Órgano más denso nutricionalmente. Máximo 5% del plan total. "
            "Exceso → hipervitaminosis A (tóxico acumulativo). "
            "Muy alto en fósforo — contraindicado en renal."
        ),
    ),

    AnimalProtein(
        nombre="Riñón de res",
        aliases=["riñones de res", "riñón bovino"],
        kcal=99.0,
        proteina_g=17.4,
        grasa_g=3.1,
        carbohidratos_g=0.3,
        calcio_mg=13.0,
        fosforo_mg=257.0,
        zinc_mg=1.9,
        hierro_mg=4.6,
        taurina_mg=250.0,
        omega3_epa_dha_mg=40.0,
        notas=(
            "Alto en purinas — evitar en cistitis/enfermedad urinaria (cálculos urato). "
            "Alto en fósforo — restringir en enfermedad renal. "
            "Máximo 10% del plan."
        ),
    ),

    AnimalProtein(
        nombre="Tripa de res",
        aliases=["mondongo", "librillo", "panza de res", "callos", "tripa verde BARF"],
        kcal=85.0,
        proteina_g=12.1,
        grasa_g=3.5,
        carbohidratos_g=0.0,
        calcio_mg=13.0,
        fosforo_mg=100.0,
        zinc_mg=2.0,
        hierro_mg=1.0,
        taurina_mg=50.0,
        omega3_epa_dha_mg=10.0,
        notas=(
            "En BARF se usa tripa verde (sin lavar/blanquear) por enzimas digestivas y microbioma. "
            "La tripa vendida en mercado popular está blanqueada — menor valor enzimático. "
            "Excelente digestibilidad. Hasta 20% del plan."
        ),
    ),

    # ── CERDO ────────────────────────────────────────────────────────────────

    AnimalProtein(
        nombre="Lomo de cerdo magro",
        aliases=["solomo de cerdo", "lomo de marrano", "carne de cerdo magra"],
        kcal=143.0,
        proteina_g=21.2,
        grasa_g=6.0,
        carbohidratos_g=0.0,
        calcio_mg=9.0,
        fosforo_mg=220.0,
        zinc_mg=1.8,
        hierro_mg=0.9,
        taurina_mg=50.0,
        omega3_epa_dha_mg=10.0,
        notas=(
            "SIEMPRE cocinar bien (≥74°C) para eliminar Trichinella spiralis y Toxoplasma. "
            "NUNCA crudo en planes BARF — riesgo zoonótico real. "
            "Excluir en planes para gatos salvo cocido."
        ),
    ),

    AnimalProtein(
        nombre="Corazón de cerdo",
        aliases=["corazón de marrano"],
        kcal=118.0,
        proteina_g=17.3,
        grasa_g=4.8,
        carbohidratos_g=0.2,
        calcio_mg=7.0,
        fosforo_mg=205.0,
        zinc_mg=1.7,
        hierro_mg=4.2,
        taurina_mg=520.0,
        omega3_epa_dha_mg=30.0,
        notas="Igual advertencia que lomo: cocinar a temperatura segura. Buena fuente de taurina cocida.",
    ),

    AnimalProtein(
        nombre="Hígado de cerdo",
        aliases=["hígado de marrano"],
        kcal=134.0,
        proteina_g=20.1,
        grasa_g=3.7,
        carbohidratos_g=3.5,
        calcio_mg=6.0,
        fosforo_mg=362.0,
        zinc_mg=4.2,
        hierro_mg=18.0,
        taurina_mg=35.0,
        omega3_epa_dha_mg=0.0,
        notas=(
            "Altísimo en hierro — riesgo de toxicidad por hierro si se usa en exceso. "
            "Máximo 5% del plan. Siempre cocinar."
        ),
    ),

    # ── PESCADOS ─────────────────────────────────────────────────────────────

    AnimalProtein(
        nombre="Sardina enlatada en agua",
        aliases=["sardinas en lata", "sardineta"],
        kcal=108.0,
        proteina_g=19.4,
        grasa_g=3.3,
        carbohidratos_g=0.0,
        calcio_mg=382.0,
        fosforo_mg=490.0,
        zinc_mg=1.5,
        hierro_mg=2.9,
        taurina_mg=130.0,
        omega3_epa_dha_mg=1480.0,
        notas=(
            "Mejor fuente de omega-3 accesible en LATAM. El calcio incluye la espina blanda. "
            "Elegir en agua, no en aceite ni en salsa de tomate (sal). "
            "Alta en fósforo — restringir en enfermedad renal."
        ),
    ),

    AnimalProtein(
        nombre="Atún enlatado en agua",
        aliases=["atún en lata", "tuna"],
        kcal=86.0,
        proteina_g=19.4,
        grasa_g=0.5,
        carbohidratos_g=0.0,
        calcio_mg=15.0,
        fosforo_mg=210.0,
        zinc_mg=0.8,
        hierro_mg=1.3,
        taurina_mg=170.0,
        omega3_epa_dha_mg=220.0,
        notas=(
            "GATOS: no dar en exceso — adicción (anorexia selectiva) y déficit de vitamina E. "
            "Máximo 2-3 veces/semana en gatos. Mercurio moderado — no más del 30% de la proteína. "
            "Para perros: seguro con moderación."
        ),
    ),

    AnimalProtein(
        nombre="Salmón fresco",
        aliases=["filete de salmón", "salmon"],
        kcal=208.0,
        proteina_g=20.4,
        grasa_g=13.4,
        carbohidratos_g=0.0,
        calcio_mg=12.0,
        fosforo_mg=252.0,
        zinc_mg=0.6,
        hierro_mg=0.8,
        taurina_mg=100.0,
        omega3_epa_dha_mg=2260.0,
        notas=(
            "PERROS: NUNCA salmón crudo del Pacífico Norte (riesgo Neorickettsia helminthoeca — "
            "enfermedad del salmón, letal). En Colombia/LATAM el riesgo es menor pero cocinar es prudente. "
            "GATOS: siempre cocido. Mejor fuente de EPA+DHA del mercado."
        ),
    ),

    AnimalProtein(
        nombre="Tilapia",
        aliases=["mojarra", "tilapia roja", "tilapia nilótica"],
        kcal=96.0,
        proteina_g=20.1,
        grasa_g=1.7,
        carbohidratos_g=0.0,
        calcio_mg=10.0,
        fosforo_mg=170.0,
        zinc_mg=0.4,
        hierro_mg=0.6,
        taurina_mg=60.0,
        omega3_epa_dha_mg=115.0,
        notas=(
            "Disponibilidad muy alta en Colombia (crianza local). "
            "Perfil omega-3 bajo comparado con salmón. Magra y de bajo costo. "
            "Siempre cocinar — peces de agua dulce pueden tener parásitos."
        ),
    ),

    AnimalProtein(
        nombre="Trucha",
        aliases=["trucha arco iris", "trout"],
        kcal=141.0,
        proteina_g=19.9,
        grasa_g=6.2,
        carbohidratos_g=0.0,
        calcio_mg=20.0,
        fosforo_mg=226.0,
        zinc_mg=0.9,
        hierro_mg=0.7,
        taurina_mg=90.0,
        omega3_epa_dha_mg=900.0,
        notas=(
            "Disponible en Colombia (Nariño, Boyacá). "
            "Mayor omega-3 que tilapia. Siempre cocinar."
        ),
    ),

    AnimalProtein(
        nombre="Bagre",
        aliases=["catfish", "bagre de río", "capaz"],
        kcal=116.0,
        proteina_g=18.4,
        grasa_g=4.6,
        carbohidratos_g=0.0,
        calcio_mg=10.0,
        fosforo_mg=184.0,
        zinc_mg=0.9,
        hierro_mg=0.4,
        taurina_mg=50.0,
        omega3_epa_dha_mg=300.0,
        notas="Pez de río, disponible en Llanos y Costa. Siempre cocinar — parásitos de agua dulce.",
    ),

    # ── OTROS ────────────────────────────────────────────────────────────────

    AnimalProtein(
        nombre="Conejo",
        aliases=["carne de conejo", "rabbit"],
        kcal=136.0,
        proteina_g=20.1,
        grasa_g=5.6,
        carbohidratos_g=0.0,
        calcio_mg=19.0,
        fosforo_mg=218.0,
        zinc_mg=1.3,
        hierro_mg=1.9,
        taurina_mg=42.0,
        omega3_epa_dha_mg=30.0,
        notas=(
            "Proteína novel — excelente para casos de alergia a pollo y res. "
            "Baja en grasa. Alta digestibilidad. Disponible en Colombia (mercados regionales)."
        ),
    ),

    AnimalProtein(
        nombre="Cordero",
        aliases=["carne de cordero", "borrego", "lamb"],
        kcal=258.0,
        proteina_g=16.6,
        grasa_g=21.0,
        carbohidratos_g=0.0,
        calcio_mg=12.0,
        fosforo_mg=173.0,
        zinc_mg=3.4,
        hierro_mg=1.7,
        taurina_mg=47.0,
        omega3_epa_dha_mg=110.0,
        notas=(
            "Proteína novel para alergias múltiples. Alta en grasa — limitar en pancreático y obesidad. "
            "Disponibilidad limitada en Colombia; más accesible en Argentina, Chile, Uruguay."
        ),
    ),
]


# ---------------------------------------------------------------------------
# TABLA 2 — VEGETALES, CEREALES Y FRUTAS
# ---------------------------------------------------------------------------

ALIMENTOS_VEGETALES: list[PlantFood] = [

    # ── VEGETALES ────────────────────────────────────────────────────────────

    PlantFood(
        nombre="Zanahoria",
        aliases=["carrot", "zanahoria amarilla"],
        estado="crudo",
        kcal=41.0,
        proteina_g=0.9,
        carbohidratos_g=9.6,
        fibra_g=2.8,
        calcio_mg=33.0,
        fosforo_mg=35.0,
        indice_glucemico=16,
        notas=(
            "Excelente fuente de betacaroteno (perros lo convierten en vitamina A; gatos NO — "
            "gatos son carnívoros obligados y necesitan retinol preformado). "
            "Alta palatabilidad. Rallar o cocinar para mejorar digestibilidad."
        ),
    ),

    PlantFood(
        nombre="Ahuyama",
        aliases=["zapallo", "calabaza", "auyama", "squash", "pumpkin"],
        estado="crudo",
        kcal=26.0,
        proteina_g=1.0,
        carbohidratos_g=6.5,
        fibra_g=0.5,
        calcio_mg=21.0,
        fosforo_mg=44.0,
        indice_glucemico=75,
        notas=(
            "Alias regionales: ahuyama (CO), zapallo (AR/PE), calabaza (MX). "
            "Excelente para estreñimiento y diarrea (fibra soluble). "
            "IG alto — limitar en diabético."
        ),
    ),

    PlantFood(
        nombre="Espinaca",
        aliases=["espinacas", "spinach"],
        estado="crudo",
        kcal=23.0,
        proteina_g=2.9,
        carbohidratos_g=3.6,
        fibra_g=2.2,
        calcio_mg=99.0,
        fosforo_mg=49.0,
        indice_glucemico=15,
        notas=(
            "OXALATOS ALTOS — contraindicada en cistitis/enfermedad urinaria (cálculos de oxalato). "
            "Limitar a pequeñas cantidades en casos renales. "
            "No dar a gatos con enfermedad urinaria."
        ),
    ),

    PlantFood(
        nombre="Brócoli",
        aliases=["brécol", "broccoli"],
        estado="crudo",
        kcal=34.0,
        proteina_g=2.8,
        carbohidratos_g=6.6,
        fibra_g=2.6,
        calcio_mg=47.0,
        fosforo_mg=66.0,
        indice_glucemico=15,
        notas=(
            "Contiene isotiocianatos — irritantes gástricos en cantidades altas. "
            "Máximo 10% del plan. Cocinar suaviza los compuestos. "
            "Gas intestinal frecuente — monitorear en mascotas con gastritis."
        ),
    ),

    PlantFood(
        nombre="Pepino",
        aliases=["pepino cohombro", "cucumber", "pepino de agua"],
        estado="crudo",
        kcal=15.0,
        proteina_g=0.7,
        carbohidratos_g=3.6,
        fibra_g=0.5,
        calcio_mg=16.0,
        fosforo_mg=24.0,
        indice_glucemico=15,
        notas="Muy bajo en calorías — excelente para hidratación y snack de bajo IG. Seguro para ambas especies.",
    ),

    PlantFood(
        nombre="Apio",
        aliases=["celery", "apio españa"],
        estado="crudo",
        kcal=16.0,
        proteina_g=0.7,
        carbohidratos_g=3.0,
        fibra_g=1.6,
        calcio_mg=40.0,
        fosforo_mg=24.0,
        indice_glucemico=15,
        notas=(
            "Compuestos furanocumarínicos — fotosensibilizador en exposición a sol. "
            "Seguro en cantidades normales de dieta. Efecto diurético leve."
        ),
    ),

    PlantFood(
        nombre="Remolacha",
        aliases=["betabel", "beet", "betarraga", "remolacha roja"],
        estado="crudo",
        kcal=43.0,
        proteina_g=1.6,
        carbohidratos_g=9.6,
        fibra_g=2.8,
        calcio_mg=16.0,
        fosforo_mg=40.0,
        indice_glucemico=64,
        notas=(
            "ALTA EN OXALATOS — contraindicada en cistitis/enfermedad urinaria y cálculos de oxalato. "
            "IG moderado-alto — limitar en diabético. "
            "Coloración roja en orina/heces (betanina) — no confundir con sangre."
        ),
    ),

    PlantFood(
        nombre="Habichuela",
        aliases=["judías verdes", "vainita", "ejotes", "french beans", "green beans"],
        estado="crudo",
        kcal=31.0,
        proteina_g=1.8,
        carbohidratos_g=7.0,
        fibra_g=2.7,
        calcio_mg=37.0,
        fosforo_mg=38.0,
        indice_glucemico=15,
        notas=(
            "Alias: habichuela (CO), ejotes (MX), vainita (PE/EC). "
            "Excelente sustituto de snacks. Muy bajo IG. Segura para ambas especies."
        ),
    ),

    PlantFood(
        nombre="Chayote",
        aliases=["cidra", "guatila", "papa del aire", "chayota", "christophene"],
        estado="crudo",
        kcal=19.0,
        proteina_g=0.8,
        carbohidratos_g=4.5,
        fibra_g=1.7,
        calcio_mg=17.0,
        fosforo_mg=18.0,
        indice_glucemico=15,
        notas=(
            "Alias: chayote (MX), guatila/cidra (CO), papa del aire (CO regional). "
            "Muy bajo en calorías. Bien tolerado. Poca investigación en dietas vet."
        ),
    ),

    PlantFood(
        nombre="Papa",
        aliases=["patata", "potato", "papa criolla — diferente perfil"],
        estado="crudo",
        kcal=77.0,
        proteina_g=2.0,
        carbohidratos_g=17.5,
        fibra_g=2.2,
        calcio_mg=12.0,
        fosforo_mg=57.0,
        indice_glucemico=78,
        notas=(
            "SIEMPRE cocinar — solanina en papa cruda y verde es tóxica. "
            "IG alto — limitar en diabético. "
            "Papa criolla (CO): kcal ≈ 70, mayor contenido de vitamina C."
        ),
    ),

    PlantFood(
        nombre="Batata",
        aliases=["camote", "sweet potato", "boniato", "ñame dulce"],
        estado="crudo",
        kcal=86.0,
        proteina_g=1.6,
        carbohidratos_g=20.1,
        fibra_g=3.0,
        calcio_mg=30.0,
        fosforo_mg=47.0,
        indice_glucemico=63,
        notas=(
            "Alias: batata (CO/VE), camote (MX/PE), boniato (CU/ES). "
            "IG moderado — mejor que papa para diabéticos. "
            "Oxalatos moderados. Cocinar siempre."
        ),
    ),

    PlantFood(
        nombre="Yuca",
        aliases=["mandioca", "cassava", "tapioca root", "yuca brava — diferente"],
        estado="crudo",
        kcal=160.0,
        proteina_g=1.4,
        carbohidratos_g=38.1,
        fibra_g=1.8,
        calcio_mg=16.0,
        fosforo_mg=27.0,
        indice_glucemico=94,
        notas=(
            "IG MUY ALTO — contraindicada en diabético. "
            "La yuca dulce (amarga = yuca brava) contiene glucósidos cianogénicos — "
            "en Colombia se usa la variedad dulce, pero cocinar es obligatorio. "
            "Alta densidad calórica — limitar en sobrepeso."
        ),
    ),

    PlantFood(
        nombre="Plátano verde",
        aliases=["plátano macho verde", "banana verde", "tostone"],
        estado="crudo",
        kcal=89.0,
        proteina_g=1.1,
        carbohidratos_g=22.8,
        fibra_g=2.6,
        calcio_mg=5.0,
        fosforo_mg=22.0,
        indice_glucemico=40,
        notas=(
            "IG BAJO en estado verde (almidón resistente). "
            "Cocinar o hervir antes de servir. "
            "Plátano maduro: IG sube a 65 y azúcares libres aumentan — no recomendado en diabético."
        ),
    ),

    PlantFood(
        nombre="Lechuga",
        aliases=["lettuce", "lechuga romana", "lechuga crespa"],
        estado="crudo",
        kcal=15.0,
        proteina_g=1.4,
        carbohidratos_g=2.9,
        fibra_g=1.3,
        calcio_mg=36.0,
        fosforo_mg=29.0,
        indice_glucemico=15,
        notas="Bajo valor calórico. Usada principalmente por textura y palatabilidad. Segura.",
    ),

    # ── GRANOS Y CEREALES (cocidos) ──────────────────────────────────────────

    PlantFood(
        nombre="Arroz blanco cocido",
        aliases=["arroz blanco", "arroz largo cocido"],
        estado="cocido",
        kcal=130.0,
        proteina_g=2.7,
        carbohidratos_g=28.2,
        fibra_g=0.4,
        calcio_mg=10.0,
        fosforo_mg=43.0,
        indice_glucemico=73,
        notas=(
            "Referencia por 100g cocido. Muy digestible — estándar en planes con gastritis. "
            "IG alto — evitar en diabético como fuente principal de carbohidrato."
        ),
    ),

    PlantFood(
        nombre="Arroz integral cocido",
        aliases=["arroz moreno cocido", "brown rice cooked"],
        estado="cocido",
        kcal=123.0,
        proteina_g=2.6,
        carbohidratos_g=25.6,
        fibra_g=1.8,
        calcio_mg=10.0,
        fosforo_mg=83.0,
        indice_glucemico=55,
        notas=(
            "Referencia por 100g cocido. Mayor fibra y micronutrientes que blanco. "
            "IG moderado. Mayor fósforo — restringir en enfermedad renal."
        ),
    ),

    PlantFood(
        nombre="Avena cocida",
        aliases=["avena en hojuelas cocida", "oatmeal", "porridge"],
        estado="cocido",
        kcal=71.0,
        proteina_g=2.5,
        carbohidratos_g=12.0,
        fibra_g=1.7,
        calcio_mg=9.0,
        fosforo_mg=77.0,
        indice_glucemico=55,
        notas=(
            "Referencia por 100g cocido (en agua). Beta-glucanos: efecto prebiótico y control glicémico. "
            "Excelente para estreñimiento. Gluten en poca cantidad — evitar en dermatitis atópica hasta descartar sensibilidad."
        ),
    ),

    PlantFood(
        nombre="Quinua cocida",
        aliases=["quinoa cocida", "quinua real"],
        estado="cocido",
        kcal=120.0,
        proteina_g=4.4,
        carbohidratos_g=21.3,
        fibra_g=2.8,
        calcio_mg=17.0,
        fosforo_mg=152.0,
        indice_glucemico=53,
        notas=(
            "Referencia por 100g cocido. Proteína completa (todos los aminoácidos esenciales). "
            "Lavar bien antes de cocinar — saponinas son irritantes. "
            "Mayor valor proteico que cereales. Disponible ampliamente en Colombia."
        ),
    ),

    # ── FRUTAS ───────────────────────────────────────────────────────────────

    PlantFood(
        nombre="Manzana sin semilla",
        aliases=["manzana roja", "manzana verde", "apple"],
        estado="crudo",
        kcal=52.0,
        proteina_g=0.3,
        carbohidratos_g=13.8,
        fibra_g=2.4,
        calcio_mg=6.0,
        fosforo_mg=11.0,
        indice_glucemico=36,
        notas=(
            "RETIRAR SIEMPRE semillas y carozo — contienen amigdalina (cianuro). "
            "Pulpa y piel: seguras. Excelente snack de bajo IG. "
            "Alta en fructosa — moderar en diabético."
        ),
    ),

    PlantFood(
        nombre="Pera",
        aliases=["pear", "pera de agua"],
        estado="crudo",
        kcal=57.0,
        proteina_g=0.4,
        carbohidratos_g=15.2,
        fibra_g=3.1,
        calcio_mg=9.0,
        fosforo_mg=12.0,
        indice_glucemico=38,
        notas="Retirar semillas. Segura en cantidades moderadas. Fibra soluble útil para tránsito.",
    ),

    PlantFood(
        nombre="Sandía sin semilla",
        aliases=["patilla", "melón de agua", "watermelon"],
        estado="crudo",
        kcal=30.0,
        proteina_g=0.6,
        carbohidratos_g=7.6,
        fibra_g=0.4,
        calcio_mg=7.0,
        fosforo_mg=11.0,
        indice_glucemico=72,
        notas=(
            "Alias: patilla (CO/VE). Retirar semillas y cáscara verde. "
            "IG alto pero carga glucémica baja por alto contenido de agua. "
            "Limitar en diabético. Excelente hidratación en calor."
        ),
    ),

    PlantFood(
        nombre="Arándanos",
        aliases=["blueberries", "mora azul", "arándano azul"],
        estado="crudo",
        kcal=57.0,
        proteina_g=0.7,
        carbohidratos_g=14.5,
        fibra_g=2.4,
        calcio_mg=6.0,
        fosforo_mg=12.0,
        indice_glucemico=53,
        notas=(
            "Ricos en antocianinas (antioxidantes). Beneficio en cistitis/ITU (inhiben adhesión de E. coli). "
            "Seguros para perros y gatos en cantidades pequeñas (snack). "
            "Disponibilidad creciente en Colombia (Boyacá)."
        ),
    ),

    PlantFood(
        nombre="Mango",
        aliases=["mango tommy", "mango criollo", "manga"],
        estado="crudo",
        kcal=60.0,
        proteina_g=0.8,
        carbohidratos_g=15.0,
        fibra_g=1.6,
        calcio_mg=11.0,
        fosforo_mg=14.0,
        indice_glucemico=51,
        notas=(
            "RETIRAR semilla y cáscara — amigdalina en semilla, urushiol en cáscara (pariente del veneno de hiedra). "
            "Pulpa: segura pero alta en azúcar. "
            "CONTRAINDICADO en diabético. Limitar a snack ocasional (20-30g)."
        ),
    ),
]


# ---------------------------------------------------------------------------
# TABLA 3 — GRASAS Y ACEITES
# ---------------------------------------------------------------------------

GRASAS_ACEITES: list[Fat] = [

    Fat(
        nombre="Aceite de oliva extra virgen",
        aliases=["AOVE", "olive oil"],
        unidad="100ml",
        kcal=884.0,
        grasa_total_g=100.0,
        saturada_g=13.8,
        omega3_g=0.8,
        omega6_g=9.8,
        omega9_g=73.0,
        notas=(
            "Rico en oleocantal (antiinflamatorio — beneficio en articular). "
            "No es la mejor fuente de omega-3 para mascotas. "
            "Dosis: 1 ml/10 kg/día como máximo. Añadir fría — el calor degrada polifenoles."
        ),
    ),

    Fat(
        nombre="Aceite de coco",
        aliases=["coconut oil", "aceite de coco virgen", "MCT oil"],
        unidad="100ml",
        kcal=862.0,
        grasa_total_g=100.0,
        saturada_g=86.5,
        omega3_g=0.0,
        omega6_g=1.8,
        omega9_g=6.3,
        notas=(
            "Alto en triglicéridos de cadena media (MCT) — fuente de energía rápida, "
            "posible beneficio cognitivo en neurodegenerativo (evidencia preliminar). "
            "MUY alta en saturadas — usar con precaución en hiperlipidemia/pancreático. "
            "Dosis: 1/4 cucharadita/10 kg/día. NO reemplaza omega-3 de cadena larga."
        ),
    ),

    Fat(
        nombre="Aceite de girasol",
        aliases=["sunflower oil"],
        unidad="100ml",
        kcal=884.0,
        grasa_total_g=100.0,
        saturada_g=10.3,
        omega3_g=0.1,
        omega6_g=65.7,
        omega9_g=20.5,
        notas=(
            "MUY alto en omega-6 (LA). Usar solo cuando se necesita aumentar omega-6 "
            "específicamente (piel/dermatitis). "
            "El exceso de omega-6 es proinflamatorio — no combinar con deficiencia de omega-3."
        ),
    ),

    Fat(
        nombre="Aceite de linaza",
        aliases=["aceite de lino", "flaxseed oil", "linseed oil"],
        unidad="100ml",
        kcal=884.0,
        grasa_total_g=100.0,
        saturada_g=9.0,
        omega3_g=53.3,
        omega6_g=12.7,
        omega9_g=18.5,
        notas=(
            "Fuente de ALA (omega-3 vegetal). IMPORTANTE: perros convierten ALA→EPA/DHA "
            "de forma muy ineficiente (~5-15%); gatos prácticamente NO. "
            "NO es sustituto del aceite de pescado para EPA+DHA. "
            "Útil como suplemento antioxidante de omega-3 vegetal en dietas mixtas."
        ),
    ),

    Fat(
        nombre="Aceite de sardinas",
        aliases=["aceite de pescado", "fish oil", "aceite omega-3"],
        unidad="100ml",
        kcal=902.0,
        grasa_total_g=100.0,
        saturada_g=22.6,
        omega3_g=29.9,
        omega6_g=1.7,
        omega9_g=24.2,
        notas=(
            "MEJOR fuente de EPA+DHA para suplementación. "
            "Dosis terapéutica: 50-100 mg EPA+DHA/kg/día. "
            "Conservar refrigerado — se oxida rápido. "
            "Suplementar con vitamina E cuando se usa crónicamente (evita oxidación)."
        ),
    ),

    Fat(
        nombre="Mantequilla de maní sin xilitol",
        aliases=["crema de maní", "peanut butter", "mantequilla de cacahuate"],
        unidad="100g",
        kcal=588.0,
        grasa_total_g=50.0,
        saturada_g=10.4,
        omega3_g=0.0,
        omega6_g=15.6,
        omega9_g=24.6,
        notas=(
            "VERIFICAR SIEMPRE que NO contenga xilitol — algunas marcas lo añaden "
            "como edulcorante (LETAL para perros). "
            "Alta en calorías y grasa — usar solo como premio ocasional. "
            "Máximo 1 cucharadita/día en perros medianos. "
            "Aflatoxinas: riesgo si es artesanal o de baja calidad."
        ),
    ),
]


# ---------------------------------------------------------------------------
# TABLA 4 — SUPLEMENTOS COMUNES EN LATAM
# ---------------------------------------------------------------------------

SUPLEMENTOS: list[Supplement] = [

    Supplement(
        nombre="Aceite de pescado (omega-3)",
        aliases=["fish oil", "aceite de sardinas", "omega-3 EPA DHA"],
        funcion=(
            "Antiinflamatorio — articular, piel/dermatitis, renal (disminuye proteinuria), "
            "cardíaco, neurológico. Mejora palatabilidad. "
            "EPA reduce producción de eicosanoides proinflamatorios."
        ),
        dosis_perro_mg_kg_dia="50-100 mg EPA+DHA/kg (mantenimiento: 50; terapéutico articular/renal: 100)",
        dosis_gato_mg_kg_dia="25-50 mg EPA+DHA/kg — gatos más sensibles a oxidación lipídica",
        contraindicaciones=[
            "Coagulopatías — altas dosis tienen efecto anticoagulante leve",
            "Pancreatitis activa — introducir gradualmente post-recuperación",
            "Combinación con anticoagulantes (warfarina) — monitorear",
        ],
        notas="Suplementar vitamina E (10 UI/g de aceite) en uso crónico para prevenir oxidación.",
    ),

    Supplement(
        nombre="Vitamina D3",
        aliases=["colecalciferol", "vitamin D3"],
        funcion=(
            "Regulación Ca/P, función inmune, cardíaca y muscular. "
            "Deficiencia frecuente en dietas caseras sin vísceras ni sol."
        ),
        dosis_perro_mg_kg_dia="NRC: 3.4 UI/kg/día (mínimo) — no superar 20 UI/kg/día",
        dosis_gato_mg_kg_dia="NRC: 3.0 UI/kg/día — gatos no sintetizan vitamina D cutánea",
        contraindicaciones=[
            "Enfermedad renal crónica — hipercalcemia agrava daño renal",
            "Hipercalcemia de cualquier causa",
            "Toxicidad: 100x la dosis normal → hipercalcemia severa",
        ],
        notas=(
            "La vitamina D2 (ergocalciferol) es menos eficiente en perros y gatos. "
            "Usar siempre D3. NUNCA usar rodenticidas con colecalciferol como fuente."
        ),
    ),

    Supplement(
        nombre="Vitamina E",
        aliases=["alfa-tocoferol", "tocopherol", "vitamin E"],
        funcion=(
            "Antioxidante principal — protege ácidos grasos poliinsaturados de oxidación. "
            "Beneficio en piel/dermatitis, inmunidad, neurodegenerativo."
        ),
        dosis_perro_mg_kg_dia="1-2 mg (como alfa-tocoferol) / kg / día",
        dosis_gato_mg_kg_dia="2 mg/kg/día — gatos más sensibles al estrés oxidativo",
        contraindicaciones=[
            "Coagulopatías en dosis muy altas (antagonismo vitamina K — raro)",
            "No superar 200 UI/kg/día",
        ],
        notas="Obligatorio cuando se suplementa aceite de pescado crónicamente.",
    ),

    Supplement(
        nombre="Calcio (carbonato cálcico)",
        aliases=["carbonato de calcio", "calcium carbonate", "cáscara de huevo molida"],
        funcion=(
            "Corrección de relación Ca:P en dietas BARF/caseras. "
            "Las carnes tienen Ca:P ≈ 1:20 — necesitan 900-1200 mg Ca por 100g de carne."
        ),
        dosis_perro_mg_kg_dia="120-130 mg Ca/kg/día (adulto) — 270 mg/kg/día (cachorro)",
        dosis_gato_mg_kg_dia="80-100 mg Ca/kg/día (adulto)",
        contraindicaciones=[
            "Dietas con huesos crudos ya incluidos — no doble suplementar",
            "Hipercalcemia",
            "Enfermedad renal con hiperfosfatemia — usar calcio como quelante de fósforo con supervisión",
        ],
        notas=(
            "Cáscara de huevo molida ≈ 2000 mg Ca / cucharadita (5g). "
            "1/2 cucharadita ≈ 1000 mg Ca — alternativa natural de bajo costo."
        ),
    ),

    Supplement(
        nombre="Calcio (lactato cálcico)",
        aliases=["calcium lactate", "lactato de calcio"],
        funcion="Alternativa al carbonato cuando hay problemas de absorción digestiva.",
        dosis_perro_mg_kg_dia="Equivalente a carbonato: calcular por contenido elemental de Ca",
        dosis_gato_mg_kg_dia="Equivalente a carbonato",
        contraindicaciones=["Hipercalcemia", "Enfermedad renal con hipercalcemia"],
        notas="Mejor absorción en pH gástrico alto. Menos eficiente como quelante de fósforo.",
    ),

    Supplement(
        nombre="Zinc (gluconato de zinc)",
        aliases=["zinc gluconate", "gluconato de zinc"],
        funcion=(
            "Piel/pelaje, sistema inmune, función reproductiva. "
            "Deficiencia frecuente en razas nórdicas (Husky, Malamute — síndrome de deficiencia de zinc)."
        ),
        dosis_perro_mg_kg_dia="1-2 mg Zn/kg/día (máximo 3 mg/kg/día)",
        dosis_gato_mg_kg_dia="0.5-1 mg Zn/kg/día",
        contraindicaciones=[
            "Toxicidad por exceso (hemólisis) — no superar dosis máxima",
            "No combinar con suplementos altos en calcio o hierro (compiten por absorción)",
        ],
        notas="Tocoferol mejora absorción del zinc. Síntomas de deficiencia: costras nasales, pelo opaco.",
    ),

    Supplement(
        nombre="Probióticos",
        aliases=["Lactobacillus", "Bifidobacterium", "pro-bióticos veterinarios"],
        funcion=(
            "Modulación microbioma intestinal — diarrea, gastritis, post-antibiótico, "
            "enfermedad inflamatoria intestinal (IBD), piel/dermatitis (eje intestino-piel)."
        ),
        dosis_perro_mg_kg_dia="1-10 billones UFC/día total (no por kg) — ajustar según cepa",
        dosis_gato_mg_kg_dia="1-5 billones UFC/día total",
        contraindicaciones=[
            "Inmunosupresión severa — riesgo teórico de translocación bacteriana",
            "Sepsis activa",
        ],
        notas=(
            "Cepas con evidencia en veterinaria: Enterococcus faecium SF68, "
            "Lactobacillus acidophilus, Bifidobacterium animalis. "
            "Guardar refrigerado. Introducir gradualmente."
        ),
    ),

    Supplement(
        nombre="Glucosamina + Condroitina",
        aliases=["glucosamine chondroitin", "gluco-condroitina"],
        funcion=(
            "Condroprotector — articular/osteoartritis. "
            "Reduce degradación del cartílago. Analgesia leve. "
            "Evidencia moderada en perros, menor en gatos."
        ),
        dosis_perro_mg_kg_dia="glucosamina: 20-25 mg/kg/día · condroitina: 5-10 mg/kg/día",
        dosis_gato_mg_kg_dia="glucosamina: 125-250 mg/día total · condroitina: 50-100 mg/día total",
        contraindicaciones=[
            "Diabetes — glucosamina puede afectar sensibilidad a insulina (monitorear)",
            "Alergia a mariscos (fuente del sulfato de glucosamina)",
        ],
        notas="Inicio de efecto a las 4-6 semanas. Combinar con omega-3 para mayor efecto antiinflamatorio.",
    ),

    Supplement(
        nombre="MSM (metilsulfonilmetano)",
        aliases=["methylsulfonylmethane", "MSM"],
        funcion=(
            "Antiinflamatorio articular — complemento de glucosamina/condroitina. "
            "Fuente de azufre orgánico para síntesis de colágeno."
        ),
        dosis_perro_mg_kg_dia="50 mg/kg/día (máximo 100 mg/kg/día)",
        dosis_gato_mg_kg_dia="25-50 mg/kg/día",
        contraindicaciones=["Evitar en gestación — datos insuficientes", "Falla renal severa"],
        notas="Bien tolerado. Rara vez causa molestias GI. Usualmente en combinación con glucosamina.",
    ),

    Supplement(
        nombre="Aceite de coco (MCT)",
        aliases=["coconut oil", "aceite de coco virgen"],
        funcion=(
            "Energía de rápida disponibilidad (MCT). Posible efecto cognitivo en "
            "neurodegenerativo/disfunción cognitiva canina (evidencia preliminar). "
            "Antimicrobiano superficial (ácido láurico)."
        ),
        dosis_perro_mg_kg_dia="1 ml/10 kg/día → incrementar gradualmente hasta 1 ml/kg/día máximo",
        dosis_gato_mg_kg_dia="0.5 ml/día total — gatos toleran peor grasas saturadas",
        contraindicaciones=[
            "Pancreatitis — alto en grasas saturadas",
            "Hiperlipidemia",
            "Obesidad — alta densidad calórica",
        ],
        notas="Introducir muy gradualmente — la introducción rápida causa diarrea por saturación de MCT.",
    ),

    Supplement(
        nombre="Espirulina",
        aliases=["spirulina", "Arthrospira platensis"],
        funcion=(
            "Antioxidante, antiinflamatorio, inmunomodulador. "
            "Rica en proteína (60-70%), betacaroteno, ficocianina, vitaminas del grupo B. "
            "Uso creciente en planes funcionales."
        ),
        dosis_perro_mg_kg_dia="50-100 mg/kg/día",
        dosis_gato_mg_kg_dia="25-50 mg/kg/día",
        contraindicaciones=[
            "Fenilcetonuria (fuente de fenilalanina)",
            "Autoimmunidad activa — puede estimular sistema inmune",
            "Verificar que no contenga microcistinas (contaminación con cianobacterias tóxicas)",
        ],
        notas="Adquirir de fuentes certificadas. Contaminación con cianobacterias es riesgo real en productos no controlados.",
    ),

    Supplement(
        nombre="Levadura de cerveza",
        aliases=["brewer's yeast", "levadura seca de cerveza", "Saccharomyces cerevisiae"],
        funcion=(
            "Fuente de vitaminas B (B1, B2, B3, B5, B6, B7, B9), zinc, selenio. "
            "Prebiótico (beta-glucanos). Mejora pelaje y piel."
        ),
        dosis_perro_mg_kg_dia="100-200 mg/kg/día (o 1/4 cucharadita por 10 kg)",
        dosis_gato_mg_kg_dia="50-100 mg/kg/día",
        contraindicaciones=[
            "Levadura activa sin hornear — NUNCA dar levadura viva (produce gas en GI)",
            "Candidiasis activa — teórico (no es la misma especie pero precaución)",
            "Sensibilidad a levaduras",
        ],
        notas="Solo levadura INACTIVA/SECA. Alta en fósforo — restringir en enfermedad renal.",
    ),
]


# ---------------------------------------------------------------------------
# TABLA 5 — ALIMENTOS PELIGROSOS Y ZONA GRIS
# ---------------------------------------------------------------------------

ALIMENTOS_PELIGROSOS: list[DangerousFood] = [

    DangerousFood(
        nombre="Chocolate oscuro",
        aliases=["dark chocolate", "chocolate negro", "cacao puro"],
        nivel_riesgo="LETAL",
        especie_afectada="ambos",
        mecanismo=(
            "Teobromina y cafeína — inhibidores de fosfodiesterasa. "
            "Perros metabolizan teobromina muy lentamente (vida media 17.5h). "
            "Taquicardia, convulsiones, falla cardíaca, hipotermia."
        ),
        dosis_toxica=(
            "Chocolate oscuro (70%+): 1.3 mg teobromina/kg ya causa síntomas leves. "
            "Tóxico real: >20 mg teobromina/kg. Letal: >100-200 mg/kg. "
            "1g chocolate oscuro ≈ 16 mg teobromina → 6g/kg ya es grave."
        ),
        que_hacer=(
            "URGENCIA VETERINARIA INMEDIATA. Si ingestión < 2h: inducción de vómito "
            "(solo si veterinario lo indica). Carbón activado. Monitoreo cardíaco. "
            "No esperar síntomas."
        ),
        notas="Chocolate oscuro y de repostería son los más peligrosos. Ver tabla de teobromina por tipo.",
    ),

    DangerousFood(
        nombre="Chocolate con leche",
        aliases=["milk chocolate", "chocolate de leche"],
        nivel_riesgo="ALTO",
        especie_afectada="ambos",
        mecanismo="Igual que chocolate oscuro — menor concentración de teobromina pero igualmente peligroso en cantidad.",
        dosis_toxica=(
            "≈2.4 mg teobromina/g. Dosis tóxica: ~25g/kg en perros medianos. "
            "Una tableta de 100g puede ser grave para perros <10 kg."
        ),
        que_hacer="Igual que chocolate oscuro — urgencia veterinaria. No minimizar.",
        notas="El 'poco chocolate' de los dueños puede ser mucho para el tamaño del perro.",
    ),

    DangerousFood(
        nombre="Chocolate blanco",
        aliases=["white chocolate"],
        nivel_riesgo="MODERADO",
        especie_afectada="ambos",
        mecanismo=(
            "Contiene grasa de cacao y azúcar pero casi sin teobromina (<0.1 mg/g). "
            "Riesgo principal: pancreatitis por alta grasa, no toxicidad por teobromina."
        ),
        dosis_toxica="Sin dosis tóxica definida por teobromina. Riesgo GI y pancreatitis.",
        que_hacer="Monitorear signos de pancreatitis. Consultar vet si ingirió >10g/kg.",
        notas="Menos tóxico pero no seguro. Los dueños suelen confundirlo con el oscuro.",
    ),

    DangerousFood(
        nombre="Uvas",
        aliases=["uva", "grapes", "uva verde", "uva roja", "uva sin semilla"],
        nivel_riesgo="LETAL",
        especie_afectada="perros",
        mecanismo=(
            "Toxina no identificada completamente (posible tartrato de potasio o micotoxinas). "
            "Produce falla renal aguda. No hay dosis segura establecida. "
            "Algunos perros toleran dosis bajas; otros fallan con 1-2 uvas — no predecible."
        ),
        dosis_toxica=(
            "No hay dosis segura. Casos reportados con 1-2 uvas en perros pequeños. "
            "En general: >0.3g/kg ya es preocupante. >11-30 g/kg: falla renal severa."
        ),
        que_hacer=(
            "URGENCIA VETERINARIA INMEDIATA — no esperar síntomas. "
            "Inducción de vómito en < 2h si vet lo indica. Carbón activado. "
            "Fluidos IV. Monitoreo renal 48-72h."
        ),
        notas="Gatos: mucho menos reportado pero precaución. Pasas son más concentradas y peligrosas.",
    ),

    DangerousFood(
        nombre="Pasas",
        aliases=["raisins", "uva pasa", "sultanas", "currants"],
        nivel_riesgo="LETAL",
        especie_afectada="perros",
        mecanismo="Igual que uvas — concentración de la toxina es mayor por deshidratación.",
        dosis_toxica=(
            "Más peligrosas que uvas frescas. 2.8g/kg ya puede causar falla renal. "
            "En perros pequeños (<5kg): incluso 1-2 pasas es una emergencia."
        ),
        que_hacer="URGENCIA VETERINARIA INMEDIATA. Mismo protocolo que uvas.",
        notas="Frecuentes en productos horneados: panettone, galletas, muesli — alertar a los dueños.",
    ),

    DangerousFood(
        nombre="Cebolla cruda",
        aliases=["cebolla de bulbo", "cebolla cabezona", "onion"],
        nivel_riesgo="ALTO",
        especie_afectada="ambos",
        mecanismo=(
            "Compuestos organosulfurados (tiosulfatos) → oxidación de hemoglobina → "
            "cuerpos de Heinz → anemia hemolítica. "
            "Gatos son 2-3x más sensibles que perros."
        ),
        dosis_toxica=(
            "Perros: >0.5% del peso corporal en ingesta única = síntomas. "
            "15-30 g/kg de cebolla cruda: anemia hemolítica clínica. "
            "Gatos: >5g/kg ya es preocupante."
        ),
        que_hacer=(
            "Consulta veterinaria urgente. Si < 2h: inducción de vómito. "
            "Hemograma seriado. Soporte con fluidos y vitamina C. "
            "Transfusión en casos severos."
        ),
        notas="La toxicidad es acumulativa — pequeñas dosis diarias durante semanas también causan daño.",
    ),

    DangerousFood(
        nombre="Cebolla cocida",
        aliases=["cebolla salteada", "cebolla en sopa", "sopa de cebolla"],
        nivel_riesgo="ALTO",
        especie_afectada="ambos",
        mecanismo="El calor NO destruye los compuestos tóxicos — igual de peligrosa que cruda.",
        dosis_toxica="Igual que cebolla cruda. La cocción no reduce la toxicidad.",
        que_hacer="Igual que cebolla cruda.",
        notas="Los dueños suelen creer que cocida es segura — corrección crítica en educación.",
    ),

    DangerousFood(
        nombre="Cebolla en polvo",
        aliases=["cebolla deshidratada", "onion powder"],
        nivel_riesgo="LETAL",
        especie_afectada="ambos",
        mecanismo="Igual que cebolla — la concentración es 5x mayor que en fresco.",
        dosis_toxica="5x más potente que cebolla fresca. Incluso cantidades de condimento son peligrosas.",
        que_hacer="URGENCIA VETERINARIA INMEDIATA. Presente en muchos sazonadores comerciales.",
        notas="Frecuente en: sopas de sobre, caldos, condimentos, comida procesada humana dada a mascotas.",
    ),

    DangerousFood(
        nombre="Ajo crudo",
        aliases=["garlic", "Allium sativum"],
        nivel_riesgo="ALTO",
        especie_afectada="ambos",
        mecanismo=(
            "Mismo mecanismo que cebolla — disulfuros y tiosulfatos. "
            "El ajo es 3-5x más potente que la cebolla por peso. "
            "Gatos son más sensibles."
        ),
        dosis_toxica=(
            "Perros: 15-30 g/kg de ajo crudo (pero acumulación con dosis menores). "
            "1 diente de ajo (≈4g) en un perro de 5 kg puede ser suficiente para anemia leve. "
            "Gatos: cualquier cantidad es motivo de consulta."
        ),
        que_hacer="Urgencia veterinaria. Inducción de vómito si < 2h. Hemograma.",
        notas=(
            "Existe controversia sobre ajo a dosis muy bajas en perros — algunos estudios muestran "
            "efecto antiparasitario. La posición de NutriVet.IA es conservadora: NO incluir ajo. "
            "El riesgo supera el beneficio teórico no demostrado."
        ),
    ),

    DangerousFood(
        nombre="Ajo en polvo",
        aliases=["garlic powder", "ajo deshidratado"],
        nivel_riesgo="LETAL",
        especie_afectada="ambos",
        mecanismo="Igual que ajo crudo — concentración 5x mayor.",
        dosis_toxica="Muy pequeñas cantidades ya son peligrosas. Presente en sazonadores, aderezos, rubs.",
        que_hacer="URGENCIA VETERINARIA INMEDIATA.",
        notas="Revisar etiquetas de todos los alimentos procesados dados a mascotas.",
    ),

    DangerousFood(
        nombre="Aguacate (pulpa)",
        aliases=["palta", "avocado", "aguacate hass", "aguacate criollo"],
        nivel_riesgo="ALTO",
        especie_afectada="perros",
        mecanismo=(
            "Persina (antifúngico natural del aguacate) → cardiotoxicidad, "
            "edema mamario, mastitis no infecciosa, falla respiratoria. "
            "Concentración de persina varía por variedad — Hass tiene más que criollo. "
            "Perros son más sensibles que humanos."
        ),
        dosis_toxica="No hay dosis segura establecida para perros. Evitar completamente.",
        que_hacer="Consulta veterinaria urgente. Monitoreo cardíaco y respiratorio.",
        notas="Pájaros, conejos y roedores son extremadamente sensibles — NO dar nunca.",
    ),

    DangerousFood(
        nombre="Aguacate (semilla y cáscara)",
        aliases=["pepa de aguacate", "semilla de palta", "carozo de aguacate"],
        nivel_riesgo="LETAL",
        especie_afectada="ambos",
        mecanismo=(
            "Concentración de persina mucho mayor que la pulpa. "
            "Además obstrucción intestinal por el tamaño de la semilla."
        ),
        dosis_toxica="Cualquier cantidad es una emergencia.",
        que_hacer="URGENCIA VETERINARIA INMEDIATA. Riesgo de obstrucción + toxicidad.",
        notas="",
    ),

    DangerousFood(
        nombre="Aguacate para gatos",
        aliases=["palta para gatos"],
        nivel_riesgo="MODERADO",
        especie_afectada="gatos",
        mecanismo=(
            "Gatos son algo menos sensibles a la persina que perros y aves. "
            "Riesgo principal: trastorno GI, pancreatitis por grasa. "
            "Casos de toxicidad clínica en gatos son menos frecuentes pero existen."
        ),
        dosis_toxica="No hay dosis segura establecida. Postura conservadora: evitar.",
        que_hacer="Consultar veterinario si ingirió cantidad significativa.",
        notas="Gatos: riesgo menor que perros pero no ausente. La pulpa es el componente de menor riesgo.",
    ),

    DangerousFood(
        nombre="Xilitol",
        aliases=["xylitol", "E967", "birch sugar", "edulcorante de abedul"],
        nivel_riesgo="LETAL",
        especie_afectada="perros",
        mecanismo=(
            "En perros: estimula secreción masiva de insulina → hipoglucemia severa (30-60 min). "
            "Dosis más altas: necrosis hepática fulminante (1-2 días). "
            "Gatos: aparentemente no tienen el mismo receptor pancreático — menor sensibilidad "
            "pero no totalmente seguros."
        ),
        dosis_toxica=(
            "Hipoglucemia: 0.1 g/kg. Falla hepática: 0.5 g/kg. "
            "2 chicles sin azúcar pueden matar a un perro de 5 kg. "
            "Mantequilla de maní 'sin azúcar': SIEMPRE leer etiqueta."
        ),
        que_hacer=(
            "URGENCIA VETERINARIA INMEDIATA — una de las pocas toxicidades donde "
            "CADA MINUTO CUENTA. Glucosa IV. Monitoreo hepático seriado."
        ),
        notas=(
            "Presente en: chicles, caramelos sin azúcar, pasta de dientes, enjuague bucal, "
            "mantequilla de maní 'natural/light', vitaminas masticables, medicamentos. "
            "Revisar SIEMPRE los ingredientes de mantequilla de maní antes de dar a mascotas."
        ),
    ),

    DangerousFood(
        nombre="Macadamia",
        aliases=["nuez de macadamia", "macadamia nuts"],
        nivel_riesgo="ALTO",
        especie_afectada="perros",
        mecanismo=(
            "Toxina no identificada. Debilidad muscular posterior, hipertermia, temblores, "
            "vómito. Rara vez letal pero severo. Gatos: muy pocos casos reportados."
        ),
        dosis_toxica="2.2 g/kg de nuez cruda. 1 nuez por cada 2 kg ya puede causar síntomas.",
        que_hacer="Urgencia veterinaria. Soporte sintomático. Generalmente se recuperan en 48h.",
        notas="Peor si viene cubierta de chocolate (doble toxicidad).",
    ),

    DangerousFood(
        nombre="Café y cafeína",
        aliases=["coffee", "café molido", "café instantáneo", "te negro", "té verde", "guaraná", "Red Bull"],
        nivel_riesgo="LETAL",
        especie_afectada="ambos",
        mecanismo=(
            "Cafeína: inhibidor de fosfodiesterasa + antagonista de adenosina. "
            "Taquicardia, hipertensión, convulsiones, falla cardíaca. "
            "Mismo mecanismo que chocolate (cafeína + teobromina)."
        ),
        dosis_toxica=(
            "140 mg/kg = dosis letal media (DL50) en perros. "
            "1 taza de café ≈ 100-150 mg cafeína. En perros pequeños: 1-2 sorbos pueden ser problema."
        ),
        que_hacer="URGENCIA VETERINARIA INMEDIATA. Inducción de vómito si < 2h. Carbón activado.",
        notas="Fuentes ocultas: chicles energizantes, suplementos deportivos, pastillas de dieta.",
    ),

    DangerousFood(
        nombre="Alcohol",
        aliases=["etanol", "bebidas alcohólicas", "cerveza", "vino", "aguardiente"],
        nivel_riesgo="LETAL",
        especie_afectada="ambos",
        mecanismo=(
            "Depresión del SNC. Hipoglucemia. Acidosis metabólica. "
            "Mascotas no tienen tolerancia — incluso cantidades pequeñas son graves. "
            "La masa de levadura cruda también produce etanol por fermentación en el estómago."
        ),
        dosis_toxica=(
            "Perros: 5.5 ml etanol/kg de alcohol puro = dosis peligrosa. "
            "Cerveza (5%): 110 ml/kg. En práctica: cualquier cantidad visible es emergencia."
        ),
        que_hacer="URGENCIA VETERINARIA INMEDIATA. Glucosa IV. Soporte térmico.",
        notas="La masa de pan con levadura activa es igual de peligrosa por fermentación in vivo.",
    ),

    DangerousFood(
        nombre="Nuez (walnut)",
        aliases=["nuez nogal", "English walnut", "Juglans regia", "nuez negra"],
        nivel_riesgo="ALTO",
        especie_afectada="perros",
        mecanismo=(
            "Juglona (nuez negra) + posible contaminación con hongos Penicillium. "
            "Neurotoxicidad, temblores, convulsiones (principalmente nuez negra = Juglans nigra). "
            "La nuez de Castilla (Juglans regia) es menos peligrosa pero puede contener micotoxinas."
        ),
        dosis_toxica="No establecida claramente. Evitar preventivamente toda nuez mohosa.",
        que_hacer="Urgencia veterinaria si hay temblores. Soporte sintomático.",
        notas=(
            "Riesgo principal es la contaminación fúngica (penitrem A) en nueces viejas o mohosas. "
            "Nuez fresca, sin moho, en pequeña cantidad: riesgo bajo pero evitar por precaución."
        ),
    ),

    DangerousFood(
        nombre="Sal en exceso",
        aliases=["sodio", "cloruro de sodio", "sal de cocina"],
        nivel_riesgo="ALTO",
        especie_afectada="ambos",
        mecanismo=(
            "Hipernatremia → deshidratación celular → edema cerebral → convulsiones, coma. "
            "En bajas cantidades: los riñones sanos lo filtran. El problema es la cantidad."
        ),
        dosis_toxica=(
            "Dosis tóxica: 4g/kg en perros. Letal: ~4.5g/kg. "
            "Una cucharadita de sal ≈ 6g — peligrosa para perros pequeños. "
            "Agua de mar: concentración suficiente para intoxicación."
        ),
        que_hacer=(
            "Agua fresca disponible inmediatamente. Si ingirió mucha sal: urgencia vet. "
            "NO forzar agua — corrección rápida de hipernatremia también es peligrosa."
        ),
        notas="Riesgo oculto: salmueras, caldos concentrados, snacks salados, agua de mar.",
    ),

    DangerousFood(
        nombre="Huesos cocidos",
        aliases=["huesos hervidos", "huesos asados", "carcasa de pollo cocida"],
        nivel_riesgo="ALTO",
        especie_afectada="ambos",
        mecanismo=(
            "El calor desnaturaliza el colágeno → hueso se vuelve quebradizo y astilloso. "
            "Las astillas perforan esófago, estómago, intestino → perforación GI, peritonitis. "
            "Los huesos CRUDOS son flexibles y más seguros (se fragmentan diferente)."
        ),
        dosis_toxica="No hay dosis — el riesgo es mecánico, no por cantidad.",
        que_hacer=(
            "Si hay vómito con sangre, dolor abdominal agudo o incapacidad de defecar: "
            "URGENCIA VETERINARIA. Radiografías para localizar fragmentos."
        ),
        notas=(
            "REGLA: hueso crudo = relativamente seguro en mascotas acostumbradas. "
            "Hueso cocido = SIEMPRE peligroso. "
            "Huesos de pollo cocido: los más frecuentes en urgencias veterinarias en LATAM."
        ),
    ),

    DangerousFood(
        nombre="Masa de pan con levadura activa",
        aliases=["masa cruda con levadura", "masa de pizza cruda", "raw yeast dough"],
        nivel_riesgo="ALTO",
        especie_afectada="ambos",
        mecanismo=(
            "Fermentación en el estómago caliente produce: (1) gas → dilatación gástrica (GDV riesgo), "
            "(2) etanol → intoxicación alcohólica. "
            "La levadura activa sigue fermentando a temperatura corporal."
        ),
        dosis_toxica="Cualquier cantidad de masa con levadura viva es una emergencia potencial.",
        que_hacer="URGENCIA VETERINARIA. Pueden necesitar vaciamiento gástrico.",
        notas="La levadura INACTIVA/SECA de uso como suplemento es completamente diferente y segura.",
    ),

    DangerousFood(
        nombre="Semillas de manzana",
        aliases=["pepitas de manzana", "carozo de manzana"],
        nivel_riesgo="MODERADO",
        especie_afectada="ambos",
        mecanismo=(
            "Amigdalina → cianuro al metabolizarse. "
            "Riesgo depende de la cantidad y si se mastican (cianuro liberado al masticar). "
            "Semillas tragadas enteras: menor riesgo. "
            "La PULPA de manzana es completamente segura."
        ),
        dosis_toxica="~1-5 mg HCN/kg. 1g de semillas contiene ~0.9 mg HCN. En perros pequeños, varias semillas masticadas.",
        que_hacer="Si masticó múltiples semillas: consulta veterinaria. Carbón activado.",
        notas="Incluye semillas de pera, uva, cereza, durazno, ciruela — todas contienen amigdalina.",
    ),

    DangerousFood(
        nombre="Durazno y ciruela (semilla)",
        aliases=["melocotón", "damasco", "albaricoque", "plum", "peach pit"],
        nivel_riesgo="ALTO",
        especie_afectada="ambos",
        mecanismo=(
            "Las semillas/carozos contienen amigdalina (cianuro). "
            "Además: obstrucción intestinal por el tamaño. "
            "La pulpa es segura en pequeñas cantidades."
        ),
        dosis_toxica="Una semilla masticada de durazno = emergencia en perros medianos y pequeños.",
        que_hacer="URGENCIA VETERINARIA si ingirió semilla. Radiografía para obstrucción.",
        notas="Riesgo doble: cianuro + obstrucción mecánica.",
    ),

    DangerousFood(
        nombre="Tomate verde o sin madurar",
        aliases=["tomate verde", "planta de tomate", "tomatillo verde — diferente al mexicano"],
        nivel_riesgo="MODERADO",
        especie_afectada="ambos",
        mecanismo=(
            "Solanina y tomatina — glicoalcaloides que disminuyen al madurar. "
            "Tomate ROJO MADURO: muy baja toxicidad, generalmente seguro en pequeñas cantidades. "
            "PARTES VERDES (hojas, tallo, fruto verde): concentración alta."
        ),
        dosis_toxica="Tomate verde: >0.5g/kg puede causar síntomas GI. Partes de la planta: cualquier cantidad.",
        que_hacer="Monitorear síntomas GI. Consulta vet si ingirió partes verdes de la planta.",
        notas="Tomate rojo maduro en pequeñas cantidades: riesgo bajo, pero sin valor nutricional especial para mascotas.",
    ),

    DangerousFood(
        nombre="Nuez moscada",
        aliases=["moscada", "nutmeg", "Myristica fragrans"],
        nivel_riesgo="ALTO",
        especie_afectada="ambos",
        mecanismo=(
            "Miristicina — alucinógeno y neurotóxico. "
            "Desorientación, alucinaciones, taquicardia, convulsiones, coma. "
            "Una cucharadita entera puede ser fatal para perros pequeños."
        ),
        dosis_toxica=">0.1 g/kg ya causa síntomas. 5g (1 cucharadita) = emergencia en perros <10 kg.",
        que_hacer="URGENCIA VETERINARIA. Soporte sintomático neurológico.",
        notas="Frecuente en productos horneados navideños (bizcochos, tortas de navidad).",
    ),

    DangerousFood(
        nombre="Leche de vaca",
        aliases=["leche entera", "leche descremada", "lactosa"],
        nivel_riesgo="BAJO",
        especie_afectada="ambos",
        mecanismo=(
            "La mayoría de perros y gatos adultos son intolerantes a la lactosa — "
            "deficiencia de lactasa después del destete. "
            "No es tóxico sino genera malestar GI: diarrea, gases, vómito."
        ),
        dosis_toxica="No hay dosis tóxica — es intolerancia, no toxicidad.",
        que_hacer="Suspender. Dieta blanda 24-48h. Hidratación.",
        notas=(
            "Algunos perros toleran pequeñas cantidades. Quesos duros y yogur natural "
            "(bajo en lactosa) generalmente mejor tolerados. "
            "Gatitos: leche de gata o fórmula felina — NUNCA leche de vaca."
        ),
    ),
]


# ---------------------------------------------------------------------------
# TABLA 6 — CÁLCULO DE PORCIONES (EJEMPLO TRABAJADO)
# ---------------------------------------------------------------------------

EJEMPLO_CALCULO_PORCIONES = """
╔══════════════════════════════════════════════════════════════════════════════════╗
║ EJEMPLO TRABAJADO — PLAN CASERO/BARF PARA PERRO DE 20 KG                       ║
╚══════════════════════════════════════════════════════════════════════════════════╝

PERFIL DEL ANIMAL
─────────────────
Especie: Perro
Peso: 20 kg
BCS: 5/9 (peso ideal = peso real, sin ajuste)
Edad: 4 años (adulto, factor edad = 1.0)
Estado reproductivo: Esterilizado
Nivel de actividad: Moderado
Condiciones médicas: Ninguna
Modalidad: Dieta casera/BARF

────────────────────────────────────────────────────────────────────────────────
PASO 1 — CALCULAR RER
────────────────────────────────────────────────────────────────────────────────
RER = 70 × peso_kg^0.75
RER = 70 × 20^0.75
RER = 70 × 9.457 = 662.0 kcal/día

────────────────────────────────────────────────────────────────────────────────
PASO 2 — CALCULAR DER
────────────────────────────────────────────────────────────────────────────────
DER = RER × factor_vida × factor_edad × bcs_modifier

factor_vida (moderado + esterilizado) = 1.600
factor_edad (adulto 4 años)           = 1.0
bcs_modifier (BCS=5 → mantenimiento)  = 1.0

DER = 662.0 × 1.600 × 1.0 × 1.0 = 1059.2 kcal/día

────────────────────────────────────────────────────────────────────────────────
PASO 3 — COMPOSICIÓN DEL PLAN
────────────────────────────────────────────────────────────────────────────────
Proporciones definidas:
  • 70% muslo de pollo sin piel   → 70% × 1059.2 = 741.4 kcal
  • 15% zanahoria cruda           → 15% × 1059.2 = 158.9 kcal
  • 10% arroz integral cocido     → 10% × 1059.2 = 105.9 kcal
  •  5% aceite de sardinas        →  5% × 1059.2 =  52.9 kcal

────────────────────────────────────────────────────────────────────────────────
PASO 4 — CONVERTIR KCAL A GRAMOS
────────────────────────────────────────────────────────────────────────────────
Densidad calórica (por 100g):
  • Muslo de pollo sin piel   = 170 kcal/100g → 1 g = 1.70 kcal
  • Zanahoria cruda            = 41 kcal/100g  → 1 g = 0.41 kcal
  • Arroz integral cocido     = 123 kcal/100g  → 1 g = 1.23 kcal
  • Aceite de sardinas        = 902 kcal/100ml → 1 ml = 9.02 kcal

Gramos por ingrediente:
  • Muslo de pollo  = 741.4 ÷ 1.70   = 436.1 g
  • Zanahoria       = 158.9 ÷ 0.41   = 387.6 g
  • Arroz integral  = 105.9 ÷ 1.23   =  86.1 g (cocido)
  • Aceite sardinas =  52.9 ÷ 9.02   =   5.9 ml

TOTAL DIARIO (aprox.):
  436 g pollo + 388 g zanahoria + 86 g arroz + 6 ml aceite de sardinas
  = ≈ 916 g de alimento total al día

────────────────────────────────────────────────────────────────────────────────
PASO 5 — VERIFICACIÓN NUTRICIONAL
────────────────────────────────────────────────────────────────────────────────
Calcular aporte real vs mínimos NRC/AAFCO para mantenimiento adulto:

PROTEÍNA
  Muslo pollo:   436g × 19.7g/100g = 85.9g
  Zanahoria:     388g × 0.9g/100g  =  3.5g
  Arroz:          86g × 2.6g/100g  =  2.2g
  TOTAL PROTEÍNA: 91.6 g
  Mínimo NRC adulto 20 kg: ~2.62 g/kg/día = 52.4g ✓ (91.6 > 52.4)

GRASA
  Muslo pollo:   436g × 9.7g/100g  = 42.3g
  Aceite:          6ml × 100g/100ml × (100g total grasa) = 6.0g  (aprox, el aceite es 100% grasa)
  TOTAL GRASA: 48.3g
  Mínimo NRC adulto 20 kg: ~1.3 g/kg/día = 26g ✓ (48.3 > 26)

CALCIO
  Muslo pollo:  436g × 11mg/100g    = 47.9 mg
  Zanahoria:    388g × 33mg/100g    = 128.0 mg
  Arroz:         86g × 10mg/100g    =  8.6 mg
  TOTAL Ca sin suplemento: 184.5 mg
  Mínimo NRC adulto 20 kg: 120 mg/kg/día × 20 kg = 2400 mg ✗ DÉFICIT CRÍTICO

⚠️  DÉFICIT DE CALCIO — OBLIGATORIO suplementar
  Déficit = 2400 - 184 = 2216 mg Ca
  Carbonato de calcio (CaCO3): 40% Ca elemental → 2216 ÷ 0.40 = 5540 mg CaCO3 ≈ 5.5 g
  Alternativa: cáscara de huevo molida ≈ 2000 mg Ca/cucharadita → ≈ 1.1 cucharaditas/día

FÓSFORO
  Muslo pollo:  436g × 196mg/100g   = 854.6 mg
  Zanahoria:    388g × 35mg/100g    = 135.8 mg
  Arroz:         86g × 83mg/100g    =  71.4 mg
  TOTAL P: 1061.8 mg

  Relación Ca:P con suplemento = 2400:1062 = 2.26:1
  Rango óptimo NRC: 1:1 a 2:1 ✓ (aceptable en límite superior)

OMEGA-3 EPA+DHA
  Muslo pollo:  436g × 80mg/100g   = 348.8 mg
  Aceite sardinas: 6ml → aprox. 29.9g omega3/100ml × 6ml × EPA+DHA fraction
  El aceite de sardinas tiene ~EPA 18% + DHA 12% del total = ~30% de 6ml × 0.902g/ml
    = 6 × 0.9 × 0.30 = 1.62 g = 1620 mg EPA+DHA

  TOTAL EPA+DHA: 349 + 1620 = 1969 mg
  Objetivo terapéutico NRC: 50-100 mg/kg/día = 1000-2000 mg/día ✓

TAURINA
  Muslo pollo:  436g × 83mg/100g   = 361.9 mg
  TOTAL: 361.9 mg — suficiente para perros (gatos: verificar corazón de pollo adicional)

────────────────────────────────────────────────────────────────────────────────
PASO 6 — PLAN FINAL AJUSTADO (diario)
────────────────────────────────────────────────────────────────────────────────
  • Muslo de pollo sin piel:    436 g
  • Zanahoria cruda rallada:    388 g
  • Arroz integral cocido:       86 g
  • Aceite de sardinas:           6 ml
  • Carbonato de calcio:        5.5 g  (O 1.1 cdta cáscara de huevo molida)

Distribución recomendada: 2 comidas/día (218g pollo + 194g zanahoria + 43g arroz + 3ml aceite)
Temperatura: ambiente o ligeramente tibia — NUNCA fría directamente del refrigerador.

────────────────────────────────────────────────────────────────────────────────
NOTA SOBRE TRANSICIÓN
────────────────────────────────────────────────────────────────────────────────
Si el animal estaba en concentrado:
  Semana 1: 75% concentrado + 25% plan casero
  Semana 2: 50% concentrado + 50% plan casero
  Semana 3: 25% concentrado + 75% plan casero
  Semana 4: 100% plan casero

Monitorear: heces (consistencia), energía, pelaje, peso semanal.
"""


# ---------------------------------------------------------------------------
# Índice de búsqueda — lookup por nombre o alias
# ---------------------------------------------------------------------------

def buscar_ingrediente(nombre: str) -> dict | None:
    """
    Busca un ingrediente en todas las tablas por nombre o alias (case-insensitive).

    Args:
        nombre: Nombre o alias del ingrediente a buscar.

    Returns:
        Diccionario con 'tipo' y 'datos' del ingrediente, o None si no se encuentra.
    """
    nombre_lower = nombre.lower().strip()

    for item in PROTEINAS_ANIMALES:
        if nombre_lower == item.nombre.lower() or nombre_lower in [a.lower() for a in item.aliases]:
            return {"tipo": "proteina_animal", "datos": item}

    for item in ALIMENTOS_VEGETALES:
        if nombre_lower == item.nombre.lower() or nombre_lower in [a.lower() for a in item.aliases]:
            return {"tipo": "vegetal_cereal_fruta", "datos": item}

    for item in GRASAS_ACEITES:
        if nombre_lower == item.nombre.lower() or nombre_lower in [a.lower() for a in item.aliases]:
            return {"tipo": "grasa_aceite", "datos": item}

    for item in ALIMENTOS_PELIGROSOS:
        if nombre_lower == item.nombre.lower() or nombre_lower in [a.lower() for a in item.aliases]:
            return {"tipo": "alimento_peligroso", "datos": item}

    return None


def es_peligroso(nombre: str) -> tuple[bool, str | None]:
    """
    Verifica si un ingrediente está en la lista de alimentos peligrosos.

    Args:
        nombre: Nombre del ingrediente.

    Returns:
        Tupla (es_peligroso, nivel_riesgo). nivel_riesgo es None si no es peligroso.
    """
    resultado = buscar_ingrediente(nombre)
    if resultado and resultado["tipo"] == "alimento_peligroso":
        return True, resultado["datos"].nivel_riesgo
    return False, None
