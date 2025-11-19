# Fetch-Docs Improvement Tasks

Based on research into Archon's documentation retrieval system, this document outlines tasks for enhancing our fetch-docs process with semantic search, smart chunking, and RAG capabilities.

## Research Source
- **Research Report**: Generated 2025-01-17
- **Reference System**: [Archon](https://github.com/coleam00/Archon) - Production-grade RAG system
- **Current System**: Context7 MCP + flat markdown storage in `ai_docs/`

---

## Priority 1: Add Semantic Search (Immediate Value)

### 1.1 Choose and Integrate Embedding Model
- [ ] Evaluate embedding models:
  - [ ] `all-MiniLM-L6-v2` (384D, lightweight, fast)
  - [ ] `text-embedding-3-small` (1536D, OpenAI, higher quality)
  - [ ] Decision criteria: cost, speed, accuracy trade-offs
- [ ] Install dependencies:
  - [ ] `sentence-transformers` (for local models)
  - [ ] `faiss-cpu` or `faiss-gpu` (for vector search)
  - [ ] `openai` (if using OpenAI embeddings)
- [ ] Create embedding service:
  - [ ] `apps/rag/embedding_service.py`
  - [ ] Support batch embedding generation
  - [ ] Add rate limiting for API-based models
  - [ ] Implement caching for duplicate texts

### 1.2 Implement Document Chunking
- [ ] Create chunking utility:
  - [ ] `apps/rag/utils/chunking.py`
  - [ ] Implement smart boundary detection (code blocks, headers, paragraphs)
  - [ ] Default chunk size: 3000 characters
  - [ ] Minimum boundary threshold: 30% of chunk_size
  - [ ] Consolidate small chunks (<200 chars)
- [ ] Process existing documentation:
  - [ ] Read all markdown files from `ai_docs/`
  - [ ] Apply smart chunking to each file
  - [ ] Preserve metadata (library, category, source file, section)

### 1.3 Build FAISS Index
- [ ] Create vector store:
  - [ ] `apps/rag/services/vector_store.py`
  - [ ] Initialize FAISS index (IndexFlatL2 or IndexIVFFlat)
  - [ ] Store chunk metadata alongside vectors
  - [ ] Implement save/load functionality for persistence
- [ ] Index existing documentation:
  - [ ] Generate embeddings for all chunks
  - [ ] Add to FAISS index with metadata
  - [ ] Save index to `data/ai_docs_index.faiss`
  - [ ] Save metadata to `data/ai_docs_chunks.json`

### 1.4 Create Search Interface
- [ ] Implement search function:
  - [ ] `apps/rag/services/doc_search_service.py`
  - [ ] `search_docs(query, category=None, limit=5)`
  - [ ] Return results with similarity scores
  - [ ] Format results with library, file, content preview
- [ ] Add CLI command:
  - [ ] `/search-docs <query> [--category=<cat>] [--limit=<n>]`
  - [ ] Display formatted results in terminal
  - [ ] Show similarity scores and source files
- [ ] Test search functionality:
  - [ ] Test with technical queries ("Next.js routing")
  - [ ] Test with code-related queries ("authentication middleware")
  - [ ] Verify category filtering works
  - [ ] Validate result relevance

---

## Priority 2: Implement Smart Chunking (Foundation)

### 2.1 Adopt Boundary-Aware Chunking
- [ ] Study Archon's implementation:
  - [ ] Review `base_storage_service.py:smart_chunk_text()`
  - [ ] Understand boundary detection hierarchy
  - [ ] Note edge cases and handling
- [ ] Implement chunking algorithm:
  - [ ] Priority 1: Code blocks (```)
  - [ ] Priority 2: Headers (##, ###)
  - [ ] Priority 3: Paragraphs (\n\n)
  - [ ] Priority 4: Sentences (". ")
  - [ ] Fallback: Force split at chunk_size
- [ ] Add unit tests:
  - [ ] Test code block preservation
  - [ ] Test header-based splitting
  - [ ] Test paragraph-based splitting
  - [ ] Test small chunk consolidation
  - [ ] Test edge cases (very short/long files)

### 2.2 Update Metadata Schema
- [ ] Extend `.meta.json` structure:
  ```json
  {
    "library_name": "Next.js",
    "context7_id": "/vercel/next.js",
    "category": "frameworks",
    "last_updated": "2025-10-23T14:30:00Z",
    "version": "latest",
    "chunks": {
      "total_chunks": 45,
      "chunk_size": 3000,
      "chunking_strategy": "boundary-aware",
      "chunked_at": "2025-10-23T14:30:00Z"
    },
    "fetches": [...]
  }
  ```
- [ ] Create chunk metadata file:
  - [ ] `ai_docs/{category}/{library}/chunks.json`
  - [ ] Store per-chunk metadata (index, source_file, section, hash)
  - [ ] Link chunks to parent documents

### 2.3 Process Existing Documentation
- [ ] Create migration script:
  - [ ] `scripts/migrate_docs_to_chunks.py`
  - [ ] Iterate through all libraries in `ai_docs/`
  - [ ] Apply smart chunking to each markdown file
  - [ ] Generate chunk metadata
  - [ ] Update `.meta.json` files
- [ ] Run migration:
  - [ ] Backup existing `ai_docs/` directory
  - [ ] Execute migration script
  - [ ] Verify chunk counts and metadata
  - [ ] Validate no content loss

### 2.4 Update fetch-docs Workflow
- [ ] Modify doc-fetcher skill:
  - [ ] After fetching docs, apply chunking
  - [ ] Generate chunk metadata
  - [ ] Update `.meta.json` with chunk info
  - [ ] Generate embeddings for chunks (if semantic search enabled)
- [ ] Update storage functions:
  - [ ] Save full document to README.md (unchanged)
  - [ ] Save chunks to `chunks.json`
  - [ ] Update FAISS index with new chunks

---

## Priority 3: Add Crawling for Custom Docs (Flexibility)

### 3.1 Integrate crawl4ai Library
- [ ] Install dependencies:
  - [ ] `uv add crawl4ai`
  - [ ] `uv add playwright`
  - [ ] Run `playwright install chromium`
- [ ] Create crawling service:
  - [ ] `apps/rag/services/crawling_service.py`
  - [ ] Implement basic crawl function
  - [ ] Add markdown extraction
  - [ ] Add error handling and retries

### 3.2 Implement Discovery Service
- [ ] Create discovery utility:
  - [ ] `apps/rag/services/discovery_service.py`
  - [ ] Detect `llms.txt` and `llms-full.txt`
  - [ ] Parse sitemap.xml files
  - [ ] Check robots.txt for sitemap directives
  - [ ] Search common locations (/docs/, /static/, /public/)
- [ ] Test discovery:
  - [ ] Test with documentation sites (Next.js, React, FastAPI)
  - [ ] Verify sitemap parsing
  - [ ] Verify llms.txt detection

### 3.3 Add Crawl Command
- [ ] Extend /fetch-docs command:
  - [ ] Add `--crawl` flag for web crawling mode
  - [ ] Add `--max-depth=<n>` parameter (default: 2)
  - [ ] Add `--extract-code` flag for code extraction
- [ ] Example usage:
  ```bash
  /fetch-docs https://docs.example.com --crawl --max-depth=3
  /fetch-docs https://internal-docs.company.com --crawl --extract-code
  ```
- [ ] Implement crawl workflow:
  - [ ] Discovery phase (detect sitemaps, llms.txt)
  - [ ] Crawling phase (recursive or sitemap-based)
  - [ ] Processing phase (chunking, metadata extraction)
  - [ ] Storage phase (save to ai_docs/, update index)

### 3.4 Maintain Hybrid Approach
- [ ] Document usage patterns:
  - [ ] Context7 for public libraries (zero maintenance)
  - [ ] Crawling for proprietary/custom docs
  - [ ] Both can coexist in `ai_docs/` structure
- [ ] Add source type to metadata:
  ```json
  {
    "source_type": "context7" | "crawled" | "uploaded",
    "source_url": "https://...",
    "crawl_config": {
      "max_depth": 3,
      "extract_code": true
    }
  }
  ```

---

## Priority 4: Build MCP Server (AI Integration)

### 4.1 Design MCP Tools
- [ ] Define tool specifications:
  - [ ] `search_docs(query, category, limit)` - Semantic search
  - [ ] `get_library_docs(library_name, topic)` - Direct retrieval
  - [ ] `list_available_docs()` - List all libraries
  - [ ] `get_code_examples(query, language)` - Code-specific search
- [ ] Create tool schemas:
  - [ ] Parameter types and validation
  - [ ] Return value structures
  - [ ] Error handling specifications

### 4.2 Implement MCP Server
- [ ] Create MCP server file:
  - [ ] `apps/fetch-docs-mcp/server.py`
  - [ ] Use FastMCP framework
  - [ ] Implement HTTP/SSE transport (port 8080)
- [ ] Implement tools:
  - [ ] `@mcp.tool() search_docs()`
  - [ ] `@mcp.tool() get_library_docs()`
  - [ ] `@mcp.tool() list_available_docs()`
  - [ ] `@mcp.tool() get_code_examples()`
- [ ] Add to project structure:
  ```
  apps/
    fetch-docs-mcp/
      server.py
      pyproject.toml
      README.md
  ```

### 4.3 Configure Claude Desktop Integration
- [ ] Update `.mcp.json`:
  ```json
  {
    "mcpServers": {
      "fetch-docs": {
        "command": "uv",
        "args": ["run", "apps/fetch-docs-mcp/server.py"],
        "transport": "http",
        "port": 8080
      }
    }
  }
  ```
- [ ] Test MCP connection:
  - [ ] Start MCP server
  - [ ] Verify Claude Code can connect
  - [ ] Test each tool individually

### 4.4 Test with AI Workflows
- [ ] Create test scenarios:
  - [ ] Search for authentication patterns
  - [ ] Retrieve Next.js routing documentation
  - [ ] Find React hooks examples
  - [ ] Get FastAPI middleware code
- [ ] Validate responses:
  - [ ] Check result relevance
  - [ ] Verify formatting
  - [ ] Test error handling
  - [ ] Measure response times

---

## Priority 5: Enhanced Refresh (Quality of Life)

### 5.1 Add Refresh Policies
- [ ] Extend `.meta.json` schema:
  ```json
  {
    "refresh_policy": {
      "type": "manual" | "periodic" | "on_version_change",
      "interval_days": 7,
      "last_check": "2025-10-23T14:30:00Z",
      "next_refresh": "2025-10-30T14:30:00Z",
      "auto_refresh": false
    }
  }
  ```
- [ ] Implement policy types:
  - [ ] `manual` - User-triggered only (current behavior)
  - [ ] `periodic` - Refresh every N days
  - [ ] `on_version_change` - Monitor version and refresh on change

### 5.2 Implement Staleness Detection
- [ ] Create staleness checker:
  - [ ] `apps/resume-agent/services/staleness_detector.py`
  - [ ] Check `last_updated` vs. `interval_days`
  - [ ] Calculate `next_refresh` date
  - [ ] Return list of stale libraries
- [ ] Add CLI command:
  - [ ] `/check-stale-docs`
  - [ ] Display libraries needing refresh
  - [ ] Show days since last update
  - [ ] Offer bulk refresh option

### 5.3 Optional: Background Scheduler
- [ ] Evaluate scheduling options:
  - [ ] APScheduler (Python library)
  - [ ] Celery + Redis (production-grade)
  - [ ] Cron job (simple approach)
- [ ] Implement scheduler (if desired):
  - [ ] `apps/resume-agent/scheduler.py`
  - [ ] Daily job to check for stale docs
  - [ ] Trigger refresh for periodic policies
  - [ ] Log refresh activities
- [ ] Add configuration:
  ```python
  ENABLE_AUTO_REFRESH = False  # Default off
  SCHEDULER_CHECK_INTERVAL = "daily"
  ```

### 5.4 User Notifications
- [ ] Add notification system:
  - [ ] Console output for CLI users
  - [ ] Log file for scheduled refreshes
  - [ ] Optional: Desktop notification (if UI exists)
- [ ] Notification triggers:
  - [ ] Docs are stale (periodic check)
  - [ ] Refresh completed successfully
  - [ ] Refresh failed (with error details)

---

## Additional Enhancements (Optional)

### Code Extraction Feature
- [ ] Implement code block extraction:
  - [ ] Regex patterns for ```language blocks
  - [ ] Extract language, code, context
  - [ ] Quality validation (min length, indicators)
- [ ] Generate code summaries:
  - [ ] Optional LLM call for summarization
  - [ ] Or simple heuristics (first line, function name)
- [ ] Store code examples separately:
  ```json
  {
    "code_examples": [
      {
        "id": "ex_123",
        "language": "typescript",
        "code": "export default function Page() {...}",
        "summary": "Server component example",
        "source_file": "server-components.md",
        "section": "Data Fetching"
      }
    ]
  }
  ```

### Contextual Embeddings
- [ ] Implement LLM-based context generation:
  - [ ] Generate context for each chunk within full document
  - [ ] Prepend context to chunk before embedding
  - [ ] Format: `{context}\n---\n{chunk}`
- [ ] Add configuration:
  ```python
  USE_CONTEXTUAL_EMBEDDINGS = False  # Default off (adds cost)
  CONTEXT_PROVIDER = "anthropic"
  ```

### Version Management
- [ ] Track documentation versions:
  - [ ] Detect version changes (if available)
  - [ ] Store version-specific docs in subdirectories
  - [ ] Compare current vs. new version before refresh
- [ ] Version-specific directories:
  ```
  ai_docs/frameworks/nextjs/
    README.md           # Latest
    .meta.json
    v14/
      README.md
      .meta.json
    v15/
      README.md
      .meta.json
  ```

### PostgreSQL + PGVector Migration
- [ ] For production deployments with high query volume:
  - [ ] Set up PostgreSQL with PGVector extension
  - [ ] Create schema (similar to Archon)
  - [ ] Migrate from FAISS to PGVector
  - [ ] Implement hybrid search (vector + full-text)
  - [ ] Add reranking with CrossEncoder

---

## Testing & Validation

### Unit Tests
- [ ] Test chunking algorithm
- [ ] Test embedding generation
- [ ] Test vector search
- [ ] Test crawling service
- [ ] Test MCP tools

### Integration Tests
- [ ] Test complete fetch-docs workflow
- [ ] Test crawl → chunk → embed → index pipeline
- [ ] Test search relevance
- [ ] Test MCP server integration

### Performance Tests
- [ ] Benchmark chunking speed
- [ ] Benchmark embedding generation
- [ ] Benchmark search latency
- [ ] Measure index size and memory usage

---

## Documentation

### User Documentation
- [ ] Update QUICKSTART.md with new features
- [ ] Create semantic search guide
- [ ] Document crawling capabilities
- [ ] Add MCP integration examples

### Developer Documentation
- [ ] Architecture diagram (chunking → embedding → indexing → search)
- [ ] API documentation for services
- [ ] Configuration reference
- [ ] Troubleshooting guide

### Migration Guide
- [ ] Migrating from flat files to chunked storage
- [ ] Enabling semantic search
- [ ] Configuring refresh policies
- [ ] Setting up MCP server

---

## Success Metrics

- [ ] Semantic search accuracy (qualitative testing)
- [ ] Search response time (<500ms for typical queries)
- [ ] Index build time (acceptable for CI/CD)
- [ ] Storage overhead (chunks + embeddings vs. original files)
- [ ] AI assistant integration success rate
- [ ] User adoption of new features

---

## Timeline Estimates

- **Priority 1 (Semantic Search)**: 1-2 weeks
- **Priority 2 (Smart Chunking)**: 1 week
- **Priority 3 (Crawling)**: 1-2 weeks
- **Priority 4 (MCP Server)**: 1 week
- **Priority 5 (Enhanced Refresh)**: 3-5 days

**Total Estimated Time**: 5-7 weeks for complete implementation

---

## Notes

- Start with Priority 1 (semantic search) for immediate value
- Priorities 2-3 can be developed in parallel
- Priority 4 depends on Priorities 1-2 completion
- Priority 5 is independent and can be done anytime
- Consider phased rollout with feature flags
- Maintain backward compatibility with existing Context7 integration
- Keep hybrid approach: Context7 for public libs, crawling for custom docs

---

## References

- **Research Report**: `docs/archon-research-report.md` (if saved)
- **Archon Repository**: https://github.com/coleam00/Archon
- **Context7 Docs**: https://context7.com
- **FastMCP**: https://github.com/jlowin/fastmcp
- **crawl4ai**: https://github.com/unclecode/crawl4ai
- **FAISS**: https://github.com/facebookresearch/faiss
- **sentence-transformers**: https://www.sbert.net/
