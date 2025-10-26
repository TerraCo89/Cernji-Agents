# LangGraph Resume Agent - Development Guidance

**For AI Agents developing with LangGraph**

This document provides agent-specific development guidance for working with the LangGraph Resume Agent implementation.

## LangGraph Development Patterns

### StateGraph Construction Pattern

All workflows follow this pattern:

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

# 1. Define state schema (Pydantic or TypedDict)
class WorkflowState(TypedDict):
    input: str
    output: str | None
    errors: list[str]

# 2. Define node functions
def process_node(state: WorkflowState) -> dict:
    """Process step - returns partial state update"""
    try:
        result = do_work(state["input"])
        return {"output": result}
    except Exception as e:
        return {"errors": state["errors"] + [str(e)]}

# 3. Build graph
workflow = StateGraph(WorkflowState)
workflow.add_node("process", process_node)
workflow.set_entry_point("process")
workflow.add_edge("process", END)

# 4. Compile with checkpointer
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("data/workflow_checkpoints.db")
app = workflow.compile(checkpointer=checkpointer)

# 5. Execute with thread_id for resumption
result = app.invoke(initial_state, config={"configurable": {"thread_id": "workflow-123"}})
```

### Conditional Edges Pattern

For workflows with branching logic:

```python
def should_continue(state: WorkflowState) -> str:
    """Decide next node based on state"""
    if state.get("output"):
        return "success_node"
    else:
        return "fallback_node"

workflow.add_conditional_edges(
    "process",
    should_continue,
    {
        "success_node": "success_node",
        "fallback_node": "fallback_node"
    }
)
```

### Error Accumulation Pattern

For partial success workflows:

```python
def resilient_node(state: WorkflowState) -> dict:
    """Never raises - accumulates errors instead"""
    try:
        result = risky_operation()
        return {"output": result}
    except Exception as e:
        # Add error but allow workflow to continue
        return {"errors": state["errors"] + [f"Step failed: {str(e)}"]}
```

## MCP Tool Wrapping Pattern

All MCP tools wrap LangGraph workflows:

```python
from fastmcp import FastMCP

mcp = FastMCP("Resume Agent LangGraph")

@mcp.tool()
def analyze_job_posting(job_url: str) -> dict:
    """MCP tool wrapping job analysis workflow"""
    # Initialize state
    state = {
        "job_url": job_url,
        "workflow_id": str(uuid.uuid4()),
        "errors": []
    }

    # Execute workflow
    result = job_analysis_workflow.invoke(
        state,
        config={"configurable": {"thread_id": state["workflow_id"]}}
    )

    # Return MCP-compatible response
    return {
        "job_analysis": result.get("job_analysis"),
        "cached": result.get("cached", False),
        "errors": result.get("errors", [])
    }
```

## Caching Pattern

Workflow-level caching with cache-check node:

```python
def check_cache_node(state: WorkflowState) -> dict:
    """Check if result already cached"""
    cached_result = dal_read_from_cache(state["input"])
    if cached_result:
        return {
            "output": cached_result,
            "cached": True,
            "cache_source": "dal"
        }
    return {"cached": False}

def should_skip_processing(state: WorkflowState) -> str:
    """Conditional edge: skip processing if cached"""
    return END if state.get("cached") else "process"

workflow.add_node("check_cache", check_cache_node)
workflow.add_conditional_edges("check_cache", should_skip_processing)
workflow.set_entry_point("check_cache")
```

## Observability Integration Pattern

Emit observability events at workflow boundaries:

```python
def emit_observability_event(event_type: str, payload: dict):
    """Helper to emit events to observability server"""
    try:
        import httpx
        httpx.post(
            f"{os.getenv('OBSERVABILITY_SERVER_URL')}/events",
            json={
                "event_type": event_type,
                "source_app": "resume-agent-langgraph",
                "payload": payload,
                "timestamp": datetime.utcnow().isoformat()
            },
            timeout=1.0
        )
    except Exception:
        pass  # Don't fail workflow if observability fails

def workflow_with_observability(state: WorkflowState) -> dict:
    """Node with observability hooks"""
    # Emit SessionStart at workflow entry
    emit_observability_event("SessionStart", {"workflow_id": state["workflow_id"]})

    # Process
    result = process_step(state)

    # Emit SessionEnd at workflow exit
    emit_observability_event("SessionEnd", {
        "workflow_id": state["workflow_id"],
        "duration_ms": calculate_duration(state),
        "success": len(state.get("errors", [])) == 0
    })

    return result
```

## DAL Integration Pattern

Reuse existing data access layer without modification:

```python
# Import DAL functions from original implementation
import sys
sys.path.append("apps/resume-agent")
from resume_agent import (
    data_read_job_analysis,
    data_write_job_analysis,
    data_read_master_resume,
    # ... other DAL functions
)

# Use in LangGraph nodes
def analyze_job_node(state: WorkflowState) -> dict:
    """LangGraph node calling existing DAL"""
    try:
        # Call existing DAL function
        analysis = data_read_job_analysis(
            company=extract_company(state["job_url"]),
            job_title=extract_title(state["job_url"])
        )
        return {"job_analysis": analysis}
    except Exception as e:
        return {"errors": state["errors"] + [str(e)]}
```

## Performance Tracking Pattern

Track node-level performance for validation:

```python
def timed_node(state: WorkflowState) -> dict:
    """Node with performance tracking"""
    start_time = time.time()

    # Process
    result = do_work(state)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Update state with timing
    node_durations = state.get("node_durations", {})
    node_durations["node_name"] = duration_ms

    return {
        **result,
        "node_durations": node_durations
    }
