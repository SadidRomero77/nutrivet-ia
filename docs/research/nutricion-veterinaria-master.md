# Nutrición Veterinaria — Base de Conocimiento Clínico Master
## NutriVet.IA — Documento de Referencia para Prompts del Agente

**Fuentes primarias**: NRC 2006, AAFCO 2023, AAHA Guidelines, ACVIM Consensus, IRIS 2023, Merck Veterinary Manual, PMC peer-reviewed papers
**Validación clínica requerida**: Lady Carolina Castañeda (MV, BAMPYSVET)
**Última compilación**: 2026-03-21

---

## PARTE 1 — FÓRMULAS ENERGÉTICAS COMPLETAS

### 1.1 RER — Resting Energy Requirement

```
RER = 70 × peso_kg^0.75   ← fórmula estándar NRC (todos los pesos)
RER = 30 × peso_kg + 70   ← aproximación lineal válida para 2–45 kg
```

**Valores de referencia RER por peso:**

| Peso (kg) | RER (kcal/día) | | Peso (kg) | RER (kcal/día) |
|-----------|----------------|-|-----------|----------------|
| 1         | 70             | | 15        | 530            |
| 2         | 118            | | 20        | 662            |
| 3         | 160            | | 25        | 787            |
| 4         | 198            | | 30        | 908            |
| 5         | 234            | | 35        | 1025           |
| 6         | 268            | | 40        | 1139           |
| 7         | 301            | | 45        | 1250           |
| 8         | 333            | | 50        | 1358           |
| 9         | 364            | | 60        | 1569           |
| 10        | 394            | | 70        | 1774           |
| 10.08     | 396 ← SALLY    | | 80        | 1973           |

---

### 1.2 Factores DER — PERROS

**DER = RER × Factor_vida × Factor_edad × Factor_BCS**

#### Factor_vida por actividad y estado reproductivo:

| Actividad | Esterilizado | No esterilizado | Notas clínicas |
|-----------|-------------|-----------------|----------------|
| Sedentario (toy/apartment dog) | **1.2–1.4** | **1.6** | Ajustar a 1.2 si hay sobrepeso |
| Moderado (paseos diarios 30–60 min) | **1.6** | **2.0** | Estándar para la mayoría |
| Activo (ejercicio diario >60 min) | **1.8–2.0** | **2.4** | Perros de campo/trabajo ligero |
| Muy activo (deporte, trabajo intenso) | **2.4** | **3.0** | Sled dogs, perros de pastoreo |
| Perro de trabajo (policía, servicio) | **2.0–5.0** | **2.0–5.0** | Varía por intensidad del trabajo |
| Gestación (semanas 1–5) | —  | **1.8** | Igual que adulto activo |
| Gestación (semanas 6–9) | — | **3.0** | Fetos aumentan ~30% la demanda |
| Lactancia pico (semana 3–4) | — | **4.0–8.0** | Depende de número de cachorros |
| Lactancia declinante (semana 6–8) | — | **3.0–5.0** | Cachorros empiezan sólidos |

**Referencia NutriVet.IA (caso Sally):**
Sally = sedentario + esterilizado → Factor_vida = 1.348
DER = 396 × 1.348 = 534 kcal/día ✓

#### Factor_edad — PERROS:

| Etapa | Edad | Factor | Notas |
|-------|------|--------|-------|
| Cachorro muy temprano | 0–3 meses | **3.0** | Máxima demanda metabólica |
| Cachorro en crecimiento | 4–12 meses | **2.0** | Usar peso adulto estimado para el cálculo |
| Adulto joven | 13–24 meses | **1.2** | |
| Adulto | 25 meses – 7 años | **1.0** | Referencia estándar |
| Senior (tallas pequeñas/medianas) | >10 años | **0.9–1.0** | Tasa metabólica basal disminuye |
| Senior (tallas grandes/gigantes) | >7 años | **0.9** | Envejecimiento más temprano |

#### Factor_BCS — PERROS:

| BCS | Clasificación | Factor | Cálculo adicional |
|-----|--------------|--------|-------------------|
| 1 | Muy delgado | **1.6** | Aumentar 60% sobre RER |
| 2 | Delgado | **1.4** | |
| 3 | Bajo peso leve | **1.2** | |
| 4 | Ideal bajo | **1.0** | Mantenimiento |
| 5 | Ideal | **1.0** | Mantenimiento |
| 6 | Sobrepeso leve | **0.9** | Usar peso real |
| 7 | Sobrepeso moderado | **0.8** | **Usar peso ideal estimado** |
| 8 | Obeso | **0.75** | **Usar peso ideal estimado** |
| 9 | Obesidad severa | **0.7** | **Usar peso ideal estimado** |

**Estimación de peso ideal desde BCS:**
```
BCS 5 → peso_ideal = peso_actual
BCS 6 → peso_ideal = peso_actual × 0.91   (exceso ~10%)
BCS 7 → peso_ideal = peso_actual × 0.85   (exceso ~15–18%)
BCS 8 → peso_ideal = peso_actual × 0.77   (exceso ~23–30%)
BCS 9 → peso_ideal = peso_actual × 0.67   (exceso ~35–50%)
```

---

### 1.3 Factores DER — GATOS

#### Factor_vida — GATOS:

| Actividad | Esterilizado | No esterilizado | Notas |
|-----------|-------------|-----------------|-------|
| Indoor (sedentario) | **1.0–1.2** | **1.4** | Gatos de apartamento |
| Indoor/Outdoor (semi-activo) | **1.2–1.4** | **1.6** | Acceso a exterior parcial |
| Outdoor (activo libre) | **1.4–1.6** | **1.8** | Gatos callejeros/rurales |
| Gatito 2–6 meses | — | **2.5** | Ad libitum recomendado |
| Gatito 6–12 meses | — | **2.0** | |
| Senior (>10 años) | **1.1–1.4** | **1.1–1.4** | Algunos seniors bajan, otros suben |
| Gestación | — | **1.6–2.0** | Aumenta con la semana |
| Lactancia | — | **≥2.0** | Ad libitum recomendado en gatas |

**Nota crítica felina**: El gato indoor esterilizado con BCS ideal → Factor = 1.2. Reducir a 1.0 si hay sobrepeso.

#### Factor_BCS — GATOS (misma escala 1–9):

| BCS | Factor | Notas |
|-----|--------|-------|
| 1–3 | **1.2–1.6** | Aumentar calorías; investigar causa de bajo peso |
| 4–5 | **1.0** | Mantenimiento |
| 6–7 | **0.8** | Usar peso ideal. Máx pérdida: 1%/semana |
| 8–9 | **0.7–0.8** | Usar peso ideal. NUNCA reducir >40% DER en gatos |

---

## PARTE 2 — REQUERIMIENTOS NRC/AAFCO POR ESPECIE

### 2.1 Proteína — Perros

| Etapa de vida | AAFCO % MS | AAFCO g/1000 kcal | NRC mínimo g/1000 kcal | Recomendación práctica |
|---------------|-----------|-------------------|------------------------|------------------------|
| Cachorro (todas las etapas) | **22.5%** | **56.3** | 45 | 25–35% MS para BARF |
| Adulto mantenimiento | **18.0%** | **45.0** | 20 | 22–28% MS óptimo |
| Senior (>7 años) | 18.0% | 45.0 | **25–35** | ↑ Proteína anti-sarcopenia |
| Gestación/Lactancia | **22.5%** | **56.3** | 45–55 | Alta calidad y digestibilidad |
| Pérdida de peso | — | — | — | **≥30% MS** para preservar músculo |
| ERC moderada | — | — | — | **12–17% MS** alta digestibilidad |
| ERC severa | — | — | — | **14–20% MS** (nunca <12%) |

### 2.2 Proteína — Gatos

| Etapa de vida | AAFCO % MS | AAFCO g/1000 kcal | Notas críticas |
|---------------|-----------|-------------------|----------------|
| Gatito/Reproducción | **30.0%** | **75.0** | Mínimo — muchos gatitos necesitan más |
| Adulto | **26.0%** | **65.0** | **Mucho mayor que perros** |
| Senior (>10 años) | 26.0% | 65.0 | No reducir — riesgo sarcopenia severo |
| Gato diabético tipo 2 | — | — | **>40–45% MS** — alta proteína, bajos carbs |
| Gato ERC temprana | — | — | **26–30% MS** alta digestibilidad (NO restringir agresivamente) |
| Gato ERC avanzada | — | — | **20–26% MS** mínimo absoluto |

**REGLA NO NEGOCIABLE FELINA**: Nunca eliminar completamente la proteína animal en gatos. Un solo ayuno sin arginina → hiperamonemia en horas.

### 2.3 Grasa

| Especie/Etapa | AAFCO mínimo % MS | Máximo recomendado | Condiciones que modifican |
|---------------|------------------|--------------------|---------------------------|
| Perro adulto | **5.5%** | Sin límite AAFCO | Pancreatitis: <10%; Hiperlipidemia: <12% |
| Cachorro perro | **8.5%** | — | DHA obligatorio para cerebro |
| Gato adulto | **9.0%** | Sin límite AAFCO | Pancreatitis felina: <15% (evidencia mixta) |
| Gatito | **9.0%** | — | DHA esencial |
| Pérdida de peso | — | 10–15% | Alta proteína compensa saciedad |

### 2.4 Ácidos Grasos Esenciales

| Nutriente | Especie | AAFCO (% MS) | Dosis terapéutica | Fuentes LATAM |
|-----------|---------|-------------|-------------------|---------------|
| Ácido linoleico (omega-6) | Perro | **1.1%** | — | Girasol, pollo |
| Ácido alfa-linolénico (omega-3) | Perro | **0.06%** | — | Linaza, sardinas |
| EPA + DHA | Perro | No especificado AAFCO | **40–100 mg/kg/día terapéutico** | Sardinas, aceite pescado |
| Ácido linoleico (omega-6) | Gato | **0.6%** | — | Pollo, girasol |
| Ácido araquidónico | Gato | **0.02%** | — | Hígado, carne |
| EPA + DHA | Gato | No especificado | **40–100 mg/kg/día** | Sardinas, atún moderado |

**Dosis terapéuticas de omega-3 EPA+DHA por condición:**

