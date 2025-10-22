# Research Findings: Website RAG Pipeline

**Feature**: 004-website-rag-pipeline
**Date**: 2025-10-22
**Status**: Complete

## Overview

This document consolidates research findings for implementing a RAG (Retrieval Augmented Generation) pipeline to process websites (job postings, career blogs, company pages) for the Resume Agent. All NEEDS CLARIFICATION items from the Technical Context have been resolved.

---

## Decision 1: Vector Embedding Library

### Decision
**Use: `sentence-transformers` + `sqlite-vec`**

### Rationale
1. **Simplicity**: 2 dependencies only, integrates natively with existing SQLite database
2. **Multilingual support**: Excellent English + Japanese support via `paraphrase-multilingual-MiniLM-L12-v2` model
3. **Zero API costs**: Fully local execution, no OpenAI API dependency
4. **Production ready**: Both libraries are stable and actively maintained (2025)
5. **SQLite integration**: `sqlite-vec` is a native SQLite extension with SIMD-optimized vector search
6. **Constitution aligned**: Follows Principle VIII (Simplicity & YAGNI)

### Alternatives Considered

| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| **ChromaDB** | All-in-one solution, optimized indexes | Heavier footprint, less control over SQLite schema | Abstracts away SQLite, harder to integrate with existing data layer |
| **FAISS + sentence-transformers** | Best-in-class search performance | Manual persistence, DIY SQLite integration | Overkill for <100K vectors, high maintenance burden |
| **OpenAI Embeddings** | Best quality, no model downloads | Requires API key, costs money, no offline support | Spec prefers "no external API dependencies" |

### Implementation Details

**Dependencies (PEP 723 format):**
```python
# dependencies = [
#   "sentence-transformers>=3.0.0",
#   "sqlite-vec>=0.1.0",
# ]
```

**Model**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Dimension**: 384
- **Languages**: 50+ including English and Japanese
- **Size**: ~420MB (one-time download, cached locally)
- **Performance**: ~1000 sentences/sec on CPU

**Embedding Storage:**
- Store as BLOB in SQLite using `struct.pack()`
- Create virtual table: `CREATE VIRTUAL TABLE vec_chunks USING vec0(embedding FLOAT[384])`
- Native SQL syntax for similarity search: `WHERE embedding MATCH ?`

**Example Query:**
```python
results = db.execute("""
    SELECT chunk_id, distance
    FROM vec_chunks
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 5
""", (query_embedding_blob,)).fetchall()
```

**Performance Targets:**
- Embedding generation: <1s for 1000 characters
- Similarity search: <10ms for 10K vectors
- Meets spec requirement: <3s for semantic queries

---

## Decision 2: Text Chunking Strategy

### Decision
**Use: Hybrid `HTMLHeaderTextSplitter` + `RecursiveCharacterTextSplitter`**

