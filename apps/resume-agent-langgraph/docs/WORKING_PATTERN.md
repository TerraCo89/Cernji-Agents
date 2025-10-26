# LangGraph Agent Chat UI Message Format - Working Pattern

This document explains the correct message format for integrating LangGraph agents with Agent Chat UI.

## The Problem

When integrating a LangGraph agent with Agent Chat UI, you may encounter:
- `KeyError: 'role'` - Wrong message format
- `OSError: [Errno 22] Invalid argument` - Python version incompatibility (Windows + Python 3.13)

## The Solution

### 1. Correct Message Format

**CRITICAL**: LangGraph SDK expects `BaseMessage` objects, NOT plain dictionaries.

#### ❌ Wrong Pattern (Causes KeyError)

```python
def chat(state: State) -> dict:
    return {
        "messages": [
            {"role": "assistant", "content": "Hello"}  # WRONG - plain dict
        ]
    }
```

#### ✅ Correct Pattern

```python
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    # MUST use add_messages reducer
    messages: Annotated[list[BaseMessage], add_messages]

def chat(state: State) -> dict:
    user_input = state["messages"][-1].content
    response = f"Echo: {user_input}"

    return {
        "messages": [AIMessage(content=response)]  # CORRECT - AIMessage object
    }
```

### 2. State Schema Requirements

**Key Points:**
- State MUST use `Annotated[list[BaseMessage], add_messages]` for messages field
- The `add_messages` reducer is required for proper message handling
- Never use plain `list` or `list[dict]` for messages

```python
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class State(TypedDict):
    """State for conversational agent"""
    messages: Annotated[list[BaseMessage], add_messages]  # REQUIRED format
```

### 3. Graph Configuration for Web

**For web deployment (Agent Chat UI):**
- No input node (messages come from HTTP requests)
- Simple START -> chat -> END flow
- No checkpointer needed for basic testing (can add later)

```python
from langgraph.graph import StateGraph, START, END

def build_graph():
    graph = StateGraph(State)
    graph.add_node("chat", chat)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # No checkpointer for simplicity (optional)
    return graph.compile()
```

### 4. LangGraph Configuration

**File**: `langgraph.json`

```json
{
  "dependencies": ["."],
  "graphs": {
    "resume_agent": "./examples/minimal_agent.py:build_graph"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

**Important**: Graph ID (`resume_agent`) MUST match `NEXT_PUBLIC_ASSISTANT_ID` in Agent Chat UI `.env`

### 5. Agent Chat UI Configuration

**File**: `apps/agent-chat-ui/.env`

```bash
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=resume_agent  # MUST match langgraph.json graph ID
```

## Common Errors and Solutions

### KeyError: 'role'

**Cause**: Returning plain dicts instead of BaseMessage objects

**Solution**: Use `AIMessage(content=...)` instead of `{"role": "assistant", "content": ...}`

### OSError: [Errno 22] Invalid argument (Windows)

**Cause**: Python 3.13 compatibility issue with LangGraph on Windows

**Solution**: Use Python 3.11 as specified in `langgraph.json`

```bash
# Check Python version
python --version

# Should be Python 3.11.x, not 3.13.x
# If using Python 3.13, install Python 3.11 and recreate venv:
py -3.11 -m venv .venv
```

### Invalid assistant: 'agent'

**Cause**: Graph ID mismatch between `langgraph.json` and API request

**Solution**: Ensure graph ID in `langgraph.json` matches `NEXT_PUBLIC_ASSISTANT_ID` in Agent Chat UI

## Complete Minimal Working Example

**File**: `examples/minimal_agent.py`

```python
#!/usr/bin/env python3
"""Minimal Working LangGraph Agent for Agent Chat UI"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage, BaseMessage

# State with proper message annotation
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Chat node that returns AIMessage objects
def chat(state: State) -> dict:
    user_msg = state["messages"][-1].content
    response = f"Echo: {user_msg}"
    return {"messages": [AIMessage(content=response)]}

# Build graph for web (no input node)
def build_graph():
    graph = StateGraph(State)
    graph.add_node("chat", chat)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph.compile()
```

## Testing

### 1. Start LangGraph Server

```bash
cd apps/resume-agent-langgraph
langgraph dev --port 2024
```

Expected output:
```
Registering graph with id 'resume_agent'
```

### 2. Test via API

```bash
curl -X POST http://localhost:2024/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "resume_agent",
    "input": {"messages": [{"role": "user", "content": "Hello"}]},
    "config": {"configurable": {"thread_id": "test-123"}},
    "stream_mode": ["values"]
  }'
```

Expected response:
```
event: metadata
data: {"run_id":"..."}

event: values
data: {"messages":[{"type":"human","content":"Hello"},{"type":"ai","content":"Echo: Hello"}]}

event: end
```

### 3. Test via Agent Chat UI

```bash
cd apps/agent-chat-ui
pnpm dev
```

Open http://localhost:3000 and send a message. Should receive echoed response without errors.

## Key Takeaways

1. **Always use BaseMessage objects** (`AIMessage`, `HumanMessage`), never plain dicts
2. **Use `add_messages` reducer** in state schema for messages field
3. **Match graph IDs** between `langgraph.json` and Agent Chat UI `.env`
4. **Use Python 3.11** as specified in `langgraph.json` (not 3.13)
5. **No input node for web** - messages come from HTTP requests
6. **Simplicity first** - get basic echo working before adding complexity

## Difference from CLI Pattern

**CLI Pattern** (with input node):
```python
# Has get_input node that reads from stdin
graph.add_node("get_input", get_user_input_node)
graph.add_node("chat", chat_node)
graph.add_edge(START, "get_input")
graph.add_conditional_edges("get_input", should_continue)
graph.add_edge("chat", "get_input")  # Loop back
```

**Web Pattern** (no input node):
```python
# No get_input - messages come from HTTP requests
graph.add_node("chat", chat_node)
graph.add_edge(START, "chat")
graph.add_edge("chat", END)  # Simple flow
```

## Next Steps

Once the basic pattern works:
1. Add proper checkpointer for conversation persistence
2. Integrate LLM calls (Claude/OpenAI)
3. Add business logic (job analysis, resume tailoring, etc.)
4. Add error handling and logging
5. Deploy to production

## Resources

- **LangGraph Docs**: https://python.langchain.com/docs/langgraph
- **Agent Chat UI**: https://github.com/langchain-ai/agent-chat-ui
- **Minimal Agent**: `apps/resume-agent-langgraph/examples/minimal_agent.py`
- **Resume Agent Spec**: `/specs/006-langgraph-resume-agent/spec.md`
