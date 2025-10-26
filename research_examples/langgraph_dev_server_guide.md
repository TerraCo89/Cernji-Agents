# LangGraph Dev Server Integration Guide

Complete guide for serving LangGraph agents using `langgraph dev` for Agent Chat UI integration.

---

## Solution Description

### Overview

The LangGraph dev server (`langgraph dev`) provides a local development environment that exposes your LangGraph agents as a REST API. This server runs on port 2024 by default and provides:

1. **Hot reloading** - Automatically reloads when code changes
2. **REST API** - Standard endpoints for threads and streaming runs
3. **No Docker required** - Lightweight development setup
4. **State persistence** - In-memory checkpointing for conversation history

### How Agent Chat UI Connects

The connection flow works as follows:

```
User Browser → Agent Chat UI (Next.js) → API Proxy (/api) → LangGraph Dev Server (port 2024)
```

**Key Components:**

1. **langgraph.json** - Defines which graphs are available and their entry points
2. **Graph Builder Function** - A function that returns a compiled StateGraph with checkpointer
3. **LangGraph Dev Server** - Runs the API server (`langgraph dev`)
4. **Agent Chat UI** - React app that connects via LangGraph SDK
5. **Next.js API Proxy** - Server-side proxy for authentication/security

**Thread ID Pattern:**

- Threads are created via `/threads` endpoint
- Each thread maintains conversation state via checkpointing
- Thread ID is passed to `/runs/stream` for stateful conversations
- MemorySaver checkpointer stores state in memory

---

## Working Code Example

### 1. Directory Structure

```
apps/resume-agent-langgraph/
├── langgraph.json              # Configuration file
├── resume_agent_langgraph.py   # Graph implementation
├── graph_registry.py           # Multi-graph registry (optional)
├── .env                        # API keys
└── src/                        # Additional modules
```

### 2. langgraph.json Configuration

**Basic Single Graph:**

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

**Multiple Graphs:**

```json
{
  "dependencies": ["."],
  "graphs": {
    "resume_agent": "./resume_agent_langgraph.py:build_graph",
    "minimal_agent": "./examples/minimal_agent.py:build_graph",
    "japanese_tutor": "./japanese_tutor.py:build_graph"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

**Monorepo with Multiple Dependencies:**

```json
{
  "dependencies": [
    "./all_projects/my_project/project_one",
    "./all_projects/project_two"
  ],
  "graphs": {
    "my_first_agent": "./all_projects/my_project/project_one/main.py:graph",
    "my_second_agent": "./all_projects/project_two/main.py:graph"
  },
  "env": "./.env"
}
```

**Configuration Fields:**

- `dependencies`: Python packages/modules to install (e.g., `["."]` for current directory)
- `graphs`: Map of `assistant_id` → `path/to/file.py:function_name`
- `env`: Path to .env file for environment variables
- `python_version`: Python version (e.g., "3.11")
- `dockerfile_lines`: (optional) Custom Docker commands for production deployment

### 3. Graph Builder Function

The graph builder function must:
1. Return a compiled StateGraph
2. Include a checkpointer for state persistence
3. Use the standard message pattern (`add_messages`)

**Complete Working Example:**

```python
#!/usr/bin/env python3
"""
Resume Agent LangGraph - Web Conversation Graph
"""

import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# State Schema
# ==============================================================================

class ConversationState(TypedDict):
    """
    State for conversational agent.

    Uses Annotated[list[BaseMessage], add_messages] for proper message handling.
    This is the standard LangGraph pattern for chat history.
    """
    messages: Annotated[list[BaseMessage], add_messages]
    should_continue: bool


# ==============================================================================
# Agent Nodes
# ==============================================================================

def chat_node(state: ConversationState) -> dict:
    """
    Main chat node: processes user input with LLM.

    Args:
        state: Current conversation state with message history

    Returns:
        Partial state update with LLM's response
    """
    # Get API client
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Convert messages to API format
    api_messages = []
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            api_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            api_messages.append({"role": "assistant", "content": msg.content})

    # System prompt
    system_prompt = """You are a helpful Resume Agent assistant.
    Be friendly, concise, and helpful."""

    # Call LLM
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=system_prompt,
        messages=api_messages
    )

    # Return as AIMessage object (IMPORTANT: not plain dict!)
    return {
        "messages": [AIMessage(content=response.content[0].text)]
    }


# ==============================================================================
# Graph Builder Function (Required Entry Point)
# ==============================================================================

def build_graph():
    """
    Entry point for LangGraph API server.

    This function is called by langgraph.json via:
    "graphs": {
        "resume_agent": "./resume_agent_langgraph.py:build_graph"
    }

    MUST return a compiled StateGraph with checkpointer.
    """
    # Create graph
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("chat", chat_node)

    # Simple flow: START -> chat -> END
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # IMPORTANT: Compile with checkpointer for state persistence
    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)

    return app