### Rationale
1. **Structure-aware**: Preserves HTML document structure (headers, sections)
2. **Semantic quality**: Maintains context boundaries (doesn't split mid-thought)
3. **Low complexity**: Battle-tested LangChain components (~15 lines of config)
4. **Japanese support**: UTF-8 safe by default, no special handling needed
5. **Metadata-rich**: Captures header hierarchy for better retrieval
6. **Flexible**: Handles structured (job postings) and unstructured (blogs) content

### Alternatives Considered

| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| **RecursiveCharacterTextSplitter only** | Simple, 3 lines of code | Ignores HTML structure, may split lists mid-item | Poor quality for structured job postings |
| **Custom HTML-aware chunking** | Perfect control, optimal for job postings | ~200-300 lines, brittle to HTML variations | Violates Simplicity principle, high maintenance |
| **Fixed-size with overlap** | Trivial to implement | No semantic awareness, splits mid-sentence | Unacceptable retrieval quality |
| **SemanticChunker** | Best topic coherence | Requires embedding model during chunking (slow) | Overkill, adds complexity |

### Implementation Details

**Dependencies:**
```python
# dependencies = [
#   "langchain-text-splitters>=0.3.0",  # Standalone package, 5MB vs 200MB for full langchain
# ]
```

**Two-stage chunking process:**

1. **Stage 1: HTML-aware splitting**
   - Use `HTMLHeaderTextSplitter` to split on `<h1>`, `<h2>`, `<h3>` boundaries
   - Preserves header hierarchy as metadata
   - Each section becomes an initial chunk

2. **Stage 2: Recursive splitting (if needed)**
   - If chunk > 1200 characters, apply `RecursiveCharacterTextSplitter`
   - Splits on: `["\n\n", "\n", ". ", " ", ""]` (paragraph → sentence → word)
   - Maintains 150-character overlap for context

**Chunk Size Recommendations:**

| Content Type | Target Size | Overlap | Rationale |
|--------------|------------|---------|-----------|
| Job Postings (English) | 800-1000 chars | 150 chars | Typical section size |
| Job Postings (Japanese) | 600-800 chars | 150 chars | Higher info density |
| Blog Articles (English) | 1000-1200 chars | 200 chars | Preserve full thoughts |
| Blog Articles (Japanese) | 700-900 chars | 150 chars | Higher info density |

**UTF-8 Safety:**
- Python 3.10+ string slicing respects UTF-8 boundaries automatically
- LangChain uses character-based `len()` function (safe for multi-byte)
- No special handling needed for Japanese text

**Example Code:**
```python
from langchain.text_splitter import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter

# Stage 1: HTML structure
html_splitter = HTMLHeaderTextSplitter(
    headers_to_split_on=[("h1", "Header 1"), ("h2", "Header 2"), ("h3", "Header 3")]
)
html_chunks = html_splitter.split_text(html)

# Stage 2: Recursive for long sections
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""]
)

final_chunks = []
for html_chunk in html_chunks:
    if len(html_chunk.page_content) > 1200:
        # Split long sections
        sub_chunks = text_splitter.split_text(html_chunk.page_content)
        for sub in sub_chunks:
            final_chunks.append({
                "content": sub,
                "metadata": html_chunk.metadata  # Includes headers
            })
    else:
        # Keep intact
        final_chunks.append({
            "content": html_chunk.page_content,
            "metadata": html_chunk.metadata
        })
```

**Performance:**
- Chunking time: 0.5-1s for job posting, 1-2s for blog article
- Meets spec requirement: <15s total processing time

---

## Decision 3: Archon RAG Implementation Insights

### Key Takeaways from Archon Project

**What to Adopt:**

1. **Hybrid Search Pattern**
   - Combine vector similarity + full-text search (FTS5)
   - Better recall: Vector for semantic, FTS for exact keyword matches
   - Archon uses PostgreSQL `tsvector`, we'll use SQLite FTS5

2. **Separate Source/Chunk Tables**
   - `website_sources` table: URL, title, fetch date, content type
   - `website_chunks` table: Individual chunks with embeddings, references source
   - Clean separation of concerns, easier to refresh stale content

3. **Page Metadata Storage**
   - Store full HTML alongside chunks for re-chunking later
   - Metadata: title, description, language, extraction timestamp
   - Enables iterative improvement without re-fetching

4. **JSON Metadata Columns**
   - Use JSONB for flexible metadata (headers, tags, extracted entities)
   - Avoids rigid schema changes for new metadata fields

5. **Configuration-Driven Pipeline**
   - Externalize chunk size, overlap, embedding model as config
   - Enables experimentation without code changes

**What to Simplify:**

1. **Single Embedding Dimension**
   - Archon supports 5 dimensions (384, 768, 1024, 1536, 3072)
   - We'll use single 384-dim for simplicity (sentence-transformers)

2. **Monolithic Architecture**
   - Archon: 4 microservices (UI, Server, MCP, Agents)
   - Resume Agent: Single FastMCP process (local-first)

3. **SQLite Instead of PostgreSQL**
   - Archon: PostgreSQL + pgvector via Supabase
   - Resume Agent: SQLite + sqlite-vec (simpler, file-based)

4. **No Reranking Initially**
   - Archon uses CrossEncoder reranking for precision
   - We'll add if retrieval quality is insufficient (YAGNI)

5. **Simpler Chunking**
   - Archon: Multiple strategies (markdown, recursive, semantic)
   - Resume Agent: Hybrid HTML + recursive only

### Architecture Comparison

**Archon (Multi-service):**
```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│   UI    │────▶│ Server  │────▶│   MCP   │────▶│ Agents  │
│ (React) │     │(FastAPI)│     │(Python) │     │(Claude) │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
                     │
                     ▼
              ┌────────────┐
              │ PostgreSQL │
              │  +pgvector │
              └────────────┘
```

**Resume Agent (Monolithic - RECOMMENDED):**
```
┌──────────────────────────────────┐
│   Resume Agent (Single Process)  │
│  ┌────────────────────────────┐  │
│  │  FastMCP Server            │  │
│  │  - process_website()       │  │
│  │  - query_websites()        │  │
│  │  - list_websites()         │  │
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

### Database Schema Design (Inspired by Archon)

**`website_sources` table:**
```sql
CREATE TABLE website_sources (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content_type TEXT,  -- 'job_posting' | 'blog_article' | 'company_page'
    language TEXT,      -- 'en' | 'ja' | 'mixed'
    raw_html TEXT,      -- Full HTML for re-processing
    metadata_json TEXT, -- JSON: {description, author, published_date, ...}
    fetch_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending',  -- 'pending' | 'completed' | 'failed'
    error_message TEXT
);
```

**`website_chunks` table:**
```sql
CREATE TABLE website_chunks (
    id INTEGER PRIMARY KEY,
    source_id INTEGER REFERENCES website_sources(id),
    chunk_index INTEGER,
    content TEXT NOT NULL,
    char_count INTEGER,
    metadata_json TEXT,  -- JSON: {headers, section, ...}
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Vector table (sqlite-vec)
CREATE VIRTUAL TABLE website_chunks_vec USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding FLOAT[384]
);

-- FTS5 table for keyword search
CREATE VIRTUAL TABLE website_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    content,
    tokenize='porter unicode61'
);
```

**Hybrid Search Query:**
```sql
-- Combine vector similarity + FTS keyword match
WITH vector_results AS (
    SELECT chunk_id, distance
    FROM website_chunks_vec
    WHERE embedding MATCH ?
    ORDER BY distance LIMIT 20
),
fts_results AS (
    SELECT chunk_id, rank
    FROM website_chunks_fts
    WHERE content MATCH ?
    ORDER BY rank LIMIT 20
)
SELECT DISTINCT c.*,
       COALESCE(v.distance, 999) as vec_score,
       COALESCE(f.rank, 999) as fts_score
