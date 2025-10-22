# Data Model: Website RAG Pipeline

**Feature**: 004-website-rag-pipeline
**Date**: 2025-10-22
**Status**: Phase 1 Design

## Overview

This document defines the data entities, schemas, and relationships for the Website RAG Pipeline feature. All schemas use Pydantic for type safety and validation (Constitution Principle VII).

---

## Entity Relationship Diagram

```
┌──────────────────┐
│ WebsiteSource    │
│ ─────────────────│        1        N ┌──────────────────┐
│ id (PK)          │◄────────────────────│ WebsiteChunk     │
│ url (UNIQUE)     │                     │ ─────────────────│
│ title            │                     │ id (PK)          │
│ content_type     │                     │ source_id (FK)   │
│ language         │                     │ chunk_index      │
│ raw_html         │                     │ content          │
│ metadata_json    │                     │ char_count       │
│ fetch_timestamp  │                     │ metadata_json    │
│ status           │                     │ created_at       │
│ error_message    │                     └──────────────────┘
└──────────────────┘                              │
                                                  │ 1:1
                                     ┌────────────▼──────────┐
                                     │ WebsiteChunkVec       │
                                     │ (Virtual Table)       │
                                     │ ─────────────────────│
                                     │ chunk_id (PK)         │
                                     │ embedding FLOAT[384]  │
                                     └───────────────────────┘
                                                  │
                                                  │ 1:1
                                     ┌────────────▼──────────┐
                                     │ WebsiteChunkFTS       │
                                     │ (FTS5 Virtual Table)  │
                                     │ ─────────────────────│
                                     │ chunk_id              │
                                     │ content               │
                                     └───────────────────────┘
```

---

## Entity 1: WebsiteSource

**Purpose**: Represents a processed website (job posting, blog article, company page).

### Pydantic Schema

```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Literal, Optional
from datetime import datetime

class WebsiteSource(BaseModel):
    """
    A website that has been fetched and is ready for processing.

    Follows Constitution Principle II (Data Access Layer):
    - All fields validated via Pydantic
    - Accessed through data-access-agent only
    """

    id: Optional[int] = Field(None, description="Auto-generated primary key")
    url: HttpUrl = Field(..., description="Original URL of the website")
    title: Optional[str] = Field(None, max_length=500, description="Page title")

    content_type: Literal["job_posting", "blog_article", "company_page"] = Field(
        ...,
        description="Type of content for specialized processing"
    )

    language: Literal["en", "ja", "mixed"] = Field(
        ...,
        description="Detected language (en=English, ja=Japanese, mixed=bilingual)"
    )

    raw_html: str = Field(..., description="Full HTML content for re-processing")

    metadata_json: Optional[str] = Field(
        None,
        description="JSON-encoded metadata: {description, author, published_date, extracted_entities, ...}"
    )

    fetch_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the website was fetched"
    )

    processing_status: Literal["pending", "processing", "completed", "failed"] = Field(
        default="pending",
        description="Current processing status (FR-019: status tracking)"
    )

    error_message: Optional[str] = Field(
        None,
        description="Error details if processing_status='failed'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "url": "https://japan-dev.com/jobs/acme-corp/senior-backend-engineer",
                "title": "Senior Backend Engineer - Acme Corp",
                "content_type": "job_posting",
                "language": "en",
                "raw_html": "<html>...</html>",
                "metadata_json": '{"company": "Acme Corp", "location": "Tokyo", "salary": "8M-12M JPY"}',
                "fetch_timestamp": "2025-10-22T10:30:00Z",
                "processing_status": "completed",
                "error_message": None
            }
        }
```

### SQLite Table Schema

```sql
CREATE TABLE website_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content_type TEXT NOT NULL CHECK(content_type IN ('job_posting', 'blog_article', 'company_page')),
    language TEXT NOT NULL CHECK(language IN ('en', 'ja', 'mixed')),
    raw_html TEXT NOT NULL,
    metadata_json TEXT,
    fetch_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    processing_status TEXT DEFAULT 'pending' CHECK(processing_status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT
);

-- Indexes for performance
CREATE INDEX idx_website_sources_url ON website_sources(url);
CREATE INDEX idx_website_sources_status ON website_sources(processing_status);
CREATE INDEX idx_website_sources_content_type ON website_sources(content_type);
```

