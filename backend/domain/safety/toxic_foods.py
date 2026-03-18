"""
Listas de alimentos tóxicos para perros y gatos — NutriVet.IA
Constitution REGLA 1: estas listas son la ÚNICA fuente de verdad sobre toxicidad.
El LLM NUNCA decide si un alimento es tóxico.

NUNCA modificar sin validación veterinaria de Lady Carolina Castañeda (MV, BAMPYSVET).
"""

# Nombres canónicos en español + nombres científicos + aliases regionales
# Cada entrada puede ser nombre común, científico o alias alternativo.

TOXIC_DOGS: frozenset[str] = frozenset({
    # Allium spp. — anemia hemolítica
    "cebolla", "cebolla cabezona", "cebollín", "cebolleta", "puerro",
    "ajo", "ajo en polvo",
    "allium sativum",   # nombre científico ajo
    "allium cepa",      # nombre científico cebolla
    "allium porrum",    # nombre científico puerro
    "allium schoenoprasum",  # nombre científico cebollín
    # Uvas y derivados — falla renal aguda
    "uvas", "uva", "pasas", "pasa", "vitis vinifera",
    # Xilitol — hipoglucemia severa + falla hepática
    "xilitol", "xylitol",
    # Chocolate y derivados — teobromina + cafeína
    "chocolate", "cacao", "cocoa", "theobroma cacao",
    "cafeína", "café", "té negro", "té verde",
    # Nueces
    "macadamia", "nuez de macadamia",
    # Aguacate (persin) — cardiotoxicidad y daño muscular
    "aguacate", "palta", "persea americana",
    # Otros
    "alcohol", "etanol",
    "nuez moscada", "moscada",
    "masa de levadura cruda", "levadura cruda",
    "sal en exceso",   # referencia conceptual — no bloquea "sal" en bajas dosis
    "xilitol en arándanos procesados",  # alias de contexto
    "uvas de corinto", "grosellas",  # confusión frecuente
})

TOXIC_CATS: frozenset[str] = frozenset({
    # Allium spp. — anemia hemolítica (más sensibles que perros)
    "cebolla", "cebollín", "cebolleta", "puerro",
    "ajo", "ajo en polvo",
    "allium sativum", "allium cepa", "allium porrum", "allium schoenoprasum",
    # Uvas y derivados
    "uvas", "uva", "pasas", "pasa", "vitis vinifera",
    # Lilium spp. — falla renal aguda (CRÍTICO en gatos — incluso el polen)
    "lilium", "lirio", "azucena", "lilium longiflorum",
    "hemerocallis",    # lirio de día — también nefrotóxico
    # Chocolate
    "chocolate", "cacao", "cocoa", "theobroma cacao",
    "cafeína", "café", "té negro", "té verde",
    # Xilitol
    "xilitol", "xylitol",
    # AINES y analgésicos — metabolismo hepático limitado en gatos
    "paracetamol", "acetaminofén", "acetaminophen",
    "aspirina", "ácido acetilsalicílico",
    "ibuprofeno",
    # Propylene glycol
    "propilenglicol", "propylene glycol",
    # Aceites esenciales (dosis terapéuticas)
    "aceite esencial de tea tree", "aceite de árbol de té",
    "aceite esencial de lavanda",
    "aceite esencial de eucalipto",
    # Otros
    "alcohol", "etanol",
    "uvas de corinto",
})

# Aliases y nombres científicos mapeados al nombre canónico tóxico
# Usados para la detección de nombres científicos en ingredientes
SCIENTIFIC_ALIASES: dict[str, str] = {
    "vitis vinifera": "uvas",
    "allium sativum": "ajo",
    "allium cepa": "cebolla",
    "allium porrum": "puerro",
    "allium schoenoprasum": "cebollín",
    "theobroma cacao": "chocolate",
    "persea americana": "aguacate",
    "hemerocallis": "lilium",
    "acetaminophen": "paracetamol",
    "xylitol": "xilitol",
    "propylene glycol": "propilenglicol",
    "palta": "aguacate",
    "cocoa": "chocolate",
    "cacao": "chocolate",
}
