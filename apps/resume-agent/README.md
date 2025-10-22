# Resume Agent

MCP server providing career application tools for job applications.

## Overview

The Resume Agent is a Model Context Protocol (MCP) server that helps with:
- **RAG Pipeline**: Process and query websites (job postings, blogs, company pages) for semantic search
- Analyzing job postings with AI-powered extraction
- Tailoring resumes for specific roles with ATS optimization
- Generating personalized cover letters
- Finding portfolio examples from GitHub
- Managing career history and achievements
- Building a job-agnostic portfolio library

## Quick Start

### Prerequisites

- Python 3.10+
- UV package manager
- Claude Desktop (for MCP integration)

### Starting the Server

```bash
# From repository root
uv run apps/resume-agent/resume_agent.py
```

### MCP Configuration

Add to Claude Desktop's MCP configuration:

```json
{
  "mcpServers": {
    "resume-agent": {
      "command": "uv",
      "args": ["run", "apps/resume-agent/resume_agent.py"],
      "env": {}
    }
  }
}
```

## Tech Stack

- **Framework**: FastMCP 2.0
- **Dependencies**: UV (PEP 723 inline dependencies)
- **AI Orchestration**: Claude Agent SDK
- **Validation**: Pydantic models
- **Database**: SQLite with FTS5 and sqlite-vec for RAG
- **Embeddings**: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Chunking**: langchain-text-splitters (HTML + recursive strategies)

## Features

### 1. RAG Pipeline (Website Processing & Semantic Search)

Process websites into a searchable knowledge base using Retrieval Augmented Generation:

**Slash Commands:**
- `/career:process-website [url] [--type=TYPE] [--refresh]` - Process a URL into RAG pipeline
- `/career:query-websites [query] [--type=TYPE] [--limit=N] [--synthesize]` - Semantic search across processed content
- `/career:list-websites [--type=TYPE] [--status=STATUS]` - List all processed websites
- `/career:refresh-website [source_id]` - Re-process a website (for updates)
- `/career:delete-website [source_id]` - Delete a processed website

**Content Types:**
- `job_posting` (default) - Job boards, career pages, individual listings
- `blog_article` - Career advice blogs, technical articles, interview guides
- `company_page` - Company about/culture/values pages

**Key Features:**
- Multilingual support (English + Japanese)
- Hybrid search (vector similarity + full-text search)
- Smart chunking (HTML-aware + recursive splitting)
- Staleness detection (>30 days)
- Caching (avoid re-processing same URLs)

**Performance:**
- Job posting processing: <15s
- Blog article processing: <20s
- Semantic queries: <3s
- Cache hits: <1s

**Example Workflow:**
```bash
# Process a job posting
/career:process-website https://japan-dev.com/jobs/acme/backend-engineer

# Query for requirements
/career:query-websites "What are the key technical requirements?"

# List all processed websites
/career:list-websites --status=completed

# Refresh stale content
/career:refresh-website 42
```

### 2. Job Analysis & Application Generation

Analyze job postings and generate tailored application materials:

**Slash Commands:**
- `/career:analyze-job [url]` - Analyze job requirements and assess match
- `/career:tailor-resume [url]` - Generate ATS-optimized resume
- `/career:apply [url]` - Complete application workflow (analysis → resume → cover letter)

**Integration with RAG:**
The application workflow now uses the RAG pipeline to:
- Extract detailed job requirements with semantic understanding
- Query company culture insights for cover letters
- Find relevant portfolio examples based on job technologies

### 3. Portfolio Library Management

Build a reusable, job-agnostic portfolio library:

**Slash Commands:**
- `/career:add-portfolio [title]` - Add code example to library
- `/career:list-portfolio [--tech=X] [--company=Y]` - List portfolio examples
- `/career:search-portfolio [query]` - Search by keyword/technology

**MCP Tools:**
- `data_add_portfolio_example()` - Add new example
- `data_list_portfolio_examples()` - List with filtering
- `data_search_portfolio_examples()` - Keyword search
- `data_get_portfolio_example()` - Get by ID
- `data_update_portfolio_example()` - Update existing
- `data_delete_portfolio_example()` - Delete example

### 4. Career History Management

Manage your career history and achievements:

**MCP Tools:**
- `data_read_master_resume()` - Read master resume
- `data_read_career_history()` - Read career history
- `data_add_achievement()` - Add achievement to employment
- `data_add_technology()` - Add technology to employment

## MCP Tools Reference

### RAG Pipeline Tools

**Website Processing:**
- `rag_process_website(url, content_type, force_refresh)` - Process URL into RAG
- `rag_get_website_status(source_id)` - Get processing status
- `rag_query_websites(query, max_results, content_type_filter, source_ids, include_synthesis)` - Semantic search
- `rag_list_websites(content_type, status, limit, offset, order_by)` - List processed websites
- `rag_refresh_website(source_id)` - Re-process website
- `rag_delete_website(source_id)` - Delete website and chunks

