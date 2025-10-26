# LangGraph Message Handling Best Practices

## Overview

This document provides best practices for handling messages in LangGraph StateGraph implementations, based on research of official documentation and analysis of the Resume Agent LangGraph codebase.

## Message Format Compatibility

### The Two Message Worlds

LangGraph operates in two message format ecosystems:

1. **LangGraph SDK Format** (StateGraph internal):
   - LangChain Message objects: `HumanMessage`, `AIMessage`, `SystemMessage`
   - Dict format with `type` field: `{"type": "human", "content": "text"}`
   - Dict format with `role` field: `{"role": "user", "content": "text"}`

2. **LLM API Format** (Claude, OpenAI):
   - Dictionary with `role` and `content`: `{"role": "user", "content": "text"}`
   - Roles: `"user"`, `"assistant"`, `"system"`

### add_messages Reducer Behavior

The `add_messages` reducer from `langgraph.graph.message` accepts all three formats:

```python
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

# All these work:
add_messages([], [HumanMessage(content="Hi")])
add_messages([], [{"type": "human", "content": "Hi"}])
add_messages([], [{"role": "user", "content": "Hi"}])
add_messages([], [("user", "Hi")])  # Tuple shorthand
```

## Common Pitfall: KeyError 'role'

### Problem

```python
# This code fails with KeyError: 'role'
def chatbot_node(state):
    messages = state["messages"]
    # Calling LLM API directly with LangGraph messages
    response = anthropic_client.messages.create(
        messages=messages,  # ❌ Wrong format!
        ...
    )
```

### Root Cause

LangGraph's `add_messages` stores messages in LangChain format internally. When you pass these directly to an LLM API, the API expects `role` field but gets `type` field instead.

### Solution Pattern

Always convert messages before calling LLM APIs:

```python
def chatbot_node(state):
    # Convert from LangGraph format to API format
    api_messages = convert_langgraph_messages_to_api_format(state["messages"])

    # Now safe to call API
    response = anthropic_client.messages.create(
        messages=api_messages,
        ...
    )

    # Return in LangGraph-compatible format
    return {
        "messages": [{"role": "assistant", "content": response.content}]
    }
```

## Message Conversion Utilities

From the Resume Agent LangGraph codebase (`src/resume_agent/llm/messages.py`):

```python
"""Message format conversion utilities for LangGraph SDK compatibility."""

from typing import Any, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


def convert_langgraph_messages_to_api_format(
    messages: list[Union[BaseMessage, dict]]
) -> list[dict]:
    """
    Convert LangGraph SDK message format to LLM API format.

    LangGraph SDK uses:
    - HumanMessage, AIMessage, SystemMessage objects
    - OR dicts with 'type' field: "human", "ai", "system"

    LLM APIs expect:
    - role: "user", "assistant", "system"
    - content: string

    Examples:
        >>> from langchain_core.messages import HumanMessage
        >>> msgs = [HumanMessage(content="Hello")]
        >>> convert_langgraph_messages_to_api_format(msgs)
        [{"role": "user", "content": "Hello"}]
    """
    api_messages = []

    for msg in messages:
        # Handle BaseMessage objects
        if isinstance(msg, BaseMessage):
            role = _convert_message_type_to_role(msg)
            content = msg.content

        # Handle dict format
        elif isinstance(msg, dict):
            # Support both 'role' and 'type' fields
            role = msg.get("role") or _convert_type_to_role(msg.get("type", "human"))
            content = msg.get("content", "")

        else:
            continue

        # Handle multimodal content (arrays)
        if isinstance(content, list):
            content = _extract_text_from_content_blocks(content)

        api_messages.append({
            "role": role,
            "content": content
        })

    return api_messages


def _convert_message_type_to_role(msg: BaseMessage) -> str:
    """Convert LangChain BaseMessage to API role."""
    if isinstance(msg, HumanMessage):
        return "user"
    elif isinstance(msg, AIMessage):
        return "assistant"
    elif isinstance(msg, SystemMessage):
        return "system"
    else:
        return "user"


def _convert_type_to_role(msg_type: str) -> str:
    """Convert LangGraph SDK message type to API role."""
    mapping = {
        "human": "user",
        "ai": "assistant",
        "system": "system",
        "tool": "assistant",
    }
    return mapping.get(msg_type, "user")


def _extract_text_from_content_blocks(content_blocks: list[Any]) -> str:
    """Extract text from multimodal content array."""
    text_parts = []

    for block in content_blocks:
        if isinstance(block, dict):
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif "text" in block:
                text_parts.append(block["text"])
        elif isinstance(block, str):
            text_parts.append(block)

    return " ".join(filter(None, text_parts))
```

## Node Implementation Patterns

### Pattern 1: Simple Response Node

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]


def simple_node(state: State) -> dict:
    """
    Simple node returning a text response.

    Best for: Static responses, simple logic
    """
    return {
        "messages": [{"role": "assistant", "content": "Hello!"}]
    }
