---
name: langgraph-builder
description: Guide for building stateful, conversational agents using LangGraph. This skill should be used when creating new LangGraph agents, implementing StateGraph workflows, adding checkpointing, or integrating agents with the Agent Chat UI.
---

# LangGraph Agent Builder

Build stateful, conversational agents using LangGraph's StateGraph architecture. This skill provides comprehensive guidance for creating agents with persistence, human-in-the-loop capabilities, and web deployment.

## When to Use This Skill

Use this skill when:
- Building a new LangGraph agent from scratch
- Implementing StateGraph workflows with nodes and edges
- Adding checkpointing for conversation persistence
- Integrating agents with the Agent Chat UI
- Deploying agents via LangGraph dev server
- Converting existing agents to LangGraph architecture

**Trigger phrases:**
- "Create a new LangGraph agent"
- "Build an agent that [does X]"
- "Implement StateGraph for [feature]"
- "Add chat UI to the [agent-name] agent"
- "Deploy this agent with LangGraph"
- "Update the [agent-name] to do X"

---

## ⚠️ CRITICAL: Message Format Requirements

**THE #1 CAUSE OF AGENT CHAT UI ERRORS IS INCORRECT MESSAGE FORMAT**

### KeyError: 'role' - Most Common Error

If you see `KeyError: 'role'`, your agent is returning messages in the wrong format.

**❌ WRONG - Will cause KeyError:**
```python
def agent_node(state):
    return {
        "messages": ["Plain string response"]  # NO!
    }

def agent_node(state):
    return {
        "messages": [{"content": "Missing role field"}]  # NO!
    }
```

**✅ CORRECT - Required format:**
```python
from langchain_core.messages import AIMessage

def agent_node(state):
    return {
        "messages": [AIMessage(content="Proper response")]  # YES!
    }

# OR using dict format (must include 'role')
def agent_node(state):
    return {
        "messages": [{
            "role": "assistant",  # Required!
            "content": "Proper response"
        }]
    }
```

### Message Format Checklist

Before deploying to Agent Chat UI, verify:

- [ ] **Using `AIMessage`/`HumanMessage` classes** (recommended)
- [ ] **NOT returning plain strings** in messages array
- [ ] **NOT using dicts without `role` field**
- [ ] **State schema uses `Annotated[list[BaseMessage], add_messages]`**
- [ ] **All nodes return properly formatted messages**

### Quick Fix for Resume Agent Error

If Resume Agent shows `KeyError: 'role'`:

1. **Find all nodes returning messages**
2. **Replace plain strings/dicts with `AIMessage`:**
```python
# Before (WRONG)
return {"messages": ["response"]}
return {"messages": [{"content": "response"}]}

# After (CORRECT)
from langchain_core.messages import AIMessage
return {"messages": [AIMessage(content="response")]}
```

3. **Add message format conversion for LLM APIs:**
```python
def convert_langgraph_messages_to_api_format(messages: list) -> list:
    """Convert LangGraph SDK format to LLM API format"""
    api_messages = []
    for msg in messages:
        if isinstance(msg, dict):
            role = msg.get("role") or msg.get("type")
            if role == "human":
                role = "user"
            api_messages.append({"role": role, "content": msg["content"]})
    return api_messages

def chat_node(state):
    # Convert before calling LLM
    api_messages = convert_langgraph_messages_to_api_format(state["messages"])
    response = llm.invoke(api_messages)
    return {"messages": [AIMessage(content=response)]}
```

**See:** `references/message-format-errors.md` for complete troubleshooting guide

---

## Core Concepts

### StateGraph

The foundation of LangGraph agents. Manages conversation state and orchestrates node execution.

**Key components:**
1. **State Schema**: TypedDict defining agent state structure
2. **Nodes**: Functions that process state and return updates
3. **Edges**: Connections between nodes (fixed or conditional)
4. **Checkpointer**: Persistence layer for conversation history

### State Management

**State Schema Pattern:**
```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class ConversationState(TypedDict):
    messages: Annotated[list, add_messages]  # Append-only message history
    user_info: str  # Custom state fields
    should_continue: bool
```

**Important:**
- Use `TypedDict`, NOT Pydantic models (msgpack serialization issue)
- Use `Annotated[list, add_messages]` for message history
- Add custom fields as needed for agent logic