### Validation Rules
- **url**: Must be valid HTTP/HTTPS URL (Pydantic HttpUrl validation)
- **content_type**: Enum constraint (job_posting | blog_article | company_page)
- **language**: Enum constraint (en | ja | mixed)
- **processing_status**: Enum constraint (pending | processing | completed | failed)
- **raw_html**: Required (min length 100 characters to avoid empty pages)

### State Transitions
```
pending → processing → completed
                    └→ failed
```

**Rules:**
- Can only transition from `pending` to `processing`
- Can only transition from `processing` to `completed` or `failed`
- If `failed`, `error_message` must be set

---

## Entity 2: WebsiteChunk

**Purpose**: Represents a semantically meaningful segment of a processed website, optimized for retrieval.

### Pydantic Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class WebsiteChunk(BaseModel):
    """
    A chunk of text extracted from a website, with metadata for retrieval.

    Follows Constitution Principle II (Data Access Layer):
    - All fields validated via Pydantic
    - Accessed through data-access-agent only
    """

    id: Optional[int] = Field(None, description="Auto-generated primary key")
    source_id: int = Field(..., description="Foreign key to website_sources.id")
    chunk_index: int = Field(..., ge=0, description="Sequential index within source (0-based)")

    content: str = Field(
        ...,
        min_length=50,
        max_length=5000,
        description="The actual text content of this chunk"
    )

    char_count: int = Field(..., ge=50, le=5000, description="Character count (for validation)")

    metadata_json: Optional[str] = Field(
        None,
        description="JSON-encoded metadata: {headers, section, split_method, ...}"
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When this chunk was created"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "source_id": 1,
                "chunk_index": 0,
                "content": "We are looking for a Senior Backend Engineer with 5+ years of experience in Python, FastAPI, and PostgreSQL...",
                "char_count": 142,
                "metadata_json": '{"Header 2": "Job Requirements", "Header 3": "Technical Skills", "split_method": "html_only"}',
                "created_at": "2025-10-22T10:31:00Z"
            }
        }
```

### SQLite Table Schema

```sql
CREATE TABLE website_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES website_sources(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL CHECK(LENGTH(content) >= 50 AND LENGTH(content) <= 5000),
    char_count INTEGER NOT NULL CHECK(char_count >= 50 AND char_count <= 5000),
    metadata_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(source_id, chunk_index)  -- Ensure sequential chunks
);

-- Indexes
CREATE INDEX idx_website_chunks_source_id ON website_chunks(source_id);
CREATE INDEX idx_website_chunks_char_count ON website_chunks(char_count);

-- Vector table (sqlite-vec extension)
CREATE VIRTUAL TABLE website_chunks_vec USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding FLOAT[384]  -- 384-dim from paraphrase-multilingual-MiniLM-L12-v2
);

-- Full-text search table (FTS5)
CREATE VIRTUAL TABLE website_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    content,
    tokenize='porter unicode61'  -- Porter stemming + Unicode support (handles Japanese)
);
```

### Validation Rules
- **content**: Min 50 chars, max 5000 chars (prevents too-small or too-large chunks)
- **char_count**: Must match actual `len(content)` (enforced by Pydantic validator)
- **chunk_index**: Must be unique within source_id
- **source_id**: Must reference valid `website_sources.id` (foreign key constraint)

### Metadata JSON Structure

```typescript
interface ChunkMetadata {
    // From HTMLHeaderTextSplitter
    "Header 1"?: string;  // e.g., "Job Posting"
    "Header 2"?: string;  // e.g., "Requirements"
    "Header 3"?: string;  // e.g., "Technical Skills"

    // Processing metadata
    split_method: "html_only" | "html+recursive" | "recursive_only";

