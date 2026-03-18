# Análisis de Mercado — NutriVet.IA
**Versión**: 1.0 · **Fecha**: Marzo 2026

Basado en los datos del mercado actual, construir una plataforma de nutrición veterinaria agéntica para América Latina es altamente conveniente y representa una oportunidad estratégica, siempre y cuando se adapte a las particularidades culturales, económicas y veterinarias de la región.

---

## 1. Tamaño del Mercado y Crecimiento

### Mercado Global

El mercado global de pet care (alimentos, salud, servicios) superó los **USD 246 mil millones en 2023** y se proyecta que alcance **USD 427 mil millones para 2032** (CAGR 6.3%). El segmento de pet food representa el mayor componente, con **USD 115 mil millones en 2024**, impulsado por la tendencia de "humanización de mascotas" — los propietarios modernos tratan a sus mascotas como miembros de la familia y están dispuestos a pagar por productos de mayor calidad nutricional.

El mercado de **veterinary nutrition software y plataformas de telemedicina veterinaria** en particular está creciendo a un CAGR del 18.2% (2024-2030), impulsado por la digitalización pospandemia de los servicios de salud animal y el crecimiento del segmento D2C (directo al consumidor) en pet care.

### Mercado LATAM

América Latina es la **región de más rápido crecimiento en pet care a nivel mundial**, con un valor de mercado de **USD 12.5 mil millones en 2024** y proyección de **USD 22.3 mil millones para 2034** (CAGR 6.1%). Este crecimiento es sostenido por:

- **Expansión de la clase media**: Más hogares con capacidad de gasto en servicios premium para mascotas
- **Urbanización**: Las mascotas en apartamentos reciben más atención y cuidado médico
- **Demografía**: El 40% de los dueños de mascotas en LATAM tiene menos de 35 años — nativos digitales con alta adopción tecnológica
- **Zoonosis pospandemia**: El aumento de tenencia de mascotas durante el confinamiento (2020-2021) creó una nueva base permanente de propietarios

### Colombia — Mercado Específico

Colombia es el **segundo mercado de mayor crecimiento en pet food en LATAM** (después de Brasil):

| Indicador | Dato | Fuente |
|-----------|------|--------|
| Hogares con mascotas | 67% | DANE 2024 |
| Mercado pet food Colombia | USD 1.22B (2024) | Euromonitor |
| CAGR pet food Colombia | 8.2% (2024-2030) | Mordor Intelligence |
| Mascotas registradas Bogotá | ~850.000 | Secretaría de Salud |
| Gasto promedio mensual por mascota | $280.000 COP | Encuesta interna BAMPYSVET |
| % que practica dieta natural/BARF | ~23% | Estimación sectorial |

El 23% de dueños que practica alguna forma de dieta natural o BARF **sin guía técnica** es el segmento de mayor urgencia y mayor conversión para NutriVet.IA.

---

## 2. El Problema a Resolver (Dolores del Mercado)

### Mascotas en Riesgo por Nutrición Inadecuada

La nutrición es una de las principales causas de consulta veterinaria en Colombia. Veterinarios de clínicas urbanas reportan que:

- El **35-40% de los pacientes caninos** en consulta de rutina presentan algún grado de sobrepeso u obesidad (BCS ≥ 7/9), directamente relacionado con la sobrealimentación o el uso de concentrados inadecuados
- Las **enfermedades metabólicas** (diabetes, hepatopatía, enfermedad renal) son el diagnóstico de mayor crecimiento en medicina veterinaria interna en los últimos 5 años, asociadas parcialmente a dietas inadecuadas
- El **movimiento BARF sin guía** genera deficiencias de calcio, vitamina D y taurina con mayor frecuencia que lo reportado en la literatura anglosajona, por el uso de proteínas y vegetales locales (Colombia) con perfiles nutricionales diferentes

### La Brecha del Especialista

Colombia tiene aproximadamente **12.000 médicos veterinarios activos** (COMVEZCOL, 2024), pero solo una fracción pequeña tiene especialización formal en nutrición veterinaria. Una consulta con un especialista en nutrición:

- Cuesta entre **$150.000 y $400.000 COP** en Bogotá
- Tiene tiempos de espera de 1-3 semanas en clínicas especializadas
- Es prácticamente inexistente en ciudades medianas (Pereira, Manizales, Bucaramanga)

Esta brecha de acceso es exactamente el espacio que NutriVet.IA llena con un modelo digital escalable.

---

## 3. Panorama Competitivo y la Brecha Agéntica

### Competidores Directos

| Competidor | País | Fortalezas | Brecha que NutriVet.IA cubre |
|-----------|------|-----------|------------------------------|
| MyVetDiet | USA | Cálculo nutricional clínico | Sin app móvil, sin agente conversacional, no LATAM, no español |
| PetDesk | USA | Gestión de citas veterinarias | No es nutrición — es agenda clínica |
| Pawp | USA | Telemedicina veterinaria general | No es nutrición especializada |
| NutriPet (app) | Brasil | Cálculo calórico básico | Sin condiciones médicas, sin validación veterinaria, sin BARF |
| VetPass | Colombia | Agenda veterinaria | No es nutrición |
| PetMed Colombia | Colombia | Telemedicina veterinaria | No es nutrición especializada |

### La Brecha Confirmada

El análisis competitivo revela que **ningún competidor cubre el espacio completo** de:

```
Agente IA conversacional
+ Cálculo NRC determinista
+ Validación veterinaria (HITL)
+ Soporte BARF y dieta natural
+ Soporte concentrado comercial con OCR
+ Condiciones médicas integradas (13 condiciones)
+ App móvil en español nativo
+ LATAM-first (alimentos locales, precios COP)
+ Modelo de costos $0 en LLM para MVP (Ollama)
```

