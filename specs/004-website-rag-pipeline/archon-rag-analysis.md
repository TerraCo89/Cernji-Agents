# Archon RAG Pipeline Analysis

**Date:** 2025-10-22
**Repository:** https://github.com/coleam00/Archon
**Purpose:** Reference implementation study for Resume Agent Website RAG Pipeline

---

## Executive Summary

Archon is a production-grade RAG system designed as an MCP server for AI coding assistants. It implements a sophisticated multi-strategy retrieval pipeline with PostgreSQL (Supabase) + pgvector for vector storage, avoiding specialized vector databases. The architecture is **microservices-based** with clear separation between ingestion, storage, and retrieval concerns.

**Key Differentiators:**
- Multi-dimensional embedding support (384-3072 dimensions)
- Hybrid search (vector + full-text)
- Optional reranking with CrossEncoder
- Separate handling of code examples vs. documentation
- Configuration-driven strategy selection

---

## 1. Architecture Overview

### High-Level System Design

```
┌─────────────────┐
│  Web Crawler    │──────┐
│  (Playwright)   │      │
└─────────────────┘      │
                         ▼
                  ┌──────────────┐
                  │   Document   │
                  │  Processing  │
                  └──────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────┐
│         Embedding Service Layer             │
│  ┌───────────────────────────────────────┐  │
│  │  Multi-Dimensional Embedding Service  │  │
│  │  - Supports 384, 768, 1024,          │  │
│  │    1536, 3072 dimensions             │  │
│  │  - Model auto-detection              │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │   PostgreSQL/Supabase  │
            │   + pgvector Extension │
            │                        │
            │  Tables:               │
            │  - archon_sources      │
            │  - archon_crawled_pages│
            │  - archon_code_examples│
            │  - archon_page_metadata│
            └────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────┐
│         RAG Service (Coordinator)           │
│  ┌───────────────────────────────────────┐  │
│  │ Strategy Pipeline:                    │  │
│  │ 1. Search Strategy Selection          │  │
│  │    - BaseSearch (vector only)         │  │
│  │    - HybridSearch (vector + FTS)      │  │
│  │ 2. Candidate Retrieval (5× if rerank) │  │
│  │ 3. Optional Reranking (CrossEncoder)  │  │
│  │ 4. Result Aggregation by page_id      │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                         │
                         ▼
                ┌────────────────┐
                │  MCP Interface │
                │  (Port 8051)   │
                └────────────────┘
```

### Microservices Structure

| Service | Purpose | Technology |
|---------|---------|------------|
| **Server** (Port 8181) | Core API, document processing, all ML/AI operations | FastAPI, SocketIO |
| **MCP Server** (Port 8051) | Model Context Protocol interface for AI clients | Lightweight HTTP wrapper |
| **Agents** (Port 8052) | PydanticAI agent hosting, document/RAG agents | PydanticAI, streaming |
| **UI** (Port 3737) | Web dashboard | React, TypeScript, TailwindCSS |

**Communication:** All inter-service communication via HTTP (no shared code dependencies).

---

## 2. Database Design

### Schema Architecture

Archon uses **PostgreSQL with pgvector extension** through Supabase. The schema supports multi-dimensional embeddings natively.

#### `archon_sources`
**Purpose:** Source metadata registry

```sql
CREATE TABLE archon_sources (
    source_id TEXT PRIMARY KEY,           -- SHA256 hash
    source_url TEXT,
    source_display_name TEXT,
    title TEXT,
    summary TEXT,
    total_word_count INTEGER,
    metadata JSONB
);
```

#### `archon_crawled_pages`
**Purpose:** Document chunks with embeddings

```sql
CREATE TABLE archon_crawled_pages (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR,
    chunk_number INTEGER,
    content TEXT,
    source_id TEXT REFERENCES archon_sources(source_id),

    -- Multi-dimensional embedding support
    embedding_384 VECTOR(384),
    embedding_768 VECTOR(768),
    embedding_1024 VECTOR(1024),
    embedding_1536 VECTOR(1536),
    embedding_3072 VECTOR(3072),

    embedding_model TEXT,
    embedding_dimension INTEGER,

    -- Full-text search support
    content_search_vector tsvector,

    metadata JSONB,
    page_id UUID REFERENCES archon_page_metadata(id)
);
```

#### `archon_code_examples`
**Purpose:** Specialized code snippet storage