```

### Pattern 2: LLM Integration Node

```python
def llm_node(state: State) -> dict:
    """
    Node calling external LLM API.

    Best for: Claude, OpenAI, or custom LLM integrations
    """
    from resume_agent.llm import call_llm, convert_langgraph_messages_to_api_format

    # Convert to API format
    api_messages = convert_langgraph_messages_to_api_format(state["messages"])

    # Call LLM
    response = call_llm(api_messages, system_prompt="You are helpful")

    # Return in compatible format
    return {
        "messages": [{"role": "assistant", "content": response}]
    }
```

### Pattern 3: Multi-Field Update Node

```python
class ExtendedState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str
    processed: bool


def multi_update_node(state: ExtendedState) -> dict:
    """
    Node updating multiple state fields.

    Best for: Complex workflows with multiple state components
    """
    # Process data
    result = process_data(state["context"])

    return {
        "messages": [{"role": "assistant", "content": f"Processed: {result}"}],
        "context": result,
        "processed": True
    }
```

### Pattern 4: Error Handling Node

```python
def safe_llm_node(state: State) -> dict:
    """
    Node with robust error handling.

    Best for: Production systems requiring reliability
    """
    try:
        api_messages = convert_langgraph_messages_to_api_format(state["messages"])
        response = call_llm(api_messages)

        return {
            "messages": [{"role": "assistant", "content": response}]
        }

    except Exception as e:
        # Return error message in compatible format
        return {
            "messages": [{
                "role": "assistant",
                "content": f"Error: {str(e)}"
            }]
        }
```

## State Schema Best Practices

### When to Use TypedDict vs MessagesState

| Scenario | Recommended Approach | Rationale |
|----------|---------------------|-----------|
| Simple chatbot | `MessagesState` | Pre-configured, less code |
| Chat + custom fields | Subclass `MessagesState` | Inherit message handling |
| Complex multi-workflow | `TypedDict` + `add_messages` | Full control |
| Need type validation | `TypedDict` (not Pydantic) | Best performance |

### TypedDict Pattern (Full Control)

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class CustomState(TypedDict):
    """Full control over state schema."""
    messages: Annotated[list, add_messages]  # Message history
    context: str                              # Additional context
    iteration: int                            # Loop counter
    errors: list[str]                         # Error tracking
```

### MessagesState Subclass Pattern (Convenience)

```python
from langgraph.graph import MessagesState


class ExtendedState(MessagesState):
    """
    Inherits: messages: Annotated[list, add_messages]

    Add custom fields while getting message handling for free.
    """
    documents: list[str]
    query_count: int
```

## Message ID and Update Behavior

### Understanding Message IDs

```python
from langchain_core.messages import HumanMessage

# Messages get auto-generated IDs
msg1 = HumanMessage(content="Hello")
print(msg1.id)  # UUID automatically assigned

# Explicit ID
msg2 = HumanMessage(content="Hello", id="msg_1")
```

### Update vs Append Behavior

```python
from langgraph.graph.message import add_messages

# Append: Different IDs
msgs1 = [HumanMessage(content="First", id="1")]
msgs2 = [HumanMessage(content="Second", id="2")]
result = add_messages(msgs1, msgs2)
# Result: [HumanMessage(id="1"), HumanMessage(id="2")]

# Update: Same ID
msgs1 = [HumanMessage(content="Original", id="1")]
msgs2 = [HumanMessage(content="Updated", id="1")]
result = add_messages(msgs1, msgs2)
# Result: [HumanMessage(content="Updated", id="1")]  # REPLACED!
```

### Use Case: Human-in-the-Loop

```python
def review_node(state: State) -> dict:
    """
    Update a message after human review.

    Use same ID to replace the message.
    """
    from langgraph.types import interrupt

    # Get human feedback
    feedback = interrupt({"question": "Review this message"})

    # Get the last message ID
    last_msg_id = state["messages"][-1].id

    # Return updated message with same ID (replaces original)
    return {
        "messages": [HumanMessage(
            content=feedback["content"],
            id=last_msg_id  # Same ID = update, not append
        )]
    }
```

## Testing Message Handling

### Unit Test Pattern

```python
def test_message_conversion():
    """Test message format conversion."""
    from resume_agent.llm import convert_langgraph_messages_to_api_format
    from langchain_core.messages import HumanMessage, AIMessage

    # Test BaseMessage objects
    messages = [
        HumanMessage(content="Hello"),
        AIMessage(content="Hi there!")
    ]

    result = convert_langgraph_messages_to_api_format(messages)

    assert result == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]


def test_node_return_format():
    """Test node returns proper format."""
    state = {"messages": [{"role": "user", "content": "Test"}]}

    result = my_node(state)

    # Verify return format
    assert "messages" in result
    assert isinstance(result["messages"], list)
    assert all("role" in msg and "content" in msg for msg in result["messages"])
```

## Performance Considerations

### Message List Growth