| Condición | Dosis mg/kg/día | Evidencia | Tiempo efecto |
|-----------|----------------|-----------|---------------|
| Mantenimiento salud | 20–30 | B | — |
| Artritis/OA | **40–100** | A (revisión 2022: beneficio en 18/20 estudios) | 4–8 semanas |
| Dermatitis atópica | **40–100** | A | 8–12 semanas |
| ERC (nefroprotección) | **40–80** | B | Variable |
| Cáncer (antiinflamatorio) | **40–100** | B | Variable |
| CDS cognitiva | **40** DHA específico | B | 8–16 semanas |
| Hiperlipidemia | **20–40** (formulación concentrada) | B | 4–8 semanas |

### 2.5 Minerales Críticos — Perros

| Mineral | AAFCO mínimo (% MS) | AAFCO máximo | NRC mínimo | Notas clínicas |
|---------|--------------------|-----------|-----------:|----------------|
| **Calcio** | **0.5%** adulto / **1.2%** cachorro | **2.5%** / **1.8%** | 0.5% | Cachorro raza grande: 0.8–1.2% exacto |
| **Fósforo** | **0.4%** adulto / **1.0%** cachorro | — | 0.4% | ERC: 0.2–0.5% según estadio |
| **Ratio Ca:P** | **1:1 mínimo** | **2:1 máximo** | 1.2:1 | Cachorro raza grande: 1.1:1 a 1.4:1 |
| Magnesio | 0.04% | — | 0.04% | |
| Sodio | 0.08% | — | — | ERC/cardiaco: reducir a <0.2% |
| Potasio | 0.6% | — | — | ERC: monitorizar (hipo o hiper) |
| Hierro | 40 mg/kg | — | 7.5 mg/1000 kcal | |
| Cobre | 7.3 mg/kg | — | 1.5 mg/1000 kcal | **Razas: Bedlington, Labrador, Doberman → hepatotoxicidad por acúmulo** |
| Zinc | 120 mg/kg | — | 15 mg/1000 kcal | BARF: 15–25 mg/1000 kcal (biodisponible) |
| Yodo | 1.5 mg/kg | — | 0.23 mg/1000 kcal | Exceso también es goitrógeno |
| Selenio | 0.35 mg/kg | **2.0 mg/kg** | 0.08 mg/1000 kcal | **Margen estrecho — toxicidad real** |

### 2.6 Vitaminas Críticas — Ambas Especies

| Vitamina | Perro (AAFCO) | Gato (AAFCO) | Máximo | Notas |
|----------|--------------|-------------|--------|-------|
| **A (retinol)** | 5000 IU/kg | 9000 IU/kg | **250,000 IU/kg** | Hígado: fuente excelente pero limitar |
| **D3** | 500 IU/kg | 750 IU/kg | **10,000 IU/kg** | **Perros y gatos NO sintetizan por sol** |
| **E** | 50 IU/kg | 40 IU/kg | — | Antioxidante. Aumentar con omega-3 crónico |
| B12 (Cobalamina) | 0.028 mg/kg | 0.020 mg/kg | — | Deficiencia en EII, IPE, Samoyedo, Border Collie |
| B9 (Ácido fólico) | 0.18 mg/kg | 0.75 mg/kg | — | Crítico en gestación |
| **Taurina** | No especificado | **1000 mg/kg dieta seca / 2500 mg/kg dieta húmeda** | — | **ESENCIAL en gatos** |
| **Niacina** | 13.6 mg/kg | **60 mg/kg** | — | Gatos no sintetizan de triptófano |
| **Arginina** | 3.5 g/kg DM | **7.7–15 g/kg DM** | — | Gato: hiperamonemia sin arginina |

---

## PARTE 3 — TABLAS NUTRICIONALES INGREDIENTES LATAM

### 3.1 Proteínas Animales (por 100g peso crudo)

| Ingrediente | kcal | Prot (g) | Grasa (g) | Calcio (mg) | Fósforo (mg) | Zinc (mg) | Taurina (mg) | EPA+DHA (mg) | Notas clínicas clave |
|-------------|------|----------|-----------|-------------|--------------|-----------|--------------|--------------|----------------------|
| Pechuga pollo sin piel | 110 | 23.1 | 1.2 | 11 | 220 | 0.9 | 62 | 30 | Magra estándar. Ca:P = 1:20 → necesita calcio extra |
| Muslo pollo sin piel | 170 | 19.7 | 9.7 | 11 | 196 | 2.1 | 83 | 80 | Más palatabilidad, más zinc |
| Muslo pollo con piel | 215 | 18.6 | 15.3 | 11 | 179 | 1.9 | 80 | 75 | Evitar en pancreatitis/obesidad |
| Pechuga pollo con piel | 172 | 20.8 | 9.3 | 11 | 210 | 1.0 | 65 | 35 | Intermedia |
| **Corazón de pollo** | 185 | 16.3 | 13.0 | 11 | 194 | 6.3 | **681** | 90 | **Principal fuente taurina BARF. Máx 15%.** |
| Hígado de pollo | 119 | 16.9 | 4.8 | 8 | 298 | 2.7 | 115 | 50 | Rico vit A, B12. **Máx 5% dieta (hipervit A)** |
| Molleja de pollo | 118 | 18.2 | 4.3 | 10 | 162 | 3.1 | 130 | 40 | Músculo digestivo, muy digestible |
| Pechuga pavo sin piel | 107 | 24.1 | 0.7 | 12 | 221 | 1.5 | 79 | 35 | La más magra de aves. Buena en pancreatitis |
| Pato pechuga sin piel | 140 | 23.5 | 4.8 | 12 | 203 | 2.3 | 70 | 55 | Proteína novel. Disponibilidad limitada LATAM |
| Huevo entero crudo | 143 | 12.6 | 9.9 | 56 | 198 | 1.1 | 25 | 36 | Clara cruda: avidina une biotina. Mejor cocido |
| Clara de huevo cruda | 52 | 10.9 | 0.2 | 7 | 15 | 0.02 | 8 | 0 | Sin grasa, sin yema. Proteína de alta digestibilidad |
| Yema de huevo cruda | 322 | 15.9 | 26.5 | 129 | 390 | 2.3 | 45 | 180 | Rica en vitaminas liposolubles. Limitar en pancreatitis |
| **Carne magra de res (lomo)** | 158 | 26.1 | 5.3 | 19 | 210 | 4.5 | 50 | 40 | Alta en hierro y zinc. Buena base BARF |
| Costilla de res (con grasa) | 291 | 19.2 | 23.5 | 15 | 170 | 3.8 | 42 | 35 | Alta en grasa. Evitar pancreatitis/hiperlipidemia |
| **Corazón de res** | 112 | 17.7 | 3.9 | 7 | 212 | 1.7 | **862** | 55 | **Mayor fuente taurina conocida** |
| Hígado de res | 135 | 20.4 | 3.6 | 5 | 387 | 4.0 | 68 | 55 | Muy rico en vitamina A, cobre, B12. **Máx 5%** |
| Riñón de res | 99 | 17.4 | 3.1 | 14 | 257 | 1.9 | 45 | 40 | Alto en purinas. Evitar en enfermedad úrica (Dálmata) |
| Lomo de cerdo magro | 143 | 26.0 | 3.5 | 20 | 246 | 2.9 | 62 | 45 | **SIEMPRE cocinar** (Trichinella). Nunca crudo en BARF |
| **Sardina en agua (lata)** | 208 | 24.6 | 11.5 | **382** | 490 | 1.3 | 70 | **1480** | **Mejor fuente omega-3 accesible LATAM** + calcio |
| Atún en agua (lata) | 116 | 25.5 | 0.8 | 11 | 237 | 0.6 | 40 | 180 | Mercurio: limitar en gatos (<2x/semana) |
| Salmón fresco (crudo) | 208 | 20.4 | 13.4 | 12 | 252 | 0.6 | 130 | **2260** | Crudo Pacífico NW: riesgo Neorickettsia. Importado CO: seguro congelado |
| Tilapia/mojarra (cruda) | 96 | 20.1 | 1.7 | 14 | 170 | 0.4 | 40 | 115 | Pez LATAM accesible. Siempre cocinar en Colombia |
| Trucha arcoíris (cruda) | 141 | 19.9 | 6.2 | 67 | 226 | 0.7 | 80 | 680 | Producción Andina (Boyacá, Nariño). Rica omega-3 |
| Conejo (carne) | 136 | 20.1 | 5.6 | 16 | 205 | 1.7 | 55 | 40 | Proteína novel excelente. Magra y digestible |
| Cordero (pierna) | 258 | 25.6 | 16.5 | 17 | 220 | 4.5 | 65 | 55 | Alto en zinc. Disponibilidad limitada en Colombia |

---

### 3.2 Vegetales y Carbohidratos LATAM (por 100g)

| Ingrediente (aliases) | kcal | Prot (g) | Carbs (g) | Fibra (g) | Ca (mg) | P (mg) | IG | Notas clínicas |
|-----------------------|------|----------|-----------|-----------|---------|--------|----|----------------|
| Zanahoria (cruda) | 41 | 0.9 | 9.6 | 2.8 | 33 | 35 | 16 | Bajo IG. Snack ideal. Beta-caroteno |
| **Ahuyama/zapallo/calabaza** | 26 | 1.0 | 6.0 | 0.5 | 21 | 44 | 75 (cocida) | Beta-caroteno. Bajo en fósforo. Buena en ERC |
| Espinaca (cruda) | 23 | 2.9 | 3.6 | 2.2 | 99 | 49 | 15 | **Alta en oxalatos. LIMITAR en cistitis/ERC** |
| Brócoli (crudo) | 34 | 2.8 | 6.6 | 2.6 | 47 | 66 | 10 | **Goitrógeno >10% dieta.** Rico en vitamina C |
| Judías verdes/habichuelas/ejotes | 31 | 1.8 | 7.0 | 2.7 | 37 | 38 | 15 | Excelente fibre. Bajo IG |
| Chayote/guatila/cidra (crudo) | 19 | 0.8 | 4.5 | 1.7 | 17 | 18 | 20 | Muy baja densidad calórica. Hidratante |
| Pepino (crudo) | 15 | 0.7 | 3.6 | 0.5 | 16 | 24 | 15 | Hidratante. Bajo en todo |
| Apio (crudo) | 16 | 0.7 | 3.0 | 1.6 | 40 | 24 | 35 | Bajo en calorías |
| Remolacha/betarraga (cruda) | 43 | 1.6 | 9.6 | 2.8 | 16 | 40 | 64 | **Alta en oxalatos. Evitar en cistitis oxalato** |
| **Papa/patata (cocida, sin piel)** | 87 | 2.0 | 20.1 | 1.8 | 12 | 54 | 78 | **SIEMPRE cocinar.** Piel verde = solanina tóxica |
| **Batata/camote/boniato (cocida)** | 86 | 1.6 | 20.1 | 3.0 | 30 | 47 | 44–61 | Buen carbohidrato. Bajo IG vs papa. Apto diabéticos |
| **Yuca/mandioca (cocida)** | 160 | 1.4 | 38.1 | 1.8 | 16 | 28 | 94 | **IG muy alto → NO en diabéticos.** Siempre cocinar |
| Plátano verde (cocido) | 116 | 1.3 | 28.5 | 2.3 | 3 | 34 | 40 | Almidón resistente (prebiótico). IG bajo |
| Plátano maduro/banano | 89 | 1.1 | 22.8 | 2.6 | 5 | 22 | 65 | Alto azúcar. **LIMITAR en diabéticos** |
| Arroz blanco (cocido) | 130 | 2.7 | 28.2 | 0.4 | 10 | 43 | 73 | **Solo en gastritis aguda.** IG alto |
| Arroz integral (cocido) | 111 | 2.6 | 23.0 | 1.8 | 10 | 83 | 55 | Mejor opción si se usa arroz |
| Avena en hojuelas (cocida) | 71 | 2.5 | 12.0 | 1.7 | 10 | 70 | 55 | Beta-glucano = fibra soluble. Diabetes canina |
| Quinua (cocida, lavada) | 120 | 4.4 | 21.3 | 2.8 | 17 | 152 | 53 | Proteína completa vegetal. Lavar saponinas |
| Manzana sin semillas (cruda) | 52 | 0.3 | 13.8 | 2.4 | 6 | 11 | 38 | Semillas: amígdalina (cianuro). Sin semillas ok |

