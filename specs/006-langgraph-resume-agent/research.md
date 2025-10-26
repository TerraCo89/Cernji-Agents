# Research: LangGraph Resume Agent

**Date**: 2025-10-23
**Feature**: LangGraph Resume Agent (006)
**Purpose**: Research LangGraph architecture, patterns, and integration approach for reimplementing Resume Agent workflows

## Research Questions

1. How does LangGraph structure multi-step workflows?
2. How does LangGraph handle workflow state persistence and recovery?
3. How do we integrate LangGraph with FastMCP for MCP tool exposure?
4. What are best practices for error handling and partial success in LangGraph?
5. How do we implement caching at the workflow level in LangGraph?
6. What testing patterns work best for LangGraph workflows?

---

## R1: LangGraph Workflow Architecture

**Decision**: Use StateGraph with typed state and functional nodes

**Rationale**:
- LangGraph provides `StateGraph` class for defining workflow structure
- State is managed via Python TypedDict or Pydantic models
- Nodes are Python functions that receive state and return updates
- Edges define transitions (conditional or unconditional)
- Built-in support for cycles, branching, and parallel execution

**Key Pattern**:
```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class ApplicationState(TypedDict):
    job_url: str
    job_analysis: dict | None
    tailored_resume: str | None
    cover_letter: str | None
    portfolio_examples: list | None
    errors: list[str]

# Define nodes
def analyze_job_node(state: ApplicationState) -> ApplicationState:
    # Call existing data_read/write functions
    return {"job_analysis": result}

# Build graph
workflow = StateGraph(ApplicationState)
workflow.add_node("analyze_job", analyze_job_node)
workflow.add_node("tailor_resume", tailor_resume_node)
workflow.add_edge("analyze_job", "tailor_resume")
workflow.set_entry_point("analyze_job")
```

**Alternatives Considered**:
- **Raw state machine**: More control but no persistence, visualization, or debugging tools
- **Temporal/Airflow**: Overengineered for single-user system; requires infrastructure
- **Custom orchestration**: Reinventing the wheel; LangGraph provides exactly what we need

**References**:
- LangGraph documentation: State management, graph construction patterns
- Example multi-agent systems using LangGraph for orchestration

---

## R2: State Persistence and Recovery

**Decision**: Use LangGraph's built-in checkpointing with SQLite backend

**Rationale**:
- LangGraph provides `SqliteSaver` for persisting workflow state
- Checkpoints saved after each node execution
- Can resume from last checkpoint after interruption
- Thread-based isolation (each workflow execution gets unique thread_id)
- Automatic state versioning for rollback/replay

**Implementation**:
```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Use separate SQLite file for workflow state
checkpointer = SqliteSaver.from_conn_string("data/workflow_checkpoints.db")

# Compile graph with checkpointing
app = workflow.compile(checkpointer=checkpointer)

# Execute with thread_id for resumption
result = app.invoke(initial_state, config={"configurable": {"thread_id": workflow_id}})

# Resume after interruption
result = app.invoke(None, config={"configurable": {"thread_id": workflow_id}})
```

**Alternatives Considered**:
- **In-memory state**: Lost on process restart; doesn't meet FR-005 requirement
- **Manual serialization**: Complex, error-prone; LangGraph handles this automatically
- **Existing resume_agent.db**: Keep workflow state separate to avoid schema coupling

**Key Benefit**: 100% state recovery requirement (SC-002) achieved automatically

---

## R3: LangGraph + FastMCP Integration

**Decision**: Wrap LangGraph workflows inside MCP tool functions

**Rationale**:
- MCP tools remain the interface (backward compatibility requirement)
- LangGraph handles internal orchestration
- Each MCP tool either:
  - Executes a single workflow node (for individual operations)
  - Launches a complete workflow graph (for end-to-end operations)
- MCP streaming naturally maps to LangGraph node-by-node execution

**Architecture**:
```python
from fastmcp import FastMCP

mcp = FastMCP("Resume Agent LangGraph")

@mcp.tool()
def analyze_job_posting(job_url: str) -> dict:
    """MCP tool wrapping job analysis workflow"""
    state = {"job_url": job_url, "errors": []}
    result = job_analysis_workflow.invoke(state)
    return result["job_analysis"]

@mcp.tool()
def complete_application_workflow(job_url: str) -> dict:
    """MCP tool wrapping complete multi-step workflow"""
    state = {"job_url": job_url, "errors": []}
    result = complete_workflow_graph.invoke(state)
    return {
        "job_analysis": result["job_analysis"],
        "tailored_resume": result["tailored_resume"],
        "cover_letter": result["cover_letter"],
        "portfolio_examples": result["portfolio_examples"]
    }
```

**Alternatives Considered**:
- **Expose LangGraph as MCP resource**: Would change interface; violates backward compatibility
- **Direct LangGraph graph as MCP server**: Not supported by FastMCP; requires custom transport

**Key Benefit**: Maintains 22 existing MCP tool signatures (FR-003) while adding orchestration

---

## R4: Error Handling and Partial Success

**Decision**: Use conditional edges with error state accumulation

**Rationale**:
- Each node catches exceptions and adds to `errors` list in state
- Conditional edges check for errors and decide whether to continue or skip
- Partial success achieved by allowing workflow to proceed despite individual node failures
- Final state contains both successful results and error messages

