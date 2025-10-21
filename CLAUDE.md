# Career Application Assistant

## Purpose
This project helps me tailor resumes and generate cover letters for job applications using AI agents.

**Architecture**: MCP (Model Context Protocol) server exposing career tools to Claude Desktop and other MCP clients.

## Quick Start

**Start the MCP server:**
```bash
uv run resume_agent.py
```

Then configure Claude Desktop (see [QUICKSTART.md](QUICKSTART.md))

## Project Structure

### MCP Server
- **[resume_agent.py](resume_agent.py)** - Single-file MCP server (UV + FastMCP + Claude Agent SDK)
- **Tech Stack**: Python 3.10+, UV (Astral), FastMCP 2.0, Claude Agent SDK
- **Transport**: HTTP Streamable (port 8080)

### Documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[README-MCP-SERVER.md](README-MCP-SERVER.md)** - Complete feature guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[library-docs/](library-docs/)** - Claude Code & Agent SDK references

### Data Files
- **Master Resume**: `./resumes/kris-cernjavic-resume.yaml`
- **Original PDF**: `./resumes/kris-cernjavic-resume.pdf`
- **Career History**: `./resumes/career-history.yaml`
- **Portfolio Matrix**: `./portfolio_matrix_*.json`

### Agent Prompts
Located in `.claude/agents/`:
- `data-access-agent.md` - **Centralized data access layer** (ALL file I/O)
- `job-analyzer.md` - Job posting analysis (data-agnostic)
- `resume-writer.md` - Resume tailoring (data-agnostic)
- `cover-letter-writer.md` - Cover letter generation (data-agnostic)
- `portfolio-finder.md` - GitHub portfolio search (data-agnostic)

### Slash Commands (Direct CLI Usage)

**Atomic Commands:**
- `/career:fetch-job [url]` - Fetch, parse, and cache job posting data (idempotent)

**Workflow Commands:**
- `/career:analyze-job [url]` - Assess match between your background and job requirements
- `/career:tailor-resume [url]` - Generate ATS-optimized resume for specific job
- `/career:apply [url]` - Complete application workflow (analysis → portfolio → resume → cover letter)

**Portfolio Library (Job-Agnostic Examples):**
- `/career:add-portfolio [title]` - Add code example to centralized portfolio library
- `/career:list-portfolio [--tech=X] [--company=Y]` - List all portfolio examples with filters
- `/career:search-portfolio [query]` - Search portfolio library by keyword/technology

**Utilities:**
- `/career:find-examples [url]` - Search GitHub portfolio for relevant code examples
- `/career:portfolio-matrix` - Generate technology proficiency matrix from GitHub
- `/career:refresh-repos` - Refresh cached repository list
- `/career:update-master` - Update master resume with new achievements
- `/career:add-examples [company] [job-title]` - ⚠️ DEPRECATED: Use `/career:add-portfolio` instead

### Output
All generated applications go to: `./job-applications/{Company}_{JobTitle}/`
- `job-analysis.json` - Structured job requirements (cached by fetch-job)
- `Resume_{Company}.txt` - Tailored resume
- `CoverLetter_{Company}.txt` - Personalized cover letter
- `portfolio_examples.txt` - Relevant code examples

## Architecture: Data Access Layer

**Key Principle:** Centralized data access with validation

### Data Access Agent
All file operations go through the **data-access-agent** which:
- Provides a file-system agnostic interface for all data operations
- Uses MCP tools backed by Pydantic schemas for type safety
- Validates all data before reading/writing
- Makes it easy to swap file storage for database later

### Agent Responsibilities
All agents are now **data-agnostic** - they receive data and return content:

- **data-access-agent**: ALL file I/O with Pydantic validation
- **job-analyzer**: Parses job postings → returns JSON
- **resume-writer**: Receives data → returns resume content
- **cover-letter-writer**: Receives data → returns cover letter content
- **portfolio-finder**: Searches GitHub → returns findings

### Workflow Architecture

1. **`/career:fetch-job`** - Atomic command
   - Fetches job posting with Playwright
   - Parses with job-analyzer agent
   - Saves via data-access-agent (validated with JobAnalysis schema)
   - Idempotent: safe to run multiple times

2. **`/career:analyze-job`** - Uses cached data
   - Calls fetch-job to ensure cache exists
   - Loads data via data-access-agent (job analysis + master resume)
   - Performs match assessment