**Troubleshooting Imports:**
- If you encounter `ImportError` or `ModuleNotFoundError`, see `references/import-fix-guide.md`
- Use absolute imports (e.g., `from my_agent.state import State`), not relative imports

### Nodes

Functions that process state and return partial updates.

**Node Pattern:**
```python
def chat_node(state: ConversationState) -> dict:
    """Process user input with LLM"""
    # Extract messages from state
    messages = state["messages"]

    # Call LLM
    response = llm.invoke(messages)

    # Return partial state update (appended automatically)
    return {"messages": [{"role": "assistant", "content": response}]}
```

**Node Rules:**
- Accept state as parameter
- Return dict with partial state updates
- Never mutate state directly
- Handle errors gracefully (don't raise exceptions)

### Edges

Connect nodes to define workflow.

**Fixed Edges:**
```python
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)
```

**Conditional Edges:**
```python
def should_continue(state: ConversationState) -> str:
    if state.get("should_continue"):
        return "chat_node"
    return END

graph.add_conditional_edges(
    "user_input",
    should_continue,
    {"chat_node": "chat_node", END: END}
)
```

### Checkpointing

Enables conversation persistence and resumption.

**Checkpoint Pattern:**
```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# Invoke with thread_id for persistence
config = {"configurable": {"thread_id": "conversation-123"}}
app.invoke(state, config=config)
```

**Checkpointer Options:**
- `MemorySaver`: In-memory (development only)
- `SqliteSaver`: SQLite database (production-ready)

## Building a LangGraph Agent

### Step 1: Define State Schema

Create a TypedDict representing agent state.

**Template:**
```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    # Add custom fields based on agent requirements
```

**Existing Example (Resume Agent):**
See `apps/resume-agent-langgraph/resume_agent_langgraph.py:54-62`

### Step 2: Implement Node Functions

Create functions for each step in the agent workflow.

**Chat Node Template:**
```python
def chat_node(state: AgentState) -> dict:
    """Process conversation with LLM"""
    try:
        # Convert messages to API format
        api_messages = convert_messages(state["messages"])

        # Call LLM
        response = llm.invoke(api_messages, system=system_prompt)

        # Return assistant message
        return {
            "messages": [{
                "role": "assistant",
                "content": response
            }]
        }
    except Exception as e:
        # Return error message (don't raise)
        return {
            "messages": [{
                "role": "assistant",
                "content": f"Error: {str(e)}"
            }]
        }
```

**Existing Example (Resume Agent):**
See `apps/resume-agent-langgraph/resume_agent_langgraph.py:114-170`

### Step 3: Build StateGraph

Assemble nodes and edges into workflow.

**Graph Building Pattern:**
```python
from langgraph.graph import StateGraph, START, END

def build_agent_graph():
    """Build the agent workflow graph"""
    # Create graph
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("chat", chat_node)
    # Add more nodes as needed

    # Define flow
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # Compile with checkpointer
    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)

    return app
```

**Existing Example (Resume Agent):**
See `apps/resume-agent-langgraph/resume_agent_langgraph.py:287-314`

### Step 4: Create langgraph.json

Configure agent for LangGraph dev server.

**File Location:** `apps/[agent-name]/langgraph.json`

**Template:**
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

**Key Fields:**
- `graphs.agent`: Graph builder function (must return compiled graph)
- `env`: Path to environment variables file
- `python_version`: Required Python version

**Existing Example (Resume Agent):**
See `apps/resume-agent-langgraph/langgraph.json`

### Step 5: Configure Environment Variables

Create `.env` file with API keys.

**File Location:** `apps/[agent-name]/.env`

**Template:**
```bash
# LLM Provider Configuration
LLM_PROVIDER=claude  # Options: "claude" or "openai"
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Model Selection
CLAUDE_MODEL=claude-sonnet-4-5
OPENAI_MODEL=gpt-4o-mini
```

**Existing Example (Resume Agent):**
See `apps/resume-agent-langgraph/.env`

### Step 6: Test Locally

Run agent with LangGraph dev server.

**Terminal 1 - Start LangGraph Server:**
```bash
cd apps/[agent-name]
langgraph dev
```

**Server Endpoints:**
- REST API: `http://localhost:2024`
- Studio UI: `http://localhost:2024/studio`

**Test with curl:**
```bash
curl -X POST http://localhost:2024/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "agent",
    "input": {"messages": [{"role": "user", "content": "Hello"}]},
    "config": {"configurable": {"thread_id": "test-123"}}
  }'
```

**Existing Example (Resume Agent):**
See `apps/resume-agent-langgraph/README.md` for testing guide

## Integrating with Agent Chat UI

### Step 1: Configure UI Environment

**File Location:** `apps/agent-chat-ui/.env`

**Configuration:**
```bash
# LangGraph Server Connection
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent
```

**Key Fields:**
- `NEXT_PUBLIC_API_URL`: LangGraph server URL
- `NEXT_PUBLIC_ASSISTANT_ID`: Graph ID from `langgraph.json` (must match `graphs` key)

**Existing Example:**
See `apps/agent-chat-ui/.env`

### Step 2: Install UI Dependencies

```bash
cd apps/agent-chat-ui
pnpm install
```

### Step 3: Start UI Development Server

**Terminal 2 - Start Agent Chat UI:**
```bash
cd apps/agent-chat-ui
pnpm dev
```

**UI URL:** `http://localhost:3000`

**Existing Example:**
See `apps/agent-chat-ui/SETUP.md` for complete setup guide

### Step 4: Test Integration

1. Open `http://localhost:3000` in browser
2. Type a message in the chat interface
3. Verify agent responds correctly
4. Check message streaming works
5. Test conversation history persistence

## LLM Provider Integration

### ⚠️ CRITICAL: Environment Variable Loading

**If you see this error:**
```
TypeError: "Could not resolve authentication method. Expected either api_key or auth_token to be set..."
```

**You forgot to load your .env file!** Python does NOT automatically load `.env` files.

**Quick Fix:**
```python
from dotenv import load_dotenv

# Add this at the TOP of your file, BEFORE any LLM imports
load_dotenv()
```

**See:** `references/llm-provider-integration.md` → "Environment Variable Loading (CRITICAL)" for complete troubleshooting guide.

---

### Claude (Anthropic)

**Setup:**
```python
import anthropic
from dotenv import load_dotenv
import os

# CRITICAL: Load .env file first
load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=2048,
    system=system_prompt,
    messages=messages
)

return response.content[0].text
```

**Existing Example:**
See `apps/resume-agent-langgraph/resume_agent_langgraph.py:100-111`

### OpenAI

**Setup:**
```python
import openai

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

api_messages = [{"role": "system", "content": system_prompt}] + messages

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=api_messages,
    max_tokens=2048
)

return response.choices[0].message.content
```

**Existing Example:**
See `apps/resume-agent-langgraph/resume_agent_langgraph.py:83-96`

### Multi-Provider Support

**Pattern:**
```python
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()

def call_llm(messages: list, system_prompt: str) -> str:
    if LLM_PROVIDER == "openai":
        return call_openai(messages, system_prompt)
    else:
        return call_claude(messages, system_prompt)
```

**Existing Example:**
See `apps/resume-agent-langgraph/resume_agent_langgraph.py:69-111`

## Message Format Handling

### LangGraph SDK vs API Format

**Issue:** LangGraph SDK uses `{"type": "human"}` format, but LLM APIs use `{"role": "user"}` format.

**Solution:** Convert messages before LLM invocation.

**Conversion Function:**
```python
def convert_langgraph_messages_to_api_format(messages: list) -> list:
    """
    Convert LangGraph SDK message format to API format.

    LangGraph SDK: {"type": "human", "content": "..."}
    API Format: {"role": "user", "content": "..."}
    """
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

**Existing Example:**
See `apps/resume-agent-langgraph/src/resume_agent/llm/messages.py`

**Usage in Node:**
```python
def chat_node(state: ConversationState) -> dict:
    # Convert to API format
    api_messages = convert_langgraph_messages_to_api_format(state["messages"])

    # Call LLM with converted messages
    response = call_llm(api_messages, system_prompt)

    return {"messages": [{"role": "assistant", "content": response}]}
```

## Web vs CLI Graphs

### CLI Graph Pattern

**For:** Interactive CLI applications with user input prompts.

**Includes:** `get_input` node for CLI user interaction.

**Example:**
```python
def build_cli_graph():
    graph = StateGraph(ConversationState)

    # Add input node for CLI
    graph.add_node("get_input", get_user_input_node)
    graph.add_node("chat", chat_node)

    # Flow: get_input -> chat -> get_input (loop)
    graph.add_edge(START, "get_input")
    graph.add_conditional_edges("get_input", should_continue)
    graph.add_edge("chat", "get_input")

    return graph.compile(checkpointer=checkpointer)
```

**Existing Example:**
See `apps/resume-agent-langgraph/resume_agent_langgraph.py:245-284`

### Web Graph Pattern

**For:** HTTP-based applications (Agent Chat UI, API endpoints).

**Excludes:** `get_input` node (messages come from HTTP requests).

**Example:**
```python
def build_web_graph():
    graph = StateGraph(ConversationState)

    # Only chat node (no input node!)
    graph.add_node("chat", chat_node)

    # Simple flow: START -> chat -> END
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    return graph.compile(checkpointer=checkpointer)
```

**Existing Example:**
See `apps/resume-agent-langgraph/resume_agent_langgraph.py:287-314`

**Key Difference:**
- **CLI**: Manages input collection within the graph
- **Web**: Receives pre-populated messages from HTTP requests

## Testing and Debugging

### Unit Testing Nodes

**Pattern:**
```python
def test_chat_node():
    """Test chat node in isolation"""
    state = {
        "messages": [{"role": "user", "content": "Hello"}]
    }

    result = chat_node(state)

    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0]["role"] == "assistant"