---

### 3.3 Aceites y Grasas

| Aceite | kcal/100ml | Omega-3 (g) | Omega-6 (g) | Saturadas (g) | Notas |
|--------|-----------|-------------|-------------|---------------|-------|
| Aceite de sardinas/pescado | 902 | **30–35 EPA+DHA** | 1.5 | 24 | **La mejor fuente omega-3 terapéutico** |
| Aceite de salmón | 902 | **25–30 EPA+DHA** | 1.3 | 20 | Alternativa al de sardinas |
| Aceite de linaza | 884 | 53 ALA | 14 | 9 | ALA solo, gatos no convierten a EPA/DHA |
| Aceite de oliva virgen | 884 | 0.8 ALA | 9.8 | 14 | Omega-9. No es fuente omega-3 |
| Aceite de coco | 862 | ~0 | ~0 | **87** | MCT (C8, C10, C12). Usar con moderación |
| Aceite de girasol | 884 | 0.2 ALA | 65 | 10 | Alto omega-6. No usar como fuente omega-3 |

**Dosis suplementación aceite de pescado por peso:**

| Peso mascota | Dosis mantenimiento | Dosis terapéutica | Fuente equivalente |
|-------------|--------------------|--------------------|-------------------|
| 5 kg | 250–350 mg EPA+DHA | 200–500 mg EPA+DHA | ~35g sardinas/día |
| 10 kg | 400–600 mg | 400–1000 mg | ~70g sardinas/día |
| 20 kg | 700–1000 mg | 800–2000 mg | ~140g sardinas/día |
| 30 kg | 1000–1500 mg | 1200–3000 mg | ~200g sardinas/día |
| Gato 4 kg | 160–240 mg | 160–400 mg | ~25g sardinas/día |

---

## PARTE 4 — PROTOCOLOS CLÍNICOS POR CONDICIÓN MÉDICA (13 CONDICIONES)

### 4.1 DIABETES MELLITUS

#### Fisiopatología nutricional
- **Perros**: Diabetes tipo 1 (destrucción células β pancreáticas). Insulinodependiente. La dieta controla la velocidad de absorción de glucosa para sincronizarse con la insulina exógena.
- **Gatos**: Diabetes tipo 2 (resistencia a insulina, similar a DM2 humana). La dieta baja en carbohidratos puede lograr **remisión completa en 30–90% de gatos** (Rand et al., 2004; Mazzaferro et al., 2003).

#### PERRO DIABÉTICO — Objetivos y números exactos

**Energía**: DER estándar. Si hay obesidad comórbida → calcular sobre peso ideal.

**Fibra**:
- Fibra soluble mínima: **3–5% MS** (ralentiza absorción de glucosa, reduce pico postprandial)
- Fibra total: **8–17% MS** en perros con sobrepeso
- Fibra total: **5–12% MS** en perros con normopeso
- Fuentes: cáscara de psyllium (1–2 tsp/comida mezclado en alimento), avena cocida (beta-glucano), batata, zanahoria cocida, judías verdes

**Carbohidratos de bajo índice glucémico (IG <55)**:
- Avena cocida (IG 55), batata/camote cocida (IG 44–61), arroz integral (IG 55), quinua cocida (IG 53), judías verdes (IG 15), zanahoria cruda (IG 16)

**PROHIBIDO (IG alto o azúcares simples)**:
- Arroz blanco (IG 73), papa/yuca (IG >70), pan, harina refinada, azúcar, miel, panela, melaza, frutas muy dulces (mango maduro, banano muy maduro, uva, piña)

**Proteína**: 25–35% MS, digestibilidad ≥90%
**Grasa**: Moderada. Si hay pancreatitis concomitante: <10% MS
**Timing CRÍTICO**: Alimentar en el momento de la inyección de insulina. NO variar cantidad, ingredientes ni horario. Variación → picos glucémicos impredecibles.
**Comidas**: 2 veces/día (sincronizado con insulina) o según protocolo veterinario.

#### GATO DIABÉTICO — Objetivos y números exactos

**OPUESTO al perro**:
- **Carbohidratos**: Máximo **5–10% MS** (idealmente <5% MS). El gato es carnívoro obligado con gluconeogénesis hepática constante.
- **Proteína**: **>40–45% MS**. Alta proteína baja en carbohidratos → mayor tasa de remisión diabética.
- **Grasa**: Moderada-alta como fuente energética principal.
- **NO usar**: Dieta alta en fibra (indicada en perros, contraproducente en gatos).
- Dieta húmeda superior a seca (menor contenido de carbohidratos en paté).

**Señales de que la dieta funciona en gato diabético**: Reducción gradual de dosis de insulina → consultar vet antes de ajustar.

#### Ingredientes por categoría

```
DIABETES_PERRO_PERMITIDOS:
  proteinas: ["pollo sin piel cocido", "pavo", "res magra", "huevo cocido", "sardina en agua", "trucha"]
  carbohidratos_bajo_IG: ["batata cocida", "avena cocida", "arroz integral", "quinua", "judías verdes", "zanahoria"]
  fibra_soluble: ["psyllium", "avena", "batata"]
  vegetales_permitidos: ["brócoli cocido", "espinaca cocida moderada", "pepino", "calabacín"]

DIABETES_PERRO_PROHIBIDOS:
  ["azúcar", "miel", "panela", "melaza", "xilitol", "arroz blanco", "papa", "yuca",
   "pan", "galletas", "harina de trigo", "mango maduro", "banano maduro", "piña",
   "uvas", "pasas", "comida de mesa con condimentos"]

DIABETES_GATO_PERMITIDOS:
  proteinas: ["pollo sin piel", "pavo", "res magra", "atún (moderado)", "sardina", "salmón", "conejo"]
  grasas: ["aceite de sardinas/pescado"]
  vegetales_minimos: ["pocos vegetales — el gato no los necesita"]

DIABETES_GATO_PROHIBIDOS:
  ["cualquier carbohidrato alto", "arroz", "maíz", "trigo", "papa", "batata en exceso",
   "azúcar", "miel", "frutas dulces", "dietas secas de kibble estándar"]
```

---

### 4.2 HIPOTIROIDISMO

#### Fisiopatología nutricional
Deficiencia de T3/T4 reduce tasa metabólica basal 30–40%. Consecuencias: obesidad, dislipidemia, estreñimiento, mixedema. La dieta no trata el hipotiroidismo (necesita levotiroxina) pero minimiza complicaciones.

**Nota de especie**: El hipotiroidismo primario afecta principalmente a perros. En gatos, el hipertiroidismo es la alteración tiroidea más común (manejo nutricional diferente).

#### Objetivos nutricionales

**Calorías**: Reducir **10–20% del DER** calculado (la tasa metabólica está disminuida).
Si el perro tiene BCS ≥ 7 (muy frecuente en hipotiroidismo): calcular sobre peso ideal.

**Goitrógenos — qué evitar/limitar**:

| Alimento | Interferencia | Acción |
|----------|--------------|--------|
| Soya (todas las formas) | **Alta** | ELIMINAR de la dieta |
| Semillas de lino sin procesar en exceso | **Alta** | Limitar o procesar |
| Mijo, sorgo | **Media-alta** | Evitar como base de la dieta |
| Brócoli crudo, coliflor cruda, col cruda | **Media** | COCINAR (inactiva parcialmente) — máx 10% |
| Kale/col rizada cruda | **Media** | Cocinar o evitar |
| Rábano, nabo | **Media** | Moderar |
| Espinaca | **Baja** | Permitida con moderación |

*Nota*: Los goitrógenos interfieren con la absorción de yodo por la tiroides. En perros bajo tratamiento con levotiroxina, el impacto es menor pero real con consumo elevado crónico.

**Nutrientes de apoyo tiroideo**:
- **Selenio**: Cofactor enzimático para conversión T4→T3. Fuentes: sardinas (0.05 mg/100g), res (0.02 mg/100g), riñones. No suplementar sin análisis (toxicidad con exceso).
- **Zinc**: Cofactor T4→T3. Fuentes: res, cordero (4.5 mg/100g), semillas de calabaza. Dosis: 2–3 mg/kg/día.
- **Omega-3**: Reduce inflamación autoinmune subyacente. Dosis estándar: 40 mg/kg/día.
- **Yodo**: Fuentes naturales moderadas (pescado, mariscos). **NO suplementar yodo sin control veterinario** — tanto el déficit como el exceso suprimen la tiroides.

**Fibra moderada**: El hipotiroidismo causa estreñimiento. Fibra soluble moderada (avena, batata, judías verdes).

**Grasa**: Moderar saturadas. El hipotiroidismo predispone a hiperlipidemia. Si hay hipercolesterolemia/hipertrigliceridemia concomitante: <12% MS.

**Proteína**: Mantener o aumentar ligeramente (25–30% MS) para contrarrestar el catabolismo inducido por hipotiroidismo.

