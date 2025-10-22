# MCP Tools Contract: Website RAG Pipeline

**Feature**: 004-website-rag-pipeline
**Date**: 2025-10-22
**Status**: Phase 1 Design

## Overview

This document specifies the MCP (Model Context Protocol) tools interface for the Website RAG Pipeline. All tools follow FastMCP conventions and integrate with the existing Resume Agent MCP server.

**Server**: `apps/resume-agent/resume_agent.py` (extended)
**Transport**: HTTP Streamable (port 8080)
**Framework**: FastMCP 2.0

---

## Tool 1: `rag_process_website`

### Purpose
Process a website URL into the RAG pipeline (fetch, chunk, embed, store).

### Functional Requirements
- FR-001: Extract text content from URL
- FR-002: Parse and structure into queryable chunks
- FR-004: Cache processed content
- FR-005: Handle English and Japanese text
- FR-018: Support asynchronous processing
- FR-019: Provide status tracking

### Contract

```python
@mcp.tool()
async def rag_process_website(
    url: str,
    content_type: Literal["job_posting", "blog_article", "company_page"] = "job_posting",
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Process a website URL into the RAG pipeline.

    This tool fetches the website, extracts content, chunks it semantically,
    generates vector embeddings, and stores everything for semantic search.

    Args:
        url: Website URL to process (must be valid HTTP/HTTPS)
        content_type: Type of content for specialized processing
            - "job_posting": Job board pages (extract company, role, requirements)
            - "blog_article": Career advice blogs (extract insights, tips)
            - "company_page": Company info pages (extract culture, values)
        force_refresh: If True, re-process even if URL is cached (default: False)

    Returns:
        {
            "source_id": int,              # Database ID of processed website
            "url": str,                    # Original URL
            "status": str,                 # "processing" | "completed" | "failed"
            "chunks_created": int,         # Number of chunks generated
            "processing_time_ms": int,     # Total processing time
            "language": str,               # Detected language ("en" | "ja" | "mixed")
            "message": str,                # Human-readable status message
            "is_cached": bool,             # True if returned from cache
            "error": Optional[str]         # Error message if status="failed"
        }

    Raises:
        ValueError: If URL is invalid or inaccessible
        ProcessingError: If chunking or embedding fails

    Examples:
        # Process a job posting
        result = await rag_process_website(
            url="https://japan-dev.com/jobs/acme/backend-engineer",
            content_type="job_posting"
        )
        # Returns: {"source_id": 42, "status": "completed", "chunks_created": 8, ...}

        # Process a blog article
        result = await rag_process_website(
            url="https://blog.gaijinpot.com/getting-tech-job-japan/",
            content_type="blog_article"
        )

        # Force refresh of cached URL
        result = await rag_process_website(
            url="https://japan-dev.com/jobs/acme/backend-engineer",
            force_refresh=True
        )
    """
```

### Implementation Notes

**Async Processing (FR-018):**
- For URLs that will take >5s to process, return immediately with `status="processing"`
- Process in background task
- User can poll status with `rag_get_website_status(source_id)`
- Emit observability events: `WebsiteProcessingStart`, `WebsiteProcessingComplete`, `WebsiteProcessingFailed`

**Caching (FR-004):**
- Check if URL exists in `website_sources` table
- If exists and `force_refresh=False`, return cached `source_id` with `is_cached=True`
- If exists and `force_refresh=True`, delete old chunks and re-process

**Error Handling (FR-015):**
- Invalid URL → Immediate error with suggestion: "Please provide a valid HTTP/HTTPS URL"
- Inaccessible URL (404, timeout) → Error with actionable feedback
- Partial processing failure → Store what succeeded, mark status="failed", provide error details

### Performance Targets (SC-001, Constitution VI)
- Job posting: <15s total (async processing recommended)
- Blog article: <20s total (async processing recommended)
- Cached result: <1s (SC-004)

---

## Tool 2: `rag_query_websites`

### Purpose
Perform semantic search across all processed websites.

