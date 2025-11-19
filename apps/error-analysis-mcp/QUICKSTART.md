# Error Analysis Agent - Quick Start Guide

Congratulations! You now have a complete **Error Analysis & Prevention Agent** that helps you understand and prevent recurring development errors.

## What We Built

### 1. Elasticsearch MCP Server (`apps/error-analysis-mcp/`)

**6 powerful tools** for querying your ELK stack:
- ✅ `search_errors` - Find errors by time/service/level
- ✅ `get_error_patterns` - Detect recurring patterns
- ✅ `get_error_context` - Get full error context via trace ID
- ✅ `analyze_error_trend` - Time-series analysis
- ✅ `compare_errors` - Compare two errors
- ✅ `health_check` - Verify Elasticsearch connection

### 2. Error Analyzer Skill (`.claude/skills/error-analyzer/`)

**Complete root cause analysis workflow** that:
- Classifies errors into 4 categories (docs, examples, agent scope, config)
- Searches ELK stack for patterns
- Searches knowledge base for previous solutions
- Generates immediate fixes + systemic improvements
- Creates Linear issues automatically
- Updates knowledge base for future reference

### 3. `/analyze-error` Slash Command

**Manual trigger** for analyzing errors during development.

## How to Use It

### Quick Test (5 minutes)

#### Step 1: Verify ELK Stack is Running

```bash
# Check Elasticsearch
curl http://localhost:9200

# Should return cluster info with version 9.2.1
```

#### Step 2: Test MCP Server

```bash
# Run the MCP server directly
uv run apps/error-analysis-mcp/error_analysis_mcp.py

# Should start without errors (press Ctrl+C to stop)
```

#### Step 3: Restart Claude Desktop/Code

The MCP server is already configured in `.mcp.json`, so just restart Claude Desktop to load it.

#### Step 4: Try the Slash Command

In a Claude Code session:

```
/analyze-error
Error: ModuleNotFoundError: No module named 'fastmcp'
Service: resume-agent
Context: Running job analysis workflow
```

The agent will:
1. ✅ Query ELK stack for similar errors
2. ✅ Search knowledge base
3. ✅ Classify root cause (likely: Configuration/Dependency)
4. ✅ Propose immediate fix (add to dependencies)
5. ✅ Create Linear issue for systemic improvement
6. ✅ Update knowledge base

### Real-World Usage

#### Scenario 1: Hit an Error During Development

```
You're working on a feature, and you get:

  TypeError: 'NoneType' object has no attribute 'invoke'

Instead of just fixing it, you want to understand WHY and prevent it:

1. Copy error details
2. Run: /analyze-error <paste error>
3. Agent analyzes:
   - Checks if this error has occurred before (ELK patterns)
   - Finds it happened 5 times this week (recurring!)
   - Classifies as "Documentation Gap" (missing null check docs)
   - Proposes:
     * Immediate: Add null check before .invoke()
     * Systemic: Create docs for safe LangGraph invocation patterns
     * Knowledge base: Store solution for next time
4. You apply fix + review Linear issue for systemic improvement
```

#### Scenario 2: Automatic Monitoring (Future - Phase 4)

```
Kibana detects: 20 errors/min in resume-agent (threshold: 10)

Automatic workflow:
1. Kibana → Webhook → Observability Server
2. Observability Server → Triggers Error Analysis Agent
3. Agent analyzes patterns via MCP tools
4. Agent creates Linear issue automatically
5. You get notification with analysis report
6. Review and approve fix
```

## What's Next?

### Phase 2: Test with Real Errors (This Week)

1. **Trigger some errors** (intentionally break something simple)
2. **Use `/analyze-error`** to test the workflow
3. **Verify Linear issues** are created correctly
4. **Check knowledge base** has entries

Example errors to test:
- Missing import: Remove a dependency
- Wrong API usage: Use sync instead of async
- Missing env var: Delete from .env

### Phase 3: Automatic Monitoring Setup (Next Week)

1. **Configure Kibana alerts** (see `docker/elk/kibana-alerts.md`)
2. **Extend observability server** to trigger agent
3. **Test automatic workflow** end-to-end