```python
# ❌ Bad: Unbounded message list
class UnboundedState(TypedDict):
    messages: Annotated[list, add_messages]  # Can grow infinitely


# ✅ Good: Trim message history
def trimmed_node(state: State) -> dict:
    """Keep only last N messages."""
    MAX_MESSAGES = 20

    # Get last N messages
    messages = state["messages"][-MAX_MESSAGES:]

    # Process with trimmed history
    response = llm.invoke(messages)

    return {"messages": [response]}
```

### Large Content Handling

```python
def handle_large_content(state: State) -> dict:
    """Handle large message content efficiently."""
    # Summarize old messages
    if len(state["messages"]) > 10:
        old_messages = state["messages"][:-5]
        recent_messages = state["messages"][-5:]

        summary = summarize_messages(old_messages)

        # Replace old messages with summary
        return {
            "messages": [
                {"role": "system", "content": f"Summary: {summary}"},
                *recent_messages
            ]
        }

    # Process normally
    response = llm.invoke(state["messages"])
    return {"messages": [response]}
```

## Debugging Tips

### Print Message Format

```python
def debug_messages(state: State) -> dict:
    """Debug node to inspect message format."""
    print("\n=== MESSAGE DEBUG ===")
    for i, msg in enumerate(state["messages"]):
        if isinstance(msg, dict):
            print(f"{i}: DICT - {msg.get('role') or msg.get('type')}: {msg.get('content', '')[:50]}")
        else:
            print(f"{i}: {type(msg).__name__}: {msg.content[:50]}")
    print("===================\n")

    return state  # Pass through
```

### Validate Message Structure

```python
def validate_messages(messages: list) -> bool:
    """Validate message list structure."""
    for msg in messages:
        # Check dict format
        if isinstance(msg, dict):
            if "role" not in msg and "type" not in msg:
                print(f"❌ Missing role/type: {msg}")
                return False
            if "content" not in msg:
                print(f"❌ Missing content: {msg}")
                return False

        # Check BaseMessage format
        elif hasattr(msg, "content"):
            if not msg.content:
                print(f"❌ Empty content: {msg}")
                return False

        else:
            print(f"❌ Unknown format: {type(msg)}")
            return False

    return True
```

## Real-World Example: Resume Agent

From `apps/resume-agent-langgraph/src/resume_agent/nodes/conversation.py`:

```python
"""Conversation nodes for chat functionality."""

from ..state import ConversationState
from ..llm import call_llm, convert_langgraph_messages_to_api_format
from ..prompts import CONVERSATION_SYSTEM


def chat_node(state: ConversationState) -> dict:
    """
    Process user message with LLM.

    This demonstrates:
    1. Message format conversion
    2. LLM API integration
    3. Error handling
    4. Compatible return format
    """
    try:
        # Convert from LangGraph SDK format to API format
        # Handles both {"type": "human"} and {"role": "user"}
        api_messages = convert_langgraph_messages_to_api_format(state["messages"])

        # Call LLM with converted messages
        assistant_message = call_llm(api_messages, CONVERSATION_SYSTEM)

        # Return in compatible format (will be appended by add_messages)
        return {
            "messages": [{
                "role": "assistant",
                "content": assistant_message
            }]
        }

    except Exception as e:
        # Error handling with compatible format
        return {
            "messages": [{
                "role": "assistant",
                "content": f"Sorry, I encountered an error: {str(e)}"
            }]
        }


def get_user_input_node(state: ConversationState) -> dict:
    """
    Get user input via CLI.

    This demonstrates:
    1. Multi-field state updates
    2. Conditional logic based on input
    3. Control flow with state flags
    """
    # Display last assistant message
    if state["messages"]:
        last_msg = state["messages"][-1]
        if last_msg["role"] == "assistant":
            print(f"\n🤖 Assistant: {last_msg['content']}")

    # Get user input
    user_input = input("👤 You: ").strip()

    # Check for exit command
    if user_input.lower() in ['exit', 'quit']:
        return {
            "should_continue": False,
            "messages": [{"role": "user", "content": user_input}]
        }

    # Normal response
    return {
        "should_continue": True,
        "messages": [{"role": "user", "content": user_input}]
    }
```

## Summary Checklist

✅ **Do:**
- Use `Annotated[list, add_messages]` for message history
- Convert messages before calling LLM APIs
- Return messages as dicts with `role` and `content`
- Handle both LangChain objects and dict formats
- Use TypedDict for best performance
- Implement error handling in nodes
- Test message format compatibility

❌ **Don't:**
- Pass LangGraph messages directly to LLM APIs
- Use Pydantic BaseModel for state (slower)
- Forget to handle multimodal content
- Mix message formats inconsistently
- Let message lists grow unbounded
- Skip message validation in tests

## References

- **LangGraph Official Docs**: https://langchain-ai.github.io/langgraph/
- **Message Handling**: https://langchain-ai.github.io/langgraph/concepts/low_level/
- **State Customization**: https://langchain-ai.github.io/langgraph/tutorials/get-started/5-customize-state/
- **Resume Agent Source**: `apps/resume-agent-langgraph/src/resume_agent/`
