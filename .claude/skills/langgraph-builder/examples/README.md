# LangGraph Builder Examples

Working code examples demonstrating LangGraph agent patterns with proper message handling, streaming, and Agent Chat UI integration.

## Examples

### 1. Minimal Agent (`minimal_agent.py`)

**A complete, production-ready agent in 200 lines.**

Features:
- ✅ Proper message handling (no KeyError: 'role')
- ✅ Memory persistence with checkpointing
- ✅ Multi-provider LLM support (Claude/OpenAI)
- ✅ FastAPI server with REST API
- ✅ Agent Chat UI compatibility

**Quick Start:**
```bash
# Set environment variables
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...
export LLM_PROVIDER=claude  # or "openai"

# Run test
python minimal_agent.py

# Start server
python minimal_agent.py --server
```

**Test the API:**
```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, my name is Alice", "thread_id": "test-123"}'

curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my name?", "thread_id": "test-123"}'
```

### 2. Streaming Agent (`streaming_agent.py`)

**Real-time streaming responses with three patterns.**

Features:
- ✅ Token-level streaming (real-time LLM output)
- ✅ Message-level streaming (complete messages)
- ✅ Server-Sent Events (SSE) for web frontends
- ✅ Non-streaming fallback

**Quick Start:**
```bash
export ANTHROPIC_API_KEY=sk-ant-...

# Start server
python streaming_agent.py --server

# Test streaming client
python streaming_agent.py --test
```

**Test Streaming Endpoints:**
```bash
# Token streaming (real-time)
curl -X POST http://localhost:8080/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me a story", "thread_id": "test"}'

# Message streaming (node-by-node)
curl -X POST http://localhost:8080/stream/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain LangGraph", "thread_id": "test"}'

# Non-streaming
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "thread_id": "test"}'
```

## Prerequisites

Install dependencies:
```bash
pip install langgraph langchain-core anthropic openai fastapi uvicorn
```

Or using the project's dependencies:
```bash
cd apps/resume-agent-langgraph
uv pip install -e .
```

## Environment Variables

Create a `.env` file:
```bash
# LLM Provider
LLM_PROVIDER=claude  # or "openai"

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Models (optional)
CLAUDE_MODEL=claude-sonnet-4-5
OPENAI_MODEL=gpt-4o-mini
```

## Agent Chat UI Integration

To connect these agents to the Agent Chat UI:

### Option 1: Using FastAPI Server

1. Start the FastAPI server:
```bash
python minimal_agent.py --server
```

2. Configure Agent Chat UI `.env`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080/chat
NEXT_PUBLIC_ASSISTANT_ID=agent
```

3. The FastAPI endpoint should return responses in this format:
```json
{
  "response": "Agent's message",
  "thread_id": "conversation-id"
}
```

### Option 2: Using LangGraph Dev Server

1. Create `langgraph.json`:
```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./minimal_agent.py:build_graph"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

2. Start server:
```bash
langgraph dev
```

3. Configure Agent Chat UI `.env`:
```bash
LANGGRAPH_API_URL=http://localhost:2024
NEXT_PUBLIC_API_URL=http://localhost:3000/api
NEXT_PUBLIC_ASSISTANT_ID=agent
```

## Common Patterns

### Pattern 1: Proper Message Handling

```python
from langchain_core.messages import AIMessage

# ❌ WRONG - Will cause KeyError: 'role'
def bad_node(state):
    return {"messages": ["Plain string"]}

# ✅ CORRECT - Returns AIMessage object
def good_node(state):
    return {"messages": [AIMessage(content="Response text")]}
```

### Pattern 2: Message Format Conversion

```python
from langchain_core.messages import BaseMessage, HumanMessage

def convert_to_api_format(messages: list[BaseMessage]) -> list[dict]:
    """Convert LangGraph messages to API format"""
    api_messages = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        api_messages.append({"role": role, "content": msg.content})
    return api_messages
```

### Pattern 3: Checkpointing for Memory

```python
from langgraph.checkpoint.memory import MemorySaver

def build_graph():
    graph = StateGraph(ConversationState)
    # ... add nodes and edges

    # Compile with checkpointer for persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)

# Invoke with thread_id for persistence
config = {"configurable": {"thread_id": "user_123"}}
result = app.invoke({"messages": [...]}, config=config)
```

### Pattern 4: Streaming with FastAPI

```python
from fastapi.responses import StreamingResponse
import json

@app.post("/stream")
async def stream(request: ChatRequest):
    async def event_generator():
        async for event in graph.astream_events(..., version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

## Troubleshooting

### KeyError: 'role'

**Cause:** Returning plain strings or dicts without 'role' field

**Solution:** Always return AIMessage objects:
```python
from langchain_core.messages import AIMessage
return {"messages": [AIMessage(content="Response")]}
```

### Messages Not Persisting

**Cause:** Missing thread_id in config

**Solution:** Always provide thread_id:
```python
config = {"configurable": {"thread_id": "unique-id"}}
result = app.invoke(state, config=config)
```

### Streaming Not Working

**Cause:** Not using astream_events with version="v2"

**Solution:** Use the correct streaming method:
```python
async for event in graph.astream_events(..., version="v2"):
    if event["event"] == "on_chat_model_stream":
        # Handle token chunks
```

## Next Steps

- Review **../references/stategraph-complete-guide.md** for comprehensive patterns
- Check **../references/message-format-errors.md** for troubleshooting
- See **../references/fastapi-integration-patterns.md** for production deployment
- Read **../SKILL.md** for complete skill documentation

## Resources

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **Agent Chat UI**: https://github.com/langchain-ai/agent-chat-ui
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
