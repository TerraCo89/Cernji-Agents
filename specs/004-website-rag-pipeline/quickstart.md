# Quickstart: Website RAG Pipeline

**Feature**: 004-website-rag-pipeline
**Estimated Setup Time**: 15 minutes
**Last Updated**: 2025-10-22

## What You'll Build

A RAG (Retrieval Augmented Generation) pipeline that:
- ✅ Processes job postings, career blogs, and company pages
- ✅ Performs semantic search across all processed content
- ✅ Enhances resume/cover letter generation with company-specific insights
- ✅ Supports English and Japanese text

## Prerequisites

- Existing Resume Agent setup (from `QUICKSTART.md`)
- Python 3.10+ with UV package manager
- ~1GB disk space (for embedding models)

---

## 5-Minute Quick Start

### Step 1: Install Dependencies (2 min)

Add RAG dependencies to `apps/resume-agent/resume_agent.py`:

```python
# /// script
# dependencies = [
#   "fastmcp>=2.0",
#   "pyyaml>=6.0",
#   "httpx>=0.28.0",
#   "sqlmodel>=0.0.22",
#   "python-dotenv>=1.0.0",
#   # NEW: RAG Pipeline
#   "sentence-transformers>=3.0.0",
#   "sqlite-vec>=0.1.0",
#   "langchain-text-splitters>=0.3.0",
# ]
# requires-python = ">=3.10"
# ///
```

**First Run**: Downloads `paraphrase-multilingual-MiniLM-L12-v2` model (~420MB, one-time)

```bash
uv run apps/resume-agent/resume_agent.py
```

### Step 2: Create Database Tables (1 min)

Run migration script:

```bash
uv run apps/resume-agent/scripts/create_rag_tables.py
```

**Output:**
```
✓ Created table: website_sources
✓ Created table: website_chunks
✓ Created virtual table: website_chunks_vec
✓ Created virtual table: website_chunks_fts
✓ Created indexes (4)
Database ready: D:\source\Cernji-Agents\data\resume_agent.db
```

### Step 3: Process Your First Website (1 min)

```bash
# In Claude Desktop (with Resume Agent MCP server running)
/career:process-website https://japan-dev.com/jobs/anthropic/backend-engineer
```

**Output:**
```
✓ Processing complete!

Source ID: 1
Chunks Created: 8
Language: English
Processing Time: 11.2s
```

### Step 4: Query Processed Content (1 min)

```bash
/career:query-websites "What are the key requirements for this backend engineer role?"
```

**Output:**
```
Top Results (3):

1. [Score: 0.18] Backend Engineer - Anthropic
   Section: Requirements > Technical Skills
   "5+ years Python, FastAPI. Experience with LLMs and RAG pipelines..."

2. [Score: 0.24] Backend Engineer - Anthropic
   Section: What We're Looking For
   "Strong CS fundamentals. Distributed systems experience..."

3. [Score: 0.31] Backend Engineer - Anthropic
   Section: Nice to Have
   "Japanese language skills. Experience with Claude API..."

Confidence: High | Processing Time: 1.4s
```

**Done!** 🎉 You now have a working RAG pipeline.

---

## Common Use Cases

### Use Case 1: Enhance Job Application Workflow

**Scenario**: You're applying to a job and want company-specific insights.

```bash
# Step 1: Process the job posting
/career:process-website https://japan-dev.com/jobs/acme/backend-engineer

# Step 2: Search for company culture info
/career:query-websites "What is Acme's company culture and values?"

# Step 3: Use insights in your application
/career:apply https://japan-dev.com/jobs/acme/backend-engineer
# (Automatically uses RAG insights in resume/cover letter)
```

### Use Case 2: Research Jobs in Japan

**Scenario**: You want to learn about visa requirements and interviewing in Japan.

```bash
# Process several blog articles
/career:process-website https://blog.gaijinpot.com/tech-jobs-japan/ --type=blog_article
/career:process-website https://www.tokyodev.com/articles/visa-guide --type=blog_article

# Query across all articles
/career:query-websites "What visa do I need for software engineering jobs in Japan?" --type=blog_article --synthesize
```

**Output (with AI synthesis):**
```
Based on 2 processed articles:

For software engineering roles in Japan, you typically need a **Highly Skilled Professional visa (HSP)**
or **Engineer/Specialist visa**. Key points:

1. Requirements:
   - Bachelor's degree in CS or 10+ years experience
   - Job offer from Japanese company
   - Salary threshold: ~3.5M JPY/year (lower for HSP visa)

2. Application Process:
   - Company sponsors your visa (Certificate of Eligibility)
   - Processing time: 1-3 months
   - Can start working after visa approval

3. Benefits of HSP Visa:
   - Fast-track permanent residency (1-3 years vs 10 years)
   - Spouse can work without separate visa
   - Bring parents/domestic helpers (with conditions)

Sources:
- https://blog.gaijinpot.com/tech-jobs-japan/ (Section: "Visa Requirements")
- https://www.tokyodev.com/articles/visa-guide (Section: "Engineer Visa vs HSP")
```

### Use Case 3: Compare Multiple Job Postings

```bash
# Process multiple jobs
/career:process-website https://japan-dev.com/jobs/company-a/backend
/career:process-website https://japan-dev.com/jobs/company-b/backend
/career:process-website https://japan-dev.com/jobs/company-c/backend

# Compare requirements
/career:query-websites "What are the common requirements across backend engineer roles?" --synthesize

# Compare culture
/career:query-websites "Which companies emphasize work-life balance?"
```

