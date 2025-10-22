---
description: Perform semantic search across all processed websites (job postings, blogs, company pages)
allowed-tools: mcp__resume-agent__rag_query_websites, mcp__qdrant-vectors__qdrant-find
argument-hint: [query --type=TYPE --limit=N --synthesize]
---

# Query Processed Websites

Arguments: $ARGUMENTS

## Purpose
Perform **hybrid search** across all websites you've processed into the RAG pipeline. Combines semantic vector search (Qdrant) with keyword matching (SQLite FTS) for optimal results. Ask natural language questions and get ranked results with source citations.

## Process

### Step 1: Parse Arguments
Extract the following from $ARGUMENTS:
1. **Query**: Required - the question or search terms
   - Can be a natural language question: "What are the key requirements?"
   - Can be keywords: "Python backend senior"
2. **--limit**: Optional max results (default: 10, max: 20)
   - Example: `--limit=5`
3. **--type**: Optional content type filter
   - Values: job_posting|blog_article|company_page
   - Example: `--type=job_posting`
4. **--synthesize**: Optional flag to generate AI summary
   - Example: `--synthesize`

Example parsing:
- Input: `What skills are required? --limit=5`
- Result: query="What skills are required?", max_results=5

- Input: `company culture --type=company_page --synthesize`
- Result: query="company culture", content_type_filter="company_page", include_synthesis=true

### Step 2: Execute Hybrid Search

**Hybrid search combines:**
- **Qdrant vector search (70% weight)**: Semantic similarity via embeddings
- **SQLite FTS search (30% weight)**: Keyword matching

**Step 2a: Perform Vector Search (Qdrant)**
```python
# Get semantic matches from Qdrant
vector_results = mcp__qdrant-vectors__qdrant-find(
    query=query,
    collection_name="resume-agent-chunks",
    limit=max_results * 2  # Get more candidates for merging
)
```

**Step 2b: Perform Keyword Search (FTS)**
```python
# Get keyword matches from SQLite FTS
fts_result = mcp__resume-agent__rag_query_websites(
    query=query,
    max_results=max_results * 2,
    content_type_filter=content_type_filter,
    include_synthesis=False  # We'll synthesize after merging
)
```

**Step 2c: Merge and Score Results**
```python
import json

# Build a map of chunk_id -> result for deduplication
merged = {}

# Process vector results (70% weight)
for vec_result in vector_results.get("results", []):
    metadata = json.loads(vec_result["metadata"])
    chunk_id = metadata["chunk_id"]

    # Normalize Qdrant score (higher is better, 0-1 range)
    # Convert to 0-100 scale for consistency with FTS
    vector_score = vec_result["score"] * 100

    merged[chunk_id] = {
        "chunk_id": chunk_id,
        "content": vec_result["information"],
        "metadata": metadata,
        "vector_score": vector_score,
        "fts_score": 0.0,
        "combined_score": 0.0
    }

# Process FTS results (30% weight)
for fts_result in fts_result.get("results", []):
    chunk_id = fts_result["chunk_id"]

    # Normalize FTS score (lower is better, convert to 0-100 scale)
    # FTS ranks use negative log, normalize to 0-100 where 100 is best match
    fts_score = max(0, 100 - (fts_result["fts_rank"] * 10))

    if chunk_id in merged:
        # Update existing entry from vector search
        merged[chunk_id]["fts_score"] = fts_score
    else:
        # Add FTS-only result
        merged[chunk_id] = {
            "chunk_id": chunk_id,
            "content": fts_result["content"],
            "metadata": fts_result["metadata"],
            "vector_score": 0.0,
            "fts_score": fts_score,
            "combined_score": 0.0
        }

# Calculate combined scores (70% vector + 30% FTS)
for result in merged.values():
    result["combined_score"] = (result["vector_score"] * 0.7) + (result["fts_score"] * 0.3)

# Sort by combined score (highest first) and limit results
final_results = sorted(merged.values(), key=lambda x: x["combined_score"], reverse=True)[:max_results]

# Apply content type filter if specified
if content_type_filter:
    final_results = [r for r in final_results if r["metadata"].get("content_type") == content_type_filter]

# Build result object
result = {
    "status": "success",
    "total_results": len(final_results),
    "confidence": "high" if final_results and final_results[0]["combined_score"] > 70 else "medium" if final_results else "low",
    "results": final_results,
    "processing_time_ms": 0  # Placeholder
}
```

**Step 2d: Generate Synthesis (if requested)**
```python
if include_synthesis and final_results:
    # Use Claude to synthesize insights from results
    synthesis_prompt = f"""Based on these search results for "{query}", provide a concise 2-3 sentence summary:

{chr(10).join([f"- {r['content'][:200]}..." for r in final_results[:5]])}"""

    # Call Claude for synthesis (implementation depends on available tools)
    result["synthesis"] = "Synthesis feature coming soon"
```

### Step 3: Display Results

**If successful (status="success"):**

Format the results clearly with source citations and hybrid scores:

```
Search Results for: "{query}"

Found {total_results} matches | Confidence: {confidence_level}
Hybrid Search: Vector (70%) + Keyword (30%)

---

1. [Score: {combined_score:.1f}] {metadata['url']}
   Vector: {vector_score:.1f} | Keyword: {fts_score:.1f}
   Section: {metadata.get('Header_2') or metadata.get('Header_1') or "Main Content"}

   "{content[:300]}..."

   Source: {metadata['url']}

2. [Score: {combined_score:.1f}] {metadata['url']}
   Vector: {vector_score:.1f} | Keyword: {fts_score:.1f}
   ...

---

{synthesis if include_synthesis}

Next steps:
- Narrow search: /career:query-websites "{query}" --type=job_posting
- Process more content: /career:process-website [url]
- View all processed: /career:list-websites
```