### Phase 4: Knowledge Base Growth (Ongoing)

As you use the system:
- Knowledge base grows with solutions
- Pattern recognition improves
- Recurring errors decrease
- Time to resolution decreases

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Your Development Workflow                   │
│  (Working in Claude Code, errors occur)                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴──────────┐
                │                      │
         Manual Trigger          Automatic Trigger
         /analyze-error          (ELK Alert)
                │                      │
                └───────────┬──────────┘
                            │
                            ▼
                ┌─────────────────────┐
                │ Error Analyzer Skill │
                └──────────┬───────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌─────────────┐
│ Error-Analysis│  │ Qdrant Vectors  │  │   Linear    │
│     MCP       │  │   Knowledge     │  │   Issues    │
│  (6 tools)    │  │     Base        │  │  Tracking   │
└───────┬───────┘  └────────┬────────┘  └──────┬──────┘
        │                   │                  │
        ▼                   ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌─────────────┐
│ Elasticsearch │  │   Solutions     │  │  Systemic   │
│  (ELK Stack)  │  │   Stored for    │  │Improvements │
│  Logs & Data  │  │  Future Reuse   │  │   Tracked   │
└───────────────┘  └─────────────────┘  └─────────────┘
```

## Files Created

- ✅ `apps/error-analysis-mcp/error_analysis_mcp.py` - MCP server (466 lines)
- ✅ `apps/error-analysis-mcp/README.md` - Documentation
- ✅ `apps/error-analysis-mcp/QUICKSTART.md` - This guide
- ✅ `.claude/skills/error-analyzer/skill.md` - Analysis workflow (560 lines)
- ✅ `.claude/commands/analyze-error.md` - Slash command
- ✅ `.mcp.json` - Updated with error-analysis server

## Configuration Checklist

- [x] Elasticsearch running on `http://localhost:9200`
- [x] MCP server created with 6 tools
- [x] MCP server configured in `.mcp.json`
- [x] Error analyzer skill created
- [x] `/analyze-error` slash command created
- [ ] Restart Claude Desktop to load MCP server
- [ ] Test with sample error
- [ ] Verify Linear integration works
- [ ] Verify knowledge base updates work

## Troubleshooting

### MCP Server Not Loading

**Check**:
```bash
# Verify UV is installed
uv --version

# Run server directly to see errors
uv run apps/error-analysis-mcp/error_analysis_mcp.py
```

**Fix**: Ensure UV dependencies are available (FastMCP, httpx)

### Elasticsearch Connection Failed

**Check**:
```bash
# Verify Elasticsearch is running
docker ps | grep elasticsearch
curl http://localhost:9200
```

**Fix**: Start ELK stack with `docker compose up -d` in `docker/elk/`

### No Errors Found in Search

**Check**:
```bash
# Verify logs are being indexed
curl "http://localhost:9200/_cat/indices/logs-*?v"
```

**Fix**: Ensure Filebeat is running and applications are logging correctly

## Tips for Best Results

1. **Be specific in error details**: Include service name, context, and full error message
2. **Check knowledge base first**: Agent searches automatically, but you can too
3. **Review Linear issues**: Don't just auto-create, ensure acceptance criteria make sense
4. **Update knowledge base**: If agent's solution works, mark it as verified
5. **Iterate on systemic improvements**: One error often reveals multiple improvements

## Support

- **MCP Server Issues**: See `apps/error-analysis-mcp/README.md`
- **Skill Workflow**: See `.claude/skills/error-analyzer/skill.md`
- **ELK Stack**: See `docker/elk/README.md` (if exists)
- **General**: Check `CLAUDE.md` for project structure

## Next Steps

Ready to use it! Here's what to do:

1. **Restart Claude Desktop** (to load the new MCP server)
2. **Trigger a test error** (or wait for real one during development)
3. **Run `/analyze-error`** with error details
4. **Review the analysis report**
5. **Check Linear** for created issue
6. **Verify knowledge base** has entry

Then, keep using it and watch your error rate decrease over time!

---

**Built**: 2025-11-17
**Phase**: 1 of 4 (Core Infrastructure) - ✅ COMPLETE
**Next Phase**: Automatic Monitoring Setup
