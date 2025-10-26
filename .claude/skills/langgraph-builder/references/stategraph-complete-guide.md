# StateGraph Complete Guide

Complete reference for building LangGraph agents with proper message handling and state management.

## Table of Contents

- [State Schema Patterns](#state-schema-patterns)
- [Message Format Handling](#message-format-handling)
- [Node Implementation Patterns](#node-implementation-patterns)
- [Graph Building Patterns](#graph-building-patterns)
- [Common Pitfalls](#common-pitfalls)

---

## State Schema Patterns

### Pattern 1: TypedDict with add_messages (Recommended)

**Best for:** Maximum control, production applications

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    context: dict
```

**Pros:**
- Full control over state structure
- Best performance (no Pydantic overhead)
- Compatible with msgpack serialization
- Explicit field definitions

**Cons:**
- More boilerplate than MessagesState
- No automatic validation

### Pattern 2: MessagesState (Quick Start)

**Best for:** Simple chatbots, rapid prototyping

```python
from langgraph.graph import MessagesState

class ConversationState(MessagesState):
    user_id: str
    context: dict
```

**Pros:**
- Minimal boilerplate
- `messages` field automatically included
- Inherits `add_messages` reducer

**Cons:**
- Less explicit than TypedDict
- Slightly more memory overhead

### Pattern 3: Custom Reducer

**Best for:** Complex state updates, non-message fields

```python
from typing import Annotated, TypedDict
from operator import add

def merge_context(left: dict, right: dict) -> dict:
    """Custom reducer for context merging"""
    return {**left, **right}

class State(TypedDict):
    messages: Annotated[list, add_messages]
    scores: Annotated[list[float], add]  # Append scores
    context: Annotated[dict, merge_context]  # Merge dicts
```

---

## Message Format Handling

### The Three Message Formats

| Format | Structure | Used By |
|--------|-----------|---------|
| **LangChain Classes** | `HumanMessage(content="...")` | LangGraph internal |
| **LangGraph SDK** | `{"type": "human", "content": "..."}` | Agent Chat UI |
| **LLM APIs** | `{"role": "user", "content": "..."}` | Anthropic, OpenAI |

### Conversion Functions

```python
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

def convert_to_api_format(messages: list[BaseMessage]) -> list[dict]:
    """Convert LangGraph messages to API format"""
    api_messages = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        api_messages.append({"role": role, "content": msg.content})
    return api_messages

def convert_from_api_format(messages: list[dict]) -> list[BaseMessage]:
    """Convert API format to LangGraph messages"""
    langgraph_messages = []
    for msg in messages:
        if msg["role"] == "user":
            langgraph_messages.append(HumanMessage(content=msg["content"]))
        else:
            langgraph_messages.append(AIMessage(content=msg["content"]))
    return langgraph_messages
```

### Handling KeyError: 'role'

**Problem:** Agent Chat UI receives messages without 'role' field

**Solution:** Always return BaseMessage objects from nodes

```python
# ❌ WRONG - Will cause KeyError
def chat_node(state):
    return {"messages": ["Plain string"]}  # NO!

# ❌ WRONG - Missing role field
def chat_node(state):
    return {"messages": [{"content": "Text"}]}  # NO!

# ✅ CORRECT - Using BaseMessage
from langchain_core.messages import AIMessage

def chat_node(state):
    return {"messages": [AIMessage(content="Text")]}  # YES!

# ✅ ALSO CORRECT - With role field
def chat_node(state):
    return {"messages": [{"role": "assistant", "content": "Text"}]}  # YES!
```

---

## Node Implementation Patterns

### Pattern 1: LLM Chat Node

```python
from langchain_core.messages import AIMessage
import anthropic

def chat_node(state: ConversationState) -> dict:
    """Call LLM with proper message conversion"""
    client = anthropic.Anthropic()

    # Convert to API format
    api_messages = convert_to_api_format(state["messages"])

    # Call LLM
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system="You are a helpful assistant.",
        messages=api_messages
    )

    # Return as BaseMessage
    return {
        "messages": [AIMessage(content=response.content[0].text)]
    }
```

### Pattern 2: Tool Execution Node

```python
from langchain_core.messages import ToolMessage

def tool_node(state: ConversationState) -> dict:
    """Execute tools and return results"""
    last_message = state["messages"][-1]

    if not hasattr(last_message, "tool_calls"):
        return {"messages": []}

    tool_messages = []
    for tool_call in last_message.tool_calls:
        # Execute tool
        result = execute_tool(tool_call["name"], tool_call["args"])

        # Create tool message
        tool_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
        )

    return {"messages": tool_messages}
```

### Pattern 3: Conditional Routing Node

```python
def should_continue(state: ConversationState) -> str:
    """Route based on last message"""
    last_message = state["messages"][-1]

    # Check for tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    # Check for termination keywords
    if any(word in last_message.content.lower() for word in ["bye", "exit"]):
        return END

    # Continue conversation
    return "chat"
```

### Pattern 4: Error Handling Node

```python
def safe_node(state: ConversationState) -> dict:
    """Node with error handling"""
    try:
        # Attempt operation
        result = risky_operation(state)
        return {"messages": [AIMessage(content=result)]}

    except Exception as e:
        # Log error
        print(f"Error in node: {e}")

        # Return error message to user
        return {
            "messages": [AIMessage(content=f"I encountered an error: {str(e)}")]
        }
```

---

## Graph Building Patterns

### Pattern 1: Simple Linear Flow

```python
from langgraph.graph import StateGraph, START, END

def build_simple_graph():
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("chat", chat_node)

    # Linear flow
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    return graph.compile()
```

### Pattern 2: Conditional Branching

```python
def build_branching_graph():
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("chat", chat_node)
    graph.add_node("tools", tool_node)

    # Entry point
    graph.add_edge(START, "chat")

    # Conditional routing
    graph.add_conditional_edges(
        "chat",
        should_continue,
        {
            "tools": "tools",
            "chat": "chat",
            END: END
        }
    )

    # Return from tools to chat
    graph.add_edge("tools", "chat")

    return graph.compile()
```

### Pattern 3: With Checkpointing

```python
from langgraph.checkpoint.memory import MemorySaver

def build_persistent_graph():
    graph = StateGraph(ConversationState)

    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # Add checkpointer for persistence
    checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)
```

### Pattern 4: Multi-Node Pipeline

```python
def build_pipeline_graph():
    graph = StateGraph(ConversationState)

    # Add pipeline nodes
    graph.add_node("input_validation", validate_input)
    graph.add_node("retrieval", retrieve_context)
    graph.add_node("chat", chat_with_context)
    graph.add_node("output_formatting", format_output)

    # Sequential pipeline
    graph.add_edge(START, "input_validation")
    graph.add_edge("input_validation", "retrieval")
    graph.add_edge("retrieval", "chat")
    graph.add_edge("chat", "output_formatting")
    graph.add_edge("output_formatting", END)

    return graph.compile()
```

---

## Common Pitfalls

### ❌ Pitfall 1: Using Pydantic Models for State

```python
# WRONG - Will cause msgpack serialization errors
from pydantic import BaseModel

class State(BaseModel):
    messages: list
```

**Solution:** Use TypedDict instead

```python
# CORRECT
from typing import TypedDict

class State(TypedDict):
    messages: list
```

### ❌ Pitfall 2: Returning Plain Strings as Messages

```python
# WRONG - Will cause KeyError: 'role'
def chat_node(state):
    return {"messages": ["Hello"]}
```

**Solution:** Use BaseMessage objects

```python
# CORRECT
from langchain_core.messages import AIMessage

def chat_node(state):
    return {"messages": [AIMessage(content="Hello")]}
```

### ❌ Pitfall 3: Mutating State Directly

```python
# WRONG - Direct mutation
def bad_node(state):
    state["messages"].append(AIMessage(content="Hello"))
    return state
```

**Solution:** Return partial updates

```python
# CORRECT - Partial update
def good_node(state):
    return {"messages": [AIMessage(content="Hello")]}
```

### ❌ Pitfall 4: Missing thread_id in Config

```python
# WRONG - No thread_id, conversation won't persist
result = app.invoke({"messages": [...]})
```

**Solution:** Always provide thread_id

```python
# CORRECT
config = {"configurable": {"thread_id": "user_123"}}
result = app.invoke({"messages": [...]}, config=config)
```

### ❌ Pitfall 5: Not Converting Message Formats

```python
# WRONG - Passing LangGraph messages directly to API
def chat_node(state):
    response = client.messages.create(messages=state["messages"])
```

**Solution:** Convert to API format first

```python
# CORRECT
def chat_node(state):
    api_messages = convert_to_api_format(state["messages"])
    response = client.messages.create(messages=api_messages)
```

---

## Quick Reference Checklist

Before deploying to Agent Chat UI:

- [ ] State uses TypedDict (not Pydantic BaseModel)
- [ ] Messages field uses `Annotated[list[BaseMessage], add_messages]`
- [ ] All nodes return BaseMessage objects (not strings)
- [ ] All nodes return dicts with 'role' field OR BaseMessage objects
- [ ] Message conversion functions handle LangGraph SDK → API format
- [ ] Graph compiled with checkpointer for persistence
- [ ] thread_id provided in config for all invocations
- [ ] No direct state mutation in nodes
- [ ] Error handling in all nodes (don't raise exceptions)

---

## Additional Resources

- **Official LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **Message Format Guide**: `message-format-guide.md`
- **Debugging Guide**: `debugging-agents.md`
- **Chat UI Integration**: `chat-ui-integration.md`
