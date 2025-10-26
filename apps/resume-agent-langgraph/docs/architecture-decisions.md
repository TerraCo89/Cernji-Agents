# Architecture Decisions

**Phase 1 Deliverable**: Key architectural decisions for LangGraph Resume Agent

**Created**: 2025-10-26

---

## Overview

This document records the key architectural decisions made during Phase 1 analysis. Each decision includes the question, options considered, chosen approach, and rationale.

---

## Decision 1: Which MCP Tools Map to LangGraph Nodes?

### Question

Which of the 30 MCP tools should be reimplemented as LangGraph nodes vs. called directly as-is?

### Options Considered

**Option A**: Reimplement all 30 tools as LangGraph nodes
- Pros: Complete control, consistent architecture
- Cons: Massive duplication, high maintenance burden

**Option B**: Call all MCP tools directly via MCP client
- Pros: Maximum reuse, minimal code
- Cons: Tight coupling, no workflow control

**Option C**: Hybrid approach - reimplement workflows, reuse data access
- Pros: Best of both worlds, clear separation
- Cons: Requires clear categorization

### Decision: **Option C - Hybrid Approach**

### Implementation

| Tool Category | Approach | Rationale |
|---------------|----------|-----------|
| **Workflow Tools** (9 tools) | Reimplement as LangGraph nodes | Need state management, conditional logic, error handling |
| **Data Access Tools** (21 tools) | Reuse directly via function calls | Pure data operations, no business logic |

**Workflow Tools → Nodes**:
1. `analyze_job` → `analyze_job_node`
2. `tailor_resume` → `tailor_resume_node`
3. `apply_to_job` → `full_workflow_graph` (multi-node workflow)
4. `rag_process_website` → `process_website_node`
5. `rag_query_websites` (with synthesis) → `rag_query_node`
6. `rag_refresh_website` → `refresh_website_node`

**Data Access Tools → Direct Calls**:
- All `data_read_*` functions (6 tools)
- All `data_write_*` functions (6 tools)
- All `data_*` utility functions (7 tools)
- Simple RAG queries (2 tools)

### Code Example

```python
# Workflow tool reimplemented as node
def analyze_job_node(state: ResumeAgentState) -> dict:
    """LangGraph node wrapping job analysis logic"""

    job_url = state["current_intent"]["extracted_params"]["job_url"]

    # Business logic here (LLM calls, validation, etc.)
    analysis = perform_job_analysis(job_url)

    # Call existing data access tool to save
    from resume_agent import data_write_job_analysis
    data_write_job_analysis(
        company=analysis["company"],
        job_title=analysis["job_title"],
        job_data=analysis
    )

    return {"job_analysis": analysis}
```

```python
# Data access tool called directly
def load_master_resume_node(state: ResumeAgentState) -> dict:
    """Load master resume using existing data access tool"""

    # Direct call to existing tool
    from resume_agent import data_read_master_resume
    result = data_read_master_resume()

    return {"master_resume": result["data"]}
```

### Rationale

1. **70% Reuse**: Reuse 21 tools directly → less code, less maintenance
2. **Clear Separation**: Data access ≠ business logic
3. **Workflow Control**: LangGraph nodes give us state management, conditional routing, error accumulation
4. **Testability**: Test workflow logic separately from data access
5. **DRY Principle**: Don't duplicate data access code

---

## Decision 2: How Will State Be Shared Across Nodes?

### Question

How should state flow through the LangGraph workflow?

### Options Considered

**Option A**: Pass data as function parameters
- Pros: Explicit, type-safe
- Cons: Requires manual parameter passing, no automatic persistence

**Option B**: Global state object
- Pros: Easy access from any node
- Cons: Mutable state, hard to debug, not checkpointable

**Option C**: LangGraph StateGraph with typed state schema
- Pros: Automatic checkpointing, type hints, reducer functions
- Cons: Learning curve for TypedDict vs. Pydantic

### Decision: **Option C - StateGraph with TypedDict**

### Implementation

```python
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages

class ResumeAgentState(TypedDict, total=False):
    # Required field (conversation history)
    messages: Annotated[List[BaseMessage], add_messages]

    # Job application data
    job_analysis: Annotated[Optional[JobAnalysisDict], replace_with_latest]
    master_resume: Annotated[Optional[MasterResumeDict], replace_with_latest]
    tailored_resume: Annotated[Optional[TailoredResumeDict], replace_with_latest]
    cover_letter: Annotated[Optional[CoverLetterDict], replace_with_latest]
    portfolio_examples: Annotated[List[PortfolioExampleDict], append_unique_examples]

    # Workflow control
    current_intent: Annotated[Optional[WorkflowIntent], replace_with_latest]
    workflow_progress: Annotated[Optional[WorkflowProgress], replace_with_latest]
    requires_user_input: Annotated[bool, replace_with_latest]
    error_message: Annotated[Optional[str], replace_with_latest]

    # Metadata
    user_id: Annotated[str, replace_with_latest]
```