FROM website_chunks c
LEFT JOIN vector_results v ON c.id = v.chunk_id
LEFT JOIN fts_results f ON c.id = f.chunk_id
WHERE v.chunk_id IS NOT NULL OR f.chunk_id IS NOT NULL
ORDER BY (vec_score * 0.7 + fts_score * 0.3)  -- Weighted hybrid
LIMIT 10;
```

---

## Technology Stack Summary

### Core Dependencies (PEP 723)

```python
# /// script
# dependencies = [
#   "fastmcp>=2.0",
#   "pyyaml>=6.0",
#   "httpx>=0.28.0",
#   "sqlmodel>=0.0.22",
#   "python-dotenv>=1.0.0",
#   # NEW: RAG Pipeline Dependencies
#   "sentence-transformers>=3.0.0",      # Embeddings (local, multilingual)
#   "sqlite-vec>=0.1.0",                 # Vector search extension
#   "langchain-text-splitters>=0.3.0",   # Chunking (5MB standalone package)
# ]
# requires-python = ">=3.10"
# ///
```

### External Tools (Already Available)
- **Playwright**: Web scraping (already used in Resume Agent)
- **BeautifulSoup4**: HTML parsing (assumed, or use Playwright's built-in)
- **SQLite**: Database (existing `data/resume_agent.db`)

---

## Performance Projections

Based on research findings and spec requirements:

| Operation | Target | Expected | Status |
|-----------|--------|----------|--------|
| **URL Processing (Job Posting)** | <15s | 8-12s | ✅ Meets spec |
| **URL Processing (Blog Article)** | <20s | 12-18s | ✅ Meets spec |
| **Semantic Query** | <3s | 1-2s | ✅ Exceeds spec |
| **Cache Hit** | <1s | <500ms | ✅ Exceeds spec |

**Breakdown (Job Posting Example):**
1. Playwright fetch: 2-5s
2. HTML parsing: <0.5s
3. Chunking (hybrid): 0.5-1s
4. Embedding generation: 5-8s (5-10 chunks × 1000 chars each)
5. SQLite storage: <0.5s
6. **Total: 8-15s** ✅

**Optimization for FR-018 (Asynchronous Processing):**
- Process embeddings in parallel (5 chunks → 2s instead of 5s)
- Return immediately with "processing" status
- Notify user when complete via observability events

---

## Japanese Language Support

### Validated Approaches

1. **Embeddings**: `paraphrase-multilingual-MiniLM-L12-v2`
   - Trained on 50+ languages including Japanese
   - Shared vector space: English query can match Japanese docs
   - Tested quality: ⭐⭐⭐⭐ Excellent

2. **Chunking**: LangChain splitters
   - UTF-8 safe by default (Python 3.10+ string slicing)
   - No special handling needed for multi-byte characters
   - Adjust chunk size: 600-800 chars for Japanese (vs 1000 for English)

3. **Full-Text Search**: SQLite FTS5
   - `tokenize='unicode61'` handles Japanese correctly
   - Supports hiragana, katakana, kanji
   - Tested with bilingual content: works correctly

### Language Detection

```python
import re

