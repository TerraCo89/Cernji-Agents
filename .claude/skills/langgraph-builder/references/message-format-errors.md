# Message Format Errors - KeyError: 'role'

**CRITICAL ISSUE**: The most common error when connecting LangGraph agents to Agent Chat UI.

## The Error

```
KeyError: 'role'
```

This error occurs in the streaming pipeline when Agent Chat UI receives a message object from your LangGraph agent that's missing the required `role` field.

## Root Cause

Agent Chat UI expects ALL messages to follow the OpenAI/LangChain message schema with a **required** `role` field. When your agent returns messages in an incorrect format, the SDK attempts to access `message['role']` and fails with a KeyError.

**Where it breaks:**
- During streaming responses
- When processing agent state updates
- In the message display pipeline

---

## Common Scenarios Causing This Error

### 1. Returning Plain Strings Instead of Message Objects

**❌ INCORRECT:**
```python
def agent_node(state):
    return {
        "messages": ["Here's your response"]  # Plain string - NO!
    }
```

**✅ CORRECT:**
```python
from langchain_core.messages import AIMessage

def agent_node(state):
    return {
        "messages": [
            AIMessage(content="Here's your response")  # Message object
        ]
    }
```

**Why this happens:**
- Copy-paste from simple examples
- Not understanding LangChain message types
- Trying to simplify the code

---

### 2. Using Dictionary Without 'role' Field

**❌ INCORRECT:**
```python
def agent_node(state):
    return {
        "messages": [
            {"content": "Hello"}  # Missing 'role'
        ]
    }
```

**✅ CORRECT:**
```python
def agent_node(state):
    return {
        "messages": [
            {
                "role": "assistant",  # Required field
                "content": "Hello"
            }
        ]
    }
```

**Why this happens:**
- Forgetting required schema fields
- Mixing message formats
- Incomplete documentation reading

---

### 3. Appending to Messages Incorrectly

**❌ INCORRECT:**
```python
def agent_node(state):
    state["messages"].append("New message")  # Direct string append
    return state
```

**✅ CORRECT:**
```python
from langchain_core.messages import AIMessage

def agent_node(state):
    state["messages"].append(
        AIMessage(content="New message")
    )
    return state
```

**Why this happens:**
- Treating messages like a regular list
- Not using the reducer function properly
- Direct state mutation

---

### 4. Tool Call Results Without Proper Format

**❌ INCORRECT:**
```python
def tool_node(state):
    result = some_tool()
    return {
        "messages": [result]  # Raw tool result
    }
```

**✅ CORRECT:**
```python
from langchain_core.messages import ToolMessage

def tool_node(state):
    result = some_tool()
    return {
        "messages": [
            ToolMessage(
                content=str(result),
                tool_call_id=state["messages"][-1].tool_calls[0]["id"]
            )
        ]
    }
```

**Why this happens:**
- Not understanding tool message format
- Missing `tool_call_id` requirement
- Returning raw API responses

---

### 5. LangGraph SDK Message Format Mismatch

**❌ INCORRECT:**
```python
def chat_node(state):
    # LangGraph SDK uses {"type": "human"} format
    # But LLM APIs expect {"role": "user"}
    messages = state["messages"]  # Pass directly to LLM

    response = llm.invoke(messages)  # API error!
    return {"messages": [response]}
```

**✅ CORRECT:**
```python
def chat_node(state):
    # Convert LangGraph SDK format to API format
    api_messages = convert_langgraph_messages_to_api_format(state["messages"])

    response = llm.invoke(api_messages)

    return {
        "messages": [{
            "role": "assistant",
            "content": response
        }]
    }

def convert_langgraph_messages_to_api_format(messages: list) -> list:
    """Convert LangGraph SDK format to API format"""
    api_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role") or msg.get("type")
            if role == "human":
                role = "user"
            api_messages.append({
                "role": role,
                "content": msg["content"]
            })
    return api_messages
```

**Why this happens:**
- LangGraph SDK uses `{"type": "human"}` format
- LLM APIs expect `{"role": "user"}` format
- Need explicit conversion between formats

**Reference:** `apps/resume-agent-langgraph/src/resume_agent/llm/messages.py`

---

### 6. Missing Message Type Entirely

**❌ INCORRECT:**
```python
def agent_node(state):
    return {
        "messages": [
            {
                "content": "Hello",
                "timestamp": "2025-01-01"
            }
        ]
    }
```

**✅ CORRECT:**
```python
def agent_node(state):
    return {
        "messages": [
            {
                "role": "assistant",
                "content": "Hello",
                # Optional: additional metadata
                "metadata": {
                    "timestamp": "2025-01-01"
                }
            }
        ]
    }
```

---

### 7. Returning Nested Message Structures

**❌ INCORRECT:**
```python
def agent_node(state):
    return {
        "messages": [
            {
                "response": {
                    "role": "assistant",
                    "content": "Hello"
                }
            }
        ]
    }
```

**✅ CORRECT:**
```python
def agent_node(state):
    return {
        "messages": [
            {
                "role": "assistant",
                "content": "Hello"
            }
        ]
    }
```

---

## Quick Diagnosis