3. **`/career:tailor-resume`** - Uses cached data
   - Loads data via data-access-agent
   - Uses resume-writer agent (receives data, returns content)
   - Saves via data-access-agent

4. **`/career:apply`** - Orchestrates workflow
   - Calls fetch-job once
   - All data I/O via data-access-agent
   - Agents receive data and return content
   - All data validated before being saved

**Benefits:**
- ✅ Type-safe: All data validated against Pydantic schemas
- ✅ Centralized: Single source of truth for data operations
- ✅ Testable: Each agent can be tested independently
- ✅ Future-proof: Easy to swap file storage for database
- ✅ Consistent: All commands use identical validated data

## Architecture: Portfolio Library

**Key Principle:** Build reusable code examples over time, independent of specific job applications

### Design
The portfolio library is a centralized, job-agnostic repository for storing code examples, project highlights, and technical achievements. Unlike the old `/career:add-examples` which tied examples to specific job applications, the portfolio library allows you to:

1. **Build over time** - Add examples as you complete projects or recall past achievements
2. **Organize flexibly** - Tag by technology, company, project, or any combination
3. **Search efficiently** - Full-text search across all fields (title, description, content, technologies)
4. **Reuse across applications** - Reference the same examples when applying to multiple jobs

### Database Schema
```sql
portfolio_library (
  id              INTEGER PRIMARY KEY,
  user_id         VARCHAR DEFAULT 'default',
  title           VARCHAR,                  -- "RAG Pipeline - Customer Matching"
  company         VARCHAR,                  -- "D&D Worldwide Logistics"
  project         VARCHAR,                  -- "DDWL Platform"
  description     TEXT,                     -- What it demonstrates
  content         TEXT,                     -- Full code, explanations
  technologies_json VARCHAR,                -- ["RAG", "Redis", "Supabase"]
  file_paths_json VARCHAR,                  -- ["backend/services/matching.py:536"]
  source_repo     VARCHAR,                  -- GitHub URL (optional)
  created_at      DATETIME,
  updated_at      DATETIME
)
```

### Workflow
1. **Add examples**: `/career:add-portfolio` - Interactive or args-based
2. **Browse library**: `/career:list-portfolio` - Optional filters by tech/company
3. **Search examples**: `/career:search-portfolio` - Keyword search with tech filters
4. **Reference in applications**: Copy examples when applying to jobs

### Benefits
- ✅ Build portfolio library incrementally
- ✅ Not tied to specific job applications
- ✅ Searchable by technology, company, or keywords
- ✅ Supports multiple organizational methods
- ✅ Foundation for AI-powered example matching

## MCP Tools (Available to Claude Desktop)

### Workflow Tools
1. **analyze_job(job_url)** - Wrapper for `/career:analyze-job`
2. **tailor_resume(job_url)** - Wrapper for `/career:tailor-resume`
3. **apply_to_job(job_url)** - Wrapper for `/career:apply`

### Data Access Tools (Read Operations)
4. **data_read_master_resume()** - Read and validate master resume
5. **data_read_career_history()** - Read and validate career history
6. **data_read_job_analysis(company, job_title)** - Read cached job analysis
7. **data_read_tailored_resume(company, job_title)** - Read tailored resume
8. **data_read_cover_letter(company, job_title)** - Read cover letter
9. **data_list_applications(limit=10)** - List recent applications

### Data Access Tools (Write Operations)
10. **data_write_job_analysis(company, job_title, job_data)** - Save job analysis (validated)
11. **data_write_tailored_resume(company, job_title, content, metadata)** - Save resume
12. **data_write_cover_letter(company, job_title, content, metadata)** - Save cover letter
13. **data_write_portfolio_examples(company, job_title, content)** - Save portfolio examples

### Data Access Tools (Utilities)
14. **data_get_application_path(company, job_title, ensure_exists)** - Get/create application directory

### Portfolio Library Tools (Job-Agnostic)
15. **data_add_portfolio_example(title, content, ...)** - Add example to centralized library
16. **data_list_portfolio_examples(limit, technology_filter, company_filter)** - List portfolio examples
17. **data_search_portfolio_examples(query, technologies)** - Search portfolio by keyword
18. **data_get_portfolio_example(example_id)** - Get specific example by ID
19. **data_update_portfolio_example(example_id, ...)** - Update existing example
20. **data_delete_portfolio_example(example_id)** - Delete portfolio example