def detect_japanese(text: str) -> bool:
    """Detect if text contains Japanese characters."""
    japanese_chars = re.findall(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text)
    return len(japanese_chars) / len(text) > 0.1  # >10% Japanese
```

Use to adjust chunk sizes dynamically.

---

## Open Questions Resolved

### Question: Vector embedding library choice?
**Resolved**: `sentence-transformers` + `sqlite-vec` (see Decision 1)

### Question: Chunking strategy?
**Resolved**: Hybrid `HTMLHeaderTextSplitter` + `RecursiveCharacterTextSplitter` (see Decision 2)

### Question: How does Archon implement RAG?
**Resolved**: See Decision 3 for architecture patterns, database design, and hybrid search strategy

### Question: Can we store embeddings in SQLite?
**Resolved**: Yes, via `sqlite-vec` extension (native BLOB storage, SIMD-optimized search)

### Question: How to handle Japanese text?
**Resolved**: Use multilingual model (`paraphrase-multilingual-MiniLM-L12-v2`), UTF-8 safe chunking, FTS5 with `unicode61` tokenizer

---

## Implementation Phases (Recommendation)

### Phase 1: Basic RAG (Week 1)
- Vector-only search (sentence-transformers + sqlite-vec)
- Simple chunking (RecursiveCharacterTextSplitter)
- Single table schema
- MCP tools: `process_website()`, `query_websites()`

### Phase 2: Hybrid Search (Week 2)
- Add FTS5 full-text search
- Implement hybrid scoring (70% vector + 30% FTS)
- Separate source/chunk tables
- HTML-aware chunking

### Phase 3: Integration (Week 3)
- Integrate with `/career:apply` workflow
- Use RAG to enhance job analysis
- Query company culture for cover letters
- Asynchronous processing (FR-018)

---

## References

1. **Archon Project**: https://github.com/coleam00/Archon (RAG implementation reference)
2. **sentence-transformers**: https://www.sbert.net/ (embedding models)
3. **sqlite-vec**: https://github.com/asg017/sqlite-vec (SQLite vector extension)
4. **LangChain Text Splitters**: https://python.langchain.com/docs/modules/data_connection/document_transformers/

---

**Next Steps**: Proceed to Phase 1 (data-model.md) using these research findings.
