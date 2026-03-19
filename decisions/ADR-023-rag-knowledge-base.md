# ADR-023 — RAG con pgvector para Base de Conocimiento Nutricional

**Estado**: Aceptado
**Fecha**: 2026-03-19
**Autores**: Sadid Romero (AI Engineer)
**Revisores**: Lady Carolina Castañeda (MV, BAMPYSVET) — pendiente validación de fuentes

---

## Contexto

NutriVet.IA tiene tres capas de conocimiento nutricional:

1. **Reglas deterministas** (ya implementadas en unit-01): NRC formulas, toxicidad, restricciones médicas — Python hardcodeado, sin LLM.
2. **Conocimiento del LLM base**: Los modelos usados (Claude Sonnet, GPT-4o, Llama-70B) ya fueron entrenados con literatura veterinaria general. Suficiente para consultas estándar.
3. **Conocimiento especializado y localizado**: Tablas exactas del NRC, perfiles AAFCO actualizados, ingredientes LATAM, y conocimiento clínico de BAMPYSVET — esta capa el LLM base no la tiene de forma confiable.

El problema concreto: cuando el agente conversacional responde consultas como *"¿cuánto fósforo necesita un perro renal de 10 kg?"*, el LLM puede alucinar valores precisos del NRC. Para una app clínica esto es inaceptable.

La solución es **RAG (Retrieval Augmented Generation)**: indexar las fuentes autorizadas en una base vectorial y recuperar los chunks relevantes antes de que el LLM responda, garantizando que la respuesta esté grounded en fuentes verificadas.

---

## Decisión

Implementar RAG usando **pgvector** como base vectorial sobre el PostgreSQL existente, integrado como tool del agente LangGraph en el Consultation Subgraph.

### Arquitectura

```
Consultation Subgraph
  ├── query_classifier
  ├── nutritional_responder
  │     └── knowledge_retriever_tool   ← RAG tool (nueva en unit-05)
  │           ├── embed(query)         → vector con text-embedding-3-small
  │           ├── similarity_search()  → chunks relevantes de knowledge_chunks
  │           └── inject into context  → LLM responde grounded
  └── Referral Node (consultas médicas → vet)
```

### Esquema de base de datos

```sql
-- Extensión pgvector en el PostgreSQL existente (una migración Alembic)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_chunks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source      TEXT NOT NULL,        -- "NRC 2006 - Capítulo 5: Fósforo"
    content     TEXT NOT NULL,        -- texto del chunk (~500 tokens)
    embedding   vector(1536),         -- text-embedding-3-small de OpenAI
    species     TEXT,                 -- 'perro' | 'gato' | 'ambos'
    category    TEXT,                 -- 'macronutriente' | 'mineral' | 'vitamina' | 'ingrediente'
    source_type TEXT NOT NULL,        -- 'nrc' | 'aafco' | 'libro' | 'clinico'
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops);
```

### Fuentes a indexar (prioridad)

| Fuente | Tipo | Responsable validación |
|--------|------|------------------------|
| NRC 2006 — Nutrient Requirements of Dogs | nrc | Lady Carolina |
| NRC 2006 — Nutrient Requirements of Cats | nrc | Lady Carolina |
| AAFCO Nutrient Profiles 2024 | aafco | Sadid (official PDF) |
| Ingredientes LATAM con aliases regionales | clinico | Lady Carolina |
| Protocolos BAMPYSVET para condiciones médicas | clinico | Lady Carolina |

### Pipeline de ingesta

```
PDF / texto → chunking (~500 tokens, 50 overlap) → embedding (text-embedding-3-small)
→ INSERT INTO knowledge_chunks → disponible para retrieval
```

Script: `scripts/ingest_knowledge.py` — a implementar en unit-05.

### Tool del agente

```python
@tool
async def knowledge_retriever(query: str, species: str) -> list[str]:
    """
    Recupera chunks relevantes del knowledge base para grounding del LLM.

    Args:
        query: Consulta nutricional en texto natural.
        species: 'perro' o 'gato' para filtrar resultados.

    Returns:
        Lista de chunks ordenados por relevancia (cosine similarity).
    """
    embedding = await embed(query)
    chunks = await similarity_search(
        embedding=embedding,
        species=species,
        top_k=3,
        min_similarity=0.75,
    )
    return [chunk.content for chunk in chunks]
```

### Cuándo usar RAG vs. LLM base

| Tipo de consulta | Fuente |
|------------------|--------|
| Valores exactos NRC/AAFCO (fósforo, calcio, etc.) | RAG obligatorio |
| Ingredientes LATAM específicos | RAG si indexado, LLM como fallback |
| Consultas nutricionales generales | LLM base (sin RAG) |
| Consultas médicas (síntomas, medicamentos) | Referral Node → vet (nunca RAG ni LLM) |
| RER/DER y cálculos calóricos | Reglas deterministas (nunca RAG ni LLM) |

---

## Opciones Consideradas

| Opción | Descartada porque |
|--------|------------------|
| **Pinecone / Weaviate** | Costo adicional, servicio externo, complejidad operacional — pgvector sobre Postgres existente es suficiente para el volumen inicial |
| **Chroma (local)** | Requiere servicio adicional en Hetzner; pgvector reutiliza infraestructura ya provisionada |
| **Fine-tuning del LLM** | Costo muy alto, requiere dataset curado, difícil de actualizar — RAG es más ágil y actualizable |
| **Solo prompts del sistema** | Los system prompts tienen límite de tokens; las tablas NRC completas no caben; no escala |
| **Solo LLM base sin RAG** | Riesgo de alucinación en valores clínicos específicos — inaceptable para app médica veterinaria |

---

## Consecuencias

**Positivas**:
- Respuestas grounded en fuentes verificadas — reduce alucinaciones en valores clínicos exactos
- Actualizaciones del knowledge base sin re-deploy del agente (solo re-indexar)
- Reutiliza PostgreSQL existente — cero infraestructura adicional en Hetzner
- Trazabilidad: cada respuesta puede citar la fuente del chunk recuperado
- Lady Carolina puede auditar qué fuentes consulta el agente

**Negativas**:
- Latencia adicional: embedding + búsqueda vectorial suma ~200-400ms por consulta
- Requiere pipeline de ingesta y curación de documentos (trabajo inicial con Lady Carolina)
- Calidad del RAG depende de la calidad del chunking y los documentos indexados

**Impacto en código** (unit-05-agent-core):
- Migración Alembic: `CREATE EXTENSION vector` + tabla `knowledge_chunks`
- Nueva tool: `knowledge_retriever_tool` en `infrastructure/llm/tools/`
- Script de ingesta: `scripts/ingest_knowledge.py`
- Consultation Subgraph actualizado para usar la tool

**Impacto en operaciones**:
- Re-indexar knowledge base cuando Lady Carolina actualice fuentes clínicas
- Monitorear `retrieval_score` en agent_traces — si baja de 0.75 → revisar índice

---

## Variables de Entorno Requeridas

```bash
# Para generar embeddings (mismo proveedor que LLM, vía OpenRouter)
OPENAI_API_KEY=sk-...          # text-embedding-3-small
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
RAG_TOP_K=3
RAG_MIN_SIMILARITY=0.75
```

---

## Referencia

- Implementación planificada: **unit-05-agent-core** (Linear: NUT-9)
- Fuentes a validar con Lady Carolina antes de indexar
- pgvector docs: https://github.com/pgvector/pgvector