```sql
CREATE TABLE archon_code_examples (
    id BIGSERIAL PRIMARY KEY,
    url VARCHAR,
    chunk_number INTEGER,
    source_id TEXT,
    content TEXT,                  -- Code block content
    summary TEXT,                  -- AI-generated description

    -- Same multi-dimensional embedding support
    embedding_384 VECTOR(384),
    -- ... (same as crawled_pages)

    embedding_model TEXT,
    embedding_dimension INTEGER,
    llm_chat_model TEXT,           -- Model used for summary
    content_search_vector tsvector
);
```

#### `archon_page_metadata`
**Purpose:** Complete page storage for context

```sql
CREATE TABLE archon_page_metadata (
    id UUID PRIMARY KEY,
    url TEXT UNIQUE,
    full_content TEXT,             -- Complete markdown/text
    source_id TEXT,
    section_title TEXT,
    section_order INTEGER,
    word_count INTEGER,
    char_count INTEGER,
    chunk_count INTEGER
);
```

### Key Design Decisions

1. **Multi-dimensional embeddings**: Supports different models without schema changes
2. **Hybrid search columns**: Both vector (`embedding_*`) and full-text (`content_search_vector`)
3. **Separate code table**: Specialized handling for code examples
4. **JSONB metadata**: Flexible extension without schema migration
5. **Page aggregation**: `page_id` FK enables chunk → full document reconstruction

---

## 3. Technology Stack

### Embedding & Vector Search

| Component | Library/Service | Notes |
|-----------|----------------|-------|
| **Embeddings** | `sentence-transformers>=4.1.0` | HuggingFace models |
| **Neural models** | `torch>=2.0.0` (CPU-only) | Configured via custom PyTorch index |
| **Transformers** | `transformers>=4.30.0` | Pre-trained model access |
| **Vector DB** | Supabase (PostgreSQL + pgvector) | No specialized vector DB needed |
| **Async DB** | `asyncpg>=0.29.0` | PostgreSQL async driver |
| **Reranking** | CrossEncoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) | Optional result reordering |

### Notable Absences

- **No Pinecone/Weaviate/Milvus**: Uses pgvector instead
- **No LangChain**: Custom implementation
- **No ChromaDB**: PostgreSQL-native approach

---

## 4. RAG Pipeline Implementation

### 4.1 Document Ingestion

**Flow:**
1. Web crawling (Playwright-based)
2. Document parsing and chunking
3. Embedding generation (multi-dimensional)
4. Database insertion with multiple vector columns

**Chunking Strategy:**
- **Not explicitly defined in knowledge service**
- Code suggests ~250 words/chunk (book page reference)
- Separate handling for code examples vs. documentation
- Actual chunking logic in crawling/processing components

### 4.2 Retrieval Strategies

#### Base Search Strategy
**Vector-only semantic search**
- Generates query embedding
- Performs cosine similarity search
- Returns top-k results with similarity scores

#### Hybrid Search Strategy
**Combines vector + full-text**

```python
# Pseudo-code based on implementation
def hybrid_search(query, limit, filters):
    # Execute both searches
    vector_results = vector_search(query_embedding, limit, filters)
    fts_results = full_text_search(query_keywords, limit, filters)

    # Union of both result sets
    combined = union(vector_results, fts_results)

    # Track match type distribution
    for result in combined:
        result.match_type = "vector" | "full_text" | "both"

    return combined
```

**Key characteristics:**
- Uses PostgreSQL stored procedures (`hybrid_search_archon_crawled_pages`)
- Returns **union** of both result sets (maximum coverage)
- Includes `match_type` metadata for debugging
- No explicit ranking/scoring fusion documented

#### Reranking Strategy
**CrossEncoder-based result refinement**

```python
def rerank_results(query, candidates, top_k):
    # Build query-document pairs
    pairs = [(query, doc.content) for doc in candidates]

    # CrossEncoder scoring
    scores = cross_encoder.predict(pairs)

    # Sort by relevance
    ranked = sort_by_score(candidates, scores)

    return ranked[:top_k]
```

**Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
**Purpose:** Improve precision over initial retrieval

#### Agentic RAG Strategy
**Specialized for code example discovery**
- Domain-specific retrieval logic
- Separate from general documentation search

### 4.3 RAG Service Orchestration

**Configuration-driven pipeline:**

