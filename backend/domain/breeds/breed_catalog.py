"""
Catálogo de razas de perros y gatos — NutriVet.IA

Fuente de verdad para búsqueda y selección de razas en el wizard.
Incluye predisposiciones genéticas relevantes para la nutrición preventiva.

LATAM-relevant: razas más comunes en Colombia, México, Argentina, Chile, Ecuador.
Incluye campo Criollo/Mestizo como opción explícita para ambas especies.

Predisposiciones validadas clínicamente por Lady Carolina Castañeda (MV, BAMPYSVET).
NUNCA modificar predisposiciones sin confirmación veterinaria.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Dataclass principal
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BreedInfo:
    """
    Información de una raza para el catálogo de NutriVet.IA.

    id:                   Identificador único snake_case.
    nombre:               Nombre oficial de la raza.
    aliases:              Nombres alternativos y comunes (LATAM).
    especie:              "perro" | "gato".
    grupo_fci:            Número de grupo FCI (1-10) para perros. None para gatos.
    talla_tipica:         Talla predominante: mini/pequeño/mediano/grande/gigante.
                          None si hay variantes múltiples (ej. Poodle) o es gato.
    peso_adulto_min_kg:   Peso mínimo esperado en adulto.
    peso_adulto_max_kg:   Peso máximo esperado en adulto.
    longevidad_min:       Esperanza de vida mínima (años).
    longevidad_max:       Esperanza de vida máxima (años).
    meses_adulto:         Mes en que se considera adulto nutricionalmente.
                          Razas gigantes: 18-24. Razas pequeñas: 10-12.
    predisposiciones:     Condiciones médicas con predisposición genética documentada.
    notas_nutricionales:  Nota breve para el propietario.
    es_criollo:           True solo para Criollo/Mestizo.
    """
    id: str
    nombre: str
    especie: str                                          # "perro" | "gato"
    peso_adulto_min_kg: float
    peso_adulto_max_kg: float
    longevidad_min: int
    longevidad_max: int
    meses_adulto: int
    aliases: tuple[str, ...] = field(default_factory=tuple)
    grupo_fci: Optional[int] = None
    talla_tipica: Optional[str] = None
    predisposiciones: frozenset[str] = field(default_factory=frozenset)
    notas_nutricionales: str = ""
    es_criollo: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.predisposiciones, frozenset):
            object.__setattr__(self, "predisposiciones", frozenset(self.predisposiciones))
        if not isinstance(self.aliases, tuple):
            object.__setattr__(self, "aliases", tuple(self.aliases))


# ---------------------------------------------------------------------------
# Helper de construcción
# ---------------------------------------------------------------------------

def _b(
    id: str,
    nombre: str,
    especie: str,
    peso_min: float,
    peso_max: float,
    longevidad: tuple[int, int],
    meses_adulto: int,
    aliases: list[str] | None = None,
    grupo_fci: int | None = None,
    talla: str | None = None,
    predisposiciones: set[str] | None = None,
    notas: str = "",
    es_criollo: bool = False,
) -> BreedInfo:
    return BreedInfo(
        id=id,
        nombre=nombre,
        especie=especie,
        peso_adulto_min_kg=peso_min,
        peso_adulto_max_kg=peso_max,
        longevidad_min=longevidad[0],
        longevidad_max=longevidad[1],
        meses_adulto=meses_adulto,
        aliases=tuple(aliases or []),
        grupo_fci=grupo_fci,
        talla_tipica=talla,
        predisposiciones=frozenset(predisposiciones or set()),
        notas_nutricionales=notas,
        es_criollo=es_criollo,
    )


# ---------------------------------------------------------------------------
# Catálogo completo — PERROS
# ---------------------------------------------------------------------------

_DOGS: list[BreedInfo] = [

    # ---- Grupo 1 — Pastores y Boyeros ----
    _b("pastor_aleman", "Pastor Alemán", "perro", 22, 40, (9, 13), 18,
       aliases=["Alsaciano", "German Shepherd", "GSD"],
       grupo_fci=1, talla="grande",
       predisposiciones={"displasia_cadera", "displasia_codo", "degeneración_mielopatía",
                         "pannus", "dilatación_gástrica"},
       notas="Propenso a displasia. Control de peso esencial para proteger articulaciones."),

    _b("border_collie", "Border Collie", "perro", 12, 20, (12, 15), 12,
       aliases=["BC"],
       grupo_fci=1, talla="mediano",
       predisposiciones={"epilepsia", "anomalía_ojo_collie", "sensibilidad_MDR1"},
       notas="Muy activo — requerimientos calóricos elevados. Monitorear BCS en trabajo."),

    _b("pastor_australiano", "Pastor Australiano", "perro", 16, 32, (12, 15), 12,
       aliases=["Australian Shepherd", "Aussie"],
       grupo_fci=1, talla="mediano",
       predisposiciones={"sensibilidad_MDR1", "epilepsia", "anomalía_ojo_collie"},
       notas="Alta energía. Dieta adecuada al nivel de actividad real."),

    _b("collie_rough", "Collie (Rough)", "perro", 18, 30, (12, 14), 12,
       aliases=["Collie Pelo Largo", "Lassie"],
       grupo_fci=1, talla="grande",
       predisposiciones={"sensibilidad_MDR1", "anomalía_ojo_collie"},
       notas=""),

    _b("shetland_sheepdog", "Shetland Sheepdog", "perro", 6, 12, (12, 14), 12,
       aliases=["Shelti", "Sheltie"],
       grupo_fci=1, talla="pequeño",
       predisposiciones={"sensibilidad_MDR1", "anomalía_ojo_collie", "epilepsia"},
       notas=""),

    _b("belgian_malinois", "Belgian Malinois", "perro", 20, 30, (12, 14), 18,
       aliases=["Malinois", "Pastor Belga"],
       grupo_fci=1, talla="grande",
       predisposiciones={"displasia_cadera"},
       notas="Alta energía y trabajo. Requerimientos calóricos muy elevados en servicio."),

    _b("bernes_montania", "Bernés de la Montaña", "perro", 32, 52, (6, 9), 24,
       aliases=["Bernese Mountain Dog", "Boyero de Berna"],
       grupo_fci=2, talla="gigante",
       predisposiciones={"displasia_cadera", "displasia_codo", "cancer",
                         "meningitis_arteritica"},
       notas="Raza gigante — adulto a 24 meses. Alta incidencia de cáncer (~40%). "
             "Omega-3 antiinflamatorio preventivo."),

    # ---- Grupo 2 — Pinscher, Schnauzer, Molosoides ----
    _b("rottweiler", "Rottweiler", "perro", 35, 60, (8, 11), 24,
       aliases=["Rott"],
       grupo_fci=2, talla="gigante",
       predisposiciones={"displasia_cadera", "displasia_codo", "osteosarcoma",
                         "dilatación_volvulo_gastrico"},
       notas="Raza grande-gigante — adulto a 18-24 meses. Control de peso."),

    _b("doberman", "Doberman", "perro", 27, 45, (10, 13), 18,
       aliases=["Doberman Pinscher", "Dóberman"],
       grupo_fci=2, talla="grande",
       predisposiciones={"cardiomiopatia_dilatada", "dilatación_volvulo_gastrico",
                         "hipotiroidismo"},
       notas="Predisposición a cardiomiopatía dilatada — taurina y L-carnitina preventivos."),

    _b("schnauzer_miniatura", "Schnauzer Miniatura", "perro", 4, 8, (12, 15), 12,
       aliases=["Mini Schnauzer"],
       grupo_fci=2, talla="pequeño",
       predisposiciones={"hiperlipidemia", "pancreatitis", "urolitiasis_oxalato",
                         "diabetes", "comedones"},
       notas="Predisposición fuerte a hiperlipidemia — grasa controlada preventivamente."),

    _b("schnauzer_estandar", "Schnauzer Estándar", "perro", 14, 20, (13, 16), 12,
       aliases=["Schnauzer Mediano"],
       grupo_fci=2, talla="mediano",
       predisposiciones={"hiperlipidemia", "pancreatitis"},
       notas=""),

    _b("schnauzer_gigante", "Schnauzer Gigante", "perro", 25, 47, (10, 12), 18,
       aliases=["Giant Schnauzer"],
       grupo_fci=2, talla="grande",
       predisposiciones={"displasia_cadera", "hiperlipidemia"},
       notas=""),

    _b("boxer", "Boxer", "perro", 22, 32, (9, 11), 18,
       aliases=[],
       grupo_fci=2, talla="grande",
       predisposiciones={"cancer", "displasia_cadera", "cardiomiopatia",
                         "dilatación_volvulo_gastrico"},
       notas="Alta incidencia de cáncer. Dieta antiinflamatoria recomendada."),

    _b("gran_danes", "Gran Danés", "perro", 45, 90, (7, 10), 24,
       aliases=["Great Dane", "Dogo Alemán"],
       grupo_fci=2, talla="gigante",
       predisposiciones={"dilatación_volvulo_gastrico", "displasia_cadera",
                         "cardiomiopatia_dilatada", "osteosarcoma"},
       notas="RAZA GIGANTE — adulto a 24 meses. Mínimo 2 comidas/día. "
             "Sin ejercicio 2h post-comida (GDV). Sin comedero elevado."),

    _b("bullmastiff", "Bullmastiff", "perro", 45, 60, (7, 9), 24,
       aliases=[],
       grupo_fci=2, talla="gigante",
       predisposiciones={"displasia_cadera", "torsión_gástrica", "cancer"},
       notas="Raza gigante — adulto 18-24 meses."),

    _b("dogo_argentino", "Dogo Argentino", "perro", 35, 45, (10, 12), 18,
       aliases=["Dogo"],
       grupo_fci=2, talla="grande",
       predisposiciones={"displasia_cadera", "sordera_pigmentaria"},
       notas=""),

    _b("shar_pei", "Shar Pei", "perro", 18, 25, (8, 12), 12,
       aliases=["Charpei"],
       grupo_fci=2, talla="mediano",
       predisposiciones={"fiebre_shar_pei", "amiloidosis_renal", "hipotiroidismo",
                         "dermatitis_pliegues"},
       notas="Predisposición a amiloidosis renal — hidratación alta preventiva."),

    # ---- Grupo 3 — Terriers ----
    _b("yorkshire_terrier", "Yorkshire Terrier", "perro", 1.8, 3.2, (13, 16), 10,
       aliases=["Yorkie", "YT"],
       grupo_fci=3, talla="mini",
       predisposiciones={"hipoglucemia_cachorros", "colapso_traqueal",
                         "luxación_patelar", "hepatopatia_shunt_portosistemico"},
       notas="Cachorros toy: alto riesgo de hipoglucemia. Mínimo 4 comidas/día en cachorros."),

    _b("west_highland_white_terrier", "West Highland White Terrier", "perro", 6, 10, (12, 16), 12,
       aliases=["Westie", "WHWT"],
       grupo_fci=3, talla="pequeño",
       predisposiciones={"acumulacion_cobre_hepatica", "dermatitis_atopica",
                         "pulmonary_fibrosis"},
       notas="Restricción preventiva de cobre (sin hígado). Omega-3 para piel."),

    _b("bedlington_terrier", "Bedlington Terrier", "perro", 7, 11, (13, 16), 12,
       aliases=[],
       grupo_fci=3, talla="pequeño",
       predisposiciones={"acumulacion_cobre_hepatica"},
       notas="CRÍTICO: restricción de cobre. Sin hígado de res, sin mariscos, sin nueces."),

    _b("bull_terrier", "Bull Terrier", "perro", 18, 29, (10, 14), 12,
       aliases=["BT"],
       grupo_fci=3, talla="mediano",
       predisposiciones={"sordera", "problemas_renales", "dermatitis"},
       notas=""),

    _b("jack_russell_terrier", "Jack Russell Terrier", "perro", 5, 8, (13, 16), 10,
       aliases=["JRT", "Jack Russell"],
       grupo_fci=3, talla="pequeño",
       predisposiciones={"luxación_patelar", "ataxia_cerebelosa"},
       notas=""),

    _b("airedale_terrier", "Airedale Terrier", "perro", 18, 29, (10, 13), 12,
       aliases=["King of Terriers"],
       grupo_fci=3, talla="mediano",
       predisposiciones={"displasia_cadera", "hipotiroidismo"},
       notas=""),

    _b("scottish_terrier", "Scottish Terrier", "perro", 8, 10, (11, 13), 12,
       aliases=["Scottie"],
       grupo_fci=3, talla="pequeño",
       predisposiciones={"vonwillebrand", "cancer"},
       notas=""),

    # ---- Grupo 4 — Teckels ----
    _b("dachshund_estandar", "Dachshund Estándar", "perro", 7, 14, (12, 16), 10,
       aliases=["Teckel", "Salchicha", "Wiener"],
       grupo_fci=4, talla="pequeño",
       predisposiciones={"hernia_discal_ivdd", "obesidad", "diabetes"},
       notas="Alta tendencia a obesidad. Control calórico. Hernia discal: evitar sobrepeso."),

    _b("dachshund_miniatura", "Dachshund Miniatura", "perro", 3, 5, (12, 16), 10,
       aliases=["Teckel Miniatura", "Mini Salchicha"],
       grupo_fci=4, talla="mini",
       predisposiciones={"hernia_discal_ivdd", "obesidad", "hipoglucemia"},
       notas="Control de peso crítico — cada kilo extra aumenta riesgo de hernia discal."),

    # ---- Grupo 5 — Spitz y tipo primitivo ----
    _b("husky_siberiano", "Husky Siberiano", "perro", 16, 27, (12, 15), 18,
       aliases=["Husky", "Siberian Husky"],
       grupo_fci=5, talla="mediano",
       predisposiciones={"cataratas_hereditarias", "anomalía_ojo_collie", "hipotiroidismo"},
       notas="Raza de trabajo: en inactividad reducir 20-30% las calorías."),

    _b("alaskan_malamute", "Alaskan Malamute", "perro", 32, 43, (10, 12), 18,
       aliases=["Malamute"],
       grupo_fci=5, talla="gigante",
       predisposiciones={"displasia_cadera", "hipotiroidismo", "dia_polineuropatia"},
       notas="Raza de trabajo. Controlar peso en inactividad."),

    _b("samoyedo", "Samoyedo", "perro", 16, 30, (12, 14), 18,
       aliases=["Samoyed"],
       grupo_fci=5, talla="grande",
       predisposiciones={"displasia_cadera", "nefropatía_samoyedo",
                         "glomerulopatia"},
       notas="Predisposición a nefropatía — hidratación alta preventiva."),

    _b("akita_inu", "Akita Inu", "perro", 30, 50, (10, 13), 18,
       aliases=["Akita Japonés", "Akita"],
       grupo_fci=5, talla="gigante",
       predisposiciones={"pemfigo_foliáceo", "hipotiroidismo", "displasia_cadera"},
       notas=""),

    _b("chow_chow", "Chow Chow", "perro", 20, 32, (9, 12), 12,
       aliases=[],
       grupo_fci=5, talla="mediano",
       predisposiciones={"displasia_cadera", "hipotiroidismo", "entropión"},
       notas="Metabolismo basal más lento — controlar calorías."),

    _b("pomerania", "Pomerania", "perro", 1.4, 3.2, (12, 16), 10,
       aliases=["Spitz Enano", "Pom"],
       grupo_fci=5, talla="mini",
       predisposiciones={"colapso_traqueal", "luxación_patelar", "hipoglucemia"},
       notas="Toy: múltiples comidas pequeñas. Control de hipoglucemia en cachorros."),

    _b("shiba_inu", "Shiba Inu", "perro", 7, 11, (12, 15), 12,
       aliases=["Shiba"],
       grupo_fci=5, talla="pequeño",
       predisposiciones={"displasia_cadera", "alergias_piel"},
       notas=""),

    _b("basenji", "Basenji", "perro", 9, 12, (13, 14), 12,
       aliases=["Perro sin ladrido"],
       grupo_fci=5, talla="pequeño",
       predisposiciones={"anemia_hemolítica", "sindrome_fanconi"},
       notas="Síndrome de Fanconi: monitoreo renal y electrolítico."),

    # ---- Grupo 6 — Sabuesos ----
    _b("beagle", "Beagle", "perro", 8, 14, (12, 15), 12,
       aliases=[],
       grupo_fci=6, talla="pequeño",
       predisposiciones={"obesidad", "epilepsia", "hipotiroidismo"},
       notas="Alta tendencia a obesidad. Nunca alimentar ad libitum."),

    _b("basset_hound", "Basset Hound", "perro", 18, 29, (10, 12), 12,
       aliases=[],
       grupo_fci=6, talla="mediano",
       predisposiciones={"obesidad", "displasia_codo", "problemas_interdigitales"},
       notas="Control de peso crítico — estructura ósea no soporta sobrepeso."),

    _b("dalmata", "Dálmata", "perro", 22, 32, (11, 13), 12,
       aliases=["Dalmatian", "Dalmata"],
       grupo_fci=6, talla="mediano",
       predisposiciones={"hiperuricosuria", "cistitis_urica", "urolitiasis_urato",
                         "sordera"},
       notas="CRÍTICO: restricción de purinas. Sin hígado, anchoas, sardinas, riñón. "
             "Hidratación máxima. Monitoreo urinario semestral."),

    # ---- Grupo 7 y 8 — Caza y Cobro ----
    _b("golden_retriever", "Golden Retriever", "perro", 25, 36, (10, 14), 12,
       aliases=["Golden", "Labrador Dorado"],
       grupo_fci=8, talla="grande",
       predisposiciones={"obesidad", "displasia_cadera", "displasia_codo",
                         "cancer", "hipotiroidismo", "retinopatia_progresiva"},
       notas="60% de riesgo de cáncer en vida. Dieta antiinflamatoria preventiva. "
             "Alta tendencia a obesidad — control BCS estricto."),

    _b("labrador_retriever", "Labrador Retriever", "perro", 25, 36, (10, 14), 12,
       aliases=["Labrador", "Lab"],
       grupo_fci=8, talla="grande",
       predisposiciones={"obesidad", "displasia_cadera", "displasia_codo",
                         "miopatia_hereditaria", "retinopatia_progresiva"},
       notas="Alta tendencia a obesidad. Control BCS estricto. "
             "Nunca alimentar ad libitum."),

    _b("cocker_spaniel_ingles", "Cocker Spaniel Inglés", "perro", 9, 14, (12, 15), 12,
       aliases=["Cocker", "Cocker Inglés"],
       grupo_fci=8, talla="pequeño",
       predisposiciones={"hepatopatia_cronica", "pancreatitis", "hiperlipidemia",
                         "otitis", "retinopatia_progresiva"},
       notas="Predisposición a pancreatitis — grasa moderada preventiva."),

    _b("cocker_spaniel_americano", "Cocker Spaniel Americano", "perro", 7, 14, (12, 15), 12,
       aliases=["Cocker Americano"],
       grupo_fci=8, talla="pequeño",
       predisposiciones={"hepatopatia", "pancreatitis", "hiperlipidemia",
                         "retinopatia_progresiva"},
       notas=""),

    _b("springer_spaniel", "Springer Spaniel Inglés", "perro", 18, 25, (12, 14), 12,
       aliases=["Springer"],
       grupo_fci=8, talla="mediano",
       predisposiciones={"displasia_cadera", "hipoplasia_retina"},
       notas=""),

    _b("weimaraner", "Weimaraner", "perro", 22, 36, (10, 13), 18,
       aliases=["Braco de Weimar"],
       grupo_fci=7, talla="grande",
       predisposiciones={"dilatación_volvulo_gastrico", "displasia_cadera"},
       notas="Riesgo de GDV — mínimo 2 comidas/día, sin ejercicio 2h post-comida."),

    _b("vizsla", "Vizsla", "perro", 18, 29, (12, 15), 12,
       aliases=["Braco Húngaro", "Vizsla Húngaro"],
       grupo_fci=7, talla="mediano",
       predisposiciones={"displasia_cadera", "hipotiroidismo"},
       notas=""),

    _b("pointer", "Pointer", "perro", 20, 34, (12, 17), 12,
       aliases=["Pointer Inglés"],
       grupo_fci=7, talla="grande",
       predisposiciones={"displasia_cadera"},
       notas=""),

    # ---- Grupo 9 — Compañía ----
    _b("poodle_toy", "Poodle Toy", "perro", 1.5, 4, (14, 18), 10,
       aliases=["Caniche Toy", "Poodle Enano"],
       grupo_fci=9, talla="mini",
       predisposiciones={"epilepsia", "enfermedad_adison", "hipoglucemia",
                         "luxación_patelar", "atrofia_retina_progresiva"},
       notas=""),

    _b("poodle_miniatura", "Poodle Miniatura", "perro", 3, 7, (14, 17), 10,
       aliases=["Caniche Miniatura", "French Poodle"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"epilepsia", "enfermedad_adison", "hipoglucemia",
                         "atrofia_retina_progresiva"},
       notas="Golden case Sally: French Poodle 10.08 kg, 8 años — referencia clínica."),

    _b("poodle_estandar", "Poodle Estándar", "perro", 18, 32, (12, 15), 12,
       aliases=["Caniche Estándar", "Poodle Grande"],
       grupo_fci=9, talla="mediano",
       predisposiciones={"dilatación_volvulo_gastrico", "displasia_cadera",
                         "enfermedad_adison", "atrofia_retina_progresiva"},
       notas=""),

    _b("bulldog_frances", "Bulldog Francés", "perro", 7, 14, (10, 12), 12,
       aliases=["Bulldog Francés", "Frenchie", "French Bulldog"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"sensibilidad_digestiva", "alergia_alimentaria",
                         "urolitiasis_oxalato", "brachycephalic_syndrome",
                         "condrodistrofia"},
       notas="Transición de dieta muy gradual (3-4 semanas). "
             "Alta sensibilidad digestiva. Croquetas de tamaño braquicéfalo."),

    _b("bulldog_ingles", "Bulldog Inglés", "perro", 18, 25, (8, 10), 12,
       aliases=["English Bulldog", "British Bulldog"],
       grupo_fci=2, talla="mediano",
       predisposiciones={"displasia_cadera", "brachycephalic_syndrome",
                         "condrodistrofia", "dermatitis_pliegues"},
       notas="Sensibilidad digestiva. Control de peso por estructura ósea."),

    _b("pug", "Pug", "perro", 6, 8, (12, 15), 10,
       aliases=["Carlino", "Mops"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"obesidad", "brachycephalic_syndrome", "encefalitis_pug"},
       notas="Alta tendencia a obesidad. Control calórico estricto. BCS objetivo 4-5."),

    _b("shih_tzu", "Shih Tzu", "perro", 4, 7.5, (13, 16), 10,
       aliases=["Shih-Tzu"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"urolitiasis_oxalato", "hipoglucemia", "queratitis_ojo_seco"},
       notas=""),

    _b("maltes", "Maltés", "perro", 1.5, 4, (12, 15), 10,
       aliases=["Maltese", "Bichón Maltés"],
       grupo_fci=9, talla="mini",
       predisposiciones={"hipoglucemia", "colapso_traqueal", "luxación_patelar",
                         "shunt_portosistemico"},
       notas="Toy: múltiples comidas pequeñas. Vigilar hipoglucemia en cachorros."),

    _b("bichon_frise", "Bichón Frisé", "perro", 3, 5, (14, 15), 10,
       aliases=["Bichon Frise", "Bichón"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"luxación_patelar", "alergias_piel"},
       notas=""),

    _b("bichon_habanero", "Bichón Habanero", "perro", 3, 6, (14, 16), 10,
       aliases=["Habanero", "Havanese"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"luxación_patelar", "cataratas"},
       notas=""),

    _b("chihuahua", "Chihuahua", "perro", 1, 3, (14, 18), 10,
       aliases=["Chi"],
       grupo_fci=9, talla="mini",
       predisposiciones={"hipoglucemia", "luxación_patelar", "colapso_traqueal",
                         "hidrocefalia"},
       notas="Toy: mayor riesgo de hipoglucemia. Múltiples comidas pequeñas."),

    _b("cavalier_king_charles", "Cavalier King Charles Spaniel", "perro", 4.5, 8, (9, 15), 10,
       aliases=["Cavalier", "CKCS"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"valvulopatia_mitral", "siringomielia"},
       notas="Alta incidencia de valvulopatía mitral — taurina preventiva."),

    _b("lhasa_apso", "Lhasa Apso", "perro", 5, 8, (12, 20), 10,
       aliases=["Lhasa"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"enfermedad_renal", "queratitis_ojo_seco"},
       notas=""),

    _b("papillon", "Papillón", "perro", 3, 5, (13, 15), 10,
       aliases=["Papillon", "Mariposa"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"luxación_patelar"},
       notas=""),

    _b("pekinés", "Pekinés", "perro", 3, 6, (12, 15), 10,
       aliases=["Pekingese", "Pekines"],
       grupo_fci=9, talla="pequeño",
       predisposiciones={"brachycephalic_syndrome", "condrodistrofia",
                         "ojo_seco"},
       notas=""),

    # ---- Grupo 10 — Lebreles ----
    _b("greyhound", "Greyhound", "perro", 25, 40, (10, 14), 12,
       aliases=["Galgo Inglés"],
       grupo_fci=10, talla="grande",
       predisposiciones={"sensibilidad_anestesia"},
       notas="Sensible a anestesia — muy bajo porcentaje de grasa corporal."),

    _b("galgo_espanol", "Galgo Español", "perro", 20, 30, (12, 15), 12,
       aliases=["Galgo"],
       grupo_fci=10, talla="grande",
       predisposiciones={"sensibilidad_anestesia"},
       notas=""),

    _b("whippet", "Whippet", "perro", 12, 20, (12, 15), 12,
       aliases=[],
       grupo_fci=10, talla="mediano",
       predisposiciones={"sensibilidad_anestesia"},
       notas=""),

    # ---- CRIOLLO / MESTIZO ----
    _b("criollo_perro", "Criollo / Mestizo", "perro", 0.5, 60, (10, 15), 12,
       aliases=["Mestizo", "Callejero", "Criollo", "Adoptado", "SRD"],
       talla=None,
       predisposiciones=set(),
       notas="Sin predisposiciones genéticas conocidas. Evaluación nutricional individual.",
       es_criollo=True),
]


# ---------------------------------------------------------------------------
# Catálogo completo — GATOS
# ---------------------------------------------------------------------------

_CATS: list[BreedInfo] = [

    _b("domestico_pelo_corto", "Doméstico Pelo Corto", "gato", 3.5, 5.5, (12, 18), 12,
       aliases=["DPC", "Gato Común", "Gato Criollo Pelo Corto", "Doméstico"],
       predisposiciones=set(),
       notas="La raza más común en LATAM. Evaluación individual.",
       es_criollo=True),

    _b("domestico_pelo_largo", "Doméstico Pelo Largo", "gato", 3.5, 5.5, (12, 18), 12,
       aliases=["DPL", "Gato Común Pelo Largo"],
       predisposiciones=set(),
       notas="",
       es_criollo=True),

    _b("siames", "Siamés", "gato", 3, 4.5, (15, 20), 12,
       aliases=["Siamese", "Thai"],
       predisposiciones={"amiloidosis_hepatica", "asma_felino", "cancer_mama",
                         "estrabismo"},
       notas="Tendencia a bajo peso en vejez — monitoreo de peso frecuente en senior."),

    _b("persa", "Persa", "gato", 3, 5.5, (12, 17), 12,
       aliases=["Persian", "Gato Persa"],
       predisposiciones={"enfermedad_renal_poliquistica", "urolitiasis_oxalato",
                         "cardiomiopatia_hipertrofica", "braquicefalia"},
       notas="PKD frecuente — fósforo moderado preventivo. Hidratación alta. "
             "Preferir dieta húmeda."),

    _b("maine_coon", "Maine Coon", "gato", 4, 9, (12, 15), 18,
       aliases=["Maine"],
       predisposiciones={"cardiomiopatia_hipertrofica", "displasia_cadera",
                         "spinal_muscular_atrophy"},
       notas="HCM frecuente — taurina elevada y omega-3 preventivos. "
             "Madurez nutricional a los 18 meses. Raza grande."),

    _b("ragdoll", "Ragdoll", "gato", 4, 9, (12, 17), 18,
       aliases=["Ragdoll"],
       predisposiciones={"cardiomiopatia_hipertrofica", "enfermedad_renal_poliquistica"},
       notas="HCM y PKD — taurina, omega-3 y fósforo moderado preventivos. "
             "Madurez a los 18 meses."),

    _b("british_shorthair", "British Shorthair", "gato", 4, 8, (12, 20), 12,
       aliases=["British", "BSH"],
       predisposiciones={"cardiomiopatia_hipertrofica", "poliquistosis_renal",
                         "obesidad_tendencia"},
       notas="Tendencia a sobrepeso — control calórico desde adulto."),

    _b("scottish_fold", "Scottish Fold", "gato", 2.7, 6, (11, 15), 12,
       aliases=["Scottish"],
       predisposiciones={"osteocondrodisplasia", "artritis_severa",
                         "cardiomiopatia_hipertrofica"},
       notas="Artritis por osteocondrodisplasia — omega-3 antiinflamatorio desde joven."),

    _b("bengal", "Bengal", "gato", 3.5, 7, (14, 16), 12,
       aliases=["Bengalí", "Gato de Bengala"],
       predisposiciones={"atrofia_retina_progresiva", "enfermedad_inflamatoria_intestinal",
                         "cardiomiopatia_hipertrofica"},
       notas="Sensibilidad digestiva moderada — dieta digestible. "
             "Predisposición a retina progresiva."),

    _b("sphynx", "Sphynx", "gato", 3, 5, (12, 14), 12,
       aliases=["Esfinge", "Gato sin pelo"],
       predisposiciones={"cardiomiopatia_hipertrofica", "miopatia_hipertrofica"},
       notas="Sin pelo: mayor pérdida de calor → 10-15% más calorías. "
             "HCM frecuente — taurina preventiva."),

    _b("abisinio", "Abisinio", "gato", 3, 5.5, (14, 17), 12,
       aliases=["Abyssinian"],
       predisposiciones={"amiloidosis_renal", "atrofia_retina_progresiva"},
       notas="Amiloidosis renal — hidratación alta preventiva."),

    _b("birmano_sagrado", "Birmano Sagrado", "gato", 3.5, 6, (12, 16), 12,
       aliases=["Sagrado de Birmania", "Sacred Birman"],
       predisposiciones={"neuropatia_hipopotasemica"},
       notas=""),

    _b("russian_blue", "Russian Blue", "gato", 3, 5.5, (15, 20), 12,
       aliases=["Azul Ruso", "Russian"],
       predisposiciones={"obesidad_tendencia"},
       notas="Tendencia a sobrepeso — control calórico."),

    _b("noruego_bosque", "Noruego del Bosque", "gato", 4, 9, (14, 16), 18,
       aliases=["Norwegian Forest Cat", "Wegie"],
       predisposiciones={"glucogenosis_tipo4", "cardiomiopatia_hipertrofica"},
       notas="Raza grande — madurez a los 18 meses."),

    _b("angora_turco", "Angora Turco", "gato", 2.5, 5, (12, 18), 12,
       aliases=["Turkish Angora"],
       predisposiciones={"sordera_gen_blanco", "ataxia_cerebelosa"},
       notas=""),

    _b("devon_rex", "Devon Rex", "gato", 2.7, 4.5, (14, 17), 12,
       aliases=["Devon"],
       predisposiciones={"miopatia_devon_rex", "hipopotasemia"},
       notas=""),

    _b("cornish_rex", "Cornish Rex", "gato", 2.5, 4.5, (14, 16), 12,
       aliases=["Cornish"],
       predisposiciones=set(),
       notas=""),

    _b("bombay", "Bombay", "gato", 2.5, 5, (15, 20), 12,
       aliases=[],
       predisposiciones={"brachycephalic_syndrome_leve"},
       notas=""),

    _b("tonkines", "Tonkinés", "gato", 2.7, 5.5, (14, 18), 12,
       aliases=["Tonkinese", "Tonkines"],
       predisposiciones=set(),
       notas=""),

    _b("somali", "Somalí", "gato", 3, 5.5, (11, 16), 12,
       aliases=["Somali"],
       predisposiciones={"atrofia_retina_progresiva"},
       notas=""),

    _b("balines", "Balinés", "gato", 2.5, 5, (12, 20), 12,
       aliases=["Balinese", "Siamés Pelo Largo"],
       predisposiciones={"amiloidosis_hepatica"},
       notas=""),

    _b("manx", "Manx", "gato", 3, 5.5, (14, 16), 12,
       aliases=["Manx sin cola"],
       predisposiciones={"manx_syndrome", "artritis_espinal"},
       notas=""),

    _b("chartreux", "Chartreux", "gato", 3, 7.5, (12, 15), 12,
       aliases=["Cartujo"],
       predisposiciones={"luxación_patelar"},
       notas=""),

    _b("american_shorthair", "American Shorthair", "gato", 3.5, 7.5, (15, 20), 12,
       aliases=["ASH"],
       predisposiciones={"cardiomiopatia_hipertrofica"},
       notas=""),

    _b("selkirk_rex", "Selkirk Rex", "gato", 3, 7, (13, 15), 12,
       aliases=[],
       predisposiciones={"poliquistosis_renal", "cardiomiopatia_hipertrofica"},
       notas=""),

    _b("munchkin", "Munchkin", "gato", 2.5, 4, (12, 15), 12,
       aliases=["Gato patas cortas"],
       predisposiciones={"lordosis", "problemas_articulares_patas_cortas"},
       notas="Vigilar peso — estructura ósea no soporta sobrepeso."),

    _b("laperm", "LaPerm", "gato", 2.5, 5, (10, 15), 12,
       aliases=[],
       predisposiciones=set(),
       notas=""),

    _b("turkish_van", "Turkish Van", "gato", 3, 8, (12, 17), 12,
       aliases=["Van Turco"],
       predisposiciones={"cardiomiopatia_hipertrofica"},
       notas=""),

    _b("burmeses", "Burmés", "gato", 3, 5.5, (16, 18), 12,
       aliases=["Burmese", "Burmés"],
       predisposiciones={"hipopotasemia", "diabetes_mellitus",
                         "anemia_hemolítica"},
       notas="Predisposición a diabetes — control de carbohidratos."),

    _b("singapura", "Singapura", "gato", 2, 3.5, (14, 15), 12,
       aliases=["Singapura"],
       predisposiciones={"inercia_uterina"},
       notas="Gato de pequeño tamaño — raciones pequeñas ajustadas."),

    _b("ragamuffin", "RagaMuffin", "gato", 4, 9, (12, 18), 18,
       aliases=["Ragamuffin"],
       predisposiciones={"cardiomiopatia_hipertrofica"},
       notas="Raza grande — madurez a los 18 meses."),

    _b("american_curl", "American Curl", "gato", 3, 5, (12, 20), 12,
       aliases=["American Curl"],
       predisposiciones=set(),
       notas=""),

    _b("ocicat", "Ocicat", "gato", 2.7, 6.5, (12, 14), 12,
       aliases=[],
       predisposiciones={"amiloidosis"},
       notas=""),

    # ---- CRIOLLO / MESTIZO ----
    _b("criollo_gato", "Criollo / Mestizo", "gato", 2, 8, (12, 18), 12,
       aliases=["Mestizo", "Callejero", "Criollo", "Gato Común", "SRD"],
       predisposiciones=set(),
       notas="Sin predisposiciones genéticas conocidas. Evaluación nutricional individual.",
       es_criollo=True),
]


# ---------------------------------------------------------------------------
# Índices de búsqueda
# ---------------------------------------------------------------------------

BREED_CATALOG: dict[str, BreedInfo] = {
    breed.id: breed
    for breed in (_DOGS + _CATS)
}

# Índice invertido alias → breed_id para búsqueda rápida
_ALIAS_INDEX: dict[str, str] = {}
for _breed in (_DOGS + _CATS):
    _ALIAS_INDEX[_breed.nombre.lower()] = _breed.id
    for _alias in _breed.aliases:
        _ALIAS_INDEX[_alias.lower()] = _breed.id

# Predisposiciones por breed_id (acceso directo)
BREED_PREDISPOSITIONS: dict[str, frozenset[str]] = {
    breed_id: info.predisposiciones
    for breed_id, info in BREED_CATALOG.items()
}


# ---------------------------------------------------------------------------
# API de búsqueda
# ---------------------------------------------------------------------------

def get_breed(breed_id: str) -> BreedInfo | None:
    """
    Retorna el BreedInfo para un breed_id exacto.
    Retorna None si no existe.
    """
    return BREED_CATALOG.get(breed_id.lower())


def search_breeds(
    query: str,
    especie: str | None = None,
    limit: int = 10,
) -> list[BreedInfo]:
    """
    Busca razas por nombre o alias (case-insensitive, substring).

    Args:
        query: Texto de búsqueda. Ejemplos: "labrador", "cri", "frances".
        especie: Filtrar por especie: "perro" | "gato" | None (ambas).
        limit: Máximo de resultados a retornar.

    Returns:
        Lista de BreedInfo ordenada por relevancia (match exacto primero).
    """
    q = query.lower().strip()
    results: list[tuple[int, BreedInfo]] = []

    for breed in (_DOGS + _CATS):
        if especie and breed.especie != especie:
            continue

        score = 0
        # Match exacto en nombre
        if breed.nombre.lower() == q:
            score = 100
        # Match exacto en alias
        elif q in [a.lower() for a in breed.aliases]:
            score = 90
        # Substring en nombre
        elif q in breed.nombre.lower():
            score = 70
        # Substring en algún alias
        elif any(q in a.lower() for a in breed.aliases):
            score = 50
        # Criollo match parcial
        elif breed.es_criollo and ("criollo" in q or "mestizo" in q or "srd" in q):
            score = 80

        if score > 0:
            results.append((score, breed))

    results.sort(key=lambda x: x[0], reverse=True)
    return [b for _, b in results[:limit]]