```
HYPOTHYROID_PERMITTED:
  proteinas: ["pollo sin piel cocido", "pavo", "res magra", "pescado (sin exceso de yodo)"]
  carbohidratos: ["batata cocida", "arroz integral", "avena cocida", "judías verdes"]
  suplementos: ["aceite de pescado (omega-3)", "zinc (si déficit)", "selenio (si déficit, con control vet)"]

HYPOTHYROID_AVOID:
  ["soya en cualquier forma", "tofu", "mijo", "sorgo",
   "brócoli/coliflor/col CRUDOS (cocinar está bien en moderación)",
   "suplementos de yodo sin supervisión", "alimentos muy calóricos"]
```

---

### 4.3 CÁNCER (ONCOLOGÍA NUTRICIONAL)

#### Fisiopatología nutricional — Efecto Warburg
Las células cancerosas dependen de glucólisis anaeróbica (glucosa) para energía, incluso en presencia de oxígeno. Reducir carbohidratos "starva" las células tumorales con menor impacto en el organismo normal. Los tejidos normales pueden usar cuerpos cetónicos y ácidos grasos; las células tumorales no.

#### Objetivos nutricionales

**Carbohidratos**: REDUCIR significativamente → **<20% de energía total** (objetivo <10%).
**Proteína**: **30–40% MS** para combatir caquexia cancerosa (pérdida de masa muscular).
**Grasa**: **>35–40% MS** — fuente energética alternativa a carbohidratos.
**Omega-3 EPA+DHA**:
- Dosis terapéutica: **40–100 mg/kg/día** EPA+DHA combinados
- Efectos documentados: anti-inflamatorio, anti-caquéxico, anti-neoangiogénesis
- Evidencia: Ogilvie et al. (estudios en linfoma canino, 1996–2003): EPA a 2.8 g/día mejoró respuesta a quimioterapia y supervivencia

**Antioxidantes durante quimioterapia**: CONTROVERSIA CLÍNICA.
- Algunos agentes quimioterapéuticos actúan por estrés oxidativo → antioxidantes en altas dosis podrían interferir
- **Regla conservadora**: No suplementar vitamina E >100 IU/kg ni vitamina C >250 mg/kg durante quimioterapia sin aprobación del oncólogo
- Antioxidantes de la dieta (vegetales, frutas) a dosis normales: generalmente aceptados

**Calorías**: AUMENTAR para combatir caquexia. Meta: mantener peso y masa muscular. Si hay anorexia → estimulantes apetito (mirtazapina, grelina — decisión veterinaria).

**Por tipo de tumor**:
- Linfoma: alta evidencia de beneficio con omega-3
- Osteosarcoma: alta proteína para mantener masa
- Tumores GI: dieta muy digestible, pequeñas porciones frecuentes, baja en grasa
- Tumores hepáticos: proteína alta digestibilidad, restricción aromáticos

```
CANCER_PERMITTED:
  proteinas: ["pollo sin piel", "pavo", "res magra", "huevo", "pescado graso", "conejo"]
  grasas: ["aceite de sardinas/pescado (fuente EPA+DHA)", "yema de huevo (omegas)"]
  vegetales_bajo_carb: ["brócoli", "espinaca cocida", "judías verdes", "pepino"]
  EVITAR_carbohidratos_altos: ["arroz", "papa", "maíz", "azúcar", "cereales"]
```

---

### 4.4 ENFERMEDAD ARTICULAR (OSTEOARTRITIS, DISPLASIA)

#### Fisiopatología nutricional
La OA implica inflamación articular crónica y degradación de cartílago. La nutrición es coadyuvante — no cura la condición pero reduce el dolor y ralentiza la progresión.

#### Objetivos nutricionales — con evidencia

**Omega-3 EPA+DHA** (Evidencia A — 18/20 estudios positivos, revisión sistemática 2022):
- Dosis efectiva: **40–100 mg/kg/día EPA+DHA**
- EPA inhibe COX-2 y LOX → reduce prostaglandinas inflamatorias
- Onset de efecto: 4–8 semanas
- No hay techo de toxicidad documentado en perros/gatos a dosis terapéuticas
- Fuentes: aceite de sardinas/salmón, sardinas en agua, salmón

**Glucosamina + Condroitina** (Evidencia NEGATIVA — 2022 meta-análisis):
- 8/9 estudios sin efecto clínico significativo en dolor
- **AVMA 2024: ya NO los recomienda rutinariamente**
- Pueden incluirse sin daño, pero sin expectativa de beneficio articular real

**Control de peso** (Evidencia A — el factor más importante):
- Cada 1 kg de exceso = 4–5 kg de presión adicional en articulaciones
- Reducción de 6–8% del peso corporal → reducción significativa de dolor en OA
- **Bajar de peso es más efectivo que cualquier suplemento**

**Vitamina E**: 100–400 IU/día (antioxidante articular). Obligatorio junto con omega-3 crónico.

**Para cachorro de raza grande (prevención displasia)**:
- Calcio: **0.8–1.2% MS** exacto (ni más, ni menos)
- Ratio Ca:P: **1.1:1 a 1.4:1**
- Cachorros NO regulan absorción de calcio como adultos → exceso total se absorbe → deformidades
- **NUNCA suplementar calcio en cachorros de razas grandes** sin calcular el total de la dieta
- Proteína: moderada (exceso acelera crecimiento → más estrés articular)

```
ARTICULAR_PERMITTED:
  omega3_fuentes: ["sardinas en agua", "aceite de sardinas", "salmón", "trucha"]
  suplementos: ["vitamina E (con omega-3)", "aceite pescado calculado por peso"]
  control_peso: "prioridad absoluta si BCS > 5"
  CACHORROS_RAZAS_GRANDES: "NO calcio extra, proteína moderada, AAFCO Large Breed Puppy"
```

---

### 4.5 ENFERMEDAD RENAL CRÓNICA (ERC) — IRIS STAGING

#### Estadificación IRIS 2023 — Criterios diagnósticos

| Estadio | Creatinina perro (mg/dL) | Creatinina gato (mg/dL) | SDMA (µg/dL) | Clínica |
|---------|--------------------------|-------------------------|--------------|---------|
| **I** | <1.4 | <1.6 | <18 | No azotémico. Solo marcadores |
| **II** | 1.4–2.0 | 1.6–2.8 | 18–35 | Azotemia leve. Poliuria/polidipsia |
| **III** | 2.1–5.0 | 2.9–5.0 | 36–54 | Azotemia moderada. Signos clínicos |
| **IV** | >5.0 | >5.0 | >54 | Azotemia severa. Urgencia |

**Sub-clasificación de fósforo sérico**:
- Normofosfatémico: <4.5 mg/dL (I-II), <5.0 (III), <6.0 (IV)
- Hiperfosfatémico: por encima de esos valores → ajustar dieta urgente

#### Restricciones nutricionales por estadio IRIS

| Nutriente | Estadio I | Estadio II | Estadio III | Estadio IV |
|-----------|-----------|-----------|-------------|------------|
| **Proteína perro** | Normal (18–25% MS) | 17–20% MS | **14–17% MS** | **12–15% MS** |
| **Proteína gato** | **26–30% MS** (NO restringir) | **24–28% MS** | **20–26% MS** | **18–22% MS** |
| **Fósforo perro** | <0.6% MS | **<0.5% MS** | **<0.4% MS** | **<0.3% MS** |
| **Fósforo gato** | <0.6% MS | **<0.5% MS** | **<0.4% MS** | **<0.3% MS** |
| Sodio | Normal | **<0.3% MS** | **<0.2% MS** | **<0.2% MS** |
| Potasio | Normal | Monitorizar | **Suplementar si <3.5 mEq/L** | Monitorizar hiper/hipo |
| Omega-3 | Recomendado | **40 mg/kg/día** | **40–80 mg/kg/día** | **40–80 mg/kg/día** |
| Hidratación | Dieta húmeda preferida | **Dieta húmeda obligatoria** | **Dieta húmeda + agua extra** | **Máxima hidratación** |

#### REGLA CRÍTICA felina en ERC:
**Estadios I y II en gatos: NO restringir proteína agresivamente.**
Los gatos tienen mayor requerimiento basal de proteína. La restricción prematura → sarcopenia, caquexia → empeora pronóstico. La restricción moderada empieza en estadio III y solo con proteína de alta digestibilidad.

#### Ingredientes con bajo fósforo (preferibles en ERC):
- Clara de huevo (Ca/P = 7/15 mg/100g — excelente ratio) ← **mejor proteína en ERC**
- Pechuga de pollo sin piel (P: 220 mg/100g — moderado)
- Carne magra de res (P: 210 mg/100g)
- Zanahoria, ahuyama/zapallo (P: 35–44 mg/100g — muy bajo)

#### Ingredientes con ALTO fósforo (EVITAR en ERC):
- Hígado (P: 298–387 mg/100g)
- Sardinas en agua (P: 490 mg/100g) — alto en omega-3 pero alto en fósforo → dilema
- Riñón (P: 257 mg/100g)
- Huevo entero (P: 198 mg — yema alta)
- Legumbres (frijoles, lentejas: P: 350–450 mg/100g)
- Queso, lácteos (P: alto)

**Nota sobre fósforo inorgánico**: Los aditivos de fósforo inorgánico en alimentos procesados (E338-E452) tienen biodisponibilidad del 100% vs ~60% del fósforo orgánico en carnes. Evitar alimentos ultraprocesados en ERC.

```
ERC_PERMITTED:
  proteinas_alta_digestibilidad: ["clara de huevo cocida", "pollo sin piel cocido", "res magra"]
  vegetales_bajo_fosforo: ["zanahoria", "ahuyama", "pepino", "chayote", "lechuga"]
  omega3: ["aceite de sardinas (calcular dosis cuidadosamente)", "aceite de salmón puro"]
  hidratacion: ["dieta húmeda preferida", "agua fresca 24/7", "sopas sin sal"]

ERC_PROHIBITED:
  ["hígado", "riñones", "sardinas enteras (alto fósforo)", "legumbres", "lácteos en exceso",
   "embutidos y carnes procesadas", "alimentos con aditivos de fósforo", "sal añadida"]
```

---

### 4.6 HEPATOPATÍA Y HIPERLIPIDEMIA

#### HEPATOPATÍA — Fisiopatología
El hígado enfermo tiene capacidad reducida para: metabolizar aminoácidos (aromáticos → amoniaco → encefalopatía), sintetizar glucosa (hipoglucemia), producir bilis (malabsorción de grasas), desintoxicar.

#### Hepatopatía — Objetivos nutricionales