```python
class RAGService:
    def perform_rag_query(self, query, limit, filters):
        # Step 1: Strategy selection
        if USE_HYBRID_SEARCH:
            strategy = HybridSearchStrategy()
        else:
            strategy = BaseSearchStrategy()

        # Step 2: Candidate retrieval
        if USE_RERANKING:
            candidate_limit = limit * 5  # Over-fetch for reranking
        else:
            candidate_limit = limit

        candidates = strategy.search(query, candidate_limit, filters)

        # Step 3: Optional reranking
        if USE_RERANKING:
            results = RerankingStrategy().rerank(query, candidates, limit)
        else:
            results = candidates[:limit]

        # Step 4: Page aggregation (optional)
        if group_by_page:
            results = aggregate_by_page_id(results)

        return results
```

**Configuration flags:**
- `USE_HYBRID_SEARCH`: Enable hybrid strategy
- `USE_RERANKING`: Enable CrossEncoder reranking
- `USE_AGENTIC_RAG`: Enable code example extraction

---

## 5. Multi-Dimensional Embedding Strategy

### Purpose

Support multiple embedding models from different providers without schema changes.

### Implementation

```python
# Model → Dimension mapping (heuristic-based)
def get_embedding_dimension(model_name):
    if "large" in model_name.lower():
        return 3072  # OpenAI large
    elif "google" in model_name.lower():
        return 768   # Google models
    elif "ollama" in model_name.lower():
        return 1024  # Ollama default
    else:
        return 1536  # Default (OpenAI standard)
```

### Benefits

1. **Provider flexibility**: Switch between OpenAI, Google, Ollama, etc.
2. **Cost-performance optimization**: Choose dimension based on use case
3. **Backward compatibility**: Old embeddings remain valid
4. **Graceful degradation**: Unknown models → default dimension

### Database Storage

Each chunk can have **multiple embeddings simultaneously**:
- Small models (384, 768): Faster, cheaper
- Large models (3072): More accurate, expensive

Query uses appropriate column based on configured model.

---

## 6. API Design

### Document Ingestion

**Endpoint:** `/api/knowledge/crawl`
**Method:** POST
**Payload:**
```json
{
  "url": "https://docs.example.com",
  "source_display_name": "Example Docs",
  "crawl_type": "sitemap" | "single" | "recursive"
}
```

**Response:** WebSocket stream with progress updates

### RAG Query

**Endpoint:** `/api/search/rag`
**Method:** POST
**Payload:**
```json
{
  "query": "How do I configure embeddings?",
  "limit": 10,
  "filters": {
    "source_id": "optional-source-filter",
    "min_similarity": 0.7
  },
  "use_hybrid": true,
  "use_reranking": true
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "...",
      "similarity": 0.85,
      "match_type": "both",
      "url": "...",
      "source_id": "...",
      "metadata": {}
    }
  ],
  "execution_metadata": {
    "strategy": "hybrid",
    "reranked": true,
    "total_candidates": 50,
    "final_count": 10
  }
}
```

---

## 7. Key Takeaways for Resume Agent

### Patterns to Adopt

1. **Multi-dimensional embedding support**
   - Simple for Resume Agent: Just support OpenAI text-embedding-3-small (1536 dims)
   - Future-proof: Add column if switching models

2. **Hybrid search approach**
   - Vector search for semantic matching
   - Full-text search for exact keyword matching
   - Union results for maximum recall

3. **Configuration-driven pipeline**
   - Feature flags for strategies (hybrid, reranking)
   - Easy experimentation without code changes

4. **Separate tables for different content types**
   - `website_pages` for general documentation
   - `website_code_examples` for code snippets (if needed)

5. **Page metadata storage**
   - Keep full page content for context
   - Chunks reference parent page via FK

6. **JSONB metadata columns**
   - Flexible extension without schema migration
   - Store URL, timestamps, custom fields

### Patterns to Avoid/Simplify

1. **Multi-dimensional embeddings (initially)**
   - **Too complex for single-user system**
   - Resume Agent: Start with 1536-dim OpenAI embeddings only
   - Can add later if needed

2. **Microservices architecture**
   - **Overkill for local-first tool**
   - Resume Agent: Single FastMCP server
   - All logic in one process

3. **CrossEncoder reranking (initially)**
   - **Adds dependency and complexity**
   - Start with hybrid search only
   - Add if precision issues emerge

4. **Agentic RAG strategies**
   - **Not needed for documentation search**
   - Resume Agent: Simple hybrid search sufficient

5. **WebSocket streaming**
   - **Unnecessary for small-scale crawling**
   - Simple async with progress callbacks

### Resume Agent Architecture Adaptation

