# Archon RAG Pipeline Research Summary

**Research Date:** 2025-10-22
**Repository:** https://github.com/coleam00/Archon
**Purpose:** Inform Resume Agent Website RAG Pipeline design

---

## Quick Reference

### What is Archon?

Archon is a production-grade **knowledge and task management system** for AI coding assistants, built as an MCP server. It crawls documentation websites, chunks content, generates embeddings, and provides semantic search via multiple RAG strategies.

**Key Stats:**
- 13k GitHub stars
- Microservices architecture (FastAPI, React, PostgreSQL)
- Production features: WebSocket streaming, Docker deployment, multi-user support

---

## Technology Stack Comparison

| Component | Archon | Resume Agent (Recommended) |
|-----------|--------|----------------------------|
| **Vector DB** | PostgreSQL + pgvector (Supabase) | SQLite + sqlite-vec |
| **Embeddings** | sentence-transformers | OpenAI text-embedding-3-small |
| **Architecture** | Microservices (4 containers) | Monolithic (single process) |
| **Web Framework** | FastAPI | FastMCP |
| **Database** | PostgreSQL (cloud) | SQLite (local) |
| **Chunking** | Custom (undocumented) | RecursiveCharacterTextSplitter |
| **Search** | Hybrid (vector + FTS) | Hybrid (vector + FTS5) |
| **Reranking** | CrossEncoder (optional) | None (initially) |
| **Deployment** | Docker Compose | UV run (single file) |

---

## Architecture Diagram

### Archon (Production)
```
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│   UI    │  │ Server  │  │   MCP   │  │ Agents  │
│ :3737   │──│ :8181   │──│  :8051  │──│ :8052   │
└─────────┘  └─────────┘  └─────────┘  └─────────┘
                  │
                  ▼
          ┌──────────────┐
          │  PostgreSQL  │
          │  + pgvector  │
          └──────────────┘
```

### Resume Agent (Simplified)
```
┌──────────────────────────────────┐
│   Resume Agent (Single Process)  │
│                                  │
│  ┌────────────────────────────┐  │
│  │  FastMCP Server            │  │
│  │  - ingest_website()        │  │
│  │  - search_knowledge()      │  │
│  └────────────────────────────┘  │
│               │                  │
│  ┌────────────────────────────┐  │
│  │  SQLite + sqlite-vec       │  │
│  │  - website_sources         │  │
│  │  - website_chunks          │  │
│  │  - website_chunks_fts      │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
```

---

## Database Schema

### Archon Schema (Simplified)

**Key tables:**
1. `archon_sources` - Source metadata
2. `archon_crawled_pages` - Document chunks with multi-dimensional embeddings
3. `archon_code_examples` - Separate code snippet storage
4. `archon_page_metadata` - Full page content

**Multi-dimensional embeddings:**
```sql
CREATE TABLE archon_crawled_pages (
    id BIGSERIAL PRIMARY KEY,
    content TEXT,
    embedding_384 VECTOR(384),
    embedding_768 VECTOR(768),
    embedding_1024 VECTOR(1024),
    embedding_1536 VECTOR(1536),
    embedding_3072 VECTOR(3072),
    embedding_model TEXT,
    content_search_vector tsvector,  -- Full-text search
    -- ...
);
```

### Resume Agent Schema (Recommended)

**Simplified for single-user, local-first:**

```sql
-- Sources
CREATE TABLE website_sources (
    source_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata JSON
);

-- Chunks with single embedding dimension
CREATE TABLE website_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT REFERENCES website_sources(source_id),
    page_url TEXT,
    chunk_number INTEGER,
    content TEXT NOT NULL,
    embedding_1536 BLOB,  -- OpenAI 1536-dim embeddings
    metadata JSON
);

-- Full-text search (FTS5 virtual table)
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
    chunk_count INTEGER,
    metadata JSON
);
```

---

## RAG Pipeline Flow

### Archon's Pipeline (Configuration-Driven)

```python
# Pseudo-code
def perform_rag_query(query, limit):
    # Step 1: Strategy selection
    if USE_HYBRID_SEARCH:
        results = hybrid_search(query, limit)
    else:
        results = vector_search(query, limit)

    # Step 2: Optional reranking
    if USE_RERANKING:
        results = rerank_with_crossencoder(query, results)

    # Step 3: Page aggregation
    results = aggregate_by_page_id(results)

    return results
```

### Resume Agent Pipeline (Simplified)

```python
# Recommended approach
async def search_knowledge(query: str, limit: int = 10):
    # 1. Generate query embedding
    query_embedding = await openai_embed(query)

    # 2. Vector search (cosine similarity)
    vector_results = await vector_search(query_embedding, limit * 2)

    # 3. Full-text search (FTS5)
    fts_results = await fts_search(query, limit * 2)

    # 4. Union and deduplicate
    all_results = merge_results(vector_results, fts_results)

    # 5. Simple ranking (prioritize "both" matches)
    ranked = sort_by_match_type_and_similarity(all_results)

    return ranked[:limit]
```

