---
description: Process a website URL into the RAG pipeline for semantic search (job postings, blogs, company pages)
allowed-tools: mcp__resume-agent__rag_process_website, mcp__resume-agent__rag_get_website_status
argument-hint: [url --type=TYPE --refresh]
---

# Process Website into RAG Pipeline

Arguments: $ARGUMENTS

## Purpose
Process website URLs (job postings, career blogs, company pages) into a searchable knowledge base using RAG (Retrieval Augmented Generation). The system extracts content, chunks it semantically, generates embeddings, and stores it for later semantic search.

## Process

### Step 1: Parse Arguments
Extract the following from $ARGUMENTS:
1. **URL**: Required - the website to process (must start with http:// or https://)
2. **--type**: Optional content type flag (job_posting|blog_article|company_page)
   - Default: job_posting
   - Example: `--type=blog_article`
3. **--refresh**: Optional flag to force re-processing
   - If present, re-process even if URL is already cached
   - Example: `--refresh`

Example parsing:
- Input: `https://japan-dev.com/jobs/acme/engineer --type=job_posting`
- Result: url="https://japan-dev.com/jobs/acme/engineer", content_type="job_posting", force_refresh=false

- Input: `https://blog.example.com/article --type=blog_article --refresh`
- Result: url="https://blog.example.com/article", content_type="blog_article", force_refresh=true

### Step 2: Call RAG Processing Tool
Execute the MCP tool to process the website:
```
result = mcp__resume-agent__rag_process_website(
    url=url,
    content_type=content_type,
    force_refresh=force_refresh
)
```

### Step 2.5: Store Vectors in Qdrant
If processing succeeded, store each chunk's vector in Qdrant for semantic search:
```
if result["status"] == "success" and "chunks_data" in result:
    for chunk_data in result["chunks_data"]:
        # Store in Qdrant (will generate 384-dim embeddings internally)
        mcp__qdrant-vectors__qdrant-store(
            information=chunk_data["content"],
            metadata=json.dumps(chunk_data["metadata"]),
            collection_name="resume-agent-chunks"
        )
```

**Note**: This step enables hybrid search (Qdrant vectors 70% + SQLite FTS 30%)

### Step 3: Handle Result

**If successful (status="success"):**
```
✓ Website processed successfully!

Source ID: {source_id}
URL: {url}
Title: {title}
Type: {content_type}
Language: {language}

Chunks created: {chunk_count}
Processing time: {processing_time_seconds}s

The content is now searchable via /career:query-websites
```

**If cached (status="cached"):**
```
✓ Website already processed

Source ID: {source_id}
Processing status: {processing_status}
Chunks: {chunk_count}

The content is already in the knowledge base.
To re-process, use: /career:process-website {url} --refresh
```

**If error (status="error"):**
```
✗ Failed to process website

Error: {error}

Common issues:
- Invalid URL format (must include http:// or https://)
- Network timeout or connection error
- Content too short or no extractable text
- Embedding generation failure

Please check the URL and try again.
```

### Step 4: Optional - Show What's Next

After successful processing, suggest next steps:
```
What's next?
1. Query the processed content:
   /career:query-websites "What are the key requirements?"

2. Check processing status:
   mcp__resume-agent__rag_get_website_status({source_id})

3. List all processed websites:
   /career:list-websites
```

## Content Type Guidance

**job_posting** (default):
- Job posting URLs from job boards
- Company career pages
- Individual job listings
- Optimized for: requirements, skills, responsibilities

**blog_article**:
- Career advice blogs
- Technical articles
- Interview preparation guides
- Optimized for: insights, tips, recommendations

**company_page**:
- Company about pages
- Culture/values pages
- Team pages
- Optimized for: company culture, values, work environment

## Error Handling

### URL Validation Errors:
- Missing protocol: Ask user to include http:// or https://
- Malformed URL: Show example of valid URL format

### Fetch Errors:
- 404 Not Found: URL doesn't exist or is no longer available
- Timeout: Website didn't respond within 30 seconds
- Connection error: Network issue or website is down

### Processing Errors:
- No content extracted: HTML may be empty or JavaScript-heavy (needs Playwright)
- Chunking failed: Content structure is unusual
- Embedding failed: Check dependencies are installed

### Cache Behavior:
- URL already processed → returns cached result (unless --refresh is used)
- Processing status tracked: pending → processing → completed/failed
- Failed processing can be retried with same URL

## Usage Examples

### Process a job posting (default):
```bash
/career:process-website https://japan-dev.com/jobs/acme/backend-engineer
```

### Process a blog article:
```bash
/career:process-website https://blog.gaijinpot.com/tech-jobs-japan/ --type=blog_article
```

### Force refresh of cached content:
```bash
/career:process-website https://old-url.com --refresh
```

### Process company culture page:
```bash
/career:process-website https://company.com/about/culture --type=company_page
```

## Performance Expectations

| Content Type | Processing Time | Notes |
|--------------|----------------|-------|
| Job posting | 8-15s | Includes fetch + chunk + embed |
| Blog article | 12-20s | Longer content = more chunks |
| Company page | 10-18s | Varies by page size |
| Cached URL | <1s | Instant return |

First-time use: Add +30s for model download (~420MB, one-time only).

## Important Notes

- Uses **MCP tool mcp__resume-agent__rag_process_website** for processing
- Stores data in SQLite database with vector embeddings (sqlite-vec)
- Supports English and Japanese content (multilingual model)
- Content is chunked semantically (preserves document structure)
- Hybrid search enabled (vector similarity + full-text search)
- All processed content is queryable via /career:query-websites
- Cache prevents duplicate processing (use --refresh to override)