```

### Integration Testing Graphs

**Pattern:**
```python
def test_agent_graph():
    """Test full graph execution"""
    app = build_web_conversation_graph()

    state = {
        "messages": [{"role": "user", "content": "Hello"}]
    }

    config = {"configurable": {"thread_id": "test-123"}}
    result = app.invoke(state, config=config)

    assert len(result["messages"]) > 1  # User + assistant messages
    assert result["messages"][-1]["role"] == "assistant"
```

### LangGraph Studio

Visual debugging tool included with dev server.

**Access:** `http://localhost:2024/studio`

**Features:**
- Visualize graph structure
- Inspect state transitions
- View message flow
- Debug node execution
- Step through workflow

**Existing Example:**
See `apps/agent-chat-ui/SETUP.md:206-214`

### Common Issues

**Issue 1: Pydantic Model in StateGraph**

**Symptom:** `msgpack` serialization errors

**Solution:** Use `TypedDict` instead of Pydantic models
```python
# ❌ Wrong
class State(BaseModel):
    messages: list

# ✅ Correct
class State(TypedDict):
    messages: list
```

**Issue 2: Message Format Mismatch**

**Symptom:** LLM API errors, missing messages

**Solution:** Convert LangGraph messages to API format
```python
api_messages = convert_langgraph_messages_to_api_format(state["messages"])
```

