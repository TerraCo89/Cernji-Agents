# Slash Commands Contract: Website RAG Pipeline

**Feature**: 004-website-rag-pipeline
**Date**: 2025-10-22
**Status**: Phase 1 Design

## Overview

This document specifies the slash commands for user-facing interaction with the Website RAG Pipeline. Commands are stored in `.claude/commands/` and execute via the SlashCommand tool.

---

## Command 1: `/career:process-website`

### Purpose
Process a website URL into the RAG pipeline for semantic search.

### File Location
`.claude/commands/career-process-website.md`

### Command Spec

```markdown
# /career:process-website - Process Website for RAG Pipeline

## Purpose
Process a website (job posting, blog article, company page) into the RAG pipeline for semantic search and application generation.

## Usage

```
/career:process-website [URL] [--type=TYPE] [--refresh]
```

## Arguments

- **URL** (required): Website URL to process
- **--type** (optional): Content type hint
  - `job_posting` (default): Job board pages
  - `blog_article`: Career advice blogs
  - `company_page`: Company information pages
- **--refresh** (optional): Force re-processing even if cached

## Examples

```bash
# Process a job posting
/career:process-website https://japan-dev.com/jobs/acme/backend-engineer

# Process a blog article
/career:process-website https://blog.gaijinpot.com/tech-jobs-japan/ --type=blog_article

# Refresh a previously processed URL
/career:process-website https://japan-dev.com/jobs/acme/backend-engineer --refresh
```

## Workflow

1. **Validate URL**: Check if URL is valid HTTP/HTTPS
2. **Check cache**: If URL already processed and `--refresh` not set, return cached result
3. **Fetch content**: Use Playwright to fetch HTML
4. **Detect language**: Identify English, Japanese, or mixed content
5. **Chunk content**: Split into semantic chunks (800-1200 chars)
6. **Generate embeddings**: Create vector embeddings for each chunk
7. **Store**: Save to SQLite (sources, chunks, vectors, FTS)
8. **Report**: Show processing summary

## Output

```
✓ Processing complete: https://japan-dev.com/jobs/acme/backend-engineer

Source ID: 42
Content Type: job_posting
Language: English
Chunks Created: 8
Processing Time: 12.3s

You can now query this content with /career:query-websites
```

## Error Handling

- **Invalid URL**: "Error: Please provide a valid HTTP/HTTPS URL"
- **Fetch failure**: "Error: Could not fetch URL (404 Not Found). Please check the URL and try again."
- **Processing failure**: "Error: Failed to process website. Details: {error_message}"

## Integration

This command uses the `rag_process_website` MCP tool internally.

See: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\contracts\mcp-tools.md`
```

---

## Command 2: `/career:query-websites`

### Purpose
Query processed websites using semantic search.

### File Location
`.claude/commands/career-query-websites.md`

### Command Spec

```markdown
# /career:query-websites - Semantic Search Across Processed Websites

## Purpose
Query all processed websites using natural language to find relevant information for job applications.

## Usage

```
/career:query-websites [QUERY] [--type=TYPE] [--limit=N] [--synthesize]
```

## Arguments

- **QUERY** (required): Natural language question
- **--type** (optional): Filter by content type (job_posting | blog_article | company_page)
- **--limit** (optional): Maximum results (default: 10, max: 20)
- **--synthesize** (optional): Generate AI summary of results

## Examples

```bash
# Basic semantic search
/career:query-websites "What are the key requirements for backend engineer roles in Tokyo?"

# Filter by content type
/career:query-websites "Tips for interviewing at Japanese companies" --type=blog_article

# Get AI synthesis
/career:query-websites "Company culture at tech startups" --limit=5 --synthesize
```

## Workflow

1. **Generate query embedding**: Convert question to vector
2. **Hybrid search**:
   - Vector similarity search (semantic matching)
   - Full-text keyword search (exact matches)
   - Combine scores (70% vector + 30% FTS)
3. **Rank results**: Sort by combined score
4. **Format output**: Include source citations
5. **Synthesize** (optional): Generate AI summary