### If you see `KeyError: 'role'`, check:

1. **Are you using plain strings?**
   - Search for: `"messages": ["string"]`
   - Replace with: `"messages": [AIMessage(content="string")]`

2. **Are you using dicts without 'role'?**
   - Search for: `{"content": ...}` without `"role"`
   - Add: `"role": "assistant"` or use `AIMessage`

3. **Are you mutating state directly?**
   - Search for: `state["messages"].append("string")`
   - Replace with: `state["messages"].append(AIMessage(...))`

4. **Are you converting message formats?**
   - Check if you're passing LangGraph SDK messages directly to LLM APIs
   - Add conversion function: `convert_langgraph_messages_to_api_format()`

5. **Are tool results properly formatted?**
   - Search for: tool call results
   - Ensure wrapped in `ToolMessage` objects

---

## Error Stack Trace Example

When this error occurs, you'll see something like:

```
Traceback (most recent call last):
  File "langgraph-sdk/streaming.py", line 123, in stream_messages
    role = message['role']
KeyError: 'role'
```

**This means:**
- Your agent returned a message without `role` field
- The streaming pipeline tried to process it
- UI couldn't display the message

---

## Prevention

### Use Type Hints

```python
from langchain_core.messages import BaseMessage, AIMessage
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def agent_node(state: State) -> dict:
    """Type hints enforce correct message types"""
    return {
        "messages": [AIMessage(content="Response")]
    }
```

### Use Validation Helper

```python
from langchain_core.messages import BaseMessage

def validate_messages(messages: list) -> bool:
    """Validate all messages have proper format"""
    for i, msg in enumerate(messages):
        # Check if it's a LangChain message object
        if isinstance(msg, BaseMessage):
            continue

        # If it's a dict, verify it has 'role'
        if isinstance(msg, dict):
            if "role" not in msg:
                raise ValueError(
                    f"Message {i} missing 'role' field: {msg}"
                )
            if "content" not in msg:
                raise ValueError(
                    f"Message {i} missing 'content' field: {msg}"
                )
        else:
            raise ValueError(
                f"Message {i} has invalid type {type(msg)}: {msg}"
            )

    return True

def agent_node(state: State) -> dict:
    response = generate_response(state)

    # Validate before returning
    validate_messages(state["messages"])

    return state
```

### Test Before Deploying

```python
from langchain_core.messages import HumanMessage

def test_agent_message_format():
    """Test that agent returns proper message format"""
    result = app.invoke({
        "messages": [HumanMessage(content="Test")]
    })

    # Verify all messages have proper format
    for msg in result["messages"]:
        assert hasattr(msg, "content"), "Message missing content"
        assert hasattr(msg, "type"), "Message missing type"
        print(f"✅ Message valid: {type(msg).__name__}")

# Run before connecting to Agent Chat UI
test_agent_message_format()
```

---

## Multi-Agent Systems

When routing between agents, ensure ALL agents return proper format:

```python
def resume_agent(state):
    resume_content = generate_resume(state)

    return {
        "messages": [
            AIMessage(
                content="I've created your resume.",
                additional_kwargs={
                    "artifact": {
                        "type": "resume",
                        "content": resume_content
                    }
                }
            )
        ]
    }

def japanese_tutor_agent(state):
    flashcards = generate_flashcards(state)

    return {
        "messages": [
            AIMessage(
                content="Here are your flashcards.",
                additional_kwargs={
                    "artifact": {
                        "type": "flashcard_deck",
                        "content": flashcards
                    }
                }
            )
        ]
    }

def route_to_agent(state):
    agent_type = state.get("agent_type", "resume")

    if agent_type == "resume":
        return resume_agent(state)
    else:
        return japanese_tutor_agent(state)
```

---

## SDK Version Compatibility

**Check versions:**
```bash
pip show langgraph
npm list @langchain/langgraph-sdk
```

**Ensure compatibility:**
- `langgraph` (Python) >= 0.2.0
- `@langchain/langgraph-sdk` (TypeScript) >= 0.0.20

**Update if needed:**
```bash
pip install -U langgraph
npm install @langchain/langgraph-sdk@latest
```

---

## Related Resources

- **Message Format Guide:** `references/message-format-guide.md`
- **Debugging Guide:** `references/debugging-agents.md`
- **Message Conversion:** `apps/resume-agent-langgraph/src/resume_agent/llm/messages.py`
- **Working Example:** `apps/resume-agent-langgraph/resume_agent_langgraph.py:114-170`

---

## Still Getting the Error?

If you've checked all the above and still see `KeyError: 'role'`:

1. **Add logging to every node:**
```python
import logging
logger = logging.getLogger(__name__)

def agent_node(state):
    logger.info(f"Message types: {[type(m) for m in state['messages']]}")
    logger.info(f"Message content: {state['messages']}")
    # ... rest of node
```

2. **Test with minimal graph:**
Use the working example from `references/message-format-guide.md`

3. **Check for middleware interference:**
If you have custom middleware, it might be modifying messages

4. **Inspect the full state:**
Log the entire state object being returned from each node

5. **Use LangGraph Studio:**
Visual debugging at `http://localhost:2024/studio`