**Custom Reducers**:

```python
def replace_with_latest(existing: Optional[dict], new: Optional[dict]) -> Optional[dict]:
    """Replace existing value with new value"""
    return new if new is not None else existing

def append_unique_examples(existing: List[dict], new: List[dict]) -> List[dict]:
    """Append new examples without duplicates"""
    if not existing:
        return new
    if not new:
        return existing

    # Deduplicate by id/title
    existing_ids = {e.get("id") or e.get("title") for e in existing}
    unique_new = [e for e in new if (e.get("id") or e.get("title")) not in existing_ids]

    return existing + unique_new
```

### Rationale

1. **Automatic Checkpointing**: State automatically persisted after each node
2. **Type Safety**: TypedDict provides IDE autocomplete and type checking
3. **Reducers**: Custom merge logic for different field types (replace vs. append)
4. **LangGraph Standard**: Follows LangGraph best practices
5. **msgpack Serialization**: TypedDict is serializable (Pydantic models are not)

### Trade-offs

**Why TypedDict instead of Pydantic?**
- LangGraph requires msgpack serialization
- Pydantic models cannot be serialized with msgpack
- Use Pydantic for **validation** (convert to dict before passing to graph)

```python
# Validate with Pydantic, convert to dict for state
from pydantic import BaseModel

class JobAnalysisModel(BaseModel):
    company: str
    job_title: str
    # ... validation rules

# Validate input
validated = JobAnalysisModel(company="Acme", job_title="Developer")

# Convert to dict for state
job_analysis_dict = validated.model_dump(mode='json')

# Update state
return {"job_analysis": job_analysis_dict}
```

---

## Decision 3: Should We Reuse MCP Tools Directly or Re-implement?

### Question

How should we integrate existing MCP data access functions?

### Options Considered

**Option A**: Import and call directly
- Pros: Maximum reuse, single source of truth
- Cons: Tight coupling to MCP server code

**Option B**: Duplicate logic in new data access layer
- Pros: Complete independence
- Cons: Massive code duplication, divergence risk

**Option C**: Create thin wrappers around MCP functions
- Pros: Reuse + abstraction
- Cons: Extra layer of indirection

### Decision: **Option A - Import and Call Directly**

### Implementation

```python
# In LangGraph node
import sys
sys.path.append("apps/resume-agent")
from resume_agent import (
    data_read_master_resume,
    data_write_job_analysis,
    data_search_portfolio_examples,
    # ... other data access functions
)

def load_master_resume_node(state: ResumeAgentState) -> dict:
    """Load master resume using existing DAL"""

    # Direct call to existing function
    result = data_read_master_resume()

    if result.get("status") == "error":
        return {
            "error_message": result.get("message"),
            "messages": [AIMessage(content="Could not load master resume")]
        }

    return {
        "master_resume": result["data"],
        "messages": [AIMessage(content="Loaded master resume")]
    }
```

### Rationale

1. **Single Source of Truth**: Database access logic in one place
2. **No Duplication**: Don't rewrite 21 data access functions
3. **Consistency**: Both MCP server and LangGraph agent use same DAL
4. **Maintenance**: Fix bugs once, both implementations benefit
5. **Testing**: Existing tests cover data access logic

### Risk Mitigation

**Risk**: Changes to MCP server break LangGraph agent

**Mitigation**:
1. **Contract Tests**: Verify function signatures and return types
2. **Integration Tests**: Test LangGraph nodes calling DAL functions
3. **Version Pinning**: Pin MCP server code version if needed
4. **Deprecation Policy**: Coordinate changes across both implementations

---

## Decision 4: How Should Errors Propagate Through Workflows?

### Question

What happens when a node fails? Should we raise exceptions or accumulate errors?

### Options Considered

**Option A**: Raise exceptions, halt workflow
- Pros: Explicit failure, easy to debug
- Cons: No partial success, can't recover

**Option B**: Accumulate errors in state, continue workflow
- Pros: Partial success, resilient workflows
- Cons: Need explicit error checking

**Option C**: Hybrid - raise for critical errors, accumulate for recoverable errors
- Pros: Balance of safety and resilience
- Cons: Complexity in deciding what's critical

### Decision: **Option B - Accumulate Errors in State**

### Implementation