**Issue 3: Missing thread_id**

**Symptom:** Conversation history not persisted

**Solution:** Always provide thread_id in config
```python
config = {"configurable": {"thread_id": "unique-id"}}
app.invoke(state, config=config)
```

**Issue 4: ImportError - attempted relative import**

**Symptom:** `langgraph dev` fails with `ImportError: attempted relative import with no known parent package` or `ModuleNotFoundError`

**Causes:**
- Using relative imports (e.g., `from .state import ...`) in graph modules
- Missing `./src` in `langgraph.json` dependencies array

**Solution:**
1. Change all relative imports to absolute imports
2. Update `langgraph.json` to include `"./src"` in dependencies: `"dependencies": [".", "./src"]`
3. Ensure all directories have `__init__.py` files

**See:** `references/import-fix-guide.md` for complete resolution steps and verification commands

## Best Practices

### State Management

1. **Use TypedDict for state schemas** (not Pydantic)
2. **Use `Annotated[list, add_messages]`** for message history
3. **Return partial state updates** from nodes (don't mutate state)
4. **Add custom fields** as needed for agent logic

### Error Handling

1. **Never raise exceptions in nodes** (breaks workflow)
2. **Accumulate errors in state** for graceful degradation
3. **Return error messages** to user when failures occur
4. **Log errors** for debugging

### Performance

1. **Use appropriate checkpointer** (MemorySaver for dev, SqliteSaver for production)
2. **Minimize state size** (store only essential data)
3. **Implement conditional edges** for efficient routing
4. **Use streaming** for real-time UI updates

### Security

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive configuration
3. **Validate user input** before processing
4. **Implement rate limiting** for production deployments

## Reference Files

For detailed examples and patterns:

### Critical Troubleshooting Guides
- **Import Errors (LangGraph Server):** `references/import-fix-guide.md` ⚠️ Required for src/ layouts
- **Message Format Errors (KeyError: 'role'):** `references/message-format-errors.md` ⚠️ READ FIRST
- **Message Format Guide:** `references/message-format-guide.md`
- **Debugging Agents:** `references/debugging-agents.md`

### Complete Implementation Guides (NEW)
- **StateGraph Complete Guide:** `references/stategraph-complete-guide.md` - Comprehensive patterns for state management and message handling
- **FastAPI Integration Patterns:** `references/fastapi-integration-patterns.md` - Production-ready FastAPI + LangGraph with streaming
- **LLM Provider Integration:** `references/llm-provider-integration.md` - Anthropic Claude and OpenAI GPT integration patterns

### Working Code Examples (NEW)
- **Minimal Agent:** `examples/minimal_agent.py` - Complete agent in 200 lines (includes FastAPI server)
- **Streaming Agent:** `examples/streaming_agent.py` - Real-time streaming with SSE
- **Examples README:** `examples/README.md` - Quick start guide for all examples

### Project-Specific Guides
- **Working Agent Implementation:** `apps/resume-agent-langgraph/resume_agent_langgraph.py`
- **Agent Development Guide:** `apps/resume-agent-langgraph/CLAUDE.md`
- **LangGraph Configuration:** `apps/resume-agent-langgraph/langgraph.json`
- **Chat UI Setup:** `apps/agent-chat-ui/SETUP.md`
- **LangGraph Patterns:** `references/langgraph-patterns.md`
- **Agent Chat UI Integration:** `references/chat-ui-integration.md`

## Additional Resources

### Official Documentation
- **LangGraph Documentation:** https://python.langchain.com/docs/langgraph
- **LangGraph GitHub:** https://github.com/langchain-ai/langgraph
- **Agent Chat UI Repo:** https://github.com/langchain-ai/agent-chat-ui
- **LangGraph Studio:** Included with `langgraph dev` command
- **Context7 Docs:** Use `/fetch-docs langgraph` for latest documentation

### Production Examples (GitHub)
- **Agent Service Toolkit:** https://github.com/JoshuaC215/agent-service-toolkit - Full-stack with PostgreSQL and Docker
- **Assistant UI + LangGraph:** https://github.com/Yonom/assistant-ui-langgraph-fastapi - Modern FastAPI + Next.js template
- **Production Template:** https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template - JWT, Langfuse, Prometheus

### Package Versions (This Project)
```
langgraph>=0.2.0
fastapi>=0.115.0
anthropic>=0.39.0
openai>=1.0.0
@langchain/langgraph-sdk ^0.1.0 (Agent Chat UI)
```

## Quick Start Workflow

### For New Agents

1. **Start with working example:**
   ```bash
   python .claude/skills/langgraph-builder/examples/minimal_agent.py
   ```

2. **Define state schema** (TypedDict with `add_messages`)
   - Use absolute imports if your project uses src/ layout
   - If you encounter import errors, see `references/import-fix-guide.md`
   ```python
   from typing import Annotated, TypedDict
   from langgraph.graph.message import add_messages

   class State(TypedDict):
       messages: Annotated[list, add_messages]
   ```

3. **Implement node functions** (always return AIMessage objects)
   ```python
   from langchain_core.messages import AIMessage

   def chat_node(state):
       # ... call LLM
       return {"messages": [AIMessage(content=response)]}
   ```

4. **Build StateGraph** (add nodes, edges, checkpointer)
5. **Create langgraph.json** (configure graph builder)
6. **Set up .env** (API keys, model configuration)
7. **Test with langgraph dev** (verify graph execution)
8. **Configure Agent Chat UI** (point to LangGraph server)
9. **Test UI integration** (verify chat interface works)
10. **Iterate and refine** (improve agent behavior)

### For FastAPI Deployment

1. **Use streaming example:**
   ```bash
   python .claude/skills/langgraph-builder/examples/streaming_agent.py --server
   ```

2. **Review FastAPI patterns:** `references/fastapi-integration-patterns.md`
3. **Add production features:** CORS, auth, error handling
4. **Deploy with Docker:** See deployment section in FastAPI guide

## Support

**Issues:**
- Review existing working example: `apps/resume-agent-langgraph/`
- Check Agent Chat UI setup guide: `apps/agent-chat-ui/SETUP.md`
- Use LangGraph Studio for visual debugging
- Refer to project-specific guidance: `apps/resume-agent-langgraph/CLAUDE.md`