---

## Key Takeaways

### ✅ Patterns to Adopt

1. **Hybrid Search (Vector + FTS)**
   - **Why:** Combines semantic understanding with keyword precision
   - **Implementation:** SQLite with sqlite-vec + FTS5
   - **Benefit:** Better recall and precision

2. **Separate Source and Chunk Tables**
   - **Why:** Clean data model, efficient queries
   - **Implementation:** `website_sources` + `website_chunks`
   - **Benefit:** Easy source management, bulk operations

3. **Page Metadata Storage**
   - **Why:** Preserve full context for retrieval
   - **Implementation:** `website_page_metadata` with `full_content`
   - **Benefit:** Can show complete page if needed

4. **JSONB/JSON Metadata Columns**
   - **Why:** Flexible extension without schema changes
   - **Implementation:** `metadata JSON` in all tables
   - **Benefit:** Store custom fields (timestamps, URLs, tags)

5. **Configuration-Driven Pipeline**
   - **Why:** Easy experimentation
   - **Implementation:** Feature flags for hybrid search, reranking
   - **Benefit:** A/B testing, gradual rollout

### ❌ Patterns to Avoid/Simplify

1. **Multi-Dimensional Embeddings**
   - **Why too complex:** Resume Agent uses single provider (OpenAI)
   - **Recommendation:** Start with 1536-dim only, add later if needed

2. **Microservices Architecture**
   - **Why overkill:** Single-user, local-first tool
   - **Recommendation:** Monolithic FastMCP server

3. **CrossEncoder Reranking (Initially)**
   - **Why premature:** Adds dependency, complexity
   - **Recommendation:** Start with hybrid search, add if precision issues

4. **WebSocket Streaming**
   - **Why unnecessary:** Small-scale crawling
   - **Recommendation:** Simple async with progress callbacks

5. **Separate Code Examples Table**
   - **Why not needed:** Resume Agent focuses on general documentation
   - **Recommendation:** Single chunks table, use metadata for content type

---

## Implementation Recommendations

### Phase 1: Basic RAG (Week 1)

**Goal:** Crawl single website, perform vector search

**Tasks:**
1. Create SQLite schema (sources, chunks, page_metadata)
2. Implement Playwright crawler
3. Add RecursiveCharacterTextSplitter (1000 chars, 200 overlap)
4. Generate OpenAI embeddings (text-embedding-3-small)
5. Store in sqlite-vec
6. Implement vector-only search
7. MCP tool: `ingest_website(url)`
8. MCP tool: `search_knowledge(query, limit)`

**Success Criteria:**
- Crawl 1-2 documentation sites
- Search returns relevant chunks
- < 1 second query latency

### Phase 2: Hybrid Search (Week 2)

**Goal:** Improve retrieval with full-text search

**Tasks:**
1. Create FTS5 virtual table
2. Populate during ingestion
3. Implement hybrid search (vector + FTS)
4. Add match_type tracking
5. Compare vector vs hybrid results

**Success Criteria:**
- Hybrid search finds keyword + semantic matches
- Comparison shows hybrid > vector-only

### Phase 3: Integration (Week 3)

**Goal:** Use in resume workflow

**Tasks:**
1. Crawl job posting documentation
2. Query for relevant technologies
3. Enhance resume with keywords
4. Reference docs in cover letter

**Success Criteria:**
- Can answer "What technologies does this company use?"
- Resume includes relevant keywords from docs

---

## Code Examples

### Ingestion (Resume Agent)

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
import openai

async def ingest_website(url: str) -> dict:
    # 1. Crawl website
    pages = await crawl_website(url)

    # 2. Chunk content
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    # 3. Process each page
    for page in pages:
        chunks = splitter.split_text(page.content)

        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = await openai.embeddings.create(
                input=chunk,
                model="text-embedding-3-small"
            )

            # Store in database
            await db.execute(
                """
                INSERT INTO website_chunks
                (source_id, page_url, chunk_number, content, embedding_1536)
                VALUES (?, ?, ?, ?, ?)
                """,
                [source_id, page.url, i, chunk, embedding.data[0].embedding]
            )

    return {"status": "success", "chunks": len(chunks)}