---

## Full Workflow Example

### End-to-End: Apply to a Job with RAG Insights

**Goal**: Apply to a Backend Engineer role at "Acme Corp" with tailored materials.

```bash
# 1. Process the job posting
/career:process-website https://japan-dev.com/jobs/acme/backend-engineer

# 2. Research the company
/career:process-website https://acme.com/about/culture --type=company_page
/career:query-websites "What does Acme value in their engineering culture?"

# Output:
# "Acme emphasizes collaboration, innovation, and continuous learning.
#  They offer 2-3 days remote work per week and invest heavily in
#  professional development. English is the primary language."

# 3. Search for relevant blog advice
/career:process-website https://blog.example.com/how-to-interview-at-acme --type=blog_article
/career:query-websites "Tips for interviewing at Acme" --type=blog_article

# 4. Generate tailored application
/career:apply https://japan-dev.com/jobs/acme/backend-engineer

# The RAG pipeline automatically:
# - Identifies key requirements from the job posting
# - Incorporates company culture insights into cover letter
# - Uses blog advice to highlight relevant achievements
```

**Result**: Application materials that feel personalized and well-researched.

---

## Command Reference

### Processing Commands

```bash
# Process a website
/career:process-website [URL] [--type=TYPE] [--refresh]

# Types:
#   job_posting   (default)
#   blog_article
#   company_page

# Examples:
/career:process-website https://japan-dev.com/jobs/acme/backend
/career:process-website https://blog.com/article --type=blog_article
/career:process-website https://old-url.com --refresh
```

### Query Commands

```bash
# Semantic search
/career:query-websites [QUERY] [--type=TYPE] [--limit=N] [--synthesize]

# Examples:
/career:query-websites "What are the requirements?"
/career:query-websites "Company culture" --synthesize
/career:query-websites "Interview tips" --type=blog_article --limit=5
```

### Management Commands

```bash
# List processed websites
/career:list-websites [--type=TYPE] [--status=STATUS]

# Refresh a website
/career:refresh-website [SOURCE_ID]

# Delete a website
/career:delete-website [SOURCE_ID]
```

---

## Performance Expectations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Process job posting | 8-15s | First time (includes embedding) |
| Process cached URL | <1s | Instant cache hit |
| Process blog article | 12-20s | Longer due to more content |
| Semantic query | 1-3s | Includes ranking and formatting |
| Query with synthesis | 3-8s | +AI summary generation |
| List websites | <500ms | Database query |

**First Run**: Add +30s for model download (~420MB, one-time only).

---

## Troubleshooting

### Issue: "Model download failed"

**Symptom**: Error during first run: `Failed to download paraphrase-multilingual-MiniLM-L12-v2`

**Solution**:
```bash
# Manual download
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"

# Model cached to: ~/.cache/torch/sentence_transformers/
```

### Issue: "sqlite-vec extension not found"

**Symptom**: `Error: sqlite-vec extension could not be loaded`

**Solution**:
```bash
# Reinstall sqlite-vec
uv pip install --force-reinstall sqlite-vec>=0.1.0

# Verify
python -c "import sqlite_vec; print(sqlite_vec.__version__)"
```

### Issue: "Processing takes >30s"

**Symptom**: Job posting processing exceeds 15s target

**Possible Causes**:
1. **Large webpage**: Blog articles with lots of content
2. **Slow network**: Playwright fetch timeout
3. **CPU-bound**: Embedding generation on slow CPU

**Solutions**:
```bash
# Use async processing (returns immediately)
/career:process-website [URL] --async

# Check status later
/career:get-website-status [SOURCE_ID]

# Or: Process in smaller batches (for blogs)
# The chunking strategy will automatically split large content
```

### Issue: "Query returns irrelevant results"

**Symptom**: Semantic search returns off-topic chunks

**Possible Causes**:
1. Query too vague
2. Not enough processed content
3. Language mismatch (English query on Japanese content)

**Solutions**:
```bash
# Be more specific
❌ /career:query-websites "requirements"
✅ /career:query-websites "What are the key technical requirements for backend engineer roles in Tokyo?"

# Filter by content type
/career:query-websites "company culture" --type=company_page

# Use synthesis for better context
/career:query-websites "interview tips" --synthesize
```

---

## What's Next?

### Phase 1 (Completed)
✅ Vector embeddings with sentence-transformers
✅ Hybrid search (vector + FTS)
✅ MCP tools and slash commands
✅ English + Japanese support

### Phase 2 (Future)
- [ ] Reranking with CrossEncoder (improved precision)
- [ ] Auto-refresh stale content (>30 days)
- [ ] Multi-source synthesis (combine insights from 5+ sources)
- [ ] Export RAG insights to markdown report

### Phase 3 (Future)
- [ ] Browser extension for one-click processing
- [ ] Automatic job board monitoring
- [ ] Collaborative library (share processed content)

---

## Useful Resources

- **Feature Spec**: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\spec.md`
- **Data Model**: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\data-model.md`
- **MCP Tools**: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\contracts\mcp-tools.md`
- **Research Decisions**: `D:\source\Cernji-Agents\specs\004-website-rag-pipeline\research.md`

---

## Feedback & Support

- **Issues**: Report at https://github.com/anthropics/claude-code/issues
- **Discussions**: Join the Cernji-Agents community
- **Feature Requests**: Submit via `/speckit.specify`

---

**Need Help?** Run `/help` in Claude Desktop or check the troubleshooting section above.
