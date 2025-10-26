# Agent Chat UI Integration Guide

Complete guide for integrating LangGraph agents with the Agent Chat UI.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [LangGraph Server Setup](#langgraph-server-setup)
4. [Agent Chat UI Configuration](#agent-chat-ui-configuration)
5. [Message Flow](#message-flow)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```
┌─────────────────────────┐
│   Agent Chat UI         │
│   (Next.js Frontend)    │
│   Port: 3000            │
└───────────┬─────────────┘
            │ HTTP/REST
            │ LangGraph SDK Client
            ▼
┌─────────────────────────┐
│  LangGraph Server       │
│  (Agent API)            │
│  Port: 2024             │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  StateGraph             │
│  (Agent Logic)          │
└─────────────────────────┘
```

**Communication:**
- UI uses `@langchain/langgraph-sdk` to connect to LangGraph server
- Server exposes REST API at `http://localhost:2024`
- Graph builder function registered in `langgraph.json`
- Checkpointer enables conversation persistence

**Example:** See `apps/agent-chat-ui/SETUP.md:6-26`

---

## Prerequisites

### System Requirements

1. **Node.js & pnpm** (for Agent Chat UI)
```bash
# Install pnpm if needed
npm install -g pnpm
```

2. **Python & UV** (for LangGraph server)
```bash
# Install UV if needed
pip install uv
```

3. **LangGraph CLI** (to run server)
```bash
pip install "langgraph-cli[inmem]"
```

4. **API Keys**
- `ANTHROPIC_API_KEY` (for Claude) OR
- `OPENAI_API_KEY` (for GPT models)

**Example:** See `apps/agent-chat-ui/SETUP.md:28-49`

---

## LangGraph Server Setup

### Step 1: Create langgraph.json

**File Location:** `apps/[agent-name]/langgraph.json`

```json
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./agent_file.py:build_web_conversation_graph"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

**Key Points:**
- `graphs.agent`: The graph ID (must match UI's `NEXT_PUBLIC_ASSISTANT_ID`)
- Function must return compiled StateGraph with checkpointer
- Use `build_web_conversation_graph` (not CLI version)

**Example:** `apps/resume-agent-langgraph/langgraph.json`

---

### Step 2: Implement Web-Compatible Graph

**File Location:** `apps/[agent-name]/agent_file.py`

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

def build_web_conversation_graph():
    """
    Build web-compatible graph (no CLI input node).

    IMPORTANT: Messages come from HTTP requests, not CLI input.
    """
    graph = StateGraph(ConversationState)

    # Add only chat node (NO get_input node!)
    graph.add_node("chat", chat_node)

    # Simple flow: START -> chat -> END
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # Compile with checkpointer (required for persistence)
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
```

**Critical Differences from CLI Graph:**
- ❌ NO `get_input` node (UI sends messages via HTTP)
- ✅ Messages pre-populated in state from HTTP requests
- ✅ Checkpointer REQUIRED for conversation history
- ✅ Function exported for LangGraph server

**Example:** `apps/resume-agent-langgraph/resume_agent_langgraph.py:287-314`

---

### Step 3: Configure Environment

**File Location:** `apps/[agent-name]/.env`

```bash
# LLM Provider
LLM_PROVIDER=claude  # or "openai"
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Model Selection
CLAUDE_MODEL=claude-sonnet-4-5
OPENAI_MODEL=gpt-4o-mini
```

**Example:** `apps/resume-agent-langgraph/.env`

---

### Step 4: Start LangGraph Server

```bash
cd apps/[agent-name]

# Ensure dependencies installed
uv sync

# Start dev server
langgraph dev
```

**Server Endpoints:**
- **REST API:** `http://localhost:2024` (for Agent Chat UI)
- **Studio UI:** `http://localhost:2024/studio` (for debugging)

**Verify Server:**
```bash
# Health check
curl http://localhost:2024/health

# List graphs
curl http://localhost:2024/graphs
```

**Example:** `apps/agent-chat-ui/SETUP.md:53-69`

---

## Agent Chat UI Configuration

### Step 1: Configure Environment

**File Location:** `apps/agent-chat-ui/.env`

```bash
# LangGraph Server Connection
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
```

**Critical Points:**
- `NEXT_PUBLIC_API_URL`: LangGraph server URL
- `NEXT_PUBLIC_ASSISTANT_ID`: MUST match `graphs` key in `langgraph.json`

**Example:** `apps/agent-chat-ui/.env`

---

### Step 2: Install Dependencies

```bash
cd apps/agent-chat-ui
pnpm install
```

---

### Step 3: Start UI Development Server

```bash
cd apps/agent-chat-ui
pnpm dev
```

**UI URL:** `http://localhost:3000`

**Example:** `apps/agent-chat-ui/SETUP.md:71-84`

---

## Message Flow

### User Input to Agent Response

1. **User types message** in UI input field
2. **UI creates thread** (if first message) with `thread_id`
3. **UI sends message** to LangGraph server:
```typescript
const response = await client.runs.stream(
  threadId,
  assistantId,
  {
    input: {
      messages: [{ role: "user", content: userInput }]
    }
  }
)
```
4. **Server invokes graph** with message and `thread_id`:
```python
result = graph.invoke(
    {"messages": [{"role": "user", "content": userInput}]},
    config={"configurable": {"thread_id": threadId}}
)
```
5. **Graph processes message** through nodes
6. **Checkpointer saves state** after each node
7. **Server streams response** to UI
8. **UI displays message** in chat interface

**Example:** See `apps/agent-chat-ui/src/providers/client.ts`

---

### Conversation Persistence

**How it works:**
1. UI generates unique `thread_id` per conversation
2. Each message invocation includes `thread_id` in config
3. Checkpointer stores state keyed by `thread_id`
4. Subsequent messages retrieve state from checkpointer
5. Agent maintains full conversation history

**Code Example:**
```python
# First message
config = {"configurable": {"thread_id": "conv-123"}}
result1 = graph.invoke({"messages": [...]}, config=config)

# Second message (continues conversation)
result2 = graph.invoke({"messages": [...]}, config=config)
# Graph has access to result1's state!
```

---

## Advanced Features

### Streaming Responses

**Enable streaming for real-time UI updates:**

```python
async def stream_node(state: State):
    """Stream response chunks"""
    messages = state["messages"]

    # Stream from LLM
    async for chunk in llm.astream(messages):
        yield {"messages": [{"role": "assistant", "content": chunk}]}
```

**UI receives chunks in real-time:**
```typescript
for await (const chunk of response) {
  // Update UI with each chunk
  appendToMessage(chunk.messages[0].content);
}
```

---

### Human-in-the-Loop

**Pause agent for user approval:**

```python
from langgraph.types import interrupt

def approval_node(state: State) -> dict:
    """Request user approval"""
    action = state["pending_action"]

    # Interrupt and wait for UI response
    response = interrupt({"action": action, "status": "pending"})

    if response["approved"]:
        return {"approved": True}
    else:
        return {"approved": False, "errors": ["User rejected action"]}
```

**UI displays approval prompt and sends response back.**

---

### Tool Integration

**Agent with tools accessible from UI:**

```python
from langgraph.prebuilt import ToolNode

def search_tool(query: str) -> str:
    """Search for information"""
    return f"Results: {query}"

tools = [search_tool]
tool_node = ToolNode(tools)

graph.add_node("tools", tool_node)
graph.add_conditional_edges("agent", should_use_tools, ["tools", END])
graph.add_edge("tools", "agent")
```

**UI displays tool calls and results in chat interface.**

---

### Multi-Agent Conversations

**Multiple agents accessible from UI:**

```python
# langgraph.json
{
  "graphs": {
    "agent1": "./agents.py:build_agent1",
    "agent2": "./agents.py:build_agent2"
  }
}
```

**UI can switch between agents:**
```bash
# Configure UI for agent1
NEXT_PUBLIC_ASSISTANT_ID=agent1

# Or agent2
NEXT_PUBLIC_ASSISTANT_ID=agent2
```

---

## Troubleshooting

### Issue: UI Can't Connect to Server

**Symptoms:**
- "Cannot connect to server" error in UI
- Network request failures

**Solutions:**
1. Verify LangGraph server is running:
```bash
curl http://localhost:2024/health
```

2. Check `NEXT_PUBLIC_API_URL` in `apps/agent-chat-ui/.env`

3. Ensure no firewall blocking port 2024

**Example:** `apps/agent-chat-ui/SETUP.md:162-169`

---

### Issue: Assistant Not Found

**Symptoms:**
- "Assistant 'agent' not found" error
- Graph not loading

**Solutions:**
1. Verify `NEXT_PUBLIC_ASSISTANT_ID` matches `langgraph.json` graph key:
```json
// langgraph.json
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

2. Restart LangGraph server after changing `langgraph.json`

---

### Issue: Messages Not Persisting

**Symptoms:**
- Agent forgets previous messages
- Conversation history lost

**Solutions:**
1. Ensure graph compiled with checkpointer:
```python
checkpointer = MemorySaver()
graph.compile(checkpointer=checkpointer)  # Required!
```

2. Verify UI sends `thread_id` in requests

3. Check server logs for checkpoint errors

---

### Issue: API Key Errors

**Symptoms:**
- "ANTHROPIC_API_KEY not found"
- LLM API failures

**Solutions:**
1. Add API key to `apps/[agent-name]/.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
# OR
OPENAI_API_KEY=sk-...
```

2. Restart LangGraph server to load new env vars

3. Verify API key is valid

**Example:** `apps/agent-chat-ui/SETUP.md:172-180`

---

### Issue: Slow Response Times

**Symptoms:**
- UI shows "Thinking..." for >10 seconds
- Timeouts

**Solutions:**
1. Use faster model:
```bash
# .env
OPENAI_MODEL=gpt-4o-mini  # Faster than gpt-4
CLAUDE_MODEL=claude-sonnet-4-5  # Fast
```

2. Optimize node logic (reduce API calls)

3. Implement streaming for perceived performance

---

### Issue: Graph Not Updating

**Symptoms:**
- Code changes not reflected in UI
- Old behavior persists

**Solutions:**
1. Restart LangGraph dev server (auto-reload may fail)
```bash
# Ctrl+C to stop
langgraph dev  # Restart
```

2. Clear UI cache and refresh browser

3. Verify correct graph file in `langgraph.json`

---

## Development Workflow

### Iterative Development

1. **Start both servers:**
```bash
# Terminal 1: LangGraph server
cd apps/[agent-name]
langgraph dev

# Terminal 2: Agent Chat UI
cd apps/agent-chat-ui
pnpm dev
```

2. **Make code changes** to graph (nodes, edges, etc.)

3. **Server auto-reloads** (usually)

4. **Refresh UI** to test changes

5. **Check LangGraph Studio** for visual debugging:
   - Open `http://localhost:2024/studio`
   - Visualize graph structure
   - Inspect state transitions

6. **Iterate** until behavior is correct

**Example:** `apps/agent-chat-ui/SETUP.md:185-214`

---

### Testing Checklist

Before deploying, verify:
- [ ] Agent responds to basic queries
- [ ] Message history persists across requests
- [ ] Streaming works (if enabled)
- [ ] Error messages display correctly
- [ ] Tools execute properly (if applicable)
- [ ] Multiple conversations work (different `thread_id`s)
- [ ] LangGraph Studio shows correct graph structure
- [ ] No errors in server logs
- [ ] UI performance is acceptable

---

## Production Deployment

### LangGraph Server

1. **Use production checkpointer:**
```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("data/checkpoints.db")
graph.compile(checkpointer=checkpointer)
```

2. **Configure production environment:**
```bash
# .env.production
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-prod-...
CHECKPOINT_DB=data/checkpoints.db
```

3. **Deploy LangGraph server:**
```bash
langgraph deploy
```

4. **Get deployment URL:**
```
https://my-agent.default.us.langgraph.app
```

---

### Agent Chat UI

1. **Configure production API URL:**
```bash
# apps/agent-chat-ui/.env.production
NEXT_PUBLIC_API_URL=https://my-agent.default.us.langgraph.app
NEXT_PUBLIC_ASSISTANT_ID=agent
```

2. **Build UI:**
```bash
cd apps/agent-chat-ui
pnpm build
```

3. **Deploy UI** (Vercel, Netlify, etc.)

---

## Client Configuration

### Custom Client Setup

**File:** `apps/agent-chat-ui/src/providers/client.ts`

```typescript
import { Client } from "@langchain/langgraph-sdk";

export function createClient(apiUrl: string, apiKey: string | undefined) {
  return new Client({
    apiKey,
    apiUrl,
  });
}
```

**Usage:**
```typescript
const client = createClient(
  process.env.NEXT_PUBLIC_API_URL,
  process.env.NEXT_PUBLIC_API_KEY
);
```

**Example:** `apps/agent-chat-ui/src/providers/client.ts`

---

## Resources

### Documentation
- **Agent Chat UI Setup:** `apps/agent-chat-ui/SETUP.md`
- **LangGraph Server:** `apps/resume-agent-langgraph/README.md`
- **Agent Chat UI Repo:** https://github.com/langchain-ai/agent-chat-ui
- **LangGraph Deployment:** https://langchain-ai.github.io/langgraph/cloud

### Example Implementation
- **Working Agent:** `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- **UI Configuration:** `apps/agent-chat-ui/.env`
- **Server Configuration:** `apps/resume-agent-langgraph/langgraph.json`

### Debugging Tools
- **LangGraph Studio:** `http://localhost:2024/studio`
- **Server Health Check:** `http://localhost:2024/health`
- **Graph List:** `http://localhost:2024/graphs`