```
┌──────────────────────────────────────────┐
│     Resume Agent (Single Process)        │
│  ┌────────────────────────────────────┐  │
│  │  MCP Server (FastMCP)              │  │
│  │  - Tools: ingest_website, query    │  │
│  └────────────────────────────────────┘  │
│               │                          │
│  ┌────────────────────────────────────┐  │
│  │  Ingestion Service                 │  │
│  │  - Playwright crawler              │  │
│  │  - Chunking (RecursiveCharacter)   │  │
│  │  - OpenAI embeddings               │  │
│  └────────────────────────────────────┘  │
│               │                          │
│  ┌────────────────────────────────────┐  │
│  │  SQLite Database (local)           │  │
│  │  - website_sources                 │  │
│  │  - website_chunks                  │  │
│  │  - website_page_metadata           │  │
│  └────────────────────────────────────┘  │
│               │                          │
│  ┌────────────────────────────────────┐  │
│  │  Retrieval Service                 │  │
│  │  - Hybrid search (vec + FTS)       │  │
│  │  - Result aggregation              │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### Simplified Schema for Resume Agent

```sql
-- Sources table
CREATE TABLE website_sources (
    source_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    chunk_count INTEGER DEFAULT 0,
    metadata JSON
);

-- Chunks table (simplified from Archon)
CREATE TABLE website_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT REFERENCES website_sources(source_id),
    page_url TEXT,
    chunk_number INTEGER,
    content TEXT NOT NULL,

    -- Single embedding column (1536 dims)
    embedding_1536 BLOB,  -- SQLite vec extension

    -- Full-text search
    -- (handled by FTS5 virtual table)

    metadata JSON
);

-- FTS5 virtual table for keyword search
CREATE VIRTUAL TABLE website_chunks_fts USING fts5(
    content,
    content=website_chunks,
    content_rowid=id
);

-- Page metadata
CREATE TABLE website_page_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT,
    page_url TEXT UNIQUE,
    full_content TEXT,
    word_count INTEGER,
    chunk_count INTEGER,
    metadata JSON
);
```

### Chunking Strategy for Resume Agent

**Recommendation:** Use LangChain's `RecursiveCharacterTextSplitter`

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,        # ~250 words
    chunk_overlap=200,      # 20% overlap
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = splitter.split_text(page_content)
```

**Why not Archon's approach:**
- Archon's chunking logic is hidden in crawling components
- RecursiveCharacterTextSplitter is proven and documented
- Easy to tune chunk_size and overlap

### Hybrid Search Implementation

```python
async def hybrid_search(query: str, limit: int = 10):
    # 1. Vector search
    query_embedding = await get_embedding(query)
    vector_results = await vector_search(query_embedding, limit * 2)

    # 2. Full-text search
    fts_results = await fts_search(query, limit * 2)

    # 3. Union and deduplicate
    all_results = {}
    for r in vector_results:
        all_results[r.id] = {**r, "match_type": "vector"}
    for r in fts_results:
        if r.id in all_results:
            all_results[r.id]["match_type"] = "both"
        else:
            all_results[r.id] = {**r, "match_type": "fts"}

    # 4. Simple ranking: prioritize "both", then by similarity
    ranked = sorted(
        all_results.values(),
        key=lambda x: (x["match_type"] == "both", x.get("similarity", 0)),
        reverse=True
    )

    return ranked[:limit]
```

---

## 8. Implementation Roadmap for Resume Agent

### Phase 1: Basic RAG (MVP)
**Goal:** Single website ingestion and retrieval

- [ ] SQLite schema with single embedding column
- [ ] Playwright-based web crawler
- [ ] RecursiveCharacterTextSplitter for chunking
- [ ] OpenAI text-embedding-3-small for embeddings
- [ ] Vector-only search (cosine similarity)
- [ ] MCP tools: `ingest_website`, `search_knowledge`

### Phase 2: Hybrid Search
**Goal:** Improve retrieval quality

- [ ] FTS5 virtual table for full-text search
- [ ] Hybrid search implementation
- [ ] Match type tracking
- [ ] Query result comparison (vector vs hybrid)

### Phase 3: Advanced Features (Optional)
**Goal:** Production-grade capabilities

- [ ] Multiple source management
- [ ] Incremental updates (re-crawl detection)
- [ ] Result reranking (CrossEncoder)
- [ ] Search filters (by source, date, etc.)
- [ ] Search analytics/logging

### Phase 4: Integration
**Goal:** Use in resume workflow

- [ ] Add job posting documentation to knowledge base
- [ ] Query for relevant technologies/frameworks
- [ ] Enhance resume with discovered keywords
- [ ] Reference documentation in cover letters

---

## 9. Code Examples

