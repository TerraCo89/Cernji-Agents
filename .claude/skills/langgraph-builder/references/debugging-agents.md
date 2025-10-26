# Debugging LangGraph Agents

Comprehensive guide for diagnosing and fixing LangGraph agent issues.

## Table of Contents

1. [Quick Diagnosis Checklist](#quick-diagnosis-checklist)
2. [Message Format Issues](#message-format-issues)
3. [Using LangGraph Studio](#using-langgraph-studio)
4. [Logging Strategies](#logging-strategies)
5. [Common Issues](#common-issues)
6. [Testing Strategies](#testing-strategies)

---

## Quick Diagnosis Checklist

Before diving deep, run through this checklist:

### Message Format Issues (Most Common)

- [ ] All messages have `role` field (if using dicts)
- [ ] All messages use `AIMessage`/`HumanMessage` classes (recommended)
- [ ] No plain strings in messages array
- [ ] Tool messages include `tool_call_id`
- [ ] State schema uses `Annotated[list[BaseMessage], add_messages]`

### Graph Configuration

- [ ] Graph compiled with checkpointer
- [ ] `langgraph.json` points to correct graph builder function
- [ ] Graph builder returns compiled graph with checkpointer
- [ ] Environment variables loaded (`.env` file exists)

### Server and UI Connection

- [ ] LangGraph server running on port 2024
- [ ] Agent Chat UI `.env` has correct `NEXT_PUBLIC_API_URL`
- [ ] `NEXT_PUBLIC_ASSISTANT_ID` matches `langgraph.json` graph key
- [ ] No CORS or firewall issues

### API Keys

- [ ] Correct API key in `apps/[agent-name]/.env`
- [ ] API key valid and not expired
- [ ] Correct provider selected (`LLM_PROVIDER=claude` or `openai`)

---

## Message Format Issues

### Diagnosing KeyError: 'role'

**Step 1: Add logging to all nodes**

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def agent_node(state):
    logger.info("=" * 60)
    logger.info("AGENT NODE CALLED")
    logger.info(f"Input message count: {len(state['messages'])}")

    # Log each message
    for i, msg in enumerate(state["messages"]):
        logger.info(f"Message {i}:")
        logger.info(f"  Type: {type(msg)}")
        logger.info(f"  Content: {msg if isinstance(msg, str) else getattr(msg, 'content', msg)}")

        # Check for role field
        if isinstance(msg, dict):
            logger.info(f"  Has 'role': {'role' in msg}")
            logger.info(f"  Has 'content': {'content' in msg}")

    # Generate response
    response = generate_response(state)

    logger.info(f"Response type: {type(response)}")
    logger.info(f"Response: {response}")
    logger.info("=" * 60)

    return {"messages": [response]}
```

**Step 2: Run locally and check logs**

```bash
cd apps/[agent-name]
langgraph dev
```

Look for:
- Messages without `role` field
- Plain strings in messages array
- Incorrect message types

**Step 3: Validate message format**

```python
from langchain_core.messages import BaseMessage

def validate_and_log_messages(messages, location="unknown"):
    """Validate and log message format"""
    logger.info(f"Validating messages at: {location}")

    for i, msg in enumerate(messages):
        logger.info(f"Message {i}:")

        # Check type
        if isinstance(msg, BaseMessage):
            logger.info(f"  ✅ LangChain message: {type(msg).__name__}")
            logger.info(f"  Content: {msg.content[:100]}...")
        elif isinstance(msg, dict):
            logger.info(f"  ⚠️  Dict message")
            if "role" in msg:
                logger.info(f"  ✅ Has 'role': {msg['role']}")
            else:
                logger.error(f"  ❌ MISSING 'role' field!")
                logger.error(f"  Full message: {msg}")
                raise ValueError(f"Message {i} missing 'role' field")

            if "content" in msg:
                logger.info(f"  ✅ Has 'content'")
            else:
                logger.error(f"  ❌ MISSING 'content' field!")
                raise ValueError(f"Message {i} missing 'content' field")
        else:
            logger.error(f"  ❌ Invalid type: {type(msg)}")
            logger.error(f"  Value: {msg}")
            raise ValueError(f"Message {i} is not a valid message type")

    logger.info("✅ All messages valid")
    return True

# Use in nodes
def agent_node(state):
    validate_and_log_messages(state["messages"], "agent_node input")

    response = generate_response(state)

    validate_and_log_messages([response], "agent_node output")

    return {"messages": [response]}
```

---

## Using LangGraph Studio

LangGraph Studio provides visual debugging for your agent.

### Accessing Studio

1. Start LangGraph dev server:
```bash
cd apps/[agent-name]
langgraph dev
```

2. Open Studio UI:
```
http://localhost:2024/studio
```

### Features

**Graph Visualization:**
- See all nodes and edges
- Identify flow issues
- Verify conditional routing

**State Inspection:**
- View state at each node
- Check message format
- Inspect custom state fields

**Execution Tracing:**
- Step through execution
- See node order
- Identify where errors occur

**Message Timeline:**
- View all messages in order
- Check message format
- Verify conversation flow

### Using Studio for Message Format Debugging

1. **Run a test query** through Studio
2. **Click on each node** to inspect state
3. **Check messages array** at each step
4. **Look for**:
   - Plain strings instead of message objects
   - Dicts missing `role` field
   - Incorrect message types

---

## Logging Strategies

### Basic Logging Setup

```python
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

### Node-Level Logging

```python
def logged_agent_node(state):
    """Agent node with comprehensive logging"""
    logger.info("=" * 80)
    logger.info("AGENT NODE EXECUTION")
    logger.info("=" * 80)

    # Log input state
    logger.info(f"State keys: {list(state.keys())}")
    logger.info(f"Message count: {len(state['messages'])}")

    # Log each message
    for i, msg in enumerate(state["messages"]):
        logger.info(f"\nMessage {i}:")
        logger.info(f"  Type: {type(msg).__name__}")
        if hasattr(msg, "type"):
            logger.info(f"  Message type: {msg.type}")
        if hasattr(msg, "content"):
            logger.info(f"  Content: {msg.content[:200]}...")
        if isinstance(msg, dict):
            logger.info(f"  Dict keys: {list(msg.keys())}")
            logger.info(f"  Full dict: {json.dumps(msg, indent=2, default=str)}")

    # Generate response
    try:
        response = generate_response(state)
        logger.info(f"\nGenerated response type: {type(response).__name__}")
        logger.info(f"Response content: {response.content[:200]}...")
    except Exception as e:
        logger.error(f"Error generating response: {e}", exc_info=True)
        raise

    logger.info("=" * 80)
    return {"messages": [response]}
```

### Graph-Level Logging

```python
from langgraph.graph import StateGraph

def build_logged_graph():
    """Build graph with logging at each step"""
    graph = StateGraph(State)

    # Wrap each node with logging
    graph.add_node("agent", logged_agent_node)
    graph.add_node("tools", logged_tool_node)

    # Add edges
    graph.add_edge(START, "agent")
    graph.add_edge("agent", "tools")
    graph.add_edge("tools", END)

    # Compile
    app = graph.compile(checkpointer=checkpointer)

    # Wrap invoke with logging
    original_invoke = app.invoke

    def logged_invoke(*args, **kwargs):
        logger.info("\n" + "=" * 80)
        logger.info("GRAPH INVOCATION START")
        logger.info("=" * 80)

        try:
            result = original_invoke(*args, **kwargs)
            logger.info("\n" + "=" * 80)
            logger.info("GRAPH INVOCATION SUCCESS")
            logger.info(f"Final message count: {len(result['messages'])}")
            logger.info("=" * 80)
            return result
        except Exception as e:
            logger.error("\n" + "=" * 80)
            logger.error("GRAPH INVOCATION FAILED")
            logger.error(f"Error: {e}", exc_info=True)
            logger.error("=" * 80)
            raise

    app.invoke = logged_invoke
    return app
```

### Conditional Logging

```python
import os

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

def debug_log(message, data=None):
    """Log only when DEBUG=true"""
    if DEBUG:
        logger.info(message)
        if data:
            logger.info(json.dumps(data, indent=2, default=str))

def agent_node(state):
    debug_log("Agent node called", {"message_count": len(state["messages"])})

    response = generate_response(state)

    debug_log("Response generated", {"type": type(response).__name__})

    return {"messages": [response]}
```

**Enable debug logging:**
```bash
# .env
DEBUG=true
```

---

## Common Issues

### Issue 1: Messages Not Persisting

**Symptom:** Agent forgets previous messages

**Diagnosis:**
```python
def check_checkpointer():
    """Verify checkpointer is working"""
    app = build_web_conversation_graph()

    # Check if checkpointer exists
    if app.checkpointer is None:
        logger.error("❌ No checkpointer configured!")
        return False

    logger.info(f"✅ Checkpointer: {type(app.checkpointer).__name__}")

    # Test persistence
    config = {"configurable": {"thread_id": "test-123"}}

    # First message
    result1 = app.invoke(
        {"messages": [HumanMessage(content="Message 1")]},
        config=config
    )
    logger.info(f"After message 1: {len(result1['messages'])} messages")

    # Second message (should remember first)
    result2 = app.invoke(
        {"messages": [HumanMessage(content="Message 2")]},
        config=config
    )
    logger.info(f"After message 2: {len(result2['messages'])} messages")

    if len(result2['messages']) < len(result1['messages']) + 2:
        logger.error("❌ Messages not persisting!")
        return False

    logger.info("✅ Messages persisting correctly")
    return True
```

**Solution:**
```python
from langgraph.checkpoint.memory import MemorySaver

def build_web_conversation_graph():
    graph = StateGraph(State)
    # ... add nodes and edges ...

    # MUST have checkpointer for persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
```

---

### Issue 2: Graph Not Found

**Symptom:** "Assistant 'agent' not found"

**Diagnosis:**
```bash
# Check what graphs are available
curl http://localhost:2024/graphs

# Should return:
# {"graphs": ["agent"]}
```

**Solution:**
1. Verify `langgraph.json` graph key matches `NEXT_PUBLIC_ASSISTANT_ID`:
```json
{
  "graphs": {
    "agent": "./agent.py:build_web_conversation_graph"
  }
}
```

```bash
# .env
NEXT_PUBLIC_ASSISTANT_ID=agent  # Must match!
```

2. Verify function exists and is exported:
```python
# agent.py
def build_web_conversation_graph():
    # ... graph building code ...
    return graph.compile(checkpointer=checkpointer)
```

3. Restart LangGraph server

---

### Issue 3: API Key Errors

**Symptom:** "ANTHROPIC_API_KEY not found"

**Diagnosis:**
```python
import os
from dotenv import load_dotenv

def check_env_vars():
    """Verify environment variables"""
    load_dotenv()

    # Check provider
    provider = os.getenv("LLM_PROVIDER", "claude")
    logger.info(f"LLM_PROVIDER: {provider}")

    # Check appropriate API key
    if provider == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            logger.info(f"✅ ANTHROPIC_API_KEY found (length: {len(api_key)})")
        else:
            logger.error("❌ ANTHROPIC_API_KEY not found")
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            logger.info(f"✅ OPENAI_API_KEY found (length: {len(api_key)})")
        else:
            logger.error("❌ OPENAI_API_KEY not found")

check_env_vars()
```

**Solution:**
1. Ensure `.env` file exists in agent directory
2. Add correct API key:
```bash
# apps/[agent-name]/.env
ANTHROPIC_API_KEY=sk-ant-...
```
3. Restart LangGraph server to load new env vars

---

### Issue 4: Slow Response Times

**Symptom:** UI shows "Thinking..." for >10 seconds

**Diagnosis:**
```python
import time

def timed_agent_node(state):
    """Measure node execution time"""
    start_time = time.time()

    response = generate_response(state)

    duration = time.time() - start_time
    logger.info(f"Agent node took {duration:.2f} seconds")

    if duration > 5:
        logger.warning("⚠️  Slow response time!")

    return {"messages": [response]}
```

**Solution:**
1. Use faster model:
```bash
# .env
OPENAI_MODEL=gpt-4o-mini  # Faster
CLAUDE_MODEL=claude-sonnet-4-5  # Fast
```

2. Reduce API calls in nodes
3. Implement streaming for better UX
4. Cache expensive operations

---

### Issue 5: Tool Calls Not Working

**Symptom:** Tools not executing or results not displaying

**Diagnosis:**
```python
def debug_tool_calls(state):
    """Debug tool call handling"""
    last_message = state["messages"][-1]

    logger.info(f"Last message type: {type(last_message).__name__}")

    if hasattr(last_message, "tool_calls"):
        logger.info(f"Tool calls: {last_message.tool_calls}")
        if last_message.tool_calls:
            for tc in last_message.tool_calls:
                logger.info(f"  Tool: {tc['name']}")
                logger.info(f"  Args: {tc['args']}")
                logger.info(f"  ID: {tc['id']}")
    else:
        logger.info("No tool_calls attribute")
```

**Solution:**
```python
from langchain_core.messages import ToolMessage

def tool_execution_node(state):
    """Execute tools with proper message format"""
    last_message = state["messages"][-1]

    if not last_message.tool_calls:
        return {"messages": []}

    tool_messages = []
    for tool_call in last_message.tool_calls:
        # Execute tool
        result = execute_tool(tool_call["name"], tool_call["args"])

        # MUST include tool_call_id
        tool_messages.append(
            ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]  # Required!
            )
        )

    return {"messages": tool_messages}
```

---

## Testing Strategies

### Unit Testing Nodes

```python
def test_agent_node_message_format():
    """Test node returns proper message format"""
    from langchain_core.messages import HumanMessage, AIMessage

    # Create test state
    state = {
        "messages": [HumanMessage(content="Test message")]
    }

    # Call node
    result = agent_node(state)

    # Assertions
    assert "messages" in result, "Result missing 'messages' key"
    assert len(result["messages"]) == 1, "Expected 1 message"

    msg = result["messages"][0]
    assert isinstance(msg, AIMessage), f"Expected AIMessage, got {type(msg)}"
    assert hasattr(msg, "content"), "Message missing 'content'"
    assert msg.content != "", "Message content is empty"

    logger.info("✅ Unit test passed")
```

### Integration Testing Graphs

```python
def test_full_graph_execution():
    """Test complete graph execution"""
    from langchain_core.messages import HumanMessage

    app = build_web_conversation_graph()

    # Test single invocation
    result = app.invoke(
        {"messages": [HumanMessage(content="Hello")]},
        config={"configurable": {"thread_id": "test-123"}}
    )

    # Verify result
    assert len(result["messages"]) >= 2, "Expected user + assistant messages"

    last_msg = result["messages"][-1]
    assert last_msg.type in ["ai", "assistant"], f"Expected AI message, got {last_msg.type}"

    # Test conversation persistence
    result2 = app.invoke(
        {"messages": [HumanMessage(content="What did I just say?")]},
        config={"configurable": {"thread_id": "test-123"}}
    )

    assert len(result2["messages"]) > len(result["messages"]), "Messages not persisting"

    logger.info("✅ Integration test passed")
```

### Load Testing

```python
import asyncio

async def test_concurrent_requests():
    """Test multiple concurrent conversations"""
    app = build_web_conversation_graph()

    async def single_conversation(thread_id):
        result = app.invoke(
            {"messages": [HumanMessage(content=f"Test {thread_id}")]},
            config={"configurable": {"thread_id": thread_id}}
        )
        return result

    # Run 10 concurrent conversations
    tasks = [single_conversation(f"thread-{i}") for i in range(10)]
    results = await asyncio.gather(*tasks)

    # Verify all succeeded
    assert len(results) == 10
    for result in results:
        assert len(result["messages"]) >= 2

    logger.info("✅ Load test passed")
```

---

## Debug Checklist

Before asking for help, verify:

- [ ] Added logging to all nodes
- [ ] Checked logs for errors
- [ ] Used LangGraph Studio to visualize execution
- [ ] Validated message format at each step
- [ ] Tested locally with minimal example
- [ ] Verified environment variables loaded
- [ ] Checked API key validity
- [ ] Confirmed checkpointer configured
- [ ] Tested with curl/Postman (bypassing UI)
- [ ] Reviewed all error messages and stack traces

---

## Getting Help

If still stuck after debugging:

1. **Capture full logs:**
```bash
langgraph dev > debug.log 2>&1
```

2. **Minimal reproduction:**
Create smallest possible example that reproduces issue

3. **Include context:**
- LangGraph version: `pip show langgraph`
- Python version: `python --version`
- Error messages and stack traces
- Relevant code snippets
- What you've tried

4. **Check resources:**
- **Error Reference:** `references/message-format-errors.md`
- **Message Guide:** `references/message-format-guide.md`
- **Working Example:** `apps/resume-agent-langgraph/`
- **LangGraph Docs:** https://python.langchain.com/docs/langgraph

---

## Resources

- **Message Format Errors:** `references/message-format-errors.md`
- **Message Format Guide:** `references/message-format-guide.md`
- **Chat UI Integration:** `references/chat-ui-integration.md`
- **LangGraph Patterns:** `references/langgraph-patterns.md`
- **Working Example:** `apps/resume-agent-langgraph/resume_agent_langgraph.py`