**Proteína**:
- Sin encefalopatía hepática (EH): **22–28% MS**, alta calidad/digestibilidad. El hígado necesita aminoácidos para regenerarse.
- Con encefalopatía hepática: **14–18% MS**, predominantemente proteína vegetal o láctea (caseína, tofu) — menor carga de aminoácidos aromáticos (fenilalanina, tirosina, triptófano).
- Fuentes preferidas sin EH: huevo (más seguro, mínimos aromáticos relativos), pescado blanco, pollo magro.
- Fuentes a REDUCIR: carne de res grasa, hígado, cerdo (altos en aromáticos).

**Grasa**: Moderada a baja: **<20% MS** sin esteatosis; <15% con hígado graso.
Permitir MCT (aceite de coco moderado) — bypass del sistema portal hepático.

**Carbohidratos**: Preferir bajo IG, **4–6 comidas pequeñas/día** para reducir carga metabólica hepática y evitar hipoglucemia.

**Vitaminas liposolubles**: La enfermedad hepática altera la absorción. Suplementar A, D, E, K bajo supervisión veterinaria.
**Vitamina E**: Hepatoprotector. Dosis: 10 IU/kg/día.
**SAMe (S-adenosilmetionina)**: Antioxidante hepático documentado. 400–1200 mg/día (vía oral).
**Zinc**: Reduce absorción intestinal de cobre. Útil en hepatopatías por cobre.

#### Razas con acumulación de cobre — RESTRICCIÓN ADICIONAL:
**Bedlington Terrier, West Highland White Terrier, Labrador (algunos linajes), Doberman, Dálmata, Skye Terrier**
→ **ELIMINAR**: hígado de cualquier especie, mariscos, nueces, chocolate
→ REDUCIR: todas las vísceras, legumbres
→ VERIFICAR: cobre en análisis sérico semestral

#### HIPERLIPIDEMIA — Objetivos nutricionales

**Razas predispuestas**: Miniature Schnauzer (>30% prevalencia en adultos), Beagle, Shetland Sheepdog, Briard.

**Grasa**: **Restricción crítica → <10–12% MS**
**Omega-3**: Paradójico pero beneficioso — EPA/DHA reducen triglicéridos séricos hasta 25%. Administrar como suplemento concentrado de EPA+DHA, no como aceite crudo (que tiene demasiada grasa total).
**Fibra soluble**: Beta-glucano (avena), psyllium — reducen absorción de colesterol. Meta: 3–5% MS fibra soluble.

```
HEPATOPATIA_PERMITTED:
  proteinas_sin_EH: ["huevo cocido", "pollo sin piel", "pescado blanco cocido", "tofu (moderado)"]
  proteinas_con_EH: ["tofu", "lácteos bajos en grasa (kéfir)", "clara de huevo"]
  carbohidratos: ["batata cocida", "arroz blanco cocido", "avena"]
  hepatoprotectores: ["vitamina E", "SAMe (supervisión vet)"]

HEPATOPATIA_PROHIBITED:
  ["hígado (especialmente razas con acumulación de cobre)", "carnes grasas",
   "piel de pollo", "chorizo/embutidos", "alcohol", "mariscos (si cobre elevado)"]

HIPERLIPIDEMIA_PROHIBITED:
  ["cerdo graso", "piel de pollo", "yema de huevo en exceso", "mantequilla",
   "aceite de coco en exceso", "carnes grasas", "cualquier alimento frito"]
```

---

### 4.7 PANCREATITIS

#### Fisiopatología nutricional
La grasa dietética estimula la secreción de colecistoquinina (CCK) → estimula la secreción pancreática exocrina → en páncreas inflamado → autodigestión. La restricción de grasa es el pilar del manejo.

#### Objetivos nutricionales

**Grasa — restricción central**:
- Pancreatitis aguda activa: Ayuno máximo **12–24 horas** con fluidos IV, luego reintroducción gradual.
- Recuperación/transición: **<10% MS de grasa**
- Pancreatitis crónica estable: **<12–15% MS de grasa**

**Proteína**: **25–30% MS**, alta digestibilidad, fuentes magras. Proteína no estimula el páncreas significativamente.

**Carbohidratos**: Digestibles, moderados. Pequeñas cantidades no estimulan el páncreas agresivamente.

**Frecuencia**: **4–6 comidas pequeñas por día**. Reduce el estímulo pancreático por comida individual.

**Regla de ayuno (REGLA 10 NutriVet)**: **NUNCA recomendar ayuno >12 horas**. En pancreatitis aguda en gatos: urgencia — la lipidosis hepática aparece en 24–48h de anorexia.

**Reintroducción post-episodio agudo** (perros):
1. Ofrecer agua primero (si tolera sin vómito, continuar)
2. 4–8h después: pequeña porción de dieta muy baja en grasa
3. Si tolera: aumentar gradualmente en 3–7 días
4. NO volver a dieta normal hasta 2–4 semanas después del episodio

**Gatos — diferencia pancreatitis**:
- La restricción de grasa en gatos es menos clara que en perros (evidencia mixta)
- La prioridad en gatos es **no ayunar** — riesgo de lipidosis hepática supera al riesgo de estimulación pancreática
- Triaditis felina (pancreatitis + IBD + colangitis): manejo multidisciplinar, dieta alta digestibilidad, baja en grasa moderada

```
PANCREATITIS_PROHIBITED_PERMANENTE:
  ["tocino", "piel de pollo", "chorizo", "salchicha", "cerdo graso",
   "cordero graso", "pato (graso)", "mantequilla", "aceite de coco en exceso",
   "yema de huevo (máx 2/semana en crónica)", "comida de mesa/sobras",
   "cualquier alimento frito", "embutidos"]

PANCREATITIS_PERMITTED:
  ["pechuga de pollo SIN piel cocida", "pavo sin piel", "atún en agua",
   "clara de huevo", "arroz blanco cocido", "batata cocida", "zanahoria cocida",
   "brócoli cocido", "sardina en agua (pequeñas cantidades — moderada en grasa)"]
```

---

### 4.8 ENFERMEDAD NEURODEGENERATIVA (CDS — Cognitive Dysfunction Syndrome)

#### Fisiopatología nutricional
Depósitos de beta-amiloide, neuroinflamación y estrés oxidativo reducen la función cognitiva. Las neuronas con resistencia a glucosa pueden usar cuerpos cetónicos (de MCT) como combustible alternativo.

#### Objetivos nutricionales

**Omega-3 DHA** (soporte neuronal — distinto de dosis articular):
- DHA específicamente para membrana neuronal y neurogénesis
- Dosis: **40–60 mg DHA/kg/día** (en adición al EPA)
- Fuentes: aceite de krill (mayor biodisponibilidad), aceite de sardinas, salmón

**MCT (triglicéridos de cadena media)**:
- Mecanismo: C8 (ácido caprílico) y C10 → cuerpos cetónicos → combustible neuronal alternativo
- Evidencia canina (Pan Y et al., 2010 — Br J Nutr): mejora cognitiva en 2 meses con MCT
- Dosis: **1–2 ml de aceite de coco/kg/día** o **0.5–1 g de aceite MCT puro/kg/día**
- Precaución: Aceite de coco tiene C12 (láurico) además de MCT reales → puede causar diarrea en exceso. Preferir aceite MCT puro.
- CONTRAINDICADO en: pancreatitis, hiperlipidemia

**Antioxidantes**:
- Vitamina E: **5–10 IU/kg/día**
- Vitamina C: 100–250 mg/día (suplemento, ya que los perros sintetizan algo pero el soporte extra puede ayudar)
- Selenio: solo si hay déficit (margen estrecho de toxicidad)

**Fosfatidilserina**: 50–100 mg/día — evidencia moderada en CDS canino.

**Textura** (avanzada): disfagia → dieta blanda, comedero elevado, porciones pequeñas.

```
CDS_RECOMENDADO:
  ["DHA específico (aceite krill, sardinas)", "aceite MCT (1-2 ml/kg/día)",
   "vitamina E", "vitamina C", "fosfatidilserina", "dieta rica en antioxidantes naturales"]
```

---

### 4.9 ENFERMEDAD BUCAL Y PERIODONTAL

#### Objetivos nutricionales

**Textura del alimento post-cirugía dental**:
- 0–3 días: Paté o alimento húmedo completamente suave, a temperatura ambiente
- 3–7 días: Alimento húmedo con textura mínima
- 7–14 días: Reintroducción gradual de croquetas si la herida lo permite
- NO dar huesos ni premios masticables hasta cicatrización completa

**Nutrientes clave**:
- **Vitamina C**: 100–250 mg/día. Síntesis de colágeno del ligamento periodontal.
- **Zinc**: 2–3 mg/kg/día. Efecto bacteriostático en placa dental.
- **Calcio + Vitamina D**: Soporte de hueso alveolar.
- **Omega-3**: Reducen inflamación gingival.

**Kibble vs húmedo y salud dental**:
- El kibble estándar NO limpia los dientes (los perros no mascan suficiente)
- Solo kibble dentales específicos (Royal Canin Dental, Hills t/d) con tamaño y textura especial tienen VOHC (Veterinary Oral Health Council) de eficacia
- Huesos crudos blandos (alas de pollo crudas): limpieza mecánica, pero riesgo de fractura en razas con mordida fuerte
- La ÚNICA forma efectiva de control de placa: cepillado dental diario

---

### 4.10 DERMATITIS Y ALERGIAS CUTÁNEAS

#### Fisiopatología
El 15–20% de la dermatitis canina tiene componente alimentario (Mueller RS et al., 2016). La distinción atópica vs alimentaria requiere dieta de eliminación estricta.

#### Protocolo de dieta de eliminación

**Duración**:
- Perros: mínimo **8 semanas** (algunos casos necesitan 12)
- Gatos: mínimo **8–10 semanas**
- Razón: El sistema inmune IgE-mediado tarda semanas en "silenciarse"

**Reglas ABSOLUTAS durante la eliminación**:
1. SOLO los alimentos del plan: sin premios, sin sobras, sin comida de mesa
2. Sin medicamentos palatables con sabor (usar tabletas sin saborizante si es posible)
3. Sin vitaminas masticables con proteínas
4. Si hay otros animales en casa: el paciente no puede acceder a su comida
5. Sin lamer platos humanos
6. Sin heces de otros animales (coprofagia puede reiniciar la exposición)
7. Cualquier transgresión reinicia el contador a 0

**Proteínas novel (nunca ha comido antes)**:

| Proteína | Disponibilidad LATAM | Novedad real | Costo relativo |
|----------|---------------------|--------------|----------------|
| Pato | Media (Colombia: tiendas especializadas) | Alta — raro en comerciales | Alto |
| Conejo | Media-alta (carnicerías, criadores) | Alta — raro en comerciales | Medio-alto |
| Cordero | Baja-media (Colombia), alta (Argentina, Chile) | Media — algunos comerciales | Alto |
| Venado/ciervo | Baja (importado) | Muy alta | Muy alto |
| Cuy/cobayo | Alta (Colombia, Ecuador, Perú) | Muy alta | Bajo en zonas de cría |
| Trucha | Alta (Boyacá, Nariño) | Media — algunos comerciales ya la incluyen | Medio |
| Codorniz | Media (Colombia, producción local) | Alta | Medio |

**Carbohidrato novel** (nunca comido antes):
- Batata (si no ha comido en comerciales)
- Papa cocida (si no ha comido)
- Quinua (rara en comerciales de mascotas)
- Tapioca/yuca (si no ha comido)
- Amaranto (muy novel)

**Reactividad cruzada entre alérgenos comunes**:

| Alérgeno primario | Reacción cruzada posible | Acción |
|-------------------|--------------------------|--------|
| Pollo | Pavo (~40%), pato (~30%), huevo (~25%) | Evitar todas en eliminación inicial |
| Res | Cordero (~35%), bisonte, búfalo | Evitar carne de rumiantes |
| Trigo | Cebada (~60%), centeno (~50%), avena (~30%) | Evitar todos los granos gluten |
| Leche de vaca | Leche de cabra (~90%), queso, lácteos | Evitar todos los lácteos |
| Soya | Otras leguminosas (~30%) | Evitar legumbres |

**Challenge (reintroducción tras dieta de eliminación exitosa)**:
1. Reintroducir **UN SOLO ingrediente** por vez
2. Duración: **2 semanas por ingrediente**
3. Señales de reacción: prurito, eritema, otitis, problemas GI → confirma alergia
4. Si no hay reacción en 2 semanas: ese ingrediente es seguro

**Omega-3 en dermatitis**:
- Dosis dermatológica: **40–100 mg/kg/día EPA+DHA**
- Efecto visible: 8–12 semanas
- Puede reducir requerimiento de corticosteroides (Olivry T et al., ICADA 2015)
- Vitamina E SIEMPRE junto con omega-3 crónico (evita oxidación de lípidos)

**Zinc en razas con malabsorción genética**:
- Husky Siberiano, Alaskan Malamute, Samoyedo, Bull Terrier
- Condición: "Zinc-Responsive Dermatosis"
- Dosis: **1–3 mg zinc elemental/kg/día** (gluconato de zinc, sulfato de zinc)
- Fuentes alimentarias: res, cordero, semillas de calabaza

```
DERMATITIS_ELIMINACION_REGLAS:
  proteina_novel: ["pato", "conejo", "cuy", "trucha", "codorniz"]
  carbohidrato_novel: ["batata", "quinua", "tapioca", "amaranto"]
  PROHIBIDO_DURANTE_ELIMINACION: ["cualquier alimento previo", "premios", "saborizantes",
    "comida humana", "leche", "queso", "cualquier cereal que haya comido"]
  duracion: "mínimo 8 semanas estrictas"
```

---

### 4.11 GASTRITIS Y SENSIBILIDAD GASTROINTESTINAL

#### GASTRITIS AGUDA — Protocolo exacto

**Fase 1 (primeras 4–12 horas)**:
- Ofrecer agua en pequeñas cantidades frecuentes
- Si tolera agua sin vómito → iniciar dieta blanda
- **NO ayuno prolongado** (>12h) — especialmente en gatos

**Dieta blanda clásica** (porción exacta):

| Ingrediente | Proporción | Preparación |
|-------------|-----------|-------------|
| Pechuga de pollo sin piel | 75% | Hervida en agua sin sal, sin especias, desmechada |
| Arroz blanco | 25% | Cocido al doble de agua normal (más blando) |
| Sin aceite, sin sal, sin especias | — | Temperatura ambiente o ligeramente tibia |

- Porciones: 1/3 de la cantidad normal, 4–6 veces/día
- Duración: 3–7 días, luego transición gradual de 5–7 días a dieta normal
- Si persiste vómito/diarrea >48h → consulta veterinaria

**Grasa máxima en gastritis aguda**: <5% MS (sin grasa añadida)

#### GASTRITIS CRÓNICA / IBD

- Proteína altamente digestible: huevo cocido, pollo, pavo (digestibilidad >90%)
- Una sola fuente proteica a la vez inicialmente
- Fibra fermentable/soluble: psyllium (1 tsp/comida), avena cocida → alimenta microbiota benéfica
- Probióticos veterinarios con evidencia: *Enterococcus faecium* SF68 (Fortiflora), *Lactobacillus acidophilus*, *Bifidobacterium animalis* AHC7. Dosis: según producto veterinario.
- Evitar: lactosa, grasas, especias, comida de mesa, cambios bruscos de dieta

**Sensibilidad GI en gatos**: Cambios de dieta deben hacerse en mínimo **10–14 días** (más lento que perros). Los gatos son muy sensibles al cambio de textura y aroma.

```
GASTRITIS_AGUDA_PERMITIDO: ["pollo cocido sin piel sin sal", "arroz blanco cocido sin sal", "agua"]
GASTRITIS_CRONICA_PERMITIDO: ["huevo cocido", "pollo cocido", "pavo cocido", "batata cocida",
  "avena cocida", "zanahoria cocida", "probióticos veterinarios"]
GASTRITIS_PROHIBITED: ["leche", "queso", "alimentos grasos", "especias", "ajo", "cebolla",
  "alimentos muy calientes/fríos", "comida de mesa", "piel de pollo", "cerdo"]
```

---

### 4.12 CISTITIS Y ENFERMEDAD URINARIA (FLUTD)

#### Tipos y diferencias de manejo

| Tipo | Prevalencia perro | Prevalencia gato | pH urinario objetivo | Objetivo dieta |
|------|------------------|-----------------|----------------------|----------------|
| Estruvita (MgNH₄PO₄) | 21% | 47% | **Ácido: 6.0–6.3** | Acidificante, baja en Mg/P |
| Oxalato de calcio | 47% | 28% | **Neutro-básico: 6.5–7.5** | Baja en oxalatos |
| Cistitis idiopática felina | Raro en perros | **~55% de FLUTD felino** | Neutro | Hidratación + estrés |
| Urato (ácido úrico) | 8% | 5% | **Alcalino: 7.0–8.0** | Baja en purinas (Dálmata) |

**HIDRATACIÓN — Intervención más importante (todos los tipos)**:
- Objetivo: densidad urinaria < 1.020 (perro), < 1.025 (gato)
- Dieta húmeda (≥70% humedad) vs seca: incrementa producción de orina en 50–100%
- Añadir agua al alimento seco si no acepta húmedo
- Múltiples fuentes de agua (bebederos en distintas ubicaciones para gatos)
- Agua corriente/fuente: estimula ingesta en gatos

**ESTRUVITA**:
- Reducir magnesio: <0.1% MS
- Reducir fósforo: <0.5% MS
- Proteína moderada: reduce excreción de amonio (precursor estruvita)
- Acidificantes naturales: proteína animal (ácido úrico), arándano (ácido hipúrico — evidencia mixta en mascotas)
- Sodio moderado (300 mg/100 kcal): estimula sed → mayor micción → dilución

**OXALATO DE CALCIO**:
- OXALATOS a evitar: espinaca (750 mg/100g), remolacha (100–900 mg/100g), ruibarbo, nueces
- Vitamina C: NO suplementar — el exceso se convierte en oxalato en orina
- Calcio dietético: paradoja — calcio oral se une a oxalato en intestino → reduce oxalato urinario. NO restringir calcio agresivamente.
- NO acidificar la orina (aumenta excreción de calcio → más oxalato)

**CISTITIS IDIOPÁTICA FELINA (FIC)**:
- ~55% de FLUTD en gatos sin causa identificable
- Estrés: rol demostrado (Buffington CA et al.) → enriquecimiento ambiental, reducción de estrés
- Hidratación: dieta húmeda reduce recurrencias significativamente
- Glicosaminoglicanos (GAG): protegen la mucosa vesical. Suplemento: condroitín sulfato.

**Dálmata — caso especial (URATOS)**:
- Defecto metabólico en conversión de ácido úrico → alantoína
- Dieta BAJA en purinas: evitar vísceras, mariscos, anchovetas, anchoas, carne muy roja
- Proteína moderada de fuentes magras
- Alcalinizar orina: vegetales, bicarbonato bajo supervisión vet

```
CISTITIS_ESTRUVITA_PERMITIDO: ["pollo magro", "pavo", "clara de huevo", "batata cocida",
  "zanahoria", "dieta húmeda", "agua adicional", "arándanos frescos (moderado)"]
CISTITIS_OXALATO_EVITAR: ["espinaca", "remolacha", "nueces", "vitamina C suplementada en exceso",
  "rhubarbo", "dietas muy acidificantes"]
CISTITIS_GENERAL_PROHIBITED: ["embutidos", "sal en exceso", "alimentos muy procesados"]
```

---

### 4.13 SOBREPESO Y OBESIDAD (BCS ≥ 7)

#### Cálculo correcto del plan de pérdida de peso

**Paso 1 — Estimar peso ideal desde BCS**:
```
BCS 6 → peso_ideal = peso_actual × 0.91
BCS 7 → peso_ideal = peso_actual × 0.85
BCS 8 → peso_ideal = peso_actual × 0.77
BCS 9 → peso_ideal = peso_actual × 0.67
```

**Paso 2 — Calcular RER sobre el PESO IDEAL (no el real)**:
```
RER = 70 × peso_ideal_kg^0.75
```

**Paso 3 — Aplicar factor de reducción**:
```
DER_reduccion = RER × factor_actividad × 0.8   (20% reducción adicional)
```

**Alternativa (AAHA 2021)**:
```
DER_reduccion = RER(peso_ideal) × 1.0    (sin multiplicar por actividad)
```

**Tasa de pérdida de peso segura**:
- Perros: **1–2% del peso corporal por semana** máximo
- Gatos: **0.5–1% del peso corporal por semana** — NUNCA más rápido
  - Razón: Movilización rápida de grasa → hígado → lipidosis hepática
  - Si el gato pierde >1%/semana → reducir restricción calórica

**Señales de alarma en gatos** (lipidosis hepática inminente):
- Rechazo del alimento por >24 horas
- Ictericia (amarillamiento esclerótica)
- Letargo extremo
- → Urgencia veterinaria