## MCP Resources (Data Access)

1. **resume://master** - Master resume (YAML, validated via MasterResume schema)
2. **resume://career-history** - Extended career details (validated via CareerHistory schema)
3. **resume://applications/recent** - Recent applications list (validated via ApplicationMetadata schema)

## Pydantic Data Schemas

All data is validated using Pydantic models defined in `resume_agent.py`:

- **PersonalInfo** - Contact information
- **Employment** - Employment history entry with achievements
- **MasterResume** - Complete resume structure
- **CareerHistory** - Extended career history
- **JobAnalysis** - Structured job posting data
- **TailoredResume** - Tailored resume with metadata
- **CoverLetter** - Cover letter with talking points
- **PortfolioExamples** - Portfolio code examples
- **ApplicationMetadata** - Application directory metadata

These schemas ensure type safety and data consistency across all operations.

## Current Status

**Phase 1 MVP - COMPLETE** ✅
- [x] HTTP Streamable MCP server
- [x] analyze_job tool
- [x] tailor_resume tool
- [x] apply_to_job orchestration
- [x] Claude Agent SDK integration
- [x] Reuses existing .claude/agents/ prompts
- [x] UV + FastMCP + PEP 723 single-file deployment

**Phase 2: Data Access Layer - COMPLETE** ✅
- [x] Pydantic schemas for all data types
- [x] Centralized data-access-agent
- [x] MCP read/write/utility tools
- [x] All agents refactored to be data-agnostic
- [x] All commands use data-access-agent
- [x] MCP resources use validated schemas
- [x] Type-safe, database-ready architecture

**Phase 3: Portfolio Library - COMPLETE** ✅
- [x] Job-agnostic portfolio library (SQLite table)
- [x] Portfolio library repository with CRUD operations
- [x] 6 MCP tools for portfolio management
- [x] `/career:add-portfolio` command
- [x] `/career:list-portfolio` command with filtering
- [x] `/career:search-portfolio` command with full-text search
- [x] Flexible organization by technology, company, or project
- [x] Independent from job applications

**Phase 4 - Next Steps**
- [ ] Resume update workflow
- [ ] Cover letter refinement tools
- [ ] Interview preparation tools
- [ ] AI-powered example matching for applications

## Key Design Decisions

1. **Single-file deployment** - `resume_agent.py` with PEP 723 inline dependencies
2. **UV package manager** - 10-100x faster than pip, auto-handles venvs
3. **FastMCP framework** - High-level MCP abstractions, decorator-based
4. **Claude Agent SDK** - Reuses `.claude/agents/` prompts as-is, handles AI orchestration
5. **HTTP Streamable** - Production-ready transport, stateless, horizontally scalable
6. **Data Access Layer** - Centralized file I/O via data-access-agent with Pydantic validation
7. **Agent Data-Agnosticism** - Agents receive data and return content (no file operations)
8. **Type Safety** - All data validated against Pydantic schemas before read/write

**NOTE**: All design decisions align with the project constitution (see `.specify/memory/constitution.md`)

## Development Workflow

```bash
# Edit agent prompts (changes take effect immediately)
notepad .claude/agents/job-analyzer.md

# Edit MCP server (restart to apply changes)
notepad resume_agent.py
uv run resume_agent.py

# Test with Claude Desktop
# (Configure in claude_desktop_config.json first)
```

## Project Governance

This project follows the **Cernji-Agents Constitution** (`.specify/memory/constitution.md`).

**Core Principles:**
- Multi-App Isolation (apps/ directory)
- Data Access Layer with validation
- Test-First Development (NON-NEGOTIABLE)
- Observability by Default
- User Experience Consistency
- Performance Standards
- Type Safety & Validation
- Simplicity & YAGNI

All feature development must pass constitution check gates. See the constitution for complete details.

## Why This Architecture?

- **74-82% faster setup** vs traditional approach
- **Reuses existing work** - agent prompts work unchanged
- **Production ready** - HTTP transport, error handling, logging
- **Single file** - Easy to deploy, version, and distribute
- **Type safe** - Pydantic models, FastMCP decorators
- **Your API key** - Uses Claude Desktop MAX subscription