```

## Testing Patterns

### Contract Testing

Verify MCP tool signatures match original:

```python
import inspect
from apps.resume_agent import resume_agent as original

def test_analyze_job_posting_signature():
    """Verify signature matches original"""
    from resume_agent_langgraph import analyze_job_posting

    orig_sig = inspect.signature(original.analyze_job_posting)
    new_sig = inspect.signature(analyze_job_posting)

    assert orig_sig == new_sig
```

### Integration Testing

Test workflows with mocked external services:

```python
from unittest.mock import patch

def test_job_analysis_workflow():
    """Test full workflow with mocked Claude API"""
    with patch('anthropic.Anthropic') as mock_claude:
        # Setup mock
        mock_claude.return_value.messages.create.return_value = mock_response

        # Execute workflow
        result = job_analysis_workflow.invoke({"job_url": "https://example.com/job"})

        # Verify result structure
        assert "job_analysis" in result
        assert result["job_analysis"]["company"] is not None
```

### Unit Testing

Test individual nodes in isolation:

```python
def test_check_cache_node():
    """Test cache lookup logic"""
    state = {"job_url": "https://example.com/job", "errors": []}

    # Test cache hit
    with patch('dal_read_from_cache') as mock_dal:
        mock_dal.return_value = {"company": "Example"}
        result = check_cache_node(state)
        assert result["cached"] is True
        assert result["output"] is not None

    # Test cache miss
    with patch('dal_read_from_cache') as mock_dal:
        mock_dal.return_value = None
        result = check_cache_node(state)
        assert result["cached"] is False
```

## Common Pitfalls

### 1. Using Pydantic Models in StateGraph

**❌ Wrong**: Passing Pydantic model to StateGraph

```python
from pydantic import BaseModel

class MyState(BaseModel):
    field: str

workflow = StateGraph(MyState)  # Causes msgpack serialization errors!
```

**✅ Correct**: Use TypedDict for StateGraph

```python
from typing import TypedDict

class MyState(TypedDict):
    field: str

workflow = StateGraph(MyState)  # Works with msgpack serialization

# Use Pydantic for validation in MCP tool:
class MyStateModel(BaseModel):
    field: str

initial_state_model = MyStateModel(field="value")
initial_state = initial_state_model.model_dump(mode='json')  # Convert to dict
workflow.invoke(initial_state)  # Pass dict, not Pydantic model
```

### 2. State Mutation

**❌ Wrong**: Mutating state directly

```python
def bad_node(state: dict) -> dict:
    state["output"] = "result"  # Don't mutate!
    return state
```

**✅ Correct**: Return partial state update

```python
def good_node(state: dict) -> dict:
    return {"output": "result"}  # Return update dict
```

### 3. Raising Exceptions in Nodes

**❌ Wrong**: Raising exceptions breaks partial success

```python
def bad_node(state: dict) -> dict:
    if error:
        raise Exception("Failed!")  # Breaks workflow
```

**✅ Correct**: Accumulate errors in state

```python
def good_node(state: dict) -> dict:
    if error:
        return {"errors": state.get("errors", []) + ["Failed!"]}
    return {"output": "success"}
```

### 4. Forgetting thread_id for Resumption

**❌ Wrong**: No thread_id means no resumption

```python
result = workflow.invoke(state)  # Lost on interruption
```

**✅ Correct**: Always provide thread_id

```python
result = workflow.invoke(
    state,
    config={"configurable": {"thread_id": "unique-id"}}
)
```

## Debugging Tips

### 1. LangGraph Studio

Use LangGraph Studio to visualize workflows:

```bash
# Start LangGraph Studio
langgraph studio

# Point to your workflow file
# View execution graph, state transitions, and node outputs
```

### 2. State Inspection

Log state at each node for debugging:

```python
def debug_node(state: WorkflowState) -> dict:
    print(f"Node state: {json.dumps(state, indent=2)}")
    result = process(state)
    print(f"Node result: {json.dumps(result, indent=2)}")
    return result
```

### 3. Checkpoint Inspection

Query checkpoints to understand workflow state:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("data/workflow_checkpoints.db")
checkpoints = checkpointer.list(thread_id="workflow-123")
for checkpoint in checkpoints:
    print(f"Checkpoint: {checkpoint}")
```

## Constitution Compliance

This implementation must follow project constitution principles:

- **Data Access Layer (II)**: All DAL functions reused without modification
- **Test-First Development (III)**: Contract/integration/unit tests before implementation
- **Observability by Default (IV)**: Events emitted at workflow boundaries
- **Type Safety (VII)**: All state schemas defined with Pydantic
- **Simplicity (VIII)**: Minimal abstraction, functional nodes

## Next Steps

1. Implement foundational state schemas (Phase 2)
2. Build job analysis workflow (Phase 3 - MVP)
3. Add resume tailoring workflow (Phase 4)
4. Implement complete orchestration workflow (Phase 5)
5. Evaluate vs. original implementation

## Resources

- **LangGraph Docs**: https://python.langchain.com/docs/langgraph
- **Feature Spec**: `/specs/006-langgraph-resume-agent/spec.md`
- **Implementation Plan**: `/specs/006-langgraph-resume-agent/plan.md`
- **Data Model**: `/specs/006-langgraph-resume-agent/data-model.md`
