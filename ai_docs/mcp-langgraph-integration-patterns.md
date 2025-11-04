# MCP + LangGraph Integration Patterns

Complete guide to integrating MCP (Model Context Protocol) servers with LangGraph agents.

---

## Pattern Comparison

### Pattern #1: MCP Client (Runtime Decoupling)

```
┌─────────────────────────────────────┐
│      LangGraph Agent Process        │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ async def analyze_job_node: │   │
│  │   result = await mcp_client │   │
│  │     .call_tool(...)          │   │
│  └─────────────┬───────────────┘   │
└────────────────┼─────────────────────┘
                 │
          MCP Protocol (IPC/HTTP)
                 │
┌────────────────▼─────────────────────┐
│       MCP Server Process             │
│                                      │
│  @mcp.tool()                        │
│  def data_read_master_resume():     │
│      return query_database(...)      │
└──────────────────────────────────────┘

Use when:
✅ Different languages (TypeScript ↔ Python)
✅ Distributed deployment
✅ Third-party MCP servers
❌ Performance critical
```

### Pattern #2: Direct Import (Performance + Code Reuse)

```
┌─────────────────────────────────────┐
│      LangGraph Agent Process        │
│                                     │
│   ┌─────────────────────────────┐   │
│   │ def analyze_job_node():     │   │
│   │   # Direct function call    │   │
│   │   result = load_resume_fn() │   │
│   └─────────────┬───────────────┘   │
│                │                    │
│                │  sys.path.append   │
│                │  + import          │
│                │                    │
│   ┌─────────────▼───────────────┐   │
│   │ MCP Server Functions        │   │
│   │ (imported as Python module) │   │
│   │                             │   │
│   │ def data_read_master_resume │   │
│   │     query_database(...)     │   │
│   └─────────────────────────────┘   │
│                                     │
│  Single Process - No IPC Overhead   │
└─────────────────────────────────────┘

Use when:
✅ Same language (both Python)
✅ Monorepo deployment
✅ Performance matters
✅ Shared database access
❌ Need runtime decoupling
```

### Pattern #3: Separate Implementations

```
┌─────────────────────────────┐     ┌───────────────────────────┐
│   LangGraph Agent           │     │   MCP Server              │
│                             │     │                           │
│  def load_resume():         │     │  @mcp.tool()              │
│    with Session(engine):    │     │  def data_read_resume():  │
│      return session.query() │     │    with Session(engine):  │
│                             │     │     return session.query()│
└──────────────┬──────────────┘     └────────────┬──────────────┘
               │                                 │
               └─────────┬───────────────────────┘
                         ▼
                ┌─────────────────┐
                │ Shared Database │
                └─────────────────┘

Use when:
✅ Different teams/schedules
✅ Completely different requirements
❌ Want to avoid code duplication (high maintenance burden)
```

---

## Your Codebase: Pattern #2 with Wrapper Layer

**Architecture**: Direct import with adapter pattern

```python
# File: apps/resume-agent-langgraph/src/resume_agent/data/access.py

import sys
from pathlib import Path

# Add MCP server to Python path
MCP_SERVER_PATH = Path(__file__).parent.parent.parent.parent.parent / "resume-agent"
sys.path.insert(0, str(MCP_SERVER_PATH))

def _get_mcp_fn(fn_name: str):
    """Unwrap FastMCP tool and return raw function"""
    import resume_agent as mcp_module
    tool_wrapper = getattr(mcp_module, fn_name)
    return tool_wrapper.fn  # Extract function from FastMCP wrapper

# Clean wrapper API for LangGraph nodes
def load_master_resume() -> dict:
    """Load resume - reuses MCP server function"""
    fn = _get_mcp_fn("data_read_master_resume")
    result = fn()

    # Convert MCP response format to plain data
    if result.get("status") == "error":
        raise ValueError(result.get("error"))

    return result.get("data", {})
```

**Why this pattern?**

1. **70% Code Reuse**: Imports 21 out of 30 MCP tools directly
2. **Single Source of Truth**: Database logic in one place
3. **Performance**: No IPC overhead (direct function calls)
4. **Wrapper Benefits**:
   - Unwraps FastMCP decorators
   - Converts response format (`{"status": "success", "data": {...}}` → `{...}`)
   - Raises Python exceptions (more idiomatic for LangGraph)

---

## Performance Comparison

| Metric | Pattern #1 (MCP Client) | Pattern #2 (Direct Import) | Pattern #3 (Separate) |
|--------|------------------------|---------------------------|---------------------|
| **Latency** | 50-200ms (IPC overhead) | <1ms (function call) | <1ms (function call) |
| **Memory** | 2 processes (high) | 1 process (low) | 2 processes (medium) |
| **Code Reuse** | 100% (via MCP) | 70% (direct import) | 0% (duplicated) |
| **Maintenance** | Low (one codebase) | Low (one codebase) | High (two codebases) |
| **Debugging** | Hard (two processes) | Easy (one process) | Medium (separate) |

---

## Decision Matrix

| Requirement | Pattern #1 | Pattern #2 | Pattern #3 |
|------------|-----------|-----------|-----------|
| Same programming language | ❌ | ✅ | ✅ |
| Cross-language support | ✅ | ❌ | ✅ |
| Performance critical | ❌ | ✅ | ✅ |
| Runtime decoupling needed | ✅ | ❌ | ✅ |
| Deployed in monorepo | ❌ | ✅ | ❌ |
| Shared database access | ⚠️ | ✅ | ⚠️ |
| Code reuse important | ✅ | ✅ | ❌ |
| Independent deployment | ✅ | ❌ | ✅ |