```

### Hybrid Search (Resume Agent)

```python
async def search_knowledge(query: str, limit: int = 10) -> list:
    # 1. Vector search
    query_embedding = await get_embedding(query)

    vector_results = await db.execute(
        """
        SELECT id, content, vec_distance_cosine(embedding_1536, ?) as similarity
        FROM website_chunks
        ORDER BY similarity
        LIMIT ?
        """,
        [query_embedding, limit * 2]
    ).fetchall()

    # 2. Full-text search
    fts_results = await db.execute(
        """
        SELECT c.id, c.content, fts.rank as fts_score
        FROM website_chunks_fts fts
        JOIN website_chunks c ON c.id = fts.rowid
        WHERE website_chunks_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        [query, limit * 2]
    ).fetchall()

    # 3. Merge results
    all_results = {}
    for r in vector_results:
        all_results[r.id] = {**r, "match_type": "vector"}
    for r in fts_results:
        if r.id in all_results:
            all_results[r.id]["match_type"] = "both"
        else:
            all_results[r.id] = {**r, "match_type": "fts"}

    # 4. Rank (prioritize "both")
    ranked = sorted(
        all_results.values(),
        key=lambda x: (x["match_type"] == "both", x.get("similarity", 0)),
        reverse=True
    )

    return ranked[:limit]
```

---

## Design Decisions

### Why SQLite instead of PostgreSQL?

| Factor | PostgreSQL (Archon) | SQLite (Resume Agent) |
|--------|---------------------|----------------------|
| **Deployment** | Requires Supabase account | Local file, no setup |
| **Performance** | Better for multi-user | Sufficient for single user |
| **Complexity** | Connection pooling, migrations | Simple file operations |
| **Cost** | $25/month (Supabase Pro) | Free |
| **Portability** | Cloud-dependent | Portable database file |

**Verdict:** SQLite aligns with Resume Agent's local-first philosophy.

### Why OpenAI Embeddings instead of sentence-transformers?

| Factor | sentence-transformers | OpenAI |
|--------|----------------------|--------|
| **Dependencies** | PyTorch (large) | API call (small) |
| **Performance** | Local inference | API latency |
| **Cost** | Free | $0.13 per 1M tokens |
| **Quality** | Good (768-1024 dims) | Excellent (1536 dims) |
| **Simplicity** | Model loading complexity | Single API call |

**Verdict:** OpenAI embeddings for simplicity. Resume Agent already uses OpenAI.

### Why No Reranking Initially?

**Rationale:**
1. Adds dependency (sentence-transformers, PyTorch)
2. Increases query latency (2-3× slower)
3. Hybrid search may be sufficient for documentation
4. Can add later if precision issues emerge

**When to add:**
- User feedback: "search returns irrelevant results"
- Metrics show low precision (< 50% relevance)
- After hybrid search optimization

---

## Performance Considerations

### Archon Performance Characteristics

**Query Latency:**
- Vector-only: ~100-200ms (PostgreSQL cosine similarity)
- Hybrid: ~200-400ms (union of two searches)
- With reranking: ~500-800ms (CrossEncoder inference)

**Ingestion Speed:**
- Crawling: Depends on website (10-100 pages/min)
- Chunking: Fast (~1000 chunks/sec)
- Embedding: API rate limits (3000 requests/min for OpenAI)

### Resume Agent Performance Targets

**Query Latency:**
- Target: < 500ms for hybrid search
- Acceptable: < 1 second

**Ingestion Speed:**
- Target: 1-5 pages/second (Playwright)
- Embedding: 100-500 chunks/min (OpenAI API)

**Storage:**
- Estimate: 1KB/chunk (text) + 6KB/embedding (1536 floats)
- 1000 chunks = ~7MB
- 10,000 chunks = ~70MB (reasonable for SQLite)

---

## Testing Strategy

### Unit Tests

```python
def test_chunking():
    content = "..." * 2000
    chunks = chunk_text(content, chunk_size=1000, overlap=200)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 for c in chunks)

async def test_vector_search():
    results = await search_knowledge("Python tutorial", limit=5)
    assert len(results) <= 5
    assert all("similarity" in r for r in results)

async def test_hybrid_search():
    results = await search_knowledge("pytest fixtures", limit=10)
    # Should find both semantic + keyword matches
    match_types = {r["match_type"] for r in results}
    assert "both" in match_types or ("vector" in match_types and "fts" in match_types)
```

### Integration Tests

```python
async def test_end_to_end_workflow():
    # 1. Ingest test documentation
    result = await ingest_website("https://docs.python.org/3/tutorial/")
    assert result["status"] == "success"
    assert result["chunks"] > 0

    # 2. Search for content
    results = await search_knowledge("list comprehension", limit=5)
    assert len(results) > 0

    # 3. Verify relevance (manual inspection)
    for r in results:
        print(f"[{r['match_type']}] {r['similarity']:.2f} - {r['content'][:100]}")
```

---

## Next Steps

1. **Review full analysis**: Read `archon-rag-analysis.md` for detailed technical breakdown
2. **Start Phase 1**: Implement basic RAG pipeline following simplified architecture
3. **Test with sample sites**: Crawl 2-3 documentation sites (Python, FastAPI, Playwright)
4. **Measure baseline**: Query latency, retrieval quality
5. **Iterate**: Add hybrid search, tune chunk size/overlap
6. **Integrate**: Use in job application workflow

---

## Resources

- **Archon Repository:** https://github.com/coleam00/Archon
- **Archon Demo Video:** https://youtu.be/8pRc_s2VQIo
- **Full Analysis:** `archon-rag-analysis.md`
- **Feature Spec:** `spec.md`

---

**End of Summary**