### Functional Requirements
- FR-003: Semantic search across processed content
- FR-006: Preserve source citations
- FR-008: Natural language queries
- SC-003: 85%+ relevant results

### Contract

```python
@mcp.tool()
async def rag_query_websites(
    query: str,
    max_results: int = 10,
    content_type_filter: Optional[Literal["job_posting", "blog_article", "company_page"]] = None,
    source_ids: Optional[List[int]] = None,
    include_synthesis: bool = False
) -> Dict[str, Any]:
    """
    Query processed websites using semantic search.

    Performs hybrid search (vector similarity + full-text keyword matching) to find
    relevant chunks. Returns ranked results with source citations.

    Args:
        query: Natural language question (e.g., "What are key requirements for backend roles in Tokyo?")
        max_results: Maximum number of results to return (default: 10, max: 20)
        content_type_filter: Optionally filter by content type
        source_ids: Optionally limit search to specific source IDs
        include_synthesis: If True, generate AI summary of results (slower)

    Returns:
        {
            "query": str,                  # Original query
            "results": [                   # Ranked results
                {
                    "chunk_id": int,
                    "source_id": int,
                    "source_url": str,
                    "content": str,
                    "vector_score": float,     # 0=similar, 1=dissimilar
                    "fts_score": Optional[float],  # Lower=better
                    "combined_score": float,
                    "metadata": {
                        "Header 2": str,
                        "Header 3": str,
                        ...
                    }
                },
                ...
            ],
            "total_results": int,          # Total matches found
            "synthesis": Optional[str],    # AI-generated summary (if include_synthesis=True)
            "confidence_level": str,       # "high" | "medium" | "low"
            "processing_time_ms": int
        }

    Raises:
        ValueError: If query is empty or max_results out of range

    Examples:
        # Basic semantic search
        result = await rag_query_websites(
            query="What are the main requirements for backend engineer roles?"
        )
        # Returns top 10 relevant chunks with citations

        # Filter by content type
        result = await rag_query_websites(
            query="Tips for interviewing at Japanese companies",
            content_type_filter="blog_article"
        )

        # Search specific sources
        result = await rag_query_websites(
            query="Company culture and values",
            source_ids=[42, 43, 44],  # Only search these 3 sources
            include_synthesis=True     # Get AI summary
        )
    """
```

### Implementation Notes

**Hybrid Search Strategy:**
1. Generate query embedding (sentence-transformers)
2. Vector similarity search (sqlite-vec) → top 20
3. FTS keyword search (FTS5) → top 20
4. Combine scores: `combined = (vector_score * 0.7) + (fts_score * 0.3)`
5. Return top `max_results`

**Source Citations (FR-006, SC-008):**
- Every result MUST include `source_url` for traceability
- Metadata includes header context for precise citation
- Example: "Source: https://company.com/careers (Section: 'Requirements > Technical Skills')"

**Confidence Level:**
- `high`: Top result score < 0.3 (very similar)
- `medium`: Top result score 0.3-0.6
- `low`: Top result score > 0.6 (weak match, may need query refinement)

**Synthesis (Optional):**
- If `include_synthesis=True`, send top 5 results to Claude with prompt:
  ```
  User query: {query}

  Relevant excerpts from processed websites:
  {top 5 chunks with citations}

  Synthesize a comprehensive answer with source citations.
  ```

### Performance Targets (Constitution VI)
- Query processing: <3s (FR requirement, SC query target)
- Vector search: <100ms
- FTS search: <100ms
- Synthesis (if enabled): +2-5s (acceptable for opt-in feature)

---

## Tool 3: `rag_list_websites`

### Purpose
List all processed websites with filtering and sorting.

### Functional Requirements
- FR-012: List processed content with filtering
- FR-017: Detect stale content

### Contract