**Your scenario** (both Python, monorepo, shared DB, performance matters):
- ✅ **Pattern #2** (Direct Import) is the optimal choice

---

## Example: Pattern #1 vs Pattern #2

### Pattern #1: MCP Client

```python
# LangGraph node using MCP client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def analyze_job_node(state: State) -> dict:
    """Call MCP server via client protocol"""

    # Setup MCP client
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "apps/resume-agent/resume_agent.py"]
    )

    # Connect and call tool
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "data_read_job_analysis",
                arguments={"company": state["company"], "job_title": state["job_title"]}
            )

            return {"job_analysis": result.content}

# Performance: ~100ms per call (process spawn + IPC)
```

### Pattern #2: Direct Import (Your Codebase)

```python
# LangGraph node using direct import
from ..data.access import get_job_analysis

def analyze_job_node(state: State) -> dict:
    """Call MCP server function directly"""

    # Direct function call - same process
    job_analysis = get_job_analysis(
        company=state["company"],
        job_title=state["job_title"]
    )

    return {"job_analysis": job_analysis}

# Performance: <1ms per call (direct function call)
```

**100x performance difference** for this use case!

---

## When to Switch Patterns

### From Pattern #2 to Pattern #1

**Switch when**:
- You want to rewrite LangGraph agent in **TypeScript/JavaScript**
- You need to **deploy separately** (e.g., MCP server on cloud, agent on edge)
- You want to use **third-party MCP servers**

**Migration path**:
1. Wrap existing MCP tools in HTTP transport (instead of stdio)
2. Update LangGraph nodes to use `mcp` client
3. Deploy MCP server as separate service
4. Update connection config (HTTP endpoint instead of stdio)

### From Pattern #1 to Pattern #2

**Switch when**:
- **Performance becomes critical** (100+ requests/sec)
- You want to **simplify deployment** (one process instead of two)
- Both implementations are **same language** and can share code

**Migration path**:
1. Extract data access functions from MCP server
2. Create wrapper module (like `data/access.py` in your codebase)
3. Update LangGraph nodes to use direct imports
4. Remove MCP client dependencies

---

## Best Practices

### Pattern #1 (MCP Client)

```python
# ✅ Reuse client connection
class MCPClientPool:
    """Connection pool for MCP client"""

    def __init__(self):
        self._clients = {}

    async def get_client(self, server_name: str):
        if server_name not in self._clients:
            # Create new client
            self._clients[server_name] = await self._create_client(server_name)
        return self._clients[server_name]

# ✅ Error handling
try:
    result = await mcp_client.call_tool(...)
except MCPError as e:
    # Accumulate error in state (don't raise)
    return {"errors": state["errors"] + [str(e)]}

# ❌ Creating new client per call (slow!)
async def bad_node(state):
    client = await create_mcp_client()  # Don't do this!
    result = await client.call_tool(...)
```

### Pattern #2 (Direct Import)

```python
# ✅ Lazy loading (avoid circular imports)
_mcp_module = None

def _get_mcp_module():
    global _mcp_module
    if _mcp_module is None:
        import resume_agent as mcp_module
        _mcp_module = mcp_module
    return _mcp_module

# ✅ Convert response format
def load_master_resume() -> dict:
    fn = _get_mcp_fn("data_read_master_resume")
    result = fn()

    # Convert MCP response to plain data
    if result.get("status") == "error":
        raise ValueError(result.get("error"))

    return result.get("data", {})  # Return data, not MCP wrapper

# ❌ Direct import without lazy loading
import resume_agent  # Can cause circular import errors!
```

---

## Architecture Decision Record

**Project**: Cernji-Agents Resume Agent
**Decision**: Use Pattern #2 (Direct Import) with wrapper layer
**Status**: Implemented ✅
**Date**: 2025-10-26

**Context**:
- MCP server (`apps/resume-agent/`) already implemented with 30 tools
- LangGraph agent (`apps/resume-agent-langgraph/`) being built as alternative implementation
- Both Python, same monorepo, shared SQLite database
- Need 70% code reuse to avoid duplication

**Decision**:
Use Pattern #2 (Direct Import) with adapter wrapper:
1. Import MCP server functions directly via `sys.path.append`
2. Create wrapper layer (`data/access.py`) to:
   - Unwrap FastMCP decorators
   - Convert response format
   - Raise exceptions instead of returning error dicts
3. Call wrapped functions from LangGraph nodes

**Consequences**:
- ✅ 70% code reuse (21 out of 30 tools)
- ✅ Single source of truth for database access
- ✅ Maximum performance (<1ms per call)
- ✅ Simple debugging (single process)
- ❌ Import-time coupling (both must be Python)
- ❌ Can't deploy separately

**Alternatives Considered**:
- Pattern #1 (MCP Client): Rejected due to performance overhead (100ms per call)
- Pattern #3 (Separate Implementations): Rejected due to code duplication (2x maintenance)

**References**:
- Architecture decisions: `apps/resume-agent-langgraph/docs/architecture-decisions.md`
- Wrapper implementation: `apps/resume-agent-langgraph/src/resume_agent/data/access.py`
- Contract tests: `apps/resume-agent-langgraph/tests/contract/test_mcp_tools.py`

---

## Resources

- **MCP SDK (Python)**: https://github.com/modelcontextprotocol/python-sdk
- **LangGraph Docs**: https://python.langchain.com/docs/langgraph
- **Your Implementation**: `apps/resume-agent-langgraph/src/resume_agent/data/access.py`
- **Architecture Docs**: `apps/resume-agent-langgraph/docs/architecture-decisions.md`