```python
def analyze_job_node(state: ResumeAgentState) -> dict:
    """Analyze job with error accumulation"""

    job_url = state["current_intent"]["extracted_params"]["job_url"]

    # Step 1: Fetch job HTML
    try:
        html_content = fetch_url(job_url)
    except Exception as e:
        # Accumulate error, don't raise
        return {
            "error_message": f"Failed to fetch job URL: {str(e)}",
            "messages": [AIMessage(content="Could not fetch the job posting. Please check the URL.")]
        }

    # Step 2: LLM analysis
    try:
        analysis = llm.invoke(build_prompt(html_content))
    except Exception as e:
        # HTML already fetched - save it for retry
        return {
            "error_message": f"LLM analysis failed: {str(e)}",
            "raw_html": html_content,  # Preserve partial success
            "messages": [AIMessage(content="Analysis failed, but job posting HTML saved for retry.")]
        }

    # Step 3: Save to database
    try:
        data_write_job_analysis(...)
    except Exception as e:
        # Analysis succeeded but save failed - return analysis anyway
        return {
            "job_analysis": analysis,
            "error_message": f"Failed to save analysis: {str(e)}",
            "messages": [AIMessage(content="Analysis complete (not saved to database).")]
        }

    # Full success
    return {
        "job_analysis": analysis,
        "messages": [AIMessage(content="Job analysis complete and saved!")]
    }
```

**Error State Schema**:

```python
class WorkflowProgress(TypedDict):
    workflow_type: str
    steps_completed: List[str]
    steps_remaining: List[str]
    current_step: Optional[str]
    errors: List[str]  # Accumulate all errors
```

### Rationale

1. **Partial Success**: User gets whatever succeeded (e.g., fetched HTML even if analysis fails)
2. **Resumability**: Workflow can be retried from current step
3. **User Experience**: Better than "all or nothing" failure
4. **Debugging**: Error history preserved in state
5. **LangGraph Best Practice**: Nodes should never raise (return error state instead)

### Error Handling Patterns

**Pattern 1: Retry Logic**:
```python
# Router checks for errors and retries
def should_retry(state: ResumeAgentState) -> str:
    if state.get("error_message") and state.get("retry_count", 0) < 3:
        return "retry_node"
    return "next_node"
```

**Pattern 2: Fallback Logic**:
```python
# Use cached data if LLM fails
def analyze_job_with_fallback(state: ResumeAgentState) -> dict:
    try:
        analysis = llm.invoke(...)
        return {"job_analysis": analysis}
    except Exception as e:
        # Fallback to cached analysis
        cached = load_from_cache(state["job_url"])
        if cached:
            return {"job_analysis": cached, "cached": True}
        return {"error_message": str(e)}
```

---

## Decision 5: How Should We Handle Streaming Responses?

### Question

Should LangGraph workflows support streaming to provide real-time feedback?

### Options Considered

**Option A**: No streaming - return final result only
- Pros: Simple implementation
- Cons: Poor UX for long-running workflows (10+ seconds)

**Option B**: Node-by-node streaming via Server-Sent Events (SSE)
- Pros: Real-time progress updates
- Cons: Requires FastAPI SSE integration

**Option C**: Token-level streaming from LLM
- Pros: Ultra-responsive (see LLM output as it generates)
- Cons: Complex implementation, not all LLMs support it

### Decision: **Option B - Node-by-Node Streaming via SSE**

### Implementation

