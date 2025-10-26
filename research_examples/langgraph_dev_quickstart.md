# LangGraph Dev Server - Quick Reference

Quick reference for serving LangGraph agents with `langgraph dev` and Agent Chat UI.

---

## Minimal Setup (3 Files)

### 1. langgraph.json

```json
{
  "dependencies": ["."],
  "graphs": {
    "resume_agent": "./resume_agent_langgraph.py:build_graph"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

### 2. resume_agent_langgraph.py

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, BaseMessage
import anthropic
import os

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def chat_node(state: State) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    api_messages = [
        {"role": "user" if msg.type == "human" else "assistant",
         "content": msg.content}
        for msg in state["messages"]
    ]

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system="You are a helpful assistant",
        messages=api_messages
    )

    return {"messages": [AIMessage(content=response.content[0].text)]}

def build_graph():
    """Entry point for langgraph.json"""
    graph = StateGraph(State)
    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    return graph.compile(checkpointer=MemorySaver())
```

### 3. .env

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Start Server

```bash
# Install
pip install "langgraph-cli[inmem]"

# Run
langgraph dev
```

Server runs on: **http://localhost:2024**

---

## Test with curl

### Create Thread

```bash
curl -X POST http://localhost:2024/threads \
  -H 'Content-Type: application/json' \
  -d '{}'
```

### Send Message

```bash
# Get thread_id from previous response
curl -X POST http://localhost:2024/threads/{thread_id}/runs/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "assistant_id": "resume_agent",
    "input": {
      "messages": [{"role": "user", "content": "Hello"}]
    },
    "stream_mode": ["updates"]
  }'
```

### Stateless (No Thread)

```bash
curl -X POST http://localhost:2024/runs/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "assistant_id": "resume_agent",
    "input": {
      "messages": [{"role": "user", "content": "Hello"}]
    },
    "stream_mode": ["values"]
  }'
```

---

## Agent Chat UI Setup

### .env (in agent-chat-ui/)

```bash
LANGGRAPH_API_URL=http://localhost:2024
NEXT_PUBLIC_API_URL=http://localhost:3000/api
NEXT_PUBLIC_ASSISTANT_ID=resume_agent
```

### Start UI

```bash
cd apps/agent-chat-ui
npm run dev
```

UI runs on: **http://localhost:3000**

---

## Python SDK

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")

# Create thread
thread = await client.threads.create()

# Stream messages
async for chunk in client.runs.stream(
    thread["thread_id"],
    "resume_agent",
    input={"messages": [{"role": "user", "content": "Hi"}]},
    stream_mode="updates"
):
    print(chunk.data)
```

---

## Key Concepts

### langgraph.json Fields

- `dependencies` - Python packages to install
- `graphs` - Map of `assistant_id → file.py:function`
- `env` - Environment variables file
- `python_version` - Python version

### Graph Builder Requirements

1. Function name must match `langgraph.json`
2. Must return compiled graph: `graph.compile(checkpointer=...)`
3. Use `MemorySaver()` for dev, `PostgresSaver` for prod
4. State must use `add_messages` for message history

### Thread ID Pattern

- **With thread_id** - Stateful, conversation history
- **Without thread_id** - Stateless, one-off queries

### Stream Modes

- `values` - Full state after each node
- `updates` - Partial updates per node
- `messages` - Only message updates
- `debug` - Debug information

---

## Common Issues

| Issue | Fix |
|-------|-----|
| "Assistant ID not found" | Check `assistant_id` in `langgraph.json` matches request |
| Messages not persisting | Ensure checkpointer in `compile()` and same thread_id |
| Module not found | Add `"."` to `dependencies` in `langgraph.json` |
| Can't connect | Verify server running: `curl http://localhost:2024/ok` |

---

## Essential Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/threads` | POST | Create thread |
| `/threads/{id}/runs/stream` | POST | Stream with thread |
| `/runs/stream` | POST | Stream stateless |
| `/threads/{id}/state` | GET | Get thread state |
| `/docs` | GET | API documentation |

---

## Complete Example Flow

```bash
# 1. Start server
langgraph dev

# 2. Create thread
thread_id=$(curl -X POST http://localhost:2024/threads \
  -H 'Content-Type: application/json' -d '{}' | jq -r '.thread_id')

# 3. First message
curl -X POST http://localhost:2024/threads/$thread_id/runs/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "assistant_id": "resume_agent",
    "input": {"messages": [{"role": "user", "content": "My name is John"}]},
    "stream_mode": ["updates"]
  }'

# 4. Follow-up (remembers context!)
curl -X POST http://localhost:2024/threads/$thread_id/runs/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "assistant_id": "resume_agent",
    "input": {"messages": [{"role": "user", "content": "What is my name?"}]},
    "stream_mode": ["updates"]
  }'
```

---

## Production Checklist

- [ ] Switch `MemorySaver` to `PostgresSaver`
- [ ] Add authentication to API endpoints
- [ ] Set up environment variable management
- [ ] Configure CORS for production domain
- [ ] Enable logging and monitoring
- [ ] Deploy with Docker or LangGraph Cloud
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure rate limiting

---

## Resources

- [Official Tutorial](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/)
- [API Reference](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html)
- [SDK Docs](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)
- [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui)