**Score Interpretation:**
- **Combined Score**: 0-100 (higher is better)
  - 70-100: Excellent match (high confidence)
  - 50-70: Good match (medium confidence)
  - <50: Weak match (low confidence)
- **Vector Score**: Semantic similarity (0-100)
- **Keyword Score**: Exact term matching (0-100)

**If no results (total_results=0):**
```
No results found for: "{query}"

Possible reasons:
- No websites processed yet
- Query terms don't match any content
- Try broader search terms

To process content:
/career:process-website [url]

To see what's in your library:
/career:list-websites
```

**If error (status="error"):**
```
✗ Query failed

Error: {error}

Common issues:
- Query too short (minimum 3 characters)
- Invalid max_results (must be 1-20)
- Database connection error

Please check your query and try again.
```

### Step 4: Format Metadata Intelligently

When displaying results, extract useful metadata:
- **Header 1/2/3**: Show document structure (section names)
- **split_method**: Indicates how chunk was created
- **content_type**: Show if filtering would help

Example metadata display:
```
Section: Requirements > Technical Skills
Type: job_posting
```

## Query Types & Examples

### Natural Language Questions
```bash
/career:query-websites "What are the key requirements for backend engineers?"
/career:query-websites "How does the company describe their culture?"
/career:query-websites "What salary ranges are mentioned?"
```

### Keyword Search
```bash
/career:query-websites "Python FastAPI PostgreSQL"
/career:query-websites "remote work visa sponsorship"
/career:query-websites "interview preparation tips"
```

### Filtered Queries
```bash
# Only job postings
/career:query-websites "requirements" --type=job_posting

# Only blog articles
/career:query-websites "interview tips" --type=blog_article --limit=5

# Company pages with synthesis
/career:query-websites "company values" --type=company_page --synthesize
```

## Understanding Results

### Score Interpretation
- **Higher combined scores = better match** (0-100 scale)
- **Combined Score** = (Vector Score × 0.7) + (FTS Score × 0.3)
- Scores 70-100 = High confidence (excellent semantic + keyword match)
- Scores 50-70 = Medium confidence (good match)
- Scores < 50 = Low confidence (weak match)

### Score Components
- **Vector Score**: Semantic similarity via embeddings (how conceptually related)
- **Keyword Score**: Exact term matching via FTS (how many query terms appear)

### Source Citations
Every result includes:
- **source_url**: Original website URL (click to verify)
- **metadata**: Document structure context
- **content**: Relevant text excerpt

### Confidence Levels
- **High**: Top result is very relevant
- **Medium**: Results are somewhat relevant
- **Low**: No results or weak matches

## Performance Expectations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Hybrid query | 200-500ms | Qdrant vector + FTS in parallel |
| Filtered query | 300-700ms | Additional content type filtering |
| With synthesis | 3-8s | +AI summary generation |
| Empty index | <50ms | Instant (no results) |
| Cold start (first query) | <1s | Model loading (one-time) |

## Tips for Better Results

### Be Specific
❌ Bad: "requirements"
✅ Good: "What are the required technical skills for this role?"

### Use Filters
```bash
# Instead of broad search across everything
/career:query-websites "Python"

# Narrow to job postings only
/career:query-websites "Python" --type=job_posting
```

### Limit Results for Speed
```bash
# Get top 3 most relevant results quickly
/career:query-websites "salary range" --limit=3
```

### Try Synthesis for Insights
```bash
# Get AI-generated summary of findings
/career:query-websites "company culture" --synthesize
```

## Workflow Integration

### Research Phase
1. Process multiple job postings:
   ```bash
   /career:process-website [url1]
   /career:process-website [url2]
   /career:process-website [url3]
   ```

2. Compare requirements:
   ```bash
   /career:query-websites "What skills are commonly required?" --type=job_posting
   ```

### Application Phase
1. Query specific company:
   ```bash
   /career:query-websites "Acme Corp culture and values"
   ```

2. Use insights in cover letter:
   ```bash
   /career:apply [job-url]
   # System automatically incorporates RAG insights
   ```

## Error Handling

### Query Too Short
```
✗ Query must be at least 3 characters long
```
Solution: Use more descriptive search terms

### Invalid Limit
```
✗ max_results must be between 1 and 20
```
Solution: Use `--limit=N` where N is 1-20

### No Content Processed
```
No results found - no websites processed yet
```
Solution: Process websites first with `/career:process-website`

### Database Error
```
✗ Database connection error
```
Solution: Ensure database is initialized with migration script

## Important Notes

- Uses **hybrid search** (Qdrant vector similarity 70% + SQLite FTS keyword matching 30%)
- All results include **source citations** (100% of the time per FR-006)
- Results are ranked by combined score (best matches first)
- Supports **content type filtering** (job_posting, blog_article, company_page)
- Query performance: <500ms for most searches (meets FR performance target)
- Results are read-only (doesn't modify processed content)
- Safe to run repeatedly (queries are non-destructive)
- **Requires Qdrant Docker container running** (see apps/resume-agent/docs/qdrant-setup.md)