**Workflow Tools:**
- `analyze_job(job_url)` - Analyze job posting
- `tailor_resume(job_url)` - Generate tailored resume
- `apply_to_job(job_url, include_cover_letter)` - Complete application

**Data Access Tools:**
- `data_read_master_resume()` - Read master resume
- `data_read_career_history()` - Read career history
- `data_read_job_analysis(company, job_title)` - Read job analysis
- `data_list_applications(limit)` - List recent applications
- `data_add_achievement(company, achievement_description, metric)` - Add achievement
- `data_add_technology(company, technologies)` - Add technologies

**Portfolio Library Tools:**
- `data_add_portfolio_example(title, content, ...)` - Add example
- `data_list_portfolio_examples(limit, technology_filter, company_filter)` - List examples
- `data_search_portfolio_examples(query, technologies)` - Search examples
- `data_get_portfolio_example(example_id)` - Get example by ID
- `data_update_portfolio_example(example_id, ...)` - Update example
- `data_delete_portfolio_example(example_id)` - Delete example

## Database Schema

### RAG Pipeline Tables

**website_sources:**
- Stores processed website metadata
- Fields: id, url, title, content_type, language, raw_html, metadata_json, fetch_timestamp, processing_status

**website_chunks:**
- Stores content chunks for semantic search
- Fields: id, source_id, chunk_index, content, char_count, metadata_json, created_at

**website_chunks_vec (sqlite-vec):**
- Virtual table for vector embeddings
- Fields: chunk_id, embedding (384-dim float array)

**website_chunks_fts (FTS5):**
- Full-text search index
- Fields: chunk_id, content

### Portfolio Library Tables

**portfolio_library:**
- Job-agnostic code examples
- Fields: id, user_id, title, company, project, description, content, technologies_json, file_paths_json, source_repo, created_at, updated_at

### Career History Tables

**personal_info, employment, education, skills, achievements:**
- Career history and resume data
- Validated with Pydantic schemas

## Architecture

### Data Access Layer
All file and database operations go through a centralized data access layer:
- Pydantic schema validation for type safety
- File-system agnostic interface
- Easy to swap file storage for database

### RAG Pipeline Flow

1. **Process**: URL → Fetch HTML → Detect Language → Chunk → Generate Embeddings → Store
2. **Query**: Natural Language Query → Generate Embedding → Hybrid Search (Vector + FTS) → Rank → Return Results

### Hybrid Search Strategy

**Vector Similarity (70% weight):**
- Semantic understanding of query intent
- Finds conceptually similar content
- Uses cosine similarity on 384-dim embeddings

**Full-Text Search (30% weight):**
- Exact keyword matches
- Handles specific terminology
- SQLite FTS5 with unicode61 tokenizer

**Combined Score:**
```
final_score = (vector_score * 0.7) + (fts_score * 0.3)
```

## Configuration

### Environment Variables

- `USER_ID` - User identifier (default: "default")
- `DATA_DIR` - Data directory path (default: "data/")
- `ANTHROPIC_API_KEY` - Claude API key (for AI synthesis)

### Database Path

- SQLite database: `data/resume_agent.db`
- Automatically created on first run
- Tables created by migration script: `apps/resume-agent/scripts/create_rag_tables.py`

## Development

### Running Tests

```bash
# Run all tests
pytest apps/resume-agent/tests/

# Run RAG pipeline tests
pytest apps/resume-agent/tests/integration/test_rag_workflow.py

# Run contract tests
pytest apps/resume-agent/tests/contract/test_rag_mcp_tools.py
```

### Database Migrations

```bash
# Create RAG pipeline tables
uv run apps/resume-agent/scripts/create_rag_tables.py

# Verify database
sqlite3 data/resume_agent.db ".tables"
```

## Troubleshooting

### Model Download Issues

First run downloads the sentence-transformers model (~420MB):
```bash
# Manual download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
```

### sqlite-vec Extension Issues

```bash
# Reinstall sqlite-vec
uv pip install --force-reinstall sqlite-vec>=0.1.0
```

### Slow Processing

- Enable async processing (returns immediately with status="processing")
- Check network connectivity (Playwright fetch timeouts)
- Verify embedding model is cached (~/.cache/torch/sentence_transformers/)

## Links

- **Project Root**: `D:\source\Cernji-Agents\`
- **Feature Spec**: `specs/004-website-rag-pipeline/spec.md`
- **Data Model**: `specs/004-website-rag-pipeline/data-model.md`
- **Quickstart Guide**: `specs/004-website-rag-pipeline/quickstart.md`
- **Research**: `specs/004-website-rag-pipeline/research.md`
