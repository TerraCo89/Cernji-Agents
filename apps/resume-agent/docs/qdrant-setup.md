# Qdrant Vector Database Setup

This guide explains how to set up Qdrant for the RAG pipeline's vector search functionality.

## Overview

The Resume Agent uses **Qdrant** as the vector database for semantic search:
- **Qdrant**: Stores 384-dim vector embeddings for semantic search
- **SQLite**: Stores metadata, relationships, and FTS index
- **Hybrid Search**: Combines Qdrant vectors (70%) + SQLite FTS (30%)

## Prerequisites

- **Docker Desktop** (for Windows/Mac) or Docker Engine (for Linux)
- **UV package manager** (for running the Qdrant MCP server)

## Quick Start

### Step 1: Start Qdrant Docker Container

**Windows (PowerShell):**
```powershell
# Create data directory
New-Item -ItemType Directory -Force -Path "$PWD\data\qdrant_storage"

# Start Qdrant
docker run -d --name qdrant `
  -p 6333:6333 -p 6334:6334 `
  -v "$PWD\data\qdrant_storage:/qdrant/storage:z" `
  qdrant/qdrant
```

**Mac/Linux (Bash):**
```bash
# Create data directory
mkdir -p ./data/qdrant_storage

# Start Qdrant
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v $(pwd)/data/qdrant_storage:/qdrant/storage:z \
  qdrant/qdrant
```

### Step 2: Verify Qdrant is Running

Check if Qdrant is accessible:
```bash
# Test the API
curl http://localhost:6333

# Should return:
# {"title":"qdrant - vector search engine","version":"..."}
```

Or visit in browser: http://localhost:6333/dashboard

### Step 3: Verify MCP Configuration

The Qdrant MCP server should already be configured in `.mcp.json`:
```json
{
  "qdrant-vectors": {
    "command": "cmd",
    "args": ["/c", "uvx", "mcp-server-qdrant"],
    "env": {
      "QDRANT_URL": "http://localhost:6333",
      "COLLECTION_NAME": "resume-agent-chunks",
      "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2"
    }
  }
}
```

### Step 4: Test the Integration

Process a test URL and query:
```bash
# In Claude Code or Claude Desktop:
/career:process-website https://japan-dev.com/jobs/test/engineer

# Query the processed content:
/career:query-websites "What are the requirements?"
```

You should see semantic search results from Qdrant + FTS hybrid search.

## Docker Management

### Check Status
```bash
docker ps | findstr qdrant
```

### View Logs
```bash
docker logs qdrant
```

### Stop Qdrant
```bash
docker stop qdrant
```

### Start Existing Container
```bash
docker start qdrant
```

### Remove Container (WARNING: Deletes data!)
```bash
docker stop qdrant
docker rm qdrant
# To also delete data: Remove ./data/qdrant_storage directory
```

## Configuration

### Environment Variables (in .mcp.json)

**QDRANT_URL**
- Default: `http://localhost:6333`
- Use for local Docker container
- For Qdrant Cloud: `https://your-cluster.cloud.qdrant.io:6333`

**COLLECTION_NAME**
- Default: `resume-agent-chunks`
- Collection where vectors are stored
- Automatically created on first use

**EMBEDDING_MODEL**
- Default: `sentence-transformers/all-MiniLM-L6-v2`
- Must match the model used in `resume_agent.py`
- 384-dimensional embeddings

### Custom Collection

To use a different collection name (e.g., for testing):

1. Update `.mcp.json`:
```json
"env": {
  "COLLECTION_NAME": "test-chunks"
}
```

2. Update slash commands to reference the new collection

## Troubleshooting

### Issue: "Connection refused" to localhost:6333

**Symptoms:**
- Qdrant MCP tools fail
- Error message: "Cannot connect to Qdrant"

**Solution:**
```bash
# Check if Docker is running
docker ps

# Check if Qdrant container is running
docker ps | findstr qdrant

# If not running, start it:
docker start qdrant

# If container doesn't exist, create it (see Step 1)
```

### Issue: Port 6333 Already in Use

**Symptoms:**
- Docker fails to start: "port is already allocated"