    // Optional extracted entities
    extracted_entities?: {
        company_name?: string;
        role_title?: string;
        location?: string;
        salary?: string;
        skills?: string[];
    };
}
```

---

## Entity 3: QueryResult

**Purpose**: Represents the response to a semantic query, with ranked results and source citations.

### Pydantic Schema

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ChunkResult(BaseModel):
    """A single chunk result with relevance score."""

    chunk_id: int = Field(..., description="ID of the matching chunk")
    source_id: int = Field(..., description="ID of the source website")
    source_url: str = Field(..., description="Original URL for citation")
    content: str = Field(..., description="Chunk content")

    vector_score: float = Field(..., ge=0, le=1, description="Vector similarity score (0=identical, 1=dissimilar)")
    fts_score: Optional[float] = Field(None, ge=0, description="FTS rank score (lower=better)")
    combined_score: float = Field(..., ge=0, description="Hybrid score (vector * 0.7 + fts * 0.3)")

    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata (headers, entities)")


class QueryResult(BaseModel):
    """
    Response to a semantic query across processed websites.

    Follows FR-006: Must preserve source citations.
    Follows SC-008: Source citations 100% of the time.
    """

    query: str = Field(..., description="Original user query")

    results: List[ChunkResult] = Field(
        ...,
        max_items=20,
        description="Ranked list of matching chunks (max 20)"
    )

    total_results: int = Field(..., ge=0, description="Total number of matches found")

    synthesis: Optional[str] = Field(
        None,
        description="AI-generated summary synthesizing the results (optional)"
    )

    confidence_level: Literal["high", "medium", "low"] = Field(
        ...,
        description="Confidence in result quality (based on top score)"
    )

    processing_time_ms: int = Field(..., ge=0, description="Query processing time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the key requirements for backend engineer roles in Tokyo?",
                "results": [
                    {
                        "chunk_id": 42,
                        "source_id": 5,
                        "source_url": "https://japan-dev.com/jobs/acme/backend-engineer",
                        "content": "5+ years Python, FastAPI, PostgreSQL...",
                        "vector_score": 0.23,
                        "fts_score": 1.2,
                        "combined_score": 0.52,
                        "metadata": {"Header 2": "Requirements"}
                    }
                ],
                "total_results": 12,
                "synthesis": "Backend engineer roles in Tokyo typically require 5+ years of Python experience...",
                "confidence_level": "high",
                "processing_time_ms": 287
            }
        }
```

---

## Entity 4: ExtractionMetadata

**Purpose**: Structured information extracted from job postings and articles.

### Pydantic Schema

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class JobPostingMetadata(BaseModel):
    """Metadata extracted from job postings (FR-009)."""

    company_name: Optional[str] = Field(None, max_length=200)
    role_title: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    salary_range: Optional[str] = Field(None, max_length=100)

    requirements: List[str] = Field(
        default_factory=list,
        max_items=50,
        description="List of job requirements"
    )

    skills_needed: List[str] = Field(
        default_factory=list,
        max_items=100,
        description="Technical skills mentioned"
    )

    benefits: List[str] = Field(
        default_factory=list,
        max_items=30,
        description="Company benefits"
    )


class BlogArticleMetadata(BaseModel):
    """Metadata extracted from career advice blogs (FR-010)."""

    main_topics: List[str] = Field(
        default_factory=list,
        max_items=10,
        description="Main topics covered"
    )

    key_insights: List[str] = Field(
        default_factory=list,
        max_items=20,
        description="Actionable insights"
    )

    actionable_tips: List[str] = Field(
        default_factory=list,
        max_items=30,
        description="Concrete tips for job seekers"
    )

    target_audience: Optional[str] = Field(None, max_length=200)
    author: Optional[str] = Field(None, max_length=100)
    published_date: Optional[str] = Field(None)


class ExtractionMetadata(BaseModel):
    """
    Wrapper for content-type-specific metadata.
    Stored as JSON in website_sources.metadata_json.
    """

    content_type: Literal["job_posting", "blog_article", "company_page"]

    job_posting: Optional[JobPostingMetadata] = None
    blog_article: Optional[BlogArticleMetadata] = None

    # Generic metadata (applies to all types)
    description: Optional[str] = Field(None, max_length=1000)
    language: Literal["en", "ja", "mixed"] = Field(...)
```

---

## Database Indexes for Performance

### Required Indexes (Constitution Principle VI: Performance Standards)

```sql
-- website_sources
CREATE INDEX idx_ws_url ON website_sources(url);                    -- URL lookups
CREATE INDEX idx_ws_status ON website_sources(processing_status);   -- Filter by status
CREATE INDEX idx_ws_content_type ON website_sources(content_type);  -- Filter by type
CREATE INDEX idx_ws_fetch_time ON website_sources(fetch_timestamp); -- Staleness queries

-- website_chunks
CREATE INDEX idx_wc_source_id ON website_chunks(source_id);         -- Join to sources
CREATE INDEX idx_wc_char_count ON website_chunks(char_count);       -- Filter by size