**FastAPI Server**:

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream LangGraph execution to client"""

    async def event_generator():
        """Generate SSE events for each state update"""

        # Execute workflow with streaming
        async for state_update in langgraph_app.astream(
            initial_state,
            config={"configurable": {"thread_id": request.thread_id}}
        ):
            # Emit state update event
            yield {
                "event": "state_update",
                "data": json.dumps({
                    "node": state_update.get("current_node"),
                    "messages": [m.content for m in state_update.get("messages", [])],
                    "progress": state_update.get("workflow_progress")
                })
            }

        # Final event
        yield {
            "event": "done",
            "data": json.dumps({"status": "complete"})
        }

    return EventSourceResponse(event_generator())
```

**Agent Chat UI (Next.js)**:

```typescript
// Stream LangGraph execution
const eventSource = new EventSource(`/api/chat/stream?thread_id=${threadId}`);

eventSource.addEventListener('state_update', (event) => {
    const data = JSON.parse(event.data);

    // Update UI with progress
    setCurrentNode(data.node);
    setMessages(prev => [...prev, ...data.messages]);
    setProgress(data.progress);
});

eventSource.addEventListener('done', (event) => {
    eventSource.close();
    setLoading(false);
});
```

### Rationale

1. **Real-Time Feedback**: User sees progress as workflow executes
2. **Better UX**: No "black box" waiting (especially for 10+ second workflows)
3. **Debugging**: See which node is executing, what's in state
4. **Standard Protocol**: SSE is widely supported, simple to implement
5. **LangGraph Support**: `.astream()` method built-in

### User Experience

**Without Streaming**:
```
User: "Apply to this job"
[Wait 30 seconds...]
Agent: "Application complete! Resume tailored, cover letter written, portfolio examples found."
```

**With Streaming**:
```
User: "Apply to this job"

[2 seconds]
Agent: "Analyzing job posting..."

[5 seconds]
Agent: "Job analysis complete. Found 12 required skills."

[8 seconds]
Agent: "Tailoring your resume..."

[15 seconds]
Agent: "Resume tailored with 8 ATS keywords."

[18 seconds]
Agent: "Writing cover letter..."

[25 seconds]
Agent: "Cover letter complete."

[28 seconds]
Agent: "Searching portfolio for relevant examples..."

[30 seconds]
Agent: "Application complete! Found 3 portfolio examples."
```

**Much better UX!**

---

## Decision Summary Table

| # | Decision | Chosen Approach | Key Benefit |
|---|----------|-----------------|-------------|
| 1 | Which tools → nodes? | Hybrid: Workflows as nodes, data access reused | 70% code reuse |
| 2 | How to share state? | StateGraph with TypedDict + custom reducers | Auto checkpointing |
| 3 | Reuse MCP tools? | Import and call directly | Single source of truth |
| 4 | Error propagation? | Accumulate in state, never raise | Partial success + resumability |
| 5 | Streaming? | Node-by-node SSE streaming | Real-time UX feedback |

---

## Implications for Implementation

### Phase 3: Data Access Layer

- **Action**: Import existing DAL functions from `resume_agent.py`
- **No Action**: Don't rewrite data access logic
- **Testing**: Add contract tests to verify DAL function signatures

### Phase 4: Job Analysis Workflow

- **Action**: Implement `analyze_job_node` as LangGraph node
- **Action**: Use error accumulation pattern (no raises)
- **Action**: Call `data_write_job_analysis` directly
- **Testing**: Test node in isolation with mocked DAL

### Phase 5: Resume Tailoring Workflow

- **Action**: Implement multi-node workflow: load → tailor → save
- **Action**: Use conditional edges for data loading
- **Action**: Implement streaming for progress updates
- **Testing**: Integration test full workflow with checkpointing

### Phase 6: FastAPI Integration

- **Action**: Implement SSE endpoint for streaming
- **Action**: Expose LangGraph workflows as FastAPI endpoints
- **Action**: Handle thread_id management
- **Testing**: E2E test with Agent Chat UI

---

## Open Questions

### Q1: Should we expose LangGraph workflows as MCP tools?

**Context**: Users can access via Claude Desktop (MCP) or Web UI (FastAPI).

**Options**:
- **A**: Keep MCP server separate (current approach)
- **B**: Wrap LangGraph workflows as MCP tools
- **C**: Deprecate MCP server, migrate fully to LangGraph

**Current Decision**: **A** (keep separate)

**Reasoning**: Dual access paths. Revisit after Phase 5 evaluation.

---

### Q2: Should we implement parallel node execution?

**Context**: Some operations (portfolio search + RAG query) could run in parallel.

**Options**:
- **A**: Sequential execution only (simpler)
- **B**: Parallel execution for independent operations (faster)

**Current Decision**: **Defer to Phase 5** (implement sequential first, optimize later)

**Reasoning**: Premature optimization. Validate workflows work correctly before optimizing performance.

---

### Q3: Should we use LangGraph Cloud for deployment?

**Context**: LangGraph Cloud provides managed deployment with built-in APIs.

**Options**:
- **A**: Self-hosted (FastAPI + LangGraph server + Docker)
- **B**: LangGraph Cloud (managed service)

**Current Decision**: **A** (self-hosted)

**Reasoning**:
- Full control over infrastructure
- No vendor lock-in
- Cost considerations (personal project)
- Can migrate to LangGraph Cloud later if needed

---

## Next Steps

- **Task 1.14**: Create Phase 1 summary in `phase-1-summary.md`
- **Phase 2**: Implement state schemas (complete)
- **Phase 3**: Implement data access layer wrappers
- **Phase 4**: Implement first workflow (job analysis)

---

## References

- **MCP Tools Inventory**: `docs/mcp-tools-inventory.md`
- **State Schema**: `docs/state-schema.md`
- **Workflow Mapping**: `docs/workflow-mapping.md`
- **Checkpointing Plan**: `docs/checkpointing-plan.md`
- **Architecture Comparison**: `docs/architecture-comparison.md`

---

**Generated**: 2025-10-26
**Phase**: 1 - Analysis & Discovery
**Status**: Complete
