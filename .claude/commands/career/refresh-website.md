---
description: Refresh a processed website by re-fetching and re-processing its content
allowed-tools: mcp__resume-agent__rag_refresh_website, mcp__resume-agent__rag_get_website_status
argument-hint: [source_id]
---

# Refresh Processed Website

Arguments: $ARGUMENTS

## Purpose
Re-fetch and re-process a website that was previously processed into the RAG pipeline. This is useful when:
- Content has been updated (job posting changes, blog article edits)
- Processing failed and you want to retry
- Content is stale (>30 days old)
- You want to update chunking or embedding strategy

## Process

### Step 1: Parse Arguments
Extract the following from $ARGUMENTS:
1. **source_id**: Required - the database ID of the website source
   - Must be an integer
   - Get from `/career:list-websites` output
   - Example: `42`

Example parsing:
- Input: `42`
- Result: source_id=42

- Input: `source_id=42`
- Result: source_id=42

### Step 2: Get Current Website Info
First, check the website status to show what will be refreshed:
```
status_result = mcp__resume-agent__rag_get_website_status(source_id=source_id)
```

Display current info:
```
🔄 Refreshing Website

Source ID: {source_id}
URL: {url}
Title: {title}
Current status: {processing_status}
Current chunks: {chunk_count}
Last fetched: {days_ago} days ago

Proceeding with refresh...
```

### Step 3: Call Refresh Tool
Execute the MCP tool to refresh the website:
```
result = await mcp__resume-agent__rag_refresh_website(source_id=source_id)
```

**Note**: This is an async operation and may take 10-20 seconds.

### Step 4: Handle Result

**If successful (status="success" or status="completed"):**
```
✓ Website refreshed successfully!

Source ID: {source_id}
URL: {url}
Title: {title}

Old chunks: {old_chunk_count}
New chunks: {chunk_count}
Processing time: {processing_time_seconds}s

The updated content is now searchable via /career:query-websites
```

**If processing (status="processing"):**
```
⏳ Website refresh in progress

Source ID: {source_id}
URL: {url}

Processing started. This may take 10-20 seconds.

Check status with:
mcp__resume-agent__rag_get_website_status({source_id})
```

**If error (status="error"):**
```
✗ Failed to refresh website

Source ID: {source_id}
Error: {error}

Common issues:
- Website is no longer accessible (404, timeout)
- URL has moved or changed
- Network connectivity issues
- Processing failure (chunking, embedding)

You can try again or delete the website if it's no longer needed:
/career:delete-website {source_id}
```

### Step 5: Show Impact

After successful refresh, show the changes:
```
Changes:
- Chunks: {old_chunk_count} → {new_chunk_count} ({diff > 0: "+", diff < 0: "-"}{abs(diff)})
- Language: {old_language} → {new_language} {different: "(changed)"}
- Status: {old_status} → completed

{if new_chunk_count > old_chunk_count:}
More content was extracted this time. The website may have been updated.
{elif new_chunk_count < old_chunk_count:}
Less content was extracted. The website may have been simplified or restructured.
{else:}
Same amount of content extracted. No significant changes detected.
{endif}
```

## Confirmation Prompt (Optional)

For websites that are not stale (<30 days), consider asking for confirmation:
```
⚠️ This website was fetched {days_ago} days ago and may still be current.

Are you sure you want to refresh it? (yes/no)
```

If user says no, cancel the operation.

## Use Cases

### Refresh Stale Content (>30 days):
```bash
/career:list-websites --status=completed
# Shows: [42] Backend Engineer - Acme Corp (fetched 45 days ago) ⚠️ STALE
/career:refresh-website 42
```

### Retry Failed Processing:
```bash
/career:list-websites --status=failed
# Shows: [23] Career Tips Blog (failed: "Network timeout")
/career:refresh-website 23
```

### Update Recently Changed Content:
```bash
# Job posting was updated with new requirements
/career:refresh-website 15
```

### Re-process After Chunking Strategy Change:
```bash
# You updated chunking parameters and want to re-process
/career:refresh-website 8
```

## What Gets Updated

**Deleted:**
- All old chunks
- Old embeddings (website_chunks_vec)
- Old FTS entries (website_chunks_fts)

**Re-fetched:**
- HTML content (raw_html)
- Page title
- Language detection

**Re-generated:**
- Chunks (using current chunking strategy)
- Embeddings (using current embedding model)
- FTS indexing

**Preserved:**
- Source ID (stays the same)
- URL (stays the same)
- Original fetch_timestamp (updated to current time)

## Performance Expectations

| Content Type | Refresh Time | Notes |
|--------------|-------------|-------|
| Job posting | 8-15s | Full re-processing |
| Blog article | 12-20s | Longer content |
| Company page | 10-18s | Varies by size |
| Cached in memory | N/A | Full re-fetch required |

**Refresh always bypasses cache** (equivalent to force_refresh=true).

## Error Handling

### Website Not Found:
```
✗ Website source {source_id} not found

This source ID doesn't exist in the database.

List all websites:
/career:list-websites
```

### Fetch Failed:
```
✗ Failed to refresh website

Error: Failed to fetch URL: {reason}

Common reasons:
- 404 Not Found: Website no longer exists
- Timeout: Website didn't respond within 30s
- Connection error: Network issue or website is down
- Redirect: URL may have moved permanently

Consider deleting this website if it's permanently unavailable:
/career:delete-website {source_id}
```

### Processing Failed:
```
✗ Failed to refresh website

Error: {processing_error}

The website was fetched but processing failed.
This might indicate:
- Invalid HTML structure
- No extractable text content
- Embedding generation failure

Check the website manually or try again later.
```

## Important Notes

- Uses **MCP tool mcp__resume-agent__rag_refresh_website** for refresh operation
- Refresh is **destructive**: old chunks are permanently deleted
- Processing time: 8-20s depending on content size
- Refresh **always re-fetches** from the URL (no cache)
- Source ID remains the same (database record is reused)
- **Cannot undo** a refresh - old chunks are lost
- If refresh fails, old chunks are already deleted (website will need re-processing or deletion)

## Related Commands

- **List websites**: `/career:list-websites` (to find source IDs)
- **Check status**: `mcp__resume-agent__rag_get_website_status([source_id])`
- **Delete website**: `/career:delete-website [source_id]` (if refresh fails)
- **Query content**: `/career:query-websites "question"` (after refresh)