**Pattern**:
```python
def analyze_job_node(state: ApplicationState) -> ApplicationState:
    try:
        analysis = perform_job_analysis(state["job_url"])
        return {"job_analysis": analysis}
    except Exception as e:
        return {"errors": state["errors"] + [f"Job analysis failed: {str(e)}"]}

def should_continue_to_resume(state: ApplicationState) -> str:
    """Conditional edge: proceed to resume if job analysis succeeded"""
    if state.get("job_analysis"):
        return "tailor_resume"
    else:
        return "skip_to_cover_letter"  # Try cover letter even if analysis fails

workflow.add_conditional_edges(
    "analyze_job",
    should_continue_to_resume,
    {
        "tailor_resume": "tailor_resume",
        "skip_to_cover_letter": "generate_cover_letter"
    }
)
```

**Alternatives Considered**:
- **Fail fast**: Violates SC-009 requirement (90%+ partial success)
- **Try-catch at graph level**: Loses granular error tracking per node
- **Retry logic**: Adds complexity; better to fail gracefully and report

**Key Benefit**: Achieves FR-007 (partial success) and SC-009 (90%+ partial success rate)

---

## R5: Workflow-Level Caching

**Decision**: Add cache-check node at graph entry with state-based bypass

**Rationale**:
- LangGraph state can store cache metadata (e.g., `cached: bool`, `cache_source: str`)
- Add "check_cache" node as first step in each workflow
- If cached data exists, populate state and skip to END
- If no cache, proceed with normal workflow execution
- Leverage existing caching in data access layer (already implemented)

**Pattern**:
```python
def check_job_analysis_cache(state: ApplicationState) -> ApplicationState:
    """Check if job analysis already cached"""
    cached_analysis = data_read_job_analysis_from_db(state["job_url"])
    if cached_analysis:
        return {
            "job_analysis": cached_analysis,
            "cached": True,
            "cache_source": "job_analysis"
        }
    return {"cached": False}

def should_skip_analysis(state: ApplicationState) -> str:
    return END if state.get("cached") else "analyze_job"

workflow.add_node("check_cache", check_job_analysis_cache)
workflow.add_conditional_edges("check_cache", should_skip_analysis)
workflow.set_entry_point("check_cache")
```

**Alternatives Considered**:
- **LangGraph built-in caching**: Not available for arbitrary state-based caching
- **External cache layer**: Adds complexity; existing DAL already has caching
- **No workflow-level caching**: Misses SC-004 target (80% reduction in duplicate processing)

**Key Benefit**: Achieves SC-004 (80% reduction via caching) by reusing existing DAL cache logic

---

## R6: Testing Patterns for LangGraph Workflows

**Decision**: Three-tier testing strategy - contract, integration, unit

**Rationale**:
- **Contract tests**: Verify MCP tool signatures unchanged (backward compatibility)
- **Integration tests**: Execute complete workflows with mocked external services (Claude API, GitHub API)
- **Unit tests**: Test individual node functions in isolation with mock state

**Testing Structure**:
```python
# tests/contract/test_mcp_tools.py
def test_analyze_job_posting_signature():
    """Ensure MCP tool signature matches original"""
    # Verify function signature, return type

# tests/integration/test_job_analysis_workflow.py
def test_complete_job_analysis_workflow():
    """Test full workflow execution"""
    with mock_claude_api(), mock_github_api():
        result = job_analysis_workflow.invoke({"job_url": "..."})
        assert result["job_analysis"] is not None

# tests/unit/test_langgraph_nodes.py
def test_analyze_job_node():
    """Test single node in isolation"""
    state = {"job_url": "https://example.com/job"}
    result = analyze_job_node(state)
    assert "job_analysis" in result
```

**Alternatives Considered**:
- **Only integration tests**: Slower, harder to debug failures
- **Snapshot testing**: Brittle for LLM-generated content
- **End-to-end tests**: Too slow, requires real API keys

**Key Benefit**: Satisfies Constitution principle III (Test-First Development) and FR-009 (test coverage)

---

## Summary of Key Decisions

| Area | Decision | Primary Benefit |
|------|----------|-----------------|
| **Workflow Structure** | StateGraph with typed state (Pydantic/TypedDict) | Type safety, clear state contracts |
| **Persistence** | SqliteSaver checkpointing (separate DB file) | Automatic state recovery (SC-002) |
| **MCP Integration** | MCP tools wrap LangGraph workflows | Backward compatibility (FR-003) |
| **Error Handling** | Conditional edges + error accumulation | Partial success (FR-007, SC-009) |
| **Caching** | Cache-check node at graph entry | 80% reduction in duplicate processing (SC-004) |
| **Testing** | Contract + integration + unit tests | Test coverage, backward compatibility verification |

---

## Open Questions Resolved

✅ **Q1**: How to structure workflows? → StateGraph with typed state
✅ **Q2**: How to persist state? → SqliteSaver with separate checkpoint DB
✅ **Q3**: How to integrate with MCP? → MCP tools wrap LangGraph workflows
✅ **Q4**: How to handle errors? → Conditional edges + error state accumulation
✅ **Q5**: How to implement caching? → Cache-check node + existing DAL cache
✅ **Q6**: How to test? → Three-tier strategy (contract, integration, unit)

**Status**: All research questions resolved. Ready for Phase 1 (Data Model & Contracts).
