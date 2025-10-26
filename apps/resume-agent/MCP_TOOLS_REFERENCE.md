# MCP Tools Reference

Complete reference for all 30 MCP tools exposed by the Resume Agent MCP server.

## Tool Categories

- [Data Access - Read Operations](#data-access---read-operations) (6 tools)
- [Data Access - Write Operations](#data-access---write-operations) (6 tools)
- [Data Access - Utility Operations](#data-access---utility-operations) (7 tools)
- [RAG Pipeline - Website Processing](#rag-pipeline---website-processing) (6 tools)
- [Job Application Workflow](#job-application-workflow) (3 tools)
- [Portfolio Management](#portfolio-management) (2 tools)

---

## Data Access - Read Operations

Tools for reading career data from the database.

| Function Name | Description | Parameters | Return Type |
|--------------|-------------|------------|-------------|
| `data_read_master_resume` | Read the master resume and return validated data. | None | `dict[str, Any]` with status and data |
| `data_read_career_history` | Read the career history and return validated data. | None | `dict[str, Any]` with status and data |
| `data_read_job_analysis` | Read job analysis data for a specific application. | `company: str`<br>`job_title: str` | `dict[str, Any]` with status and analysis data |
| `data_read_tailored_resume` | Read tailored resume for a specific application. | `company: str`<br>`job_title: str` | `dict[str, Any]` with status and content |
| `data_read_cover_letter` | Read cover letter for a specific application. | `company: str`<br>`job_title: str` | `dict[str, Any]` with status and content |
| `data_list_applications` | List recent job applications. | `limit: int = 10` | `dict[str, Any]` with list of applications |

---

## Data Access - Write Operations

Tools for writing/updating career data in the database.

| Function Name | Description | Parameters | Return Type |
|--------------|-------------|------------|-------------|
| `data_write_job_analysis` | Save job analysis data for an application. | `company: str`<br>`job_title: str`<br>`job_data: dict` | `dict[str, Any]` with status |
| `data_write_tailored_resume` | Save tailored resume for an application. | `company: str`<br>`job_title: str`<br>`content: str`<br>`metadata: dict = None` | `dict[str, Any]` with status and file path |
| `data_write_cover_letter` | Save cover letter for an application. | `company: str`<br>`job_title: str`<br>`content: str`<br>`metadata: dict = None` | `dict[str, Any]` with status and file path |
| `data_write_portfolio_examples` | Save portfolio examples for an application. | `company: str`<br>`job_title: str`<br>`content: str` | `dict[str, Any]` with status and file path |
| `data_write_master_resume` | Write the master resume with validated data. | `resume_data: dict` | `dict[str, Any]` with status and file path |
| `data_write_career_history` | Write the career history with validated data. | `history_data: dict` | `dict[str, Any]` with status and file path |

---

## Data Access - Utility Operations

Utility tools for managing career data, achievements, technologies, and portfolio.

| Function Name | Description | Parameters | Return Type |
|--------------|-------------|------------|-------------|
| `data_add_achievement` | Add an achievement to a specific employment entry in career history. | `company: str`<br>`achievement_description: str`<br>`metric: str = None` | `dict[str, Any]` with status |
| `data_add_technology` | Add technologies to a specific employment entry in career history. Also updates master resume skills. | `company: str`<br>`technologies: List[str]` | `dict[str, Any]` with status |
| `data_get_application_path` | Get application directory/identifier. | `company: str`<br>`job_title: str`<br>`ensure_exists: bool = False` | `dict[str, Any]` with directory path and existence status |
| `data_add_portfolio_example` | Add a new example to your job-agnostic portfolio library. | `title: str`<br>`content: str`<br>`company: str = None`<br>`project: str = None`<br>`description: str = None`<br>`technologies: List[str] = None`<br>`file_paths: List[str] = None`<br>`source_repo: str = None` | `dict[str, Any]` with status and example ID |
| `data_list_portfolio_examples` | List portfolio examples with optional filters. | `limit: int = None`<br>`technology_filter: str = None`<br>`company_filter: str = None` | `dict[str, Any]` with list of examples |
| `data_search_portfolio_examples` | Search portfolio examples by keyword and/or technologies. | `query: str`<br>`technologies: List[str] = None` | `dict[str, Any]` with matching examples |
| `data_get_portfolio_example` | Get a specific portfolio example by ID. | `example_id: int` | `dict[str, Any]` with example details |

---

## Portfolio Management

Additional portfolio management tools for updating and deleting examples.

| Function Name | Description | Parameters | Return Type |
|--------------|-------------|------------|-------------|
| `data_update_portfolio_example` | Update an existing portfolio example. | `example_id: int`<br>`title: str = None`<br>`content: str = None`<br>`company: str = None`<br>`project: str = None`<br>`description: str = None`<br>`technologies: List[str] = None`<br>`file_paths: List[str] = None`<br>`source_repo: str = None` | `dict[str, Any]` with status |
| `data_delete_portfolio_example` | Delete a portfolio example. | `example_id: int` | `dict[str, Any]` with status |

---

## RAG Pipeline - Website Processing

Tools for processing websites into the RAG pipeline for semantic search.

| Function Name | Description | Parameters | Return Type |
|--------------|-------------|------------|-------------|
| `rag_process_website` | Process a website URL into the RAG pipeline for semantic search. Fetches HTML, detects language, chunks content, generates embeddings, and stores in database. | `url: str`<br>`content_type: Literal["job_posting", "blog_article", "company_page"] = "job_posting"`<br>`force_refresh: bool = False` | `dict[str, Any]` with source_id, chunk_count, language, processing_time |
| `rag_get_website_status` | Get the processing status of a website. | `source_id: int` | `dict[str, Any]` with processing status and chunk count |
| `rag_query_websites` | Perform semantic search across all processed websites. Uses hybrid search (70% vector similarity + 30% FTS). | `query: str`<br>`max_results: int = 10`<br>`content_type_filter: Optional[Literal["job_posting", "blog_article", "company_page"]] = None`<br>`source_ids: Optional[List[int]] = None`<br>`include_synthesis: bool = False` | `dict[str, Any]` with ranked results, confidence, processing_time |
| `rag_list_websites` | List all processed websites with optional filtering and pagination. | `content_type: Optional[Literal["job_posting", "blog_article", "company_page"]] = None`<br>`status: Optional[Literal["pending", "processing", "completed", "failed"]] = None`<br>`limit: int = 20`<br>`offset: int = 0`<br>`order_by: Literal["fetch_timestamp", "title", "content_type"] = "fetch_timestamp"` | `dict[str, Any]` with websites list, total count, staleness warnings |
| `rag_refresh_website` | Refresh a processed website by re-fetching and re-processing its content. Deletes all old chunks and re-processes from scratch. | `source_id: int` | `dict[str, Any]` with status and processing result |
| `rag_delete_website` | Delete a processed website and all its associated chunks. Destructive operation - cascades to chunks, embeddings, and FTS entries. | `source_id: int` | `dict[str, Any]` with status and deletion summary |

---

## Job Application Workflow

High-level tools for job application workflows (orchestrate slash commands).

| Function Name | Description | Parameters | Return Type |
|--------------|-------------|------------|-------------|
| `analyze_job` | Analyze a job posting and extract structured requirements. Executes `/career:analyze-job` slash command. | `job_url: str` | `dict[str, Any]` with analysis and match score |
| `tailor_resume` | Tailor your resume for a specific job opportunity. Executes `/career:tailor-resume` slash command. | `job_url: str` | `dict[str, Any]` with status and result |
| `apply_to_job` | Complete end-to-end job application workflow. Executes `/career:apply` slash command which handles job analysis, portfolio search, resume tailoring, and cover letter generation. | `job_url: str`<br>`include_cover_letter: bool = True` | `dict[str, Any]` with complete application package |

---

## Tool Usage Patterns

### Basic Data Access Pattern
```python
# Read master resume
result = data_read_master_resume()
if result["status"] == "success":
    resume_data = result["data"]
```

### Job Application Pattern
```python
# Complete application workflow
result = apply_to_job(
    job_url="https://example.com/job",
    include_cover_letter=True
)
```

### RAG Pipeline Pattern
```python
# 1. Process a job posting website
process_result = rag_process_website(
    url="https://example.com/job",
    content_type="job_posting"
)

# 2. Query the processed content
query_result = rag_query_websites(
    query="What are the key requirements?",
    max_results=5
)
```

### Portfolio Management Pattern
```python
# 1. Add portfolio example
add_result = data_add_portfolio_example(
    title="RAG Pipeline Implementation",
    content="...",
    technologies=["Python", "LangChain", "Qdrant"]
)

# 2. Search portfolio
search_result = data_search_portfolio_examples(
    query="vector database",
    technologies=["Qdrant"]
)
```

---

## Return Value Conventions

All tools follow consistent return patterns:

### Success Response
```json
{
  "status": "success",
  "data": { ... },  // or "content", "results", etc.
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Error message describing what went wrong"
}
```

### Cached Response (RAG tools)
```json
{
  "status": "cached",
  "source_id": 123,
  "chunk_count": 45,
  "message": "URL already processed. Use force_refresh=true to re-process."
}
```

---

## Database Schema

The tools interact with the following database tables:

- **master_resumes** - Master resume data (YAML)
- **career_history** - Extended career history (YAML)
- **job_applications** - Job analysis, tailored resumes, cover letters
- **portfolio_examples** - Job-agnostic code examples
- **website_sources** - Processed websites metadata
- **website_chunks** - Content chunks with embeddings
- **website_chunks_fts** - Full-text search index

---

## MCP Resources

In addition to tools, the server exposes these MCP resources:

- `resume://master` - Master resume in YAML format
- `resume://career-history` - Extended career history in YAML
- `resume://applications/recent` - Recent 10 applications (JSON)

---

## MCP Prompts

The server provides these reusable prompt templates:

- `analyze_job_posting(job_url)` - Analyze job and assess match
- `tailor_resume_for_job(job_url)` - Generate tailored resume
- `generate_cover_letter(job_url, company_name, role_title)` - Write cover letter
- `find_portfolio_examples(job_url)` - Search GitHub portfolio

---

## Notes

- All async tools (`rag_*`, `analyze_job`, `tailor_resume`, `apply_to_job`) use `await`
- RAG tools require Qdrant MCP server for vector search (optional but recommended)
- Portfolio tools store examples in SQLite database for job-agnostic reuse
- Write operations validate data with Pydantic schemas before persisting
- All tools use consistent error handling and logging

---

**Generated**: 2025-10-26
**Source**: `D:\source\Cernji-Agents\apps\resume-agent\resume_agent.py`
**Total Tools**: 30 (6 read + 6 write + 7 utility + 2 portfolio + 6 RAG + 3 workflow)