#### Composición del plan de pérdida de peso

**Proteína alta**: **≥30–35% MS** para preservar masa muscular durante déficit calórico.
En gatos: mínimo **35–40% MS** — mayor riesgo de sarcopenia.

**Fibra**: **10–15% MS** para saciedad sin calorías.
Fuentes: psyllium, avena, verduras (zanahoria, brócoli, pepino) como sustituto de premios.

**Grasa**: **8–15% MS** — reducida pero no eliminada.

**Comidas**: 2–3 veces/día con cantidades exactas medidas. **NUNCA ad libitum en obesos**.

**Premios**: Solo vegetales bajos en calorías (zanahoria, pepino, brócoli).

```
OBESIDAD_ESTRATEGIA:
  proteina: "≥30% MS para preservar músculo"
  fibra: "alta para saciedad"
  grasa: "reducida pero presente"
  comidas: "medidas exactas, 2-3x/día"
  premios: "zanahoria, pepino, brócoli (no croquetas)"
  gatos_especial: "NUNCA reducir >40% del DER. Máx pérdida 1%/semana"
  ejercicio: "complementario — no sustituto de la dieta"
```

---

## PARTE 5 — INTERACCIONES ENTRE CONDICIONES MÉDICAS

### Matriz de conflictos y resolución

| Condición 1 | Condición 2 | Conflicto | Resolución |
|-------------|-------------|-----------|------------|
| Diabetes (perro) | Obesidad | Ambas necesitan restricción calórica | Usar peso ideal. Priorizar glucemia estable: horario fijo, baja en carbohidratos simples |
| Diabetes (gato) | Obesidad | Gato: bajos carbs + reducción calórica | Pérdida de peso muy lenta (0.5%/semana). La dieta low-carb ya ayuda la diabetes |
| Hepatopatía | Hiperlipidemia | Ambas requieren baja en grasa | Máxima restricción de grasa (<10% MS). Sin diferencia práctica — suelen coexistir |
| Pancreatitis | Hiperlipidemia | Ambas: restricción grasa agresiva | Dieta hipograsa es idéntica para ambas. La hiperlipidemia agrava la pancreatitis |
| ERC | Diabetes (perro) | ERC: restringir proteína. Diabetes: alta fibra | Prioridad ERC: restricción de fósforo > restricción de proteína. Usar fuentes alta digestibilidad |
| Cistitis oxalato | ERC | Oxalato: no acidificar. ERC: bajo fósforo | Evitar oxalatos (espinaca). Hidratación máxima para ambas. Bajo fósforo. Sin acidificantes |
| Cáncer | Pancreatitis | Cáncer: alta grasa (omega-3). Pancreatitis: baja en grasa | Usar omega-3 concentrado (suplemento EPA+DHA puro) en lugar de aceite crudo. Grasa total <12% MS |
| Hepatopatía | ERC | Hepatopatía: proteína moderada-alta. ERC: restringir proteína | Proteína de MUY ALTA digestibilidad (huevo, pollo sin piel). Estadio ERC guía la restricción |
| Articular | Obesidad | Ambas: control de peso crítico | Pérdida de peso es el tratamiento más efectivo para la articulación. Dieta hipograsa + alta proteína |
| Gastritis | Hepatopatía | Gastritis: baja en grasa, dieta blanda. Hepatopatía: baja en grasa, comidas frecuentes | Compatible: ambas se benefician de baja en grasa y comidas pequeñas frecuentes |
| Hipotiroidismo | Hiperlipidemia | Hipotiroidismo causa hiperlipidemia | Tratamiento hormonal (levotiroxina) resuelve hiperlipidemia. Dieta: baja en grasa + sin goitrógenos |

**Regla general para condiciones múltiples**:
1. Listar TODAS las restricciones de cada condición
2. Donde hay conflicto: aplicar la restricción **más conservadora**
3. Donde no hay conflicto: aplicar cada una
4. Con 3+ condiciones → usar **claude-sonnet-4-5** (override obligatorio NutriVet)
5. Con 3+ condiciones → el plan SIEMPRE va a **PENDING_VET**

**Caso Sally (5 condiciones: Diabetes + Hepatopatía + Hiperlipidemia + Gastritis + Cistitis)**:

| Parámetro | Resultado cruzado |
|-----------|------------------|
| Grasa | **MUY BAJA (<10% MS)** — hepatopatía + hiperlipidemia + pancreatitis |
| Carbohidratos | **BAJO + bajo IG** — diabetes (sinc. insulina) |
| Proteína | **MODERADA-ALTA alta digestibilidad** — hepatopatía + diabetes + cistitis |
| Sodio | **BAJO** — cistitis |
| Oxalatos | **EVITAR** (sin espinaca) — cistitis |
| Fósforo | **MODERADO** — cistitis moderada |
| Fibra | **SOLUBLE moderada** — diabetes + hepatopatía + gastritis |
| Frecuencia | **4–5 comidas pequeñas, horario fijo** — diabetes + gastritis + hepatopatía |
| Horario | **FIJO** sincronizado insulina |

---

## PARTE 6 — ALERGIAS ALIMENTARIAS: PROTOCOLOS COMPLETOS

### 6.1 Alérgenos más frecuentes — Perros (por prevalencia)

| Alérgeno | Frecuencia | Proteína alergénica | Reactividad cruzada |
|----------|-----------|--------------------|--------------------|
| **Res/carne vacuna** | ~34% | Seroalbúmina bovina | Cordero (35%), bisonte |
| **Productos lácteos** | ~17% | Caseína, β-lactoglobulina | Leche de cabra (90%) |
| **Pollo** | ~15% | α-parvalbúmina | Pavo (40%), pato (30%), huevo (25%) |
| **Trigo** | ~13% | Gliadina, glutenina | Cebada (60%), centeno (50%), avena (30%) |
| **Huevo** | ~10% | Ovoalbúmina (clara), vitelina (yema) | Pollo (25%) |
| **Soya** | ~6% | Glicinina, β-conglicinina | Otras leguminosas (30%) |
| **Cerdo** | ~5% | — | Res (moderada) |
| **Cordero** | ~5% | — | Res (35%) |
| **Mariscos** | ~3% | Tropomiosina | Otros crustáceos |
| **Pez** | ~3% | Parvalbúmina | Otros peces |

### 6.2 Alérgenos más frecuentes — Gatos

| Alérgeno | Frecuencia |
|----------|-----------|
| Res | ~20% |
| Pescado | ~20% |
| Pollo | ~20% |
| Productos lácteos | ~14% |
| Trigo | ~6% |

### 6.3 Reactividad cruzada — Protocolo de exclusión

**Si es alérgico a POLLO**: Evitar también pavo (probable), huevo (posible), pato (posible).
**Si es alérgico a RES**: Evitar también cordero (probable), bisonte, búfalo.
**Si es alérgico a TRIGO**: Evitar también cebada, centeno. Avena con precaución.
**Si es alérgico a LECHE**: Evitar todos los productos lácteos, incluyendo leche de cabra.
**Si es alérgico a HUEVO**: Probar si la alergia es a clara, yema, o ambas (diferentes proteínas).

### 6.4 Proteínas hidrolizadas — cuándo usar

**Indicaciones para hidrolizados veterinarios**:
- Paciente con alergias múltiples confirmadas sin proteína novel disponible
- Paciente donde la dieta de eliminación fracasó con novel protein (posible sensibilización múltiple)
- Paciente con EII + alergia alimentaria simultánea (doble indicación)

**Mecanismo**: Hidrólisis enzimática rompe proteínas en péptidos < 1 kDa → no reconocidos por IgE → sin respuesta alérgica.

**Comerciales disponibles en Colombia**: Purina Pro Plan HA, Royal Canin Anallergenic, Hills z/d.

---

## PARTE 7 — BARF: PROPORCIONES DETALLADAS Y CÁLCULO

### 7.1 Proporciones estándar por especie

#### BARF Perros — Modelo práctico LATAM

```
50–60% Músculo (incluye corazón como músculo):
  - Pollo (pechuga + muslo sin piel): principal
  - Res magra: rotación
  - Pavo: opción extra

10–15% Vísceras secretoras:
  - MÁXIMO 5% hígado (hipervitaminosis A si se excede)
  - Riñón, molleja, corazón: restantes hasta 10–15%

10–15% Hueso crudo comestible (fuente de calcio):
  - Alas de pollo, cuello de pollo, carcasa → SEGUROS
  - Costilla de cordero cruda: moderado
  - NUNCA fémur de res entero (fractura dental)

7–10% Vegetales (triturar para digestibilidad):
  - Zanahoria + ahuyama + judías verdes + brócoli (< 10%)
  - EVITAR: espinaca en exceso (oxalatos), cebolla/ajo (tóxicos)

2–3% Huevo completo (rotacional)

SUPLEMENTOS OBLIGATORIOS:
  - Aceite de sardinas/salmón: 0.5–2 ml/kg/día (omega-3 + vitamina D)
  - Calcio suplementado si no hay hueso: CaCO₃ 900 mg/100g de carne
  - Vitamina E: 2–5 IU/kg/día
```

#### BARF Gatos — Diferencias críticas

```
70–80% Músculo:
  - MÁS proteína que perros (carnívoro obligado)
  - INCLUIR SIEMPRE fuente de taurina: corazón de pollo/res (5–10%)
  - Pollo, pavo, conejo, pescado (cocido preferible para taurina)

10% Vísceras:
  - Hígado: 5% máximo (vitamina A preformada)
  - Corazón: fuente primaria taurina

5–8% Hueso crudo molido o cartílago

0–5% Vegetales (opcional — el gato no los necesita metabólicamente):
  - Si se incluyen: zanahoria, ahuyama triturados
  - SIN espinaca (oxalatos + sensibilidad felina)

SUPLEMENTOS OBLIGATORIOS GATO:
  - Taurina: si la dieta es cocida, SUPLEMENTAR (cocción destruye 80%)
  - Aceite de pescado: 0.5 ml/kg/día (EPA+DHA + vitamina D)
  - Vitamina E: 2–5 IU/kg/día
  - Sin suplementar B12 con dieta de carne fresca (ya está)
```

### 7.2 Cálculo completo ejemplo — Perro 20 kg adulto BARF