```python
@mcp.tool()
async def rag_list_websites(
    content_type: Optional[Literal["job_posting", "blog_article", "company_page"]] = None,
    status: Optional[Literal["pending", "processing", "completed", "failed"]] = None,
    limit: int = 50,
    offset: int = 0,
    order_by: Literal["fetch_timestamp", "url", "status"] = "fetch_timestamp",
    order: Literal["ASC", "DESC"] = "DESC"
) -> Dict[str, Any]:
    """
    List all processed websites with filtering and pagination.

    Args:
        content_type: Filter by content type (optional)
        status: Filter by processing status (optional)
        limit: Maximum results per page (default: 50, max: 100)
        offset: Pagination offset (default: 0)
        order_by: Sort field ("fetch_timestamp" | "url" | "status")
        order: Sort order ("ASC" | "DESC")

    Returns:
        {
            "websites": [
                {
                    "id": int,
                    "url": str,
                    "title": str,
                    "content_type": str,
                    "language": str,
                    "fetch_timestamp": str,  # ISO 8601
                    "processing_status": str,
                    "chunks_count": int,
                    "is_stale": bool,        # True if >30 days old
                    "error_message": Optional[str]
                },
                ...
            ],
            "total_count": int,
            "limit": int,
            "offset": int,
            "has_more": bool
        }

    Examples:
        # List all job postings
        result = await rag_list_websites(content_type="job_posting")

        # List failed processing attempts
        result = await rag_list_websites(status="failed")

        # Paginate through all websites
        page1 = await rag_list_websites(limit=20, offset=0)
        page2 = await rag_list_websites(limit=20, offset=20)
    """
```

### Implementation Notes

**Staleness Detection (FR-017):**
- Calculate `is_stale = (now - fetch_timestamp) > 30 days`
- Include in response for user awareness
- User can use `rag_refresh_website()` to update

**Pagination:**
- Use LIMIT/OFFSET for pagination
- Include `has_more` flag for UI convenience

---

## Tool 4: `rag_refresh_website`

### Purpose
Refresh a previously processed website.

### Functional Requirements
- FR-013: Refresh processed content
- FR-017: Detect and update stale content

### Contract

```python
@mcp.tool()
async def rag_refresh_website(
    source_id: int
) -> Dict[str, Any]:
    """
    Refresh a previously processed website.

    Deletes old chunks and re-processes the website. Useful for updating stale content
    or fixing processing errors.

    Args:
        source_id: Database ID of the website to refresh

    Returns:
        {
            "source_id": int,
            "url": str,
            "old_chunks_deleted": int,
            "new_chunks_created": int,
            "status": str,  # "completed" | "failed"
            "processing_time_ms": int,
            "message": str
        }

    Raises:
        NotFoundError: If source_id doesn't exist
        ProcessingError: If refresh fails

    Examples:
        result = await rag_refresh_website(source_id=42)
        # Returns: {"source_id": 42, "old_chunks_deleted": 8, "new_chunks_created": 10, ...}
    """
```

---

## Tool 5: `rag_delete_website`

### Purpose
Delete a processed website and all associated chunks.

### Functional Requirements
- FR-013: Delete processed content

### Contract

```python
@mcp.tool()
async def rag_delete_website(
    source_id: int
) -> Dict[str, Any]:
    """
    Delete a processed website and all associated data.

    Deletes the website source, all chunks, embeddings, and FTS entries.
    This action is IRREVERSIBLE.

    Args:
        source_id: Database ID of the website to delete

    Returns:
        {
            "source_id": int,
            "url": str,
            "chunks_deleted": int,
            "message": str
        }

    Raises:
        NotFoundError: If source_id doesn't exist

    Examples:
        result = await rag_delete_website(source_id=42)
        # Returns: {"source_id": 42, "url": "...", "chunks_deleted": 8, "message": "Deleted successfully"}
    """
```

### Implementation Notes

**Cascading Deletes:**
- SQLite foreign key constraint: `ON DELETE CASCADE`
- Deleting from `website_sources` automatically deletes:
  - All `website_chunks` rows with matching `source_id`
  - All `website_chunks_vec` entries (via chunk_id)
  - All `website_chunks_fts` entries (via chunk_id)

---

## Tool 6: `rag_get_website_status`

