---
description: List all processed websites in the RAG pipeline with filtering and pagination
allowed-tools: mcp__resume-agent__rag_list_websites
argument-hint: [--type=TYPE] [--status=STATUS] [--limit=N]
---

# List Processed Websites

Arguments: $ARGUMENTS

## Purpose
View all websites that have been processed into the RAG pipeline knowledge base, with filtering by content type, processing status, and pagination support. Shows staleness warnings for content older than 30 days.

## Process

### Step 1: Parse Arguments
Extract the following from $ARGUMENTS:
1. **--type**: Optional content type filter (job_posting|blog_article|company_page)
   - Example: `--type=blog_article`
2. **--status**: Optional status filter (pending|processing|completed|failed)
   - Example: `--status=completed`
3. **--limit**: Optional result limit (default: 20)
   - Example: `--limit=50`
4. **--offset**: Optional pagination offset (default: 0)
   - Example: `--offset=20`
5. **--order-by**: Optional sort order (fetch_timestamp|title|content_type, default: fetch_timestamp)
   - Example: `--order-by=title`

Example parsing:
- Input: `--type=blog_article --status=completed`
- Result: content_type="blog_article", status="completed", limit=20, offset=0

- Input: `--limit=50 --offset=50`
- Result: content_type=None, status=None, limit=50, offset=50 (page 2)

### Step 2: Call Listing Tool
Execute the MCP tool to list websites:
```
result = mcp__resume-agent__rag_list_websites(
    content_type=content_type,
    status=status,
    limit=limit,
    offset=offset,
    order_by=order_by or "fetch_timestamp"
)
```

### Step 3: Format Output

**If successful (status="success"):**
```
📚 Processed Websites ({returned_count} of {total_count})

{for each website:}
[{source_id}] {title}
URL: {url}
Type: {content_type} | Language: {language} | Status: {processing_status}
Chunks: {chunk_count} | Fetched: {days_old} days ago {is_stale: "⚠️ STALE"}
{if error_message: "Error: {error_message}"}

---

Summary:
- Total websites: {total_count}
- Showing: {returned_count}
- Stale content (>30 days): {stale_count}

{if pagination.has_more:}
To see more results, use: /career:list-websites --offset={offset + limit}
{endif}
```

**Staleness Warning:**
If any websites are stale (>30 days):
```
⚠️ {stale_count} websites have stale content (>30 days old)

Stale content may be outdated. Consider refreshing:
/career:refresh-website [source_id]
```

**If empty list:**
```
📚 No processed websites found

{if filters applied:}
No websites match your filters:
- Content type: {content_type}
- Status: {status}

Try removing filters or process a new website:
/career:process-website [URL]
{else:}
No websites have been processed yet.

Get started:
/career:process-website https://japan-dev.com/jobs/company/role
{endif}
```

**If error (status="error"):**
```
✗ Failed to list websites

Error: {error}

This might indicate a database issue. Please check the logs.
```

### Step 4: Suggest Next Actions

After showing the list:
```
What's next?
1. View specific website details:
   mcp__resume-agent__rag_get_website_status([source_id])

2. Refresh stale content:
   /career:refresh-website [source_id]

3. Delete unwanted websites:
   /career:delete-website [source_id]

4. Query processed content:
   /career:query-websites "your question"
```

## Filtering Examples

### Show only job postings:
```bash
/career:list-websites --type=job_posting
```

### Show only completed processing:
```bash
/career:list-websites --status=completed
```

### Show failed processing (for troubleshooting):
```bash
/career:list-websites --status=failed
```

### Pagination (next 20 results):
```bash
/career:list-websites --offset=20
```

### Show more results per page:
```bash
/career:list-websites --limit=50
```

### Sort by title:
```bash
/career:list-websites --order-by=title
```

### Combine filters:
```bash
/career:list-websites --type=blog_article --status=completed --limit=10
```

## Output Formatting Tips

**For each website, show:**
- Source ID (for reference in other commands)
- Title (or URL if no title)
- Content type icon: 💼 (job), 📝 (blog), 🏢 (company)
- Processing status icon: ✅ (completed), ⏳ (processing), ❌ (failed), ⏸️ (pending)
- Staleness indicator: ⚠️ (>30 days)
- Chunk count (indicates content size)
- Days since fetched (for staleness awareness)

**Example formatted entry:**
```
[42] 💼 Backend Engineer - Acme Corp ✅
URL: https://japan-dev.com/jobs/acme/backend-engineer
Type: job_posting | Language: English | Status: completed
Chunks: 8 | Fetched: 5 days ago
```

**Example stale entry:**
```
[23] 📝 Career Tips for Japan ⚠️ STALE
URL: https://blog.example.com/career-tips-japan
Type: blog_article | Language: Mixed (EN/JA) | Status: completed
Chunks: 15 | Fetched: 45 days ago
```

## Staleness Detection (FR-017)

**Threshold**: 30 days
**Logic**: Compare fetch_timestamp with current date
**Action**: Mark as "is_stale" and suggest refresh

**Staleness Reasons:**
- Job postings may be closed or updated
- Blog articles may have new content
- Company pages may reflect new culture/values

## Pagination Support (FR-016)

**Default Behavior:**
- Limit: 20 results per page
- Offset: 0 (first page)
- Order: Most recent first (fetch_timestamp DESC)

**Navigation:**
- Next page: `--offset=20` (or current offset + limit)
- Previous page: `--offset=0` (or current offset - limit)
- Larger pages: `--limit=50`

**Pagination Response:**
```
pagination: {
    limit: 20,
    offset: 0,
    has_more: true  // More results available
}
```

## Performance Expectations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| List (no filter) | <500ms | Database query |
| List (with filter) | <300ms | Indexed queries |
| List (large result set) | <1s | Pagination helps |

## Important Notes

- Uses **MCP tool mcp__resume-agent__rag_list_websites** for data retrieval
- Staleness threshold: 30 days (configurable in future)
- Default sort: Most recent first (fetch_timestamp DESC)
- Supports pagination for large libraries (100+ websites)
- Shows chunk count to indicate content size
- Error messages for failed processing help troubleshooting
- Source IDs are needed for refresh/delete operations

## Related Commands

- **Process new website**: `/career:process-website [URL]`
- **Query content**: `/career:query-websites "question"`
- **Refresh website**: `/career:refresh-website [source_id]`
- **Delete website**: `/career:delete-website [source_id]`