## Output

```
Query: "What are the key requirements for backend engineer roles in Tokyo?"

Top Results (10):

1. [Score: 0.23] Senior Backend Engineer - Acme Corp
   Source: https://japan-dev.com/jobs/acme/backend-engineer
   Section: Requirements > Technical Skills

   "5+ years of experience in Python, FastAPI, and PostgreSQL.
   Strong understanding of microservices architecture.
   Experience with AWS or GCP..."

2. [Score: 0.31] Backend Developer - StartupXYZ
   Source: https://japan-dev.com/jobs/startupxyz/backend-dev
   Section: What We're Looking For

   "3+ years backend development. Python or Go.
   Familiarity with Docker, Kubernetes.
   Japanese language skills preferred but not required..."

[... 8 more results ...]

Confidence: High
Processing Time: 1.8s

---

💡 Use these insights to tailor your resume with /career:tailor-resume
```

## Integration

This command uses the `rag_query_websites` MCP tool internally.

See: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\contracts\mcp-tools.md`
```

---

## Command 3: `/career:list-websites`

### Purpose
List all processed websites with filtering.

### File Location
`.claude/commands/career-list-websites.md`

### Command Spec

```markdown
# /career:list-websites - Manage Processed Websites Library

## Purpose
View, filter, and manage all websites processed into the RAG pipeline.

## Usage

```
/career:list-websites [--type=TYPE] [--status=STATUS] [--limit=N]
```

## Arguments

- **--type** (optional): Filter by content type
- **--status** (optional): Filter by processing status (pending | processing | completed | failed)
- **--limit** (optional): Maximum results (default: 50)

## Examples

```bash
# List all processed websites
/career:list-websites

# List only job postings
/career:list-websites --type=job_posting

# List failed processing attempts
/career:list-websites --status=failed

# List recent 20 entries
/career:list-websites --limit=20
```

## Workflow

1. **Query database**: Fetch websites matching filters
2. **Check staleness**: Mark entries >30 days old as stale
3. **Format output**: Table view with key info

## Output

```
Processed Websites (Total: 47)

┌────┬──────────────────────────────────────┬─────────────┬──────────┬───────────┬────────┐
│ ID │ URL                                  │ Type        │ Language │ Fetched   │ Status │
├────┼──────────────────────────────────────┼─────────────┼──────────┼───────────┼────────┤
│ 42 │ japan-dev.com/jobs/acme/backend-eng  │ job_posting │ en       │ 2d ago    │ ✓      │
│ 41 │ blog.gaijinpot.com/tech-jobs-japan   │ blog_article│ en       │ 5d ago    │ ✓      │
│ 40 │ japan-dev.com/jobs/startup/fullstack │ job_posting │ mixed    │ 7d ago    │ ✓      │
│ 35 │ company.com/about/culture            │ company_page│ en       │ 32d ago ⚠ │ ✓ Stale│
└────┴──────────────────────────────────────┴─────────────┴──────────┴───────────┴────────┘

Legend:
  ✓ = Completed
  ⚠ = Stale (>30 days old, consider refreshing)

Actions:
  - Refresh stale entry: /career:refresh-website [ID]
  - Delete entry: /career:delete-website [ID]
  - Query all: /career:query-websites [QUERY]
```

## Integration

This command uses the `rag_list_websites` MCP tool internally.
```

---

## Command 4: `/career:refresh-website`

### Purpose
Refresh a stale or failed website.

### File Location
`.claude/commands/career-refresh-website.md`

### Command Spec

```markdown
# /career:refresh-website - Refresh Processed Website

## Purpose
Re-process a website to update stale content or retry failed processing.

## Usage

```
/career:refresh-website [SOURCE_ID]
```

## Arguments

- **SOURCE_ID** (required): Database ID of the website (from /career:list-websites)

## Examples

```bash
# Refresh website with ID 35
/career:refresh-website 35
```

## Workflow

1. **Validate source ID**: Check if website exists
2. **Delete old chunks**: Remove existing chunks, embeddings, FTS entries
3. **Re-fetch content**: Fetch latest HTML
4. **Re-process**: Chunk, embed, store
5. **Report**: Show before/after comparison

## Output

```
Refreshing website ID 35...