**Solution:**
```bash
# Find what's using port 6333
netstat -ano | findstr :6333

# Kill the process or change Qdrant port:
docker run -d --name qdrant \
  -p 6335:6333 -p 6336:6334 \
  ... qdrant/qdrant

# Then update QDRANT_URL in .mcp.json to http://localhost:6335
```

### Issue: Qdrant Data Corrupted

**Symptoms:**
- Queries return no results
- Collection doesn't exist after restart

**Solution:**
```bash
# Stop and remove container
docker stop qdrant && docker rm qdrant

# Delete storage
rm -rf ./data/qdrant_storage  # Mac/Linux
Remove-Item -Recurse ./data/qdrant_storage  # Windows PowerShell

# Recreate container (see Step 1)
# Re-process all websites
/career:list-websites
# For each website:
/career:refresh-website [source_id]
```

### Issue: MCP Server Won't Start

**Symptoms:**
- Claude Code shows "qdrant-vectors: disconnected"
- Cannot use mcp__qdrant-vectors tools

**Solution:**
```bash
# Test uvx can run the server
uvx mcp-server-qdrant --version

# If not found, install:
pip install mcp-server-qdrant

# Restart Claude Code
```

### Issue: Slow Vector Search (>5s)

**Possible Causes:**
1. Large collection (>10K vectors)
2. Docker resource limits

**Solution:**
```bash
# Check collection size
curl http://localhost:6333/collections/resume-agent-chunks

# Increase Docker memory:
# Docker Desktop → Settings → Resources → Memory: 4GB+

# Or use Qdrant Cloud for production
```

## Qdrant Cloud (Optional)

For production use or if you don't want to run Docker:

### Setup

1. Create account at https://cloud.qdrant.io
2. Create a cluster (free tier: 1GB)
3. Get API key and cluster URL
4. Update `.mcp.json`:
```json
"env": {
  "QDRANT_URL": "https://xyz.cloud.qdrant.io:6333",
  "QDRANT_API_KEY": "your-api-key",
  "COLLECTION_NAME": "resume-agent-chunks"
}
```

### Advantages

✅ No Docker required
✅ Managed service (automatic backups, scaling)
✅ Better performance for large collections
✅ Accessible from multiple machines

### Trade-offs

⚠️ Network latency (vs localhost)
⚠️ Free tier limits (1GB storage, 100K vectors)
⚠️ Requires internet connection

## Architecture

### Data Flow

```
User Query
    ↓
resume_agent.py
    ↓
generate_embeddings() → 384-dim vector
    ↓
Parallel:
    ├─→ mcp__qdrant-vectors__qdrant-find (semantic search)
    └─→ SQLite FTS5 (keyword search)
    ↓
Hybrid Scoring (70% vector + 30% FTS)
    ↓
Ranked Results
```

### Storage Distribution

**Qdrant (vectors):**
- Vector embeddings (384-dim float arrays)
- Payload metadata: chunk_id, source_id, content_type, url

**SQLite (metadata):**
- website_sources: URL, title, status, fetch_timestamp
- website_chunks: content, char_count, metadata_json
- website_chunks_fts: Full-text search index

### Why Hybrid Storage?

✅ **Best tool for the job**: Qdrant for vectors, SQLite for relations
✅ **Performance**: Vector search is fast, FTS is fast
✅ **Flexibility**: Could swap Qdrant for Pinecone/Weaviate
✅ **Cost**: Qdrant Cloud free tier, SQLite is free

## Performance Expectations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Store vector in Qdrant | <50ms | Per chunk |
| Vector search (10K vectors) | <100ms | Qdrant HNSW index |
| FTS search | <50ms | SQLite FTS5 |
| Hybrid query (total) | <200ms | Combined |
| First query (cold start) | <1s | Model loading |

## Data Persistence

**Local Docker:**
- Data stored in: `./data/qdrant_storage/`
- Persists across restarts (via Docker volume)
- Backup: Copy the entire directory

**Qdrant Cloud:**
- Data stored in Qdrant's cloud
- Automatic backups
- Export: Use Qdrant API to download snapshots

## Next Steps

- ✅ Start Qdrant Docker
- ✅ Verify MCP connection
- → Process test URLs
- → Query with semantic search
- → Verify hybrid scoring works

For more information:
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **MCP Server**: https://github.com/qdrant/mcp-server-qdrant
- **Resume Agent README**: `apps/resume-agent/README.md`
