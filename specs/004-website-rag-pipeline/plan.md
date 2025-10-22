# Implementation Plan: Website RAG Pipeline for Career Applications

**Branch**: `004-website-rag-pipeline` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-website-rag-pipeline/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a RAG (Retrieval Augmented Generation) pipeline to extract, process, and query information from websites (job postings, company pages, career blogs) to enhance the Resume Agent's ability to generate tailored application materials. The system will use vector embeddings for semantic search, asynchronous processing for better UX, and integrate with the existing Resume Agent MCP server architecture.

## Technical Context

**Language/Version**: Python 3.10+ (matching existing Resume Agent)
**Primary Dependencies**:
  - **Embeddings**: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2, 384-dim)
  - **Vector Store**: sqlite-vec (native SQLite extension with SIMD optimization)
  - **Chunking**: langchain-text-splitters (HTMLHeaderTextSplitter + RecursiveCharacterTextSplitter hybrid)
**Storage**: SQLite (existing `data/resume_agent.db`) - extend with tables: website_sources, website_chunks, website_chunks_vec (virtual), website_chunks_fts (FTS5)
**Testing**: pytest (matching Resume Agent test suite)
**Target Platform**: Cross-platform (Windows/macOS/Linux) - MCP server runs locally
**Project Type**: Single project - extends existing `apps/resume-agent/`
**Performance Goals**:
  - URL processing: <15s for job postings, <20s for blog articles
  - Semantic queries: <3s for retrieval + synthesis
  - Cache hits: <1s
**Constraints**:
  - Must integrate with existing Resume Agent MCP server
  - Must use Pydantic schemas for all data validation
  - Must support asynchronous processing (non-blocking UX)
  - Playwright already available for web scraping
**Scale/Scope**:
  - Single user (local deployment)
  - ~50-100 processed websites per job search cycle
  - ~1000-5000 content chunks total
  - Vector embeddings stored in SQLite with sqlite-vec extension

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gates (Before Phase 0)

- [x] **Does this feature belong in an existing app or require a new one?**
  - **Decision**: Extends existing `apps/resume-agent/`
  - **Rationale**: RAG pipeline is a core capability for the Resume Agent's job application workflow. Adding a separate app would create unnecessary complexity and break the cohesive user experience.

- [x] **If new app: Is the complexity justified?**
  - **N/A**: Not creating a new app

- [x] **Can this be achieved without adding new dependencies?**
  - **Partial**: Will require vector embedding library (NEEDS CLARIFICATION in Phase 0)
  - **Justification**: Vector embeddings are fundamental to semantic search - cannot be avoided. Will research minimal dependency options (sentence-transformers vs langchain-openai) to minimize bloat.

- [x] **Does this follow the Data Access Layer pattern?**
  - **Yes**: Will create Pydantic schemas for `ProcessedWebsite`, `ContentChunk`, `QueryResult`, `ExtractionMetadata`
  - **Implementation**: All data operations will go through data-access-agent with schema validation, matching existing portfolio library pattern

- [x] **Are performance requirements defined?**
  - **Yes**: See Technical Context:
    - URL processing: <15s for job postings, <20s for articles
    - Semantic queries: <3s
    - Cache hits: <1s

- [x] **Is observability integration planned?**
  - **Yes**: Will emit events via existing hooks:
    - `WebsiteProcessingStart`, `WebsiteProcessingComplete`, `WebsiteProcessingFailed`
    - `SemanticQueryStart`, `SemanticQueryComplete`
    - All events include `source_app: "resume-agent"` and structured payloads

### Post-Design Gates (After Phase 1)

- [x] **Are all data schemas defined with Pydantic/TypeScript types?**
  - **Yes**: All schemas defined in `data-model.md`:
    - `WebsiteSource` (Pydantic BaseModel)
    - `WebsiteChunk` (Pydantic BaseModel)
    - `QueryResult` with `ChunkResult` (Pydantic BaseModel)
    - `ExtractionMetadata` with `JobPostingMetadata`, `BlogArticleMetadata` (Pydantic BaseModel)
  - All fields include validation rules (min/max length, enums, constraints)
  - All data passes through Pydantic validation before read/write

- [x] **Are contract tests planned for all interfaces?**
  - **Yes**: Contract test suite specified in `contracts/mcp-tools.md`:
    - `test_rag_process_website()` - URL processing, caching, validation
    - `test_rag_query_websites()` - Semantic search, source citations (SC-008), filtering
    - `test_rag_list_websites()` - Pagination, filtering, staleness detection
    - Test location: `apps/resume-agent/tests/contract/test_rag_mcp_tools.py`
  - Integration tests planned: `tests/integration/test_rag_workflow.py`

- [x] **Is the implementation the simplest approach?**
  - **Yes**: Follows Constitution Principle VIII (Simplicity & YAGNI):
    - Extends existing app (no new app created)
    - Uses battle-tested libraries (sentence-transformers, langchain-text-splitters)
    - Hybrid chunking strategy (15-20 lines, not 200+ for custom)
    - SQLite + sqlite-vec (native integration, no external services)
    - Monolithic architecture (vs Archon's 4 microservices)
    - Single embedding dimension (384-dim, vs Archon's 5 dimensions)
    - No premature optimization (reranking deferred to Phase 2)

- [x] **Are all dependencies justified in Complexity Tracking?**
  - **Yes**: See Complexity Tracking section below
  - Vector embedding library: Justified (core RAG requirement)
  - sentence-transformers: 1 dependency for embeddings
  - sqlite-vec: 1 dependency for vector search
  - langchain-text-splitters: 1 dependency for chunking (5MB standalone package)
  - Total: 3 new dependencies (minimal for RAG capabilities)

**Reference**: See `.specify/memory/constitution.md` for complete principles

**GATE STATUS: ✅ PASSED** - All post-design gates satisfied. Implementation can proceed.

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
apps/resume-agent/
├── resume_agent.py           # Main MCP server (extended with RAG tools)
├── .claude/
│   ├── agents/
│   │   ├── data-access-agent.md       # Extended with RAG schemas
│   │   └── website-processor-agent.md # NEW: Handles web extraction & chunking
│   └── commands/
│       ├── /career:process-website    # NEW: Process a URL into RAG pipeline
│       ├── /career:query-websites     # NEW: Semantic search across processed content
│       └── /career:list-websites      # NEW: Library management
├── tests/
│   ├── contract/
│   │   └── test_rag_mcp_tools.py     # NEW: Contract tests for RAG MCP tools
│   ├── integration/
│   │   └── test_rag_workflow.py      # NEW: End-to-end RAG pipeline tests
│   └── unit/
│       ├── test_chunking.py          # NEW: Chunking strategy tests
│       └── test_embeddings.py        # NEW: Embedding generation tests
└── README.md                          # Updated with RAG pipeline docs

data/
└── resume_agent.db                    # Extended with RAG tables

.claude/commands/
├── career-process-website.md          # NEW: Slash command for URL processing
├── career-query-websites.md           # NEW: Slash command for semantic queries
└── career-list-websites.md            # NEW: Slash command for library management
```

**Structure Decision**: Extends existing `apps/resume-agent/` with RAG capabilities rather than creating a new app. This follows Constitution Principle I (Multi-App Isolation) which states apps should only be created when functionality is independent and reusable. RAG pipeline is tightly coupled to Resume Agent's job application workflow, so integration is the simplest approach.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Vector embedding library dependency | Semantic search requires vector similarity computation, which is the core RAG capability | Simple keyword search insufficient for matching user queries with relevant content across diverse website structures and phrasing variations |