Esta es la **brecha agéntica**: los competidores ofrecen herramientas de cálculo estático o gestión de citas, no un agente que razone sobre el perfil clínico completo de la mascota y entregue un plan accionable con supervisión veterinaria.

### Competidores Indirectos (Sustitutos)

- **Grupos de Facebook/WhatsApp de BARF**: Comunidades no moderadas, información no validada, sin personalización
- **YouTube/TikTok**: Contenido educativo generalista, sin personalización clínica
- **El veterinario de confianza**: Canal preferido, pero con tiempo limitado en consulta y sin especialización en nutrición
- **Concentrados premium con hotline**: Marcas como Royal Canin tienen línea telefónica de asesoría, pero no personalizada y sin condiciones médicas específicas

---

## 4. Tendencias que Favorecen el Producto

### Humanización de Mascotas

La tendencia global de "pet parenthood" — tratar a la mascota como un hijo — es particularmente fuerte en el segmento 25-35 años de LATAM. Este segmento:

- Gasta en promedio **3x más** por mascota que generaciones anteriores
- Busca activamente información nutricional antes de cambiar la dieta
- Confía en apps y herramientas digitales para la salud propia y la de su mascota
- Tiene alta penetración de smartphones (>85% en Bogotá, Medellín, Santiago, Ciudad de México)

### Adopción de IA en Salud

La adopción de IA conversacional en salud humana normalizó la idea de "consultar con una IA antes de ir al médico". La extensión a salud veterinaria es natural:

- Los propietarios de mascotas ya usan apps de síntomas (PetSymptoms, WebMD Pets)
- La penetración de chatbots en servicios de salud en LATAM creció 47% entre 2023 y 2025
- La resistencia a la IA en salud veterinaria es menor que en salud humana (menor regulación, menor riesgo percibido)

### Regulación Colombiana Favorable

La **Ley 1774/2016** reconoce a los animales como seres sintientes y asigna responsabilidad a los propietarios por su bienestar, incluyendo la alimentación adecuada. Esto crea:

- Motivación legal y ética para que los propietarios busquen guía nutricional profesional
- Un marco donde NutriVet.IA puede operar como asesoría nutricional digital con disclaimers apropiados (sin reclamar ser diagnóstico médico)
- Base para posibles alianzas con entes regulatorios o colegiados veterinarios

---

## 5. Factores Clave de Éxito (Go-to-Market en LATAM)

Para que NutriVet.IA sea exitosa en el mercado colombiano y latinoamericano, debe cumplir con requisitos específicos del contexto local:

**1. Alimentos locales en la base de datos**
Las recomendaciones de ingredientes deben incluir proteínas y vegetales disponibles en Colombia: cogote de res, murillo, contramuslo de pollo, papa criolla, ahuyama (con advertencia de toxicidad), arracacha, plátano verde. Un plan que recomiende alimentos que no existen en el mercado local genera rechazo inmediato.

**2. Precios en COP**
Todo el producto — suscripciones, porciones, costos estimados de dieta — debe estar en pesos colombianos. La fricción de convertir de USD a COP aleja al usuario colombiano.

**3. Validación por un veterinario local como ancla de confianza**
El mercado colombiano tiene alta desconfianza hacia las "apps de salud". La figura de Lady Carolina Castañeda (MV, BAMPYSVET) como co-diseñadora y validadora clínica es el diferenciador de confianza más importante para la adopción inicial.

**4. Modelo de bajo costo de LLM durante el MVP**
El MVP debe operar con costo $0 en LLM (Qwen2.5 + Ollama) para validar el producto antes de comprometer costos operativos. La estrategia de Ollama → Groq → GPT-4o por complejidad asegura sostenibilidad desde el día 0.

**5. BAMPYSVET como caso piloto real**
La clínica BAMPYSVET como primer cliente real aporta: casos clínicos reales para validar el motor nutricional, retroalimentación directa de veterinarios en ejercicio, y credibilidad de marca para el marketing B2B con otras clínicas.

---

## 6. Modelo de Monetización

| Canal | Descripción | Precio estimado | Fase |
|-------|-------------|----------------|------|
| Suscripción owner básica | Hasta 1 mascota, 1 plan/mes | $29.900 COP/mes | MVP |
| Suscripción owner premium | Hasta 3 mascotas, planes ilimitados, OCR ilimitado | $59.900 COP/mes | MVP |
| Suscripción veterinario | Dashboard clínico, múltiples pacientes, trazabilidad | $89.000 COP/mes | MVP |
| Sponsors verificados | Marcas de alimento con tag "Patrocinado", verificación vet obligatoria | Variable | Mes 6+ |
| Licencia B2B clínicas | Dashboard multi-veterinario, co-branding | $250.000-$600.000 COP/mes | Mes 9+ |

**Break-even estimado (MVP)**: 500 suscriptores pagos de nivel básico cubren los costos operativos fijos (infraestructura AWS, equipo mínimo).

---

## 7. Conclusión

Construir NutriVet.IA para LATAM es altamente conveniente. El mercado tiene el tamaño, el crecimiento y la urgencia clínica para justificar la inversión. La estrategia ganadora consiste en:

1. **Anclar en Colombia** con BAMPYSVET como piloto validador y Lady Carolina como embajadora
2. **Diferenciarse por HITL + seguridad no negociable**: ningún competidor ofrece la combinación de agente IA + validación veterinaria + restricciones hard-coded
3. **Escalar regionalmente** con alimentos y contexto local de cada país (México, Perú, Argentina, Chile)
4. **Operar con costo $0 en LLM** durante el MVP para validar el modelo antes de comprometer costos operativos

El espacio está vacío. El momento es ahora.