### Purpose
Get processing status for a website (supports async processing).

### Functional Requirements
- FR-019: Status tracking for in-progress processing

### Contract

```python
@mcp.tool()
async def rag_get_website_status(
    source_id: int
) -> Dict[str, Any]:
    """
    Get current processing status of a website.

    Useful for polling async processing operations started by rag_process_website().

    Args:
        source_id: Database ID of the website

    Returns:
        {
            "source_id": int,
            "url": str,
            "processing_status": str,  # "pending" | "processing" | "completed" | "failed"
            "chunks_created": int,
            "fetch_timestamp": str,
            "error_message": Optional[str],
            "message": str
        }

    Raises:
        NotFoundError: If source_id doesn't exist

    Examples:
        # Start async processing
        process_result = await rag_process_website(url="...")
        source_id = process_result["source_id"]

        # Poll status
        while True:
            status = await rag_get_website_status(source_id)
            if status["processing_status"] in ["completed", "failed"]:
                break
            await asyncio.sleep(2)  # Wait 2 seconds
    """
```

---

## Data Access Layer Integration

### Existing Data-Access-Agent Extension

Update `apps/resume-agent/.claude/agents/data-access-agent.md` with:

```markdown
## RAG Pipeline Data Access

### MCP Tools (via resume_agent.py)

**Write Operations:**
- `data_create_website_source(url, content_type, ...) -> WebsiteSource`
- `data_create_website_chunks(source_id, chunks: List[dict]) -> int`
- `data_update_website_status(source_id, status, error_message) -> None`
- `data_delete_website_source(source_id) -> None`

**Read Operations:**
- `data_read_website_source(source_id) -> WebsiteSource`
- `data_read_website_chunks(source_id) -> List[WebsiteChunk]`
- `data_list_website_sources(filters, limit, offset) -> List[WebsiteSource]`
- `data_query_chunks_hybrid(query_embedding, query_text, max_results) -> List[ChunkResult]`

All data operations validate against Pydantic schemas (Constitution Principle VII).
```

---

## Observability Events

### Event Emissions (Constitution Principle IV)

All RAG tools emit structured events via existing observability hooks:

```python
# Before processing
emit_event("WebsiteProcessingStart", {
    "source_app": "resume-agent",
    "tool_name": "rag_process_website",
    "url": url,
    "content_type": content_type,
    "timestamp": datetime.now().isoformat()
})

# After processing
emit_event("WebsiteProcessingComplete", {
    "source_app": "resume-agent",
    "tool_name": "rag_process_website",
    "source_id": source_id,
    "chunks_created": chunks_count,
    "processing_time_ms": elapsed_ms,
    "timestamp": datetime.now().isoformat()
})

# On failure
emit_event("WebsiteProcessingFailed", {
    "source_app": "resume-agent",
    "tool_name": "rag_process_website",
    "url": url,
    "error": str(error),
    "timestamp": datetime.now().isoformat()
})

# Query events
emit_event("SemanticQueryStart", {
    "source_app": "resume-agent",
    "query": query,
    "filters": {...}
})

emit_event("SemanticQueryComplete", {
    "source_app": "resume-agent",
    "results_count": len(results),
    "processing_time_ms": elapsed_ms
})
```

---

## Contract Tests (Constitution Principle III)

### Test Suite Location
`apps/resume-agent/tests/contract/test_rag_mcp_tools.py`

### Test Cases

