---
description: Delete a processed website and all its associated chunks from the RAG pipeline
allowed-tools: mcp__resume-agent__rag_delete_website, mcp__resume-agent__rag_get_website_status
argument-hint: [source_id] [--confirm]
---

# Delete Processed Website

Arguments: $ARGUMENTS

## Purpose
Permanently delete a website and all its associated chunks, embeddings, and FTS entries from the RAG pipeline. This is useful when:
- Website is no longer relevant
- Job posting is closed
- You want to clean up old content
- Website processing failed and cannot be recovered
- You want to free up database space

## ⚠️ WARNING: DESTRUCTIVE OPERATION

**This operation is irreversible!**
- All chunks will be permanently deleted
- All embeddings will be permanently deleted
- All FTS entries will be permanently deleted
- The website will need to be re-processed if you change your mind

## Process

### Step 1: Parse Arguments
Extract the following from $ARGUMENTS:
1. **source_id**: Required - the database ID of the website source
   - Must be an integer
   - Get from `/career:list-websites` output
   - Example: `42`
2. **--confirm**: Optional flag to skip confirmation prompt
   - If present, delete immediately without asking
   - Example: `--confirm`

Example parsing:
- Input: `42`
- Result: source_id=42, skip_confirm=false

- Input: `42 --confirm`
- Result: source_id=42, skip_confirm=true

### Step 2: Get Website Info
First, fetch the website details to show what will be deleted:
```
status_result = mcp__resume-agent__rag_get_website_status(source_id=source_id)
```

### Step 3: Confirmation Prompt

**If --confirm flag is NOT present:**
```
⚠️ DELETE CONFIRMATION

You are about to permanently delete:

Source ID: {source_id}
URL: {url}
Title: {title}
Type: {content_type}
Chunks: {chunk_count}
Fetched: {fetch_timestamp}

This will delete:
- {chunk_count} content chunks
- {chunk_count} vector embeddings
- {chunk_count} FTS index entries

⚠️ This action cannot be undone.

Are you sure you want to delete this website? (yes/no)
```

**Wait for user response:**
- If user says "yes" or "y" or "confirm" → proceed to Step 4
- If user says "no" or "n" or "cancel" → abort and show:
  ```
  ✗ Deletion cancelled

  Website {source_id} was not deleted.
  ```

**If --confirm flag IS present:**
Skip to Step 4 immediately (no prompt).

### Step 4: Call Delete Tool
Execute the MCP tool to delete the website:
```
result = mcp__resume-agent__rag_delete_website(source_id=source_id)
```

### Step 5: Handle Result

**If successful (status="success"):**
```
✓ Website deleted successfully

Source ID: {source_id}
URL: {url}
Title: {title}

Deleted:
- {chunks_deleted} content chunks
- {chunks_deleted} vector embeddings
- {chunks_deleted} FTS index entries

The website has been permanently removed from the RAG pipeline.

To re-add this website, use:
/career:process-website {url}
```

**If error (status="error"):**
```
✗ Failed to delete website

Error: {error}

Common issues:
- Website source {source_id} not found
- Database error
- Permission denied

Please check the source ID and try again.
List all websites:
/career:list-websites
```

### Step 6: Suggest Next Actions

After successful deletion:
```
What's next?
1. View remaining websites:
   /career:list-websites

2. Process a new website:
   /career:process-website [URL]

3. Query remaining content:
   /career:query-websites "question"
```

## Confirmation Bypass (--confirm flag)

Use the `--confirm` flag to skip the confirmation prompt:

```bash
/career:delete-website 42 --confirm
```

This is useful for:
- Scripting/automation
- Deleting multiple websites in sequence
- When you're absolutely sure

**Caution**: Always double-check the source ID before using `--confirm`.

## Use Cases

### Delete Closed Job Posting:
```bash
/career:list-websites --type=job_posting
# Shows: [42] Backend Engineer - Acme Corp (fetched 45 days ago)
# Job is now closed, no longer relevant
/career:delete-website 42
```

### Clean Up Failed Processing:
```bash
/career:list-websites --status=failed
# Shows: [23] Career Tips Blog (failed: "Invalid HTML")
# Cannot be recovered, delete to clean up
/career:delete-website 23 --confirm
```

### Remove Outdated Content:
```bash
# Old blog article from 2020, no longer relevant
/career:delete-website 15
```

### Free Up Database Space:
```bash
# Delete multiple old websites
/career:list-websites --limit=100
# Identify old/unwanted websites, then delete one by one
/career:delete-website 8 --confirm
/career:delete-website 12 --confirm
/career:delete-website 19 --confirm
```

## What Gets Deleted

**Permanently Removed:**
- Website source record (website_sources table)
- All content chunks (website_chunks table)
- All vector embeddings (website_chunks_vec table)
- All FTS index entries (website_chunks_fts table)
- All metadata (stored in source and chunks)

**Cascade Deletion:**
- Chunks are deleted via `ON DELETE CASCADE` foreign key
- FTS entries are deleted explicitly (if cascade doesn't handle it)
- Vector embeddings are deleted by chunk_id

**Not Affected:**
- Other websites in the database
- Query history (if implemented)
- Application-level caches

## Performance Expectations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Small website (<10 chunks) | <100ms | Fast deletion |
| Medium website (10-50 chunks) | <200ms | Quick deletion |
| Large website (50+ chunks) | <500ms | May take longer |

Deletion is **always fast** (< 1 second) regardless of content size.

## Error Handling

### Website Not Found:
```
✗ Website source {source_id} not found

This source ID doesn't exist in the database.

Possible reasons:
- Already deleted
- Invalid source ID
- Database inconsistency

List all websites:
/career:list-websites
```

### Database Error:
```
✗ Failed to delete website

Error: {database_error}

This indicates a database issue.
Please check the logs and try again.

If the issue persists, the database may need manual cleanup.
```

### Partial Deletion:
If deletion partially succeeds (chunks deleted but source remains):
```
⚠️ Partial deletion

Chunks were deleted, but the source record couldn't be removed.

The website will appear in /career:list-websites with 0 chunks.
You may need to manually clean up the database.

Contact support if this issue persists.
```

## Safety Features

**Confirmation Prompt:**
- Default behavior: always ask for confirmation
- Shows exactly what will be deleted
- User must explicitly confirm with "yes"

**No Batch Delete:**
- Can only delete one website at a time
- Prevents accidental bulk deletion
- Forces deliberate action

**Source ID Required:**
- Must specify exact source ID
- Cannot delete by URL (forces user to check /career:list-websites first)

**Audit Logging:**
- Deletion is logged (logger.info)
- Includes source ID, URL, and chunk count
- Helps with troubleshooting and audit trails

## Important Notes

- Uses **MCP tool mcp__resume-agent__rag_delete_website** for deletion
- Deletion is **irreversible** - no undo functionality
- Deletion is **fast** (<1 second for most websites)
- **Confirmation required** by default (unless --confirm flag used)
- Cascading deletion ensures all related data is removed
- Source ID is required (cannot delete by URL alone)
- **No batch delete** - must delete one at a time for safety

## Related Commands

- **List websites**: `/career:list-websites` (to find source IDs)
- **Check status**: `mcp__resume-agent__rag_get_website_status([source_id])` (verify before delete)
- **Refresh website**: `/career:refresh-website [source_id]` (alternative to delete+re-add)
- **Process new website**: `/career:process-website [URL]` (to re-add after deletion)
