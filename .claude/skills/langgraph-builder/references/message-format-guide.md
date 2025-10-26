# Message Format Guide for LangGraph Agents

**REQUIRED READING**: Proper message formatting is critical for Agent Chat UI integration.

## Overview

Agent Chat UI requires messages to follow the OpenAI/LangChain message schema. There are two valid approaches:

1. **LangChain Message Classes** (Recommended)
2. **Dictionary Format** (Alternative)

---

## LangChain Message Classes (Recommended)

### Import Required Classes

```python
from langchain_core.messages import (
    AIMessage,      # For agent/assistant responses
    HumanMessage,   # For user messages
    SystemMessage,  # For system prompts
    ToolMessage,    # For tool results
    BaseMessage     # Base class for type hints
)
```

### AI/Assistant Messages

**When to use:** Agent responses to user queries

```python
AIMessage(content="I can help with that")

# With metadata
AIMessage(
    content="Here's your resume",
    additional_kwargs={
        "artifact": {
            "type": "resume",
            "content": resume_data
        }
    }
)

# With tool calls
AIMessage(
    content="Let me search for that",
    tool_calls=[{
        "id": "call_123",
        "name": "search_tool",
        "args": {"query": "LangGraph"}
    }]
)
```

### Human/User Messages

**When to use:** User input to the agent

```python
HumanMessage(content="Hello, how are you?")

# With metadata
HumanMessage(
    content="Analyze this job posting",
    additional_kwargs={
        "url": "https://example.com/job"
    }
)
```

### System Messages

**When to use:** Setting agent behavior/context

```python
SystemMessage(content="You are a helpful resume writing assistant")

# With detailed instructions
SystemMessage(
    content="""You are a professional resume writer.

    Guidelines:
    - Focus on achievements, not responsibilities
    - Use action verbs
    - Quantify results when possible
    """
)
```

### Tool Messages

**When to use:** Returning tool execution results

```python
ToolMessage(
    content="Search results: ...",
    tool_call_id="call_123"  # REQUIRED: Must match tool call ID
)

# With structured data
ToolMessage(
    content=json.dumps({"results": [...]}),
    tool_call_id="call_123"
)
```

---

## Dictionary Format (Alternative)

If you prefer dictionaries over message classes, follow this schema:

### AI/Assistant Message

```python
{
    "role": "assistant",  # REQUIRED
    "content": "I can help with that"  # REQUIRED
}

# With additional data
{
    "role": "assistant",
    "content": "Here's your resume",
    "metadata": {
        "artifact_type": "resume"
    }
}
```

### Human/User Message

```python
{
    "role": "user",  # REQUIRED
    "content": "Hello"  # REQUIRED
}
```

### System Message

```python
{
    "role": "system",  # REQUIRED
    "content": "You are a helpful assistant"  # REQUIRED
}
```

### Tool Message

```python
{
    "role": "tool",  # REQUIRED
    "content": "Tool result",  # REQUIRED
    "tool_call_id": "call_123"  # REQUIRED for tool messages
}
```

---

## State Schema Definition

### Basic Conversation State

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
```

**Key Points:**
- Use `Annotated[list[BaseMessage], add_messages]`
- `add_messages` reducer ensures messages are appended, not replaced
- `BaseMessage` for type safety

### State with Additional Fields

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    session_data: dict
    step: str
```

---

## Node Implementation Patterns

### Simple Chat Node

```python
from langchain_core.messages import AIMessage

def chat_node(state: ConversationState) -> dict:
    """Process user message and return AI response"""
    # Extract user message
    user_message = state["messages"][-1].content

    # Generate response (simplified)
    response = f"You said: {user_message}"

    # Return as AIMessage
    return {
        "messages": [AIMessage(content=response)]
    }
```

### Node with LLM Call

```python
from langchain_core.messages import AIMessage
import anthropic

def llm_chat_node(state: ConversationState) -> dict:
    """Call Claude API and return formatted response"""
    client = anthropic.Anthropic()

    # Convert messages to API format
    api_messages = convert_to_api_format(state["messages"])

    # Call LLM
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        messages=api_messages
    )

    # Return as AIMessage
    return {
        "messages": [AIMessage(content=response.content[0].text)]
    }

def convert_to_api_format(messages: list) -> list:
    """Convert LangChain messages to Claude API format"""
    api_messages = []
    for msg in messages:
        if isinstance(msg, BaseMessage):
            role = "user" if msg.type == "human" else msg.type
            api_messages.append({
                "role": role,
                "content": msg.content
            })
    return api_messages
```

### Node with Tool Calls