```python
import pytest
from apps.resume_agent import resume_agent

class TestRAGProcessWebsite:
    """Contract tests for rag_process_website tool."""

    async def test_process_valid_job_posting(self):
        """Should process a valid job posting URL."""
        result = await resume_agent.rag_process_website(
            url="https://japan-dev.com/jobs/test-company/backend-engineer",
            content_type="job_posting"
        )

        assert result["status"] in ["completed", "processing"]
        assert result["chunks_created"] >= 0
        assert result["language"] in ["en", "ja", "mixed"]

    async def test_process_cached_url(self):
        """Should return cached result for previously processed URL."""
        url = "https://japan-dev.com/jobs/test-company/backend-engineer"

        # First call
        result1 = await resume_agent.rag_process_website(url=url)
        source_id1 = result1["source_id"]

        # Second call (should be cached)
        result2 = await resume_agent.rag_process_website(url=url)

        assert result2["is_cached"] is True
        assert result2["source_id"] == source_id1

    async def test_force_refresh(self):
        """Should re-process when force_refresh=True."""
        url = "https://japan-dev.com/jobs/test-company/backend-engineer"

        result1 = await resume_agent.rag_process_website(url=url)
        result2 = await resume_agent.rag_process_website(url=url, force_refresh=True)

        assert result2["is_cached"] is False

    async def test_invalid_url_error(self):
        """Should raise ValueError for invalid URL."""
        with pytest.raises(ValueError, match="valid HTTP/HTTPS URL"):
            await resume_agent.rag_process_website(url="not-a-url")


class TestRAGQueryWebsites:
    """Contract tests for rag_query_websites tool."""

    async def test_semantic_query_returns_results(self):
        """Should return ranked results for semantic query."""
        result = await resume_agent.rag_query_websites(
            query="What are backend engineer requirements?"
        )

        assert "results" in result
        assert isinstance(result["results"], list)
        assert result["total_results"] >= 0
        assert result["confidence_level"] in ["high", "medium", "low"]

    async def test_all_results_have_citations(self):
        """Should include source_url in every result (SC-008)."""
        result = await resume_agent.rag_query_websites(
            query="Company culture"
        )

        for chunk_result in result["results"]:
            assert "source_url" in chunk_result
            assert chunk_result["source_url"].startswith("http")

    async def test_content_type_filter(self):
        """Should filter results by content_type."""
        result = await resume_agent.rag_query_websites(
            query="interview tips",
            content_type_filter="blog_article"
        )

        # All results should be from blog articles
        # (Verify by checking source metadata)

    async def test_max_results_respected(self):
        """Should respect max_results parameter."""
        result = await resume_agent.rag_query_websites(
            query="job requirements",
            max_results=5
        )

        assert len(result["results"]) <= 5


# Additional test classes for other tools...
```

---

## Performance Requirements Summary

| Tool | Target | Metric |
|------|--------|--------|
| `rag_process_website` (job posting) | <15s | Total processing time |
| `rag_process_website` (cached) | <1s | Cache lookup + return |
| `rag_query_websites` | <3s | Query + rank + return |
| `rag_list_websites` | <500ms | Database query + format |
| `rag_refresh_website` | <15s | Delete + re-process |
| `rag_delete_website` | <100ms | Cascading delete |
| `rag_get_website_status` | <50ms | Single row lookup |

---

## Error Handling Standards

### Error Types

```python
class RAGError(Exception):
    """Base exception for RAG pipeline errors."""

class URLFetchError(RAGError):
    """Failed to fetch URL (404, timeout, connection error)."""

class ChunkingError(RAGError):
    """Failed to chunk content."""

class EmbeddingError(RAGError):
    """Failed to generate embeddings."""

class DataValidationError(RAGError):
    """Pydantic validation failed."""
```

### Error Response Format

```python
{
    "error": {
        "type": "URLFetchError",
        "message": "Failed to fetch URL: Connection timeout after 30s",
        "details": {
            "url": "https://slow-website.com/jobs/123",
            "status_code": None,
            "timeout_seconds": 30
        },
        "suggestion": "Check if the URL is accessible and try again. If the site is slow, consider processing it asynchronously."
    }
}
```

---

## Next Steps

1. **Implement MCP tools** in `apps/resume-agent/resume_agent.py`
2. **Write contract tests** in `apps/resume-agent/tests/contract/test_rag_mcp_tools.py`
3. **Update data-access-agent** with new data operations
4. **Create slash commands** for user-facing workflow

**Related Files:**
- Pydantic schemas: `apps/resume-agent/resume_agent.py`
- Data model: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\data-model.md`
- Research: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\research.md`
