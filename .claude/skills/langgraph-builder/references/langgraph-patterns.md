# LangGraph Patterns Reference

Comprehensive patterns and examples for building LangGraph agents.

## Table of Contents

1. [State Schema Patterns](#state-schema-patterns)
2. [Node Function Patterns](#node-function-patterns)
3. [Edge Patterns](#edge-patterns)
4. [Checkpointing Patterns](#checkpointing-patterns)
5. [Error Handling Patterns](#error-handling-patterns)
6. [Multi-Agent Patterns](#multi-agent-patterns)
7. [Tool Integration Patterns](#tool-integration-patterns)

---

## State Schema Patterns

### Basic Conversation State

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]
    should_continue: bool
```

**Use Case:** Simple conversational agents

**Key Features:**
- `add_messages` ensures message history is append-only
- `should_continue` controls conversation loop

**Example:** `apps/resume-agent-langgraph/resume_agent_langgraph.py:54-62`

---

### Stateful Agent with Context

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_info: str
    session_data: dict
    error_count: int
```

**Use Case:** Agents requiring contextual information

**Key Features:**
- Message history persisted
- Custom fields for session context
- Error tracking for robustness

---

### Multi-Step Workflow State

```python
from typing import Annotated, TypedDict, Literal
from langgraph.graph.message import add_messages

class WorkflowState(TypedDict):
    messages: Annotated[list, add_messages]
    job_url: str
    job_analysis: dict | None
    resume_content: str | None
    cover_letter: str | None
    errors: list[str]
    step: Literal["analyze", "tailor", "generate", "complete"]
```

**Use Case:** Multi-step agents with complex workflows

**Key Features:**
- Track workflow progress with `step` field
- Store intermediate results
- Accumulate errors without breaking flow

---

## Node Function Patterns

### Basic Chat Node

```python
def chat_node(state: ConversationState) -> dict:
    """Process user input with LLM"""
    try:
        # Extract messages
        messages = state["messages"]

        # Call LLM
        response = llm.invoke(messages)

        # Return partial state update
        return {
            "messages": [{
                "role": "assistant",
                "content": response
            }]
        }
    except Exception as e:
        # Return error message (don't raise)
        return {
            "messages": [{
                "role": "assistant",
                "content": f"Error: {str(e)}"
            }]
        }
```

**Use Case:** Simple chat interaction

**Example:** `apps/resume-agent-langgraph/resume_agent_langgraph.py:114-170`

---

### Tool-Calling Node

```python
from langgraph.prebuilt import ToolNode

# Define tools
def get_weather(location: str) -> str:
    """Get weather for location"""
    return f"Weather in {location}: Sunny, 75°F"

# Create tool node
tool_node = ToolNode([get_weather])

def agent_node(state: MessagesState) -> dict:
    """Agent with tool calling"""
    messages = state["messages"]

    # LLM with tools
    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}
```

**Use Case:** Agents that use external tools

**Key Features:**
- `ToolNode` handles tool execution
- Agent decides when to call tools
- Results automatically added to messages

---

### Conditional Routing Node

```python
def routing_node(state: WorkflowState) -> dict:
    """Route based on state"""
    messages = state["messages"]
    last_message = messages[-1]

    # Determine next step
    if has_tool_calls(last_message):
        next_step = "tools"
    elif state["step"] == "analyze":
        next_step = "tailor"
    else:
        next_step = "complete"

    return {"step": next_step}
```

**Use Case:** Multi-path workflows

**Key Features:**
- Inspect state to determine routing
- Update state to guide flow
- Used with conditional edges

---

### Error Accumulation Node

```python
def process_node(state: WorkflowState) -> dict:
    """Process with error accumulation"""
    try:
        result = risky_operation(state["job_url"])
        return {"job_analysis": result}
    except Exception as e:
        # Don't raise - accumulate error
        return {
            "errors": state.get("errors", []) + [f"Analysis failed: {str(e)}"]
        }
```

**Use Case:** Resilient workflows that continue despite failures

**Key Features:**
- Never raises exceptions
- Accumulates errors in state
- Allows partial success

---

## Edge Patterns

### Simple Linear Flow

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(State)
graph.add_node("step1", step1_node)
graph.add_node("step2", step2_node)

# Linear: START -> step1 -> step2 -> END
graph.add_edge(START, "step1")
graph.add_edge("step1", "step2")
graph.add_edge("step2", END)

app = graph.compile()
```

**Use Case:** Sequential processing

---

### Conditional Edge with Routing

```python
def should_continue(state: ConversationState) -> str:
    """Route based on state"""
    if state.get("should_continue", True):
        return "chat"
    return END

graph.add_conditional_edges(
    "get_input",
    should_continue,
    {
        "chat": "chat",
        END: END
    }
)
```

**Use Case:** Dynamic flow control

**Example:** `apps/resume-agent-langgraph/resume_agent_langgraph.py:224-238`

---

### Loop Pattern

```python
# Loop: chat -> tools -> chat -> tools -> ...
graph.add_edge("chat", "tools")
graph.add_edge("tools", "chat")

# Exit condition
def should_end(state: State) -> str:
    if len(state["messages"]) > 10:
        return END
    return "chat"

graph.add_conditional_edges("chat", should_end, ["tools", END])
```

**Use Case:** Iterative processing until condition met

---

### Parallel Branches

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(State)
graph.add_node("analyze", analyze_node)
graph.add_node("search", search_node)
graph.add_node("merge", merge_node)

# Fork: START -> analyze AND search
graph.add_edge(START, "analyze")
graph.add_edge(START, "search")

# Join: analyze -> merge, search -> merge
graph.add_edge("analyze", "merge")
graph.add_edge("search", "merge")
graph.add_edge("merge", END)

app = graph.compile()
```

**Use Case:** Independent parallel operations

---

## Checkpointing Patterns

### In-Memory Checkpointing (Development)

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# Use with thread_id
config = {"configurable": {"thread_id": "user-123"}}
app.invoke(state, config=config)
```

**Use Case:** Local development, testing

**Pros:**
- Fast, no setup
- Good for testing

**Cons:**
- Lost on restart
- Not production-ready

**Example:** `apps/resume-agent-langgraph/resume_agent_langgraph.py:310`

---

### SQLite Checkpointing (Production)

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("data/checkpoints.db")
app = graph.compile(checkpointer=checkpointer)

# Use with thread_id
config = {"configurable": {"thread_id": "user-123"}}
app.invoke(state, config=config)
```

**Use Case:** Production deployments

**Pros:**
- Persistent across restarts
- Production-ready
- Can inspect checkpoints

**Cons:**
- Slightly slower than in-memory
- Requires file system access

---

### Checkpoint Inspection

```python
# Get checkpoint state
checkpoint = app.get_state(config)

# Inspect values
print(checkpoint.values["messages"])
print(checkpoint.values["user_info"])

# Resume from checkpoint
app.invoke(new_input, config=config)
```

**Use Case:** Debugging, resuming conversations

---

## Error Handling Patterns

### Graceful Error Messages

```python
def chat_node(state: State) -> dict:
    try:
        response = llm.invoke(state["messages"])
        return {"messages": [{"role": "assistant", "content": response}]}
    except Exception as e:
        # Return user-friendly error
        return {
            "messages": [{
                "role": "assistant",
                "content": f"I encountered an error: {str(e)}. Please try again."
            }]
        }
```

**Use Case:** Production agents that must never crash

**Example:** `apps/resume-agent-langgraph/resume_agent_langgraph.py:163-170`

---

### Error Accumulation with Partial Success

```python
def workflow_node(state: WorkflowState) -> dict:
    errors = []
    results = {}

    # Step 1
    try:
        results["step1"] = process_step1(state)
    except Exception as e:
        errors.append(f"Step 1 failed: {str(e)}")

    # Step 2 (continue even if step 1 failed)
    try:
        results["step2"] = process_step2(state)
    except Exception as e:
        errors.append(f"Step 2 failed: {str(e)}")

    return {
        **results,
        "errors": state.get("errors", []) + errors
    }
```

**Use Case:** Multi-step workflows requiring partial success

---

### Retry Logic

```python
def node_with_retry(state: State) -> dict:
    max_retries = 3
    retry_count = state.get("retry_count", 0)

    try:
        result = api_call(state["input"])
        return {"output": result, "retry_count": 0}
    except Exception as e:
        if retry_count < max_retries:
            return {
                "retry_count": retry_count + 1,
                "error_message": f"Retry {retry_count + 1}/{max_retries}"
            }
        else:
            return {
                "errors": [f"Failed after {max_retries} retries: {str(e)}"]
            }
```

**Use Case:** Unreliable external API calls

---

## Multi-Agent Patterns

### Agent Handoff with Command

```python
from langgraph.types import Command

def agent_1(state: State) -> Command:
    """First agent"""
    response = process_with_agent_1(state)

    # Hand off to agent_2
    return Command(
        goto="agent_2",
        update={"messages": [response]}
    )

def agent_2(state: State) -> Command:
    """Second agent"""
    response = process_with_agent_2(state)

    # Complete or hand back
    if should_continue(state):
        return Command(goto="agent_1", update={"messages": [response]})
    else:
        return Command(goto=END, update={"messages": [response]})
```

**Use Case:** Collaborative multi-agent systems

---

### Supervisor Pattern

```python
def supervisor(state: State) -> Command:
    """Supervisor decides which agent to call"""
    # Analyze state to determine next agent
    next_agent = decide_next_agent(state)

    return Command(
        goto=next_agent,
        update={"current_agent": next_agent}
    )

def specialist_1(state: State) -> Command:
    """Specialized agent 1"""
    result = perform_task_1(state)
    return Command(goto="supervisor", update={"messages": [result]})

def specialist_2(state: State) -> Command:
    """Specialized agent 2"""
    result = perform_task_2(state)
    return Command(goto="supervisor", update={"messages": [result]})

graph.add_node("supervisor", supervisor)
graph.add_node("specialist_1", specialist_1)
graph.add_node("specialist_2", specialist_2)
graph.add_edge(START, "supervisor")
```

**Use Case:** Hierarchical task delegation

---

## Tool Integration Patterns

### Simple Tool Node

```python
from langgraph.prebuilt import ToolNode

def search_tool(query: str) -> str:
    """Search for information"""
    return f"Results for: {query}"

tools = [search_tool]
tool_node = ToolNode(tools)

graph.add_node("tools", tool_node)
```

**Use Case:** Basic tool execution

---

### Tool Selection with Conditional Edge

```python
def should_use_tools(state: MessagesState) -> str:
    """Decide if tools are needed"""
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END

graph.add_conditional_edges(
    "agent",
    should_use_tools,
    {"tools": "tools", END: END}
)
graph.add_edge("tools", "agent")  # Loop back to agent
```

**Use Case:** Optional tool usage

---

### Human-in-the-Loop Tool

```python
from langgraph.types import interrupt

def approval_tool(action: str) -> str:
    """Require human approval for sensitive actions"""
    # Interrupt and wait for human response
    response = interrupt({"action": action, "status": "pending"})

    if response["approved"]:
        return f"Action '{action}' approved and executed"
    else:
        return f"Action '{action}' rejected"

# Compile with interrupt support
checkpointer = MemorySaver()
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_after=["approval_tool"]
)
```

**Use Case:** Sensitive operations requiring human review

---

## Advanced Patterns

### Streaming Support

```python
async def stream_agent_response(user_input: str):
    """Stream agent responses in real-time"""
    config = {"configurable": {"thread_id": generate_thread_id()}}
    state = {"messages": [{"role": "user", "content": user_input}]}

    async for event in app.astream(state, config=config):
        if "messages" in event:
            yield event["messages"][-1]["content"]
```

**Use Case:** Real-time UI updates

---

### State Snapshot and Resume

```python
# Save checkpoint
checkpoint = app.get_state(config)
saved_state = checkpoint.values

# Later: resume from saved state
app.invoke(saved_state, config=config)
```

**Use Case:** Long-running workflows with pauses

---

### Custom Reducer Functions

```python
from typing import Annotated

def merge_dicts(left: dict, right: dict) -> dict:
    """Custom reducer for dict fields"""
    return {**left, **right}

class State(TypedDict):
    messages: Annotated[list, add_messages]
    metadata: Annotated[dict, merge_dicts]
```

**Use Case:** Complex state merging logic

---

## Performance Patterns

### Minimize State Size

```python
class EfficientState(TypedDict):
    messages: Annotated[list, add_messages]
    # Store IDs instead of full objects
    user_id: str
    session_id: str
    # Avoid large data structures
    # Don't store: full_context: dict[str, Any]
```

**Use Case:** High-throughput applications

---

### Conditional Node Execution

```python
def should_run_expensive_node(state: State) -> str:
    """Skip expensive operations when not needed"""
    if state.get("cache_hit"):
        return "skip_expensive"
    return "expensive_node"

graph.add_conditional_edges(
    "check_cache",
    should_run_expensive_node,
    {
        "expensive_node": "expensive_node",
        "skip_expensive": "return_result"
    }
)
```

**Use Case:** Optimize for common cases

---

## Testing Patterns

### Unit Test Node

```python
def test_chat_node():
    state = {
        "messages": [{"role": "user", "content": "Hello"}]
    }

    result = chat_node(state)

    assert "messages" in result
    assert result["messages"][0]["role"] == "assistant"
```

---

### Integration Test Graph

```python
def test_agent_graph():
    app = build_web_conversation_graph()
    config = {"configurable": {"thread_id": "test-123"}}

    state = {"messages": [{"role": "user", "content": "Hello"}]}
    result = app.invoke(state, config=config)

    assert len(result["messages"]) > 1
    assert result["messages"][-1]["role"] == "assistant"
```

---

## Deployment Patterns

### Environment-Based Configuration

```python
import os

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")
MODEL_NAME = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
CHECKPOINT_DB = os.getenv("CHECKPOINT_DB", "data/checkpoints.db")

def build_production_graph():
    checkpointer = SqliteSaver.from_conn_string(CHECKPOINT_DB)
    return graph.compile(checkpointer=checkpointer)
```

---

### Health Check Endpoint

```python
def health_check():
    """Check if agent is healthy"""
    try:
        test_state = {"messages": [{"role": "user", "content": "ping"}]}
        config = {"configurable": {"thread_id": "health-check"}}
        result = app.invoke(test_state, config=config)
        return {"status": "healthy", "version": "1.0.0"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

---

## Resources

- **Working Implementation:** `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- **LangGraph Docs:** https://python.langchain.com/docs/langgraph
- **Context7:** Use `/fetch-docs langgraph` for latest documentation