```

**Key Requirements:**

1. **Function Signature**: `def build_graph() -> StateGraph`
2. **Must Return**: Compiled graph with `.compile(checkpointer=checkpointer)`
3. **Checkpointer Required**: Use `MemorySaver()` for dev, `PostgresSaver` for production
4. **Message Format**: Use `Annotated[list[BaseMessage], add_messages]` in state
5. **Message Objects**: Return `AIMessage`/`HumanMessage` objects, NOT plain dicts

### 4. Agent Chat UI Configuration

**.env file:**

```bash
# Backend API URL (server-side, used by Next.js API proxy)
LANGGRAPH_API_URL=http://localhost:2024

# Frontend API URL (client-side, must be absolute URL for SDK)
NEXT_PUBLIC_API_URL=http://localhost:3000/api

# Agent/Assistant ID - matches the key in langgraph.json "graphs"
NEXT_PUBLIC_ASSISTANT_ID=resume_agent
```

**Next.js API Proxy (src/app/api/[..._path]/route.ts):**

```typescript
import { initApiPassthrough } from "langgraph-nextjs-api-passthrough";

export const { GET, POST, PUT, PATCH, DELETE, OPTIONS, runtime } =
  initApiPassthrough({
    apiUrl: process.env.LANGGRAPH_API_URL ?? "http://localhost:2024",
    apiKey: process.env.LANGSMITH_API_KEY ?? "", // Optional for local dev
    runtime: "edge",
  });
```

**How It Works:**

1. User sends message in browser
2. React app calls `http://localhost:3000/api/runs/stream`
3. Next.js proxy forwards to `http://localhost:2024/runs/stream`
4. LangGraph dev server processes request
5. Response streams back through proxy to browser

---

## REST API Endpoints

### Core Endpoints

The LangGraph dev server exposes these endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/threads` | POST | Create a new thread |
| `/threads/{thread_id}` | GET | Get thread details |
| `/threads/{thread_id}/state` | GET | Get thread state |
| `/threads/{thread_id}/copy` | POST | Copy a thread |
| `/threads/search` | POST | Search threads by metadata |
| `/runs/stream` | POST | Stream a stateless run |
| `/threads/{thread_id}/runs/stream` | POST | Stream a stateful run |
| `/docs` | GET | OpenAPI documentation |

### Working curl Examples

#### 1. Create a Thread

```bash
curl --request POST \
  --url http://localhost:2024/threads \
  --header 'Content-Type: application/json' \
  --data '{}'
```

**Response:**

```json
{
  "thread_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2025-10-25T12:00:00.000Z",
  "metadata": {}
}
```

#### 2. Stream a Stateless Run (No Thread)

```bash
curl -s --request POST \
  --url "http://localhost:2024/runs/stream" \
  --header 'Content-Type: application/json' \
  --data '{
    "assistant_id": "resume_agent",
    "input": {
      "messages": [
        {
          "role": "human",
          "content": "What is LangGraph?"
        }
      ]
    },
    "stream_mode": "messages"
  }'
```

#### 3. Stream a Stateful Run (With Thread)

**First, create a thread and capture thread_id:**

```bash
thread_id=$(curl --request POST \
  --url http://localhost:2024/threads \
  --header 'Content-Type: application/json' \
  --data '{}' | jq -r '.thread_id')

echo "Thread ID: $thread_id"
```

**Then, stream a run using that thread:**

```bash
curl --request POST \
  --url "http://localhost:2024/threads/${thread_id}/runs/stream" \
  --header 'Content-Type: application/json' \
  --data '{
    "assistant_id": "resume_agent",
    "input": {
      "messages": [
        {
          "role": "user",
          "content": "Hello! My name is John."
        }
      ]
    },
    "stream_mode": ["updates"]
  }'
```

**Follow-up message in same thread:**

```bash
curl --request POST \
  --url "http://localhost:2024/threads/${thread_id}/runs/stream" \
  --header 'Content-Type: application/json' \
  --data '{
    "assistant_id": "resume_agent",
    "input": {
      "messages": [
        {
          "role": "user",
          "content": "What did I just tell you my name was?"
        }
      ]
    },
    "stream_mode": ["updates"]
  }'
```

**Response should remember the context from previous messages!**

#### 4. Get Thread State

```bash
curl --request GET \
  --url "http://localhost:2024/threads/${thread_id}/state" \
  --header 'Content-Type: application/json'
```

#### 5. Search Threads by Metadata

```bash
curl --request POST \
  --url "http://localhost:2024/threads/search" \
  --header 'Content-Type: application/json' \
  --data '{
    "metadata": {
      "graph_id": "resume_agent"
    },
    "limit": 10
  }'
