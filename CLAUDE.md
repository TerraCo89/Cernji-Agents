# Career Application Assistant

## Purpose
This project helps me tailor resumes and generate cover letters for job applications using AI agents.

**Architecture**: MCP (Model Context Protocol) server exposing career tools to Claude Desktop and other MCP clients.

## Quick Start

**Start the MCP server:**
```bash
uv run apps/resume-agent/resume_agent.py
```

Then configure Claude Desktop (see [QUICKSTART.md](QUICKSTART.md))

## Project Structure

**Architecture**: Multi-app monorepo with isolated applications in `apps/` directory

### Applications

- **[apps/resume-agent/](apps/resume-agent/)** - Career application MCP server
  - Single-file MCP server (UV + FastMCP + Claude Agent SDK)
  - Tech Stack: Python 3.10+, UV (Astral), FastMCP 2.0, Claude Agent SDK, sentence-transformers, sqlite-vec, langchain-text-splitters
  - Features: Job analysis, Resume tailoring, Cover letter generation, **RAG pipeline for website processing**
  - Transport: HTTP Streamable (port 8080)

- **[apps/resume-agent-langgraph/](apps/resume-agent-langgraph/)** - LangGraph Resume Agent (Experimental)
  - Conversational agent powered by LangGraph
  - Tech Stack: Python 3.11+, LangGraph, Anthropic/OpenAI SDK
  - Features: Real-time chat interface, state management, multi-provider LLM support
  - Deployment: LangGraph dev server (port 2024) with Studio UI
  - Status: Development - evaluating LangGraph for production use

- **[apps/agent-chat-ui/](apps/agent-chat-ui/)** - Web UI for LangGraph Resume Agent
  - Real-time chat interface for Resume Agent
  - Tech Stack: Next.js 15, React 19, TypeScript, TailwindCSS, LangGraph SDK
  - Features: Streaming responses, message history, dark mode
  - Port: 3000
  - See: [SETUP.md](apps/agent-chat-ui/SETUP.md)

- **[apps/observability-server/](apps/observability-server/)** - Event tracking server
  - Real-time event collection via HTTP POST
  - WebSocket broadcasting to connected clients
  - Tech Stack: Bun, TypeScript, SQLite (WAL mode)

- **[apps/client/](apps/client/)** - Web dashboard for observability
  - Real-time event monitoring
  - Filter by app, session, event type
  - Tech Stack: Vue 3, Vite, TailwindCSS

### Documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[README-MCP-SERVER.md](README-MCP-SERVER.md)** - Complete feature guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[library-docs/](library-docs/)** - Claude Code & Agent SDK references

## Development Practices

### Testing After Code Changes

**IMPORTANT**: After making any functional code changes, ALWAYS run the validation workflow to catch issues before committing.

**Quick validation** (< 30 seconds):
```bash
# Syntax + import check
python -m compileall -q . && pytest --collect-only -q

# Or use the validation script
.\scripts\validate-changes.ps1  # Windows
./scripts/validate-changes.sh   # Linux/macOS
```

**When to validate**:
- After moving/renaming files or modules
- After refactoring imports
- After changing dependencies
- After any code changes that could break functionality

**Validation checks**:
1. Python syntax validation
2. Import validation (static analysis with ruff)
3. Test collection (dynamic import check)
4. Critical module imports
5. Unit test execution

See the **test-after-changes** skill in `.claude/skills/test-after-changes/` for detailed instructions.

### Available Skills

Claude Code uses skills to provide specialized workflows:

- **test-after-changes** - Validation workflow after code changes (use after refactoring, feature work)
- **skill-creator** - Guide for creating new skills
- **deep-researcher** - Multi-angle parallel research for complex topics
- **doc-fetcher** - Fetch library documentation from Context7
- **job-analyzer** - Analyze job postings for requirements
- **resume-writer** - Transform master resume for specific jobs
- **cover-letter-writer** - Generate personalized cover letters
- **portfolio-finder** - Search GitHub for relevant code examples
- **career-enhancer** - Analyze gaps between job requirements and career history
- **langgraph-builder** - Guide for building LangGraph agents
- **data-access** - Centralized data access for career tools