### Archon's Hybrid Search (Simplified)

```python
# From: python/src/server/services/search/hybrid_search_strategy.py

class HybridSearchStrategy:
    async def search(self, query: str, limit: int, filters: dict):
        # Execute both searches via PostgreSQL functions
        vector_results = await self._vector_search(query, limit, filters)
        fts_results = await self._fts_search(query, limit, filters)

        # Union results
        combined = self._union_results(vector_results, fts_results)

        # Add match type metadata
        for result in combined:
            result["match_type"] = self._determine_match_type(
                result, vector_results, fts_results
            )

        return combined
```

### Archon's Reranking

```python
# From: python/src/server/services/search/reranking_strategy.py

from sentence_transformers import CrossEncoder

class RerankingStrategy:
    def __init__(self):
        self.model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

    def rerank(self, query: str, candidates: list, top_k: int):
        # Build query-document pairs
        pairs = [(query, doc["content"]) for doc in candidates]

        # Score with CrossEncoder
        scores = self.model.predict(pairs)

        # Sort by score
        for doc, score in zip(candidates, scores):
            doc["rerank_score"] = float(score)

        ranked = sorted(
            candidates,
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return ranked[:top_k]
```

### Archon's Multi-Dimensional Embedding

```python
# From: python/src/server/services/embeddings/multi_dimensional_embedding_service.py

def get_embedding_dimension(model_name: str) -> int:
    """Map model name to embedding dimension."""
    model_lower = model_name.lower()

    if "3072" in model_lower or "large" in model_lower:
        return 3072
    elif "1536" in model_lower:
        return 1536
    elif "1024" in model_lower:
        return 1024
    elif "768" in model_lower or "google" in model_lower:
        return 768
    elif "384" in model_lower:
        return 384
    else:
        return 1536  # Default to OpenAI standard
```

---

## 10. Conclusion

### What Makes Archon's RAG Pipeline Strong

1. **PostgreSQL-first approach**: Leverages existing database instead of specialized vector DB
2. **Multi-dimensional flexibility**: Supports various embedding models without migration
3. **Strategy pattern**: Clean separation of search strategies (base, hybrid, reranking, agentic)
4. **Configuration-driven**: Easy experimentation via feature flags
5. **Production-ready**: Microservices, WebSocket streaming, error handling

### What Resume Agent Should Borrow

1. **Hybrid search**: Vector + FTS for better recall
2. **Schema design**: Separate sources, chunks, and page metadata
3. **JSONB/JSON metadata**: Flexible extension
4. **Strategy coordinator**: Clean abstraction for search logic
5. **Match type tracking**: Debug which search method found results

### What Resume Agent Should Simplify

1. **Single embedding dimension**: 1536-dim OpenAI only (initially)
2. **Monolithic architecture**: Single FastMCP process
3. **SQLite instead of PostgreSQL**: Local-first, simpler deployment
4. **No reranking initially**: Add only if precision issues
5. **Simpler chunking**: RecursiveCharacterTextSplitter (1000 chars, 200 overlap)

### Next Steps

1. **Implement Phase 1** (Basic RAG) following simplified architecture
2. **Test hybrid search** with sample documentation sites
3. **Measure performance**: Query latency, retrieval quality
4. **Iterate based on real usage** in job application workflow

---

## Appendix: Archon Repository Structure

```
Archon/
├── python/
│   └── src/
│       ├── server/                    # Core API server
│       │   ├── services/
│       │   │   ├── embeddings/        # Embedding generation
│       │   │   │   ├── multi_dimensional_embedding_service.py
│       │   │   │   ├── contextual_embedding_service.py
│       │   │   │   └── embedding_service.py
│       │   │   ├── search/            # RAG retrieval
│       │   │   │   ├── rag_service.py
│       │   │   │   ├── hybrid_search_strategy.py
│       │   │   │   ├── reranking_strategy.py
│       │   │   │   ├── agentic_rag_strategy.py
│       │   │   │   └── base_search_strategy.py
│       │   │   ├── knowledge/         # Document management
│       │   │   │   ├── knowledge_item_service.py
│       │   │   │   └── knowledge_summary_service.py
│       │   │   ├── crawling/          # Web scraping
│       │   │   └── storage/           # Database access
│       │   └── main.py
│       ├── mcp_server/                # MCP interface
│       └── agents/                    # PydanticAI agents
├── migration/
│   └── complete_setup.sql             # Database schema
├── archon-ui-main/                    # React frontend
└── pyproject.toml                     # Dependencies
```

---

**End of Analysis**