```python
from langchain_core.messages import AIMessage, ToolMessage

def tool_calling_node(state: ConversationState) -> dict:
    """Agent decides whether to call tools"""
    # Check if we should call a tool
    if should_search(state["messages"][-1].content):
        return {
            "messages": [
                AIMessage(
                    content="Let me search for that information",
                    tool_calls=[{
                        "id": "call_search_123",
                        "name": "web_search",
                        "args": {"query": extract_query(state)}
                    }]
                )
            ]
        }
    else:
        return {
            "messages": [AIMessage(content="I can answer that directly...")]
        }

def tool_execution_node(state: ConversationState) -> dict:
    """Execute tool and return results"""
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]

    # Execute tool
    result = execute_tool(tool_call["name"], tool_call["args"])

    # Return as ToolMessage
    return {
        "messages": [
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]  # Must match!
            )
        ]
    }
```

### Node with Error Handling

```python
from langchain_core.messages import AIMessage

def safe_chat_node(state: ConversationState) -> dict:
    """Chat node with error handling"""
    try:
        # Process message
        response = generate_response(state["messages"])

        return {
            "messages": [AIMessage(content=response)]
        }
    except Exception as e:
        # Return error as AIMessage (don't raise!)
        return {
            "messages": [
                AIMessage(
                    content=f"I encountered an error: {str(e)}. Please try again."
                )
            ]
        }
```

---

## Complete Working Example

Minimal LangGraph agent that works with Agent Chat UI:

```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver

# 1. Define state with proper message handling
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# 2. Create agent node that returns proper message format
def agent_node(state: State) -> dict:
    """Simple echo agent"""
    # Get the last user message
    user_message = state["messages"][-1].content

    # Generate response (simplified)
    response_text = f"You said: {user_message}"

    # Return as AIMessage
    return {
        "messages": [AIMessage(content=response_text)]
    }

# 3. Build graph
def build_web_conversation_graph():
    graph = StateGraph(State)

    # Add agent node
    graph.add_node("agent", agent_node)

    # Simple flow: START -> agent -> END
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)

    # Compile with checkpointer (REQUIRED for persistence)
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)

# 4. Test locally before deploying
if __name__ == "__main__":
    app = build_web_conversation_graph()

    result = app.invoke(
        {"messages": [HumanMessage(content="Hello")]},
        config={"configurable": {"thread_id": "test-123"}}
    )

    # Verify message format
    for msg in result["messages"]:
        print(f"Type: {type(msg).__name__}")
        print(f"Content: {msg.content}")
        assert hasattr(msg, "content"), "Message missing content"
        assert hasattr(msg, "type"), "Message missing type"
        print("✅ Message format valid")
```

---

## Message Format Validation

### Pre-Deployment Validation

```python
from langchain_core.messages import BaseMessage

def validate_message_format(messages: list) -> bool:
    """Validate all messages have proper format"""
    for i, msg in enumerate(messages):
        # Check if it's a LangChain message object
        if isinstance(msg, BaseMessage):
            # Validate has content
            if not hasattr(msg, "content"):
                raise ValueError(f"Message {i} missing 'content' attribute")
            continue

        # If it's a dict, verify required fields
        if isinstance(msg, dict):
            if "role" not in msg:
                raise ValueError(f"Message {i} missing 'role' field: {msg}")
            if "content" not in msg:
                raise ValueError(f"Message {i} missing 'content' field: {msg}")

            # Validate role values
            valid_roles = ["user", "assistant", "system", "tool"]
            if msg["role"] not in valid_roles:
                raise ValueError(
                    f"Message {i} has invalid role '{msg['role']}'. "
                    f"Must be one of {valid_roles}"
                )
        else:
            raise ValueError(
                f"Message {i} has invalid type {type(msg)}: {msg}"
            )

    return True

# Use in nodes
def validated_agent_node(state: State) -> dict:
    response = generate_response(state)

    # Validate before returning
    validate_message_format(state["messages"])

    return state
```

### Runtime Validation

```python
import logging

logger = logging.getLogger(__name__)

def logging_agent_node(state: State) -> dict:
    """Agent node with comprehensive logging"""
    # Log incoming state
    logger.info(f"Processing {len(state['messages'])} messages")
    logger.info(f"Message types: {[type(m).__name__ for m in state['messages']]}")

    # Generate response
    response = generate_response(state)

    # Log outgoing message
    logger.info(f"Returning message type: {type(response).__name__}")
    logger.info(f"Response content: {response.content[:100]}...")

    return {"messages": [response]}
```

---

## Converting Between Formats

### LangChain to Dictionary

```python
from langchain_core.messages import BaseMessage

def message_to_dict(message: BaseMessage) -> dict:
    """Convert LangChain message to dict format"""
    role = "user" if message.type == "human" else message.type

    result = {
        "role": role,
        "content": message.content
    }

    # Include tool calls if present
    if hasattr(message, "tool_calls") and message.tool_calls:
        result["tool_calls"] = message.tool_calls

    return result
```