```

### Stream Modes

The `stream_mode` parameter controls what data is streamed:

- `"values"` - Full state after each node
- `"updates"` - Partial state updates from each node
- `"messages"` - Only message updates
- `"messages-tuple"` - Messages with metadata
- `"debug"` - Debugging information

**Example with multiple modes:**

```bash
curl --request POST \
  --url "http://localhost:2024/runs/stream" \
  --header 'Content-Type: application/json' \
  --data '{
    "assistant_id": "resume_agent",
    "input": {
      "messages": [{"role": "user", "content": "Hello"}]
    },
    "stream_mode": ["values", "updates", "debug"]
  }'
```

---

## Python SDK Examples

### Basic Client Setup

```python
from langgraph_sdk import get_client

# Connect to local dev server
client = get_client(url="http://localhost:2024")

# List available assistants
assistants = await client.assistants.search()
print(f"Available assistants: {[a['assistant_id'] for a in assistants]}")
```

### Create Thread and Stream

```python
from langgraph_sdk import get_client

client = get_client(url="http://localhost:2024")

# Create a thread
thread = await client.threads.create()
thread_id = thread["thread_id"]

print(f"Created thread: {thread_id}")

# Stream a run
assistant_id = "resume_agent"
input_data = {
    "messages": [
        {"role": "user", "content": "Hello, I need help with my resume"}
    ]
}

async for chunk in client.runs.stream(
    thread_id,
    assistant_id,
    input=input_data,
    stream_mode="updates"
):
    print(chunk.data)
```

### Stateless Run (No Thread)

```python
# Stream without creating a thread (no state persistence)
async for chunk in client.runs.stream(
    thread_id=None,  # No thread
    assistant_id="resume_agent",
    input={"messages": [{"role": "user", "content": "Quick question"}]},
    stream_mode="values"
):
    print(chunk.data)
```

### Advanced Configuration

```python
async for chunk in client.runs.stream(
    thread_id=thread_id,
    assistant_id="resume_agent",
    input={"messages": [{"role": "user", "content": "Analyze this resume"}]},
    stream_mode=["values", "debug"],
    metadata={"user_id": "user_123", "session": "resume_optimization"},
    config={"configurable": {"model_name": "claude-sonnet-4-5"}},
    interrupt_before=["human_review"],  # Pause before this node
    interrupt_after=["job_analysis"],   # Pause after this node
):
    print(chunk)
```

---

## Starting the Dev Server

### Installation

```bash
# Install LangGraph CLI with in-memory checkpointing
pip install "langgraph-cli[inmem]"
```

### Start Server

```bash
# Start with default settings (port 2024)
langgraph dev

# Start on custom port
langgraph dev --port 8080

# Disable auto-reload
langgraph dev --no-reload

# Use custom config file
langgraph dev --config my-config.json

# Don't open browser automatically
langgraph dev --no-browser
```

### Verify Server is Running

```bash
# Check health
curl http://localhost:2024/ok

# View OpenAPI docs
open http://localhost:2024/docs
```

---

## Thread ID and Config Patterns

### Thread ID Usage

**When to use thread_id:**

✅ **Use thread_id when you need:**
- Conversation history
- State persistence across messages
- Human-in-the-loop workflows
- Multi-turn interactions

❌ **Skip thread_id (use `None`) when:**
- One-off questions
- Stateless operations
- No need to remember context

### Config Pattern

The `config` parameter allows passing runtime configuration:

```python
config = {
    "configurable": {
        "thread_id": "conversation-123",  # Required for checkpointing
        "model_name": "claude-sonnet-4-5",
        "temperature": 0.7,
        # Any custom parameters your graph expects
    }
}

# In graph invocation
app.invoke(initial_state, config=config)
```

**In Graph Code:**

```python
def chat_node(state: ConversationState, config: RunnableConfig) -> dict:
    # Access config values
    model_name = config.get("configurable", {}).get("model_name", "default-model")
    temperature = config.get("configurable", {}).get("temperature", 0.5)

    # Use in LLM call
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model_name,
        temperature=temperature,
        # ... rest of params
    )

    return {"messages": [AIMessage(content=response.content[0].text)]}
```

### Checkpointer Pattern

**Development (MemorySaver):**

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)
```

**Production (PostgreSQL):**

```python
from langgraph.checkpoint.postgres import PostgresSaver

# Database connection
DB_URI = "postgresql://user:pass@localhost/dbname"

# Create checkpointer
checkpointer = PostgresSaver.from_conn_string(DB_URI)

# Compile graph
app = graph.compile(checkpointer=checkpointer)
```

---

## Troubleshooting

### Common Issues

**1. "Assistant ID not found"**

```
Error: Unknown assistant_id: 'resume_agent'
```

**Fix:** Ensure `langgraph.json` has the correct assistant_id in `graphs`:

```json
{
  "graphs": {
    "resume_agent": "./resume_agent_langgraph.py:build_graph"
  }
}
```

**2. "ModuleNotFoundError" when starting server**

```
ModuleNotFoundError: No module named 'resume_agent'
```

**Fix:** Add current directory to dependencies:

```json
{
  "dependencies": ["."]
}
```

**3. Messages not persisting across turns**

**Fix:** Ensure:
1. Graph is compiled with checkpointer: `graph.compile(checkpointer=MemorySaver())`
2. Using same `thread_id` for all messages
3. State uses `add_messages` reducer: `Annotated[list[BaseMessage], add_messages]`

**4. "Cannot connect to LangGraph server"**

**Fix:** Verify server is running:

```bash
curl http://localhost:2024/ok
```

**5. Agent Chat UI shows "Network Error"**

**Fix:** Check `.env` configuration:

```bash
LANGGRAPH_API_URL=http://localhost:2024  # Backend
NEXT_PUBLIC_API_URL=http://localhost:3000/api  # Frontend proxy
```

---

## Best Practices

### 1. State Schema Design

✅ **Do:**
```python
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]  # Standard pattern
    context: dict  # Additional context
```

❌ **Don't:**
```python
class State(TypedDict):
    messages: list  # Missing add_messages reducer!
```

### 2. Message Objects

✅ **Do:**
```python
return {"messages": [AIMessage(content="Hello")]}
```

❌ **Don't:**
```python
return {"messages": [{"role": "assistant", "content": "Hello"}]}  # Plain dict won't work!
```

### 3. Graph Builder Function

✅ **Do:**
```python
def build_graph():
    graph = StateGraph(State)
    # ... add nodes and edges
    return graph.compile(checkpointer=MemorySaver())  # Must compile with checkpointer
```

❌ **Don't:**
```python
def build_graph():
    graph = StateGraph(State)
    # ... add nodes and edges
    return graph  # Missing compile()!
```

### 4. Environment Variables

✅ **Do:**
```python
load_dotenv()  # Load .env file
api_key = os.getenv("ANTHROPIC_API_KEY")
```

❌ **Don't:**
```python
api_key = "sk-ant-..."  # Hardcoded keys!
```

---

## Sources

### Official Documentation

- **[LangGraph Local Server Tutorial](https://langchain-ai.github.io/langgraph/tutorials/langgraph-platform/local-server/)** - Complete guide to running local dev server
- **[LangGraph Platform API Reference](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html)** - REST API endpoint documentation
- **[Application Structure](https://docs.langchain.com/langgraph-platform/application-structure)** - How to structure LangGraph applications
- **[Streaming API](https://docs.langchain.com/langgraph-platform/streaming)** - Streaming patterns and examples
- **[Use Threads](https://docs.langchain.com/langgraph-platform/use-threads)** - Thread management guide

### Examples

- **[langgraph-example](https://github.com/langchain-ai/langgraph-example/blob/main/langgraph.json)** - Official example repository
- **[Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui)** - Official web UI for LangGraph agents
- **[SDK Reference (Python)](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/)** - Complete Python SDK documentation

### Community Resources

- **[LangGraph for Beginners, Part 4: StateGraph](https://medium.com/ai-agents/langgraph-for-beginners-part-4-stategraph-794004555369)** - Beginner guide to StateGraph
- **[Understanding LangGraph's StateGraph](https://medium.com/@diwakarkumar_18755/understanding-langgraphs-stategraph-a-simple-guide-020f70fc0038)** - Simple guide to StateGraph patterns
- **[LangGraph Tutorial with Practical Example](https://www.gettingstarted.ai/langgraph-tutorial-with-example/)** - Complete tutorial with examples

---

## Summary

**Key Takeaways:**

1. **langgraph.json** defines which graphs are available
2. **Graph builder function** must return compiled graph with checkpointer
3. **LangGraph dev server** exposes REST API on port 2024
4. **Thread ID** enables stateful conversations with persistent history
5. **Agent Chat UI** connects via Next.js API proxy for security
6. **Message objects** (AIMessage/HumanMessage) required, not plain dicts
7. **MemorySaver** for dev, PostgresSaver for production

**Complete Workflow:**

```mermaid
graph LR
    A[User Browser] --> B[Agent Chat UI]
    B --> C[Next.js API /api]
    C --> D[LangGraph Dev :2024]
    D --> E[Graph Builder]
    E --> F[Compiled Graph]
    F --> G[Checkpointer]
    G --> H[Thread State]
```

**Next Steps:**

1. Create `langgraph.json` with graph configuration
2. Implement graph builder function with checkpointer
3. Start dev server: `langgraph dev`
4. Test with curl to verify endpoints
5. Connect Agent Chat UI with proper .env config
6. Deploy to production with PostgreSQL checkpointer