-- UNIQUE constraint for data integrity
CREATE UNIQUE INDEX idx_wc_source_chunk ON website_chunks(source_id, chunk_index);
```

### Query Performance Targets

| Query Type | Target | Expected | Index Used |
|------------|--------|----------|------------|
| URL lookup | <10ms | <5ms | idx_ws_url (UNIQUE) |
| Chunks by source | <50ms | <20ms | idx_wc_source_id + FK |
| Vector search | <100ms | <50ms | sqlite-vec SIMD |
| FTS search | <100ms | <50ms | FTS5 index |
| Hybrid search | <200ms | <150ms | Combined above |

---

## Data Validation & Integrity Rules

### Constitution Principle VII: Type Safety & Validation

**All data must pass validation before persistence:**

1. **Pre-Write Validation** (via Pydantic):
   - Field types must match schema
   - String lengths within bounds
   - Enums must be valid values
   - Required fields must be present

2. **Database Constraints**:
   - Foreign keys enforced (ON DELETE CASCADE)
   - UNIQUE constraints on (url), (source_id, chunk_index)
   - CHECK constraints on enums and lengths

3. **Post-Read Validation** (via Pydantic):
   - All reads from database must pass schema validation
   - Invalid data triggers error (prevents silent corruption)

### Example Validation Workflow

```python
from pydantic import ValidationError

# Write path
def create_website_source(data: dict) -> WebsiteSource:
    try:
        source = WebsiteSource(**data)  # Pydantic validation
        # If valid, proceed to database
        db.execute("INSERT INTO website_sources (...) VALUES (...)", source.dict())
        return source
    except ValidationError as e:
        raise ValueError(f"Invalid website source data: {e}")

# Read path
def get_website_source(source_id: int) -> WebsiteSource:
    row = db.execute("SELECT * FROM website_sources WHERE id = ?", (source_id,)).fetchone()
    try:
        return WebsiteSource(**row)  # Re-validate on read
    except ValidationError as e:
        raise DataCorruptionError(f"Database contains invalid data: {e}")
```

---

## Data Access Patterns

### Pattern 1: Process New Website (FR-001, FR-007)

```
1. User provides URL
2. Validate URL (Pydantic HttpUrl)
3. Check if URL already exists (cache check - FR-004)
   - If exists: return cached WebsiteSource
   - If new: continue
4. Fetch HTML with Playwright
5. Create WebsiteSource (status='processing')
6. Chunk HTML → List[WebsiteChunk]
7. Generate embeddings → List[embedding vectors]
8. Store chunks + vectors + FTS entries
9. Update WebsiteSource (status='completed')
```

### Pattern 2: Semantic Query (FR-003, FR-008)

```
1. User asks natural language question
2. Generate query embedding
3. Perform hybrid search:
   a. Vector similarity (sqlite-vec)
   b. FTS keyword search (FTS5)
   c. Combine scores (70% vector + 30% FTS)
4. Retrieve top 10 chunks
5. Build QueryResult with citations
6. Return to user
```

### Pattern 3: Refresh Stale Content (FR-013, FR-017)

```
1. User requests refresh of URL
2. Check fetch_timestamp (if < 30 days, warn user)
3. Update status='processing'
4. Delete old chunks (CASCADE deletes vectors/FTS entries)
5. Re-fetch HTML
6. Re-chunk and re-embed
7. Update status='completed'
```

---

## Migration Strategy

### Phase 1: Initial Schema (v1.0)
- Tables: `website_sources`, `website_chunks`
- Virtual tables: `website_chunks_vec`, `website_chunks_fts`
- Basic indexes

### Phase 2: Metadata Enhancement (v1.1)
- Add `metadata_json` parsing
- Populate `JobPostingMetadata`, `BlogArticleMetadata`
- Add entity extraction

### Phase 3: Advanced Features (v2.0)
- Add reranking scores
- Add user feedback (thumbs up/down on results)
- Add query history

---

## Related Files

- **Pydantic schemas**: `apps/resume-agent/resume_agent.py` (extend existing schemas)
- **Database migrations**: `apps/resume-agent/migrations/` (TBD)
- **Data access agent**: `apps/resume-agent/.claude/agents/data-access-agent.md` (update with new MCP tools)

---

**Next Steps**: Proceed to API contracts (MCP tools specification).