```
PERFIL: Perro 20 kg, macho, esterilizado, moderado, BCS 5, adulto 3 años

RER = 70 × 20^0.75 = 70 × 9.46 = 662 kcal/día
DER = 662 × 1.6 (mod. esterilizado) × 1.0 (adulto) × 1.0 (BCS5) = 1059 kcal/día

PLAN BARF (densidad energética promedio ponderado ≈ 170 kcal/100g):
Total: 1059 / 170 × 100 ≈ 623g de alimento/día

DISTRIBUCIÓN:
  - Muslo de pollo sin piel (55%): 343g → 583 kcal
  - Corazón de res (10%): 62g → 69 kcal
  - Hígado de pollo (5%): 31g → 37 kcal
  - Alas de pollo crudas como hueso (10%): 62g → 89 kcal (calcio incluido)
  - Zanahoria triturada (8%): 50g → 21 kcal
  - Ahuyama triturada (7%): 44g → 11 kcal
  - Huevo entero crudo (5%): 31g → 44 kcal
TOTAL: 623g ≈ 854 kcal

AJUSTE: La densidad real es ~137 kcal/100g → aumentar a 773g total
(Iteración hasta ≈1059 kcal → ajustar cantidad de muslo de pollo)

VERIFICACIÓN NUTRICIONAL:
  Proteína: ~145g → ~27% de energía ✓ (≥18% requerido)
  Calcio (de alas): ~370 mg → BAJO. Necesita suplemento.
    → Agregar: 5g de cáscara de huevo molida (1 cdta = ~1800 mg Ca)
  Fósforo: ~890 mg → Ca:P = 370:890 = 0.4:1 → BAJO RATIO
    → Con suplemento calcio: (370+1800):890 = 2.4:1 → dentro de rango
  Taurina: corazón de res (62g × 862mg/100g = 534mg) ✓ para perros
  Omega-3: muy bajo sin suplemento → agregar 1ml aceite de sardinas (≈300mg EPA+DHA)
  Vitamina D: muy baja → aceite de pescado incluye vitamina D
```

---

## PARTE 8 — SUPLEMENTOS: DOSIS Y CONTRAINDICACIONES

| Suplemento | Dosis perro | Dosis gato | Para qué | Contraindicado en |
|-----------|------------|-----------|----------|------------------|
| **Aceite de pescado (EPA+DHA)** | 20–100 mg/kg/día | 20–80 mg/kg/día | OA, dermatitis, ERC, cáncer, CDS | Pancreatitis activa (inicio cauteloso), hiperlipidemia (forma concentrada) |
| Vitamina E | 2–10 IU/kg/día | 2–5 IU/kg/día | Antioxidante, siempre con omega-3 | Altas dosis con anticoagulantes |
| Vitamina D3 | 10–20 IU/kg/día | 10–20 IU/kg/día | Déficit, ERC | **Toxicidad real >100 IU/kg/día** |
| Calcio carbonato | 500–1200 mg/día | 200–500 mg/día | BARF sin hueso | No en ERC severa (exceso Ca) |
| Zinc gluconato | 1–3 mg/kg/día | 0.5–1 mg/kg/día | Dermatitis, hipotiroidismo | Exceso: toxicidad, anemia hemolítica |
| Probióticos (Fortiflora) | 1 sobre/día | 1 sobre/día | IBD, antibioticoterapia | Inmunocompromiso severo (precaución) |
| SAMe | 400–1200 mg/día | 100–400 mg/día | Hepatopatía, CDS | — |
| Aceite MCT | 0.5–2 ml/kg/día | 0.5–1 ml/kg/día | CDS, epilepsia | Pancreatitis, hiperlipidemia |
| Psyllium | 1–2 tsp/comida | ½ tsp/comida | Diabetes, gastritis, obesidad | Obstrucción intestinal |
| Glucosamina HCl | 500–1000 mg/día | 125–250 mg/día | OA (sin evidencia real 2024) | Diabetes (puede afectar glucemia) |

---

## PARTE 9 — ESCENARIOS DIFÍCILES Y ÁRBOL DE DECISIÓN

### 9.1 Árbol de clasificación nutricional vs médica

```
¿La pregunta implica...?

SÍNTOMAS (vómito persistente, diarrea con sangre, convulsiones, colapso, ictericia)
  → SIEMPRE ReferralMessage + urgencia según severidad

MEDICAMENTOS (insulina, quimioterapia, antibióticos, corticoides)
  → SIEMPRE ReferralMessage (ajuste de medicación = medicina, no nutrición)

DIAGNÓSTICO (¿tiene diabetes? ¿tiene cáncer? ¿qué enfermedad es?)
  → SIEMPRE ReferralMessage

URGENCIA ALIMENTARIA (ingirió xilitol, uvas, cebolla, chocolate)
  → SIEMPRE EmergencyReferral + detalles del tóxico + dosis

NUTRICIÓN CLARA (¿qué come? ¿cuánto come? ¿qué no puede comer? recetas, porciones)
  → Responder completamente

ZONA GRIS (¿el brócoli empeora el hipotiroidismo?)
  → Responder la parte nutricional: "sí, los goitrógenos interfieren con la función tiroidea,
     cocinar el brócoli reduce el efecto, limitar a <10% de la dieta"
  → Agregar: "para ajustes de medicación tiroidal consulta con tu veterinario"
```

### 9.2 Respuesta tipo para mitos LATAM frecuentes

**Mito: "Le doy ajo para las pulgas/parásitos"**
Respuesta del agente: "El ajo contiene tiosulfatos que destruyen los glóbulos rojos de perros y gatos, causando anemia hemolítica. El efecto es acumulativo: pequeñas cantidades diarias pueden ser tan dañinas como una dosis grande. No existe evidencia clínica de que el ajo elimine parásitos. Los antiparasitarios veterinarios son la única opción segura."

**Mito: "Los huesos de pollo cocido son buenos para los grandes"**
Respuesta del agente: "La cocción desnaturaliza el colágeno del hueso, haciéndolo quebradizo y astilloso. Cualquier hueso cocido —sin importar la raza o el tamaño del perro— puede astillarse y perforar el esófago, el estómago o el intestino. Esto es una emergencia quirúrgica. Los huesos crudos blandos (alas de pollo crudas) tienen menor riesgo porque el colágeno intacto les da flexibilidad."

**Mito: "La comida casera siempre es mejor que el concentrado"**
Respuesta del agente: "Una dieta casera bien formulada con todos los macro y micronutrientes puede ser excelente. Sin embargo, sin calcular calcio, fósforo, vitaminas y minerales, una dieta casera puede causar deficiencias graves en semanas o meses. Un concentrado que cumpla estándar AAFCO está nutricionalmente balanceado. La clave está en la formulación correcta, no en si es casero o comercial."

---

## PARTE 10 — ANTI-ALUCINACIÓN: REGLAS PARA EL LLM

### 10.1 Qué el LLM NUNCA debe inventar

```
REGLAS_ANTI_ALUCINACION:
  1. No inventar valores nutricionales sin indicar que son estimados
  2. No citar papers o estudios específicos sin verificación
  3. No dar dosis de suplementos sin la frase "bajo supervisión veterinaria"
  4. No afirmar que un alimento es "seguro" sin base en NRC/AAFCO
  5. No inventar ingredientes locales que no existen en LATAM
  6. No crear proporciones BARF sin calcular calorías
  7. No modificar restricciones médicas aunque el owner insista
  8. No dar diagnósticos ("parece que tiene...") — solo remitir
  9. No inventar terapias nutricionales sin evidencia (usar "evidencia limitada" o "sin evidencia")
  10. No afirmar que glucosamina/condroitina "protegen el cartílago" — decir evidencia negativa 2024
```

### 10.2 Frases de incertidumbre explícita que el LLM DEBE usar

- "Los valores nutricionales son estimados — pueden variar por fuente, región y procesamiento"
- "Esta dosis es orientativa — el veterinario debe ajustar según los análisis de sangre"
- "La evidencia en esta condición es limitada/mixta — el plan es conservador"
- "Si los síntomas persisten, consulta a tu veterinario — este plan no reemplaza el diagnóstico clínico"
- "Este plan es un punto de partida — ajustar según la respuesta de la mascota en 4–8 semanas"

---

## REFERENCIAS

### Guías Clínicas Primarias
- NRC. *Nutrient Requirements of Dogs and Cats*. National Academies Press, 2006.
- AAFCO Official Publication 2023. Dog and Cat Food Nutrient Profiles.
- AAHA. *Diabetes Management Guidelines for Dogs and Cats*, 2018 (updated 2022).
- AAHA. *Nutrition and Weight Management Guidelines*, 2021.
- ACVIM. *Consensus Statement: Diagnosis and Management of Chronic Kidney Disease in Dogs and Cats*, 2016.
- IRIS. *Staging of Chronic Kidney Disease*, 2023. iris-kidney.com
- WSAVA. *Global Nutrition Guidelines*, 2021.
- ICADA. *Olivry T et al. Critically appraised guidelines for the management of atopic dermatitis in dogs*, 2015, updated 2023.

### Papers Clave
- Rand JS et al. "Diet in the prevention of diabetes and obesity in companion animals." Asia Pac J Clin Nutr, 2003.
- Pan Y et al. "Dietary supplementation with medium-chain TAG has long-lasting cognition-enhancing effects in aged dogs." Br J Nutr, 2010.
- Dodd CE et al. "2022 Systematic Review and Meta-Analysis: Enriched Therapeutic Diets and Nutraceuticals in Canine and Feline Osteoarthritis." PMC9499673.
- Mueller RS et al. "Critically appraised topic on adverse food reactions of companion animals." BMC Vet Research, 2016.
- Xenoulis PG, Steiner JM. "Lipid metabolism and hyperlipidemia in dogs." Vet J, 2010.
- Buffington CA et al. "Clinical evaluation of cats with nonobstructive urinary tract diseases." JAVMA, 1997.
- "Amino acid nutrition and metabolism in domestic cats and dogs." PMC9942351, 2023.
- "Household Food Items Toxic to Dogs and Cats." PMC4801869, Frontiers Vet Science, 2016.
- "Current Evidence on Raw Meat Diets in Pets." MDPI Animals 15(3), 2025.

### Tablas Nutricionales
- USDA FoodData Central (fdc.nal.usda.gov) — valores por ingrediente
- ICBF Colombia. *Tabla de Composición de Alimentos Colombianos*, 2015.
- FAO LATINFOODS. *Tabla de Composición de Alimentos de América Latina*.

---

*Este documento es la base de conocimiento clínico para los prompts del agente NutriVet.IA.*
*No reemplaza el juicio veterinario. Toda restricción para mascotas con condiciones médicas debe ser validada por Lady Carolina Castañeda (MV, BAMPYSVET).*
*NutriVet.IA es asesoría nutricional digital — no reemplaza el diagnóstico médico veterinario.*