### Dictionary to LangChain

```python
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

def dict_to_message(msg_dict: dict) -> BaseMessage:
    """Convert dict to LangChain message"""
    role = msg_dict["role"]
    content = msg_dict["content"]

    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(
            content=content,
            tool_calls=msg_dict.get("tool_calls")
        )
    elif role == "system":
        return SystemMessage(content=content)
    elif role == "tool":
        return ToolMessage(
            content=content,
            tool_call_id=msg_dict["tool_call_id"]
        )
    else:
        raise ValueError(f"Unknown role: {role}")
```

### LangGraph SDK to LLM API

**Critical for Resume Agent fix:**

```python
def convert_langgraph_messages_to_api_format(messages: list) -> list:
    """
    Convert LangGraph SDK message format to LLM API format.

    LangGraph SDK format: {"type": "human", "content": "..."}
    API format: {"role": "user", "content": "..."}
    """
    api_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            # Get role from either 'role' or 'type' field
            role = msg.get("role") or msg.get("type")

            # Convert 'human' to 'user'
            if role == "human":
                role = "user"

            api_messages.append({
                "role": role,
                "content": msg["content"]
            })
        elif isinstance(msg, BaseMessage):
            # Convert LangChain message
            role = "user" if msg.type == "human" else msg.type
            api_messages.append({
                "role": role,
                "content": msg.content
            })

    return api_messages
```

**Reference:** `apps/resume-agent-langgraph/src/resume_agent/llm/messages.py`

---

## Testing Message Format

### Unit Test

```python
def test_message_format():
    """Test that agent returns proper message format"""
    from langchain_core.messages import HumanMessage, AIMessage

    # Create state
    state = {
        "messages": [HumanMessage(content="Test")]
    }

    # Call node
    result = agent_node(state)

    # Verify result structure
    assert "messages" in result
    assert len(result["messages"]) == 1

    # Verify message format
    msg = result["messages"][0]
    assert isinstance(msg, AIMessage)
    assert hasattr(msg, "content")
    assert msg.content != ""

    print("✅ Message format test passed")
```

### Integration Test

```python
def test_graph_message_format():
    """Test full graph message handling"""
    from langchain_core.messages import HumanMessage

    app = build_web_conversation_graph()

    result = app.invoke(
        {"messages": [HumanMessage(content="Hello")]},
        config={"configurable": {"thread_id": "test-123"}}
    )

    # Verify all messages have proper format
    for i, msg in enumerate(result["messages"]):
        assert hasattr(msg, "content"), f"Message {i} missing content"
        assert hasattr(msg, "type"), f"Message {i} missing type"
        print(f"✅ Message {i} valid: {type(msg).__name__}")
```

---

## Best Practices

### 1. Always Use Message Classes

**Prefer:**
```python
return {"messages": [AIMessage(content=response)]}
```

**Over:**
```python
return {"messages": [{"role": "assistant", "content": response}]}
```

**Why:** Type safety, better IDE support, catches errors early

### 2. Never Return Plain Strings

**Never:**
```python
return {"messages": [response_text]}  # ❌
```

**Always:**
```python
return {"messages": [AIMessage(content=response_text)]}  # ✅
```

### 3. Use Type Hints

```python
from langchain_core.messages import BaseMessage

def agent_node(state: State) -> dict:
    """Type hints help catch format errors"""
    pass
```

### 4. Validate Before Returning

```python
def agent_node(state: State) -> dict:
    response = generate_response(state)

    # Validate
    validate_message_format([response])

    return {"messages": [response]}
```

### 5. Test Message Format Locally

Before connecting to Agent Chat UI:
```python
# Test script
result = app.invoke({"messages": [HumanMessage(content="Test")]})
validate_message_format(result["messages"])
```

---

## Troubleshooting

### KeyError: 'role'

**Problem:** Message missing `role` field

**Solution:** See `references/message-format-errors.md`

### Message Not Displaying in UI

**Problem:** Message format accepted but not rendering

**Checklist:**
- [ ] Message has `content` field
- [ ] `content` is a string (not dict/list)
- [ ] Message type is valid (user/assistant/system/tool)
- [ ] No circular references in message data

### Tool Messages Not Working

**Problem:** Tool results not displaying

**Requirements:**
- Must use `ToolMessage` class or dict with `"role": "tool"`
- Must include `tool_call_id` matching original tool call
- `content` must be string (use `json.dumps()` for dicts)

---

## Resources

- **Error Reference:** `references/message-format-errors.md`
- **Debugging Guide:** `references/debugging-agents.md`
- **Working Example:** `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- **Message Conversion:** `apps/resume-agent-langgraph/src/resume_agent/llm/messages.py`
- **LangChain Messages Docs:** https://python.langchain.com/docs/concepts/messages