URL: https://company.com/about/culture
Old Chunks: 6 (deleted)
New Chunks: 8 (created)
Processing Time: 10.2s

✓ Refresh complete
```

## Integration

This command uses the `rag_refresh_website` MCP tool internally.
```

---

## Command 5: `/career:delete-website`

### Purpose
Delete a processed website from the RAG pipeline.

### File Location
`.claude/commands/career-delete-website.md`

### Command Spec

```markdown
# /career:delete-website - Delete Processed Website

## Purpose
Remove a website and all associated data from the RAG pipeline.

⚠️ **WARNING**: This action is IRREVERSIBLE.

## Usage

```
/career:delete-website [SOURCE_ID]
```

## Arguments

- **SOURCE_ID** (required): Database ID of the website

## Examples

```bash
# Delete website with ID 35
/career:delete-website 35
```

## Workflow

1. **Confirm deletion**: Prompt user for confirmation
2. **Delete**: Remove source, chunks, embeddings, FTS entries (cascading)
3. **Report**: Confirm deletion

## Output

```
⚠️  WARNING: You are about to DELETE this website and all associated data.

URL: https://company.com/about/culture
Chunks: 6
Embeddings: 6
FTS Entries: 6

This action is IRREVERSIBLE. Are you sure? (yes/no): yes

✓ Deleted website ID 35
```

## Integration

This command uses the `rag_delete_website` MCP tool internally.
```

---

## Integration with Existing Workflow

### Enhanced `/career:apply` Command

Update the existing `/career:apply` command to use RAG pipeline:

```markdown
# Enhanced /career:apply Workflow

## New Steps (with RAG integration)

1. Fetch job posting URL (existing)
2. **NEW**: Process job posting into RAG pipeline (`/career:process-website`)
3. Analyze job requirements (existing)
4. **NEW**: Query RAG for company culture insights (`/career:query-websites "company culture at [company]"`)
5. Search GitHub portfolio (existing)
6. **NEW**: Use RAG insights to tailor resume (enhanced with company-specific keywords)
7. Generate tailored resume (existing)
8. **NEW**: Use RAG insights for cover letter talking points (enhanced with culture fit)
9. Generate cover letter (existing)

## Example

```bash
/career:apply https://japan-dev.com/jobs/acme/backend-engineer
```

**Output (with RAG enhancement):**

```
Step 1/9: Fetching job posting...
Step 2/9: Processing into RAG pipeline... ✓ (8 chunks created)
Step 3/9: Analyzing requirements...
Step 4/9: Querying company culture insights...

  Found: "Acme values collaboration, innovation, and work-life balance.
  Remote work 2-3 days/week. English-speaking environment."

Step 5/9: Searching GitHub portfolio...
Step 6/9: Tailoring resume with company-specific keywords...
Step 7/9: Generating tailored resume... ✓
Step 8/9: Generating cover letter with culture fit examples... ✓

✓ Application complete! See: job-applications/Acme_Backend_Engineer/
```

---

## Command Summary Table

| Command | Purpose | Primary Tool | Async? |
|---------|---------|--------------|--------|
| `/career:process-website` | Add website to RAG | `rag_process_website` | Optional |
| `/career:query-websites` | Semantic search | `rag_query_websites` | No |
| `/career:list-websites` | View library | `rag_list_websites` | No |
| `/career:refresh-website` | Update stale content | `rag_refresh_website` | Optional |
| `/career:delete-website` | Remove website | `rag_delete_website` | No |

---

## Next Steps

1. **Create command files** in `.claude/commands/`
2. **Implement MCP tools** (prerequisite for commands)
3. **Test end-to-end workflow** with sample job postings
4. **Update `/career:apply`** to integrate RAG insights

**Related Files:**
- MCP Tools: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\contracts\mcp-tools.md`
- Data Model: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\data-model.md`
