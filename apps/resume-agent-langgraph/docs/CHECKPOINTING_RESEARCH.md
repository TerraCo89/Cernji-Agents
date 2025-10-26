# LangGraph Checkpointing and State Persistence Research

**Date**: 2025-10-24
**Purpose**: Production-ready persistence strategies for LangGraph Resume Agent
**Focus**: Checkpointers, thread management, scalability, performance optimization

---

## Table of Contents

1. [Available Checkpointers](#available-checkpointers)
2. [Production Persistence Patterns](#production-persistence-patterns)
3. [Thread Management](#thread-management)
4. [Cross-Thread Persistence (Store Interface)](#cross-thread-persistence-store-interface)
5. [Complete Code Examples](#complete-code-examples)
6. [Performance Considerations](#performance-considerations)
7. [Maintenance and Operations](#maintenance-and-operations)
8. [State Size Optimization](#state-size-optimization)
9. [Sources](#sources)

---

## Available Checkpointers

LangGraph provides multiple checkpointer implementations for different use cases, all conforming to the `BaseCheckpointSaver` interface.

### 1. MemorySaver / InMemorySaver

**Description**: In-memory checkpoint storage using Python defaultdict.

**Use Cases**:
- Testing and debugging
- Development environment
- Short-lived experiments

**Pros**:
- Zero configuration
- Fast operations
- No external dependencies

**Cons**:
- Data lost on restart
- Not suitable for production
- No multi-process support

**Installation**:
```bash
# Included in base langgraph package
pip install langgraph
```

**Example**:
```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

**Production Recommendation**: NEVER use for production - debugging/testing only.

---

### 2. SqliteSaver / AsyncSqliteSaver

**Description**: SQLite-based persistent storage with synchronous and async variants.

**Use Cases**:
- Local development workflows
- Demos and small projects
- Single-user applications
- Prototyping before Postgres

**Pros**:
- File-based persistence
- No external database server
- Simple setup
- Good for development

**Cons**:
- Lightweight, synchronous use cases only
- Does NOT scale to multiple threads/processes
- Poor write performance under load
- NOT recommended for production

**Installation**:
```bash
pip install langgraph-checkpoint-sqlite
```

**Basic Example**:
```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# File-based storage
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
checkpointer = SqliteSaver(conn)
graph = builder.compile(checkpointer=checkpointer)

# Or using connection string
checkpointer = SqliteSaver.from_conn_string("sqlite:///checkpoints.db")
checkpointer.setup()  # Create tables
```

**In-Memory Example**:
```python
checkpointer = SqliteSaver.from_conn_string(":memory:")
checkpointer.setup()
```

**Production Recommendation**: Use for development only. Migrate to PostgreSQL for production.

---

### 3. PostgresSaver / AsyncPostgresSaver

**Description**: Production-grade PostgreSQL checkpoint storage used in LangGraph Platform.

**Use Cases**:
- Production deployments
- Multi-user applications
- High-concurrency workloads
- Enterprise applications

**Pros**:
- Robust and reliable
- Excellent concurrent write performance
- Used by LangGraph Platform
- Battle-tested for production
- Supports connection pooling
- Handles large states efficiently

**Cons**:
- Requires PostgreSQL server
- More complex setup than SQLite
- Network latency (mitigated by pooling)

**Installation**:
```bash
pip install langgraph-checkpoint-postgres
```

**Synchronous Example**:
```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://user:password@localhost:5432/langgraph"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    checkpointer.setup()  # Create tables (first time only)
    graph = builder.compile(checkpointer=checkpointer)
```

**Async Example (Recommended for Production)**:
```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

DB_URI = "postgresql://user:password@localhost:5432/langgraph"

# Create connection pool (reuse across requests)
pool = AsyncConnectionPool(
    conninfo=DB_URI,
    max_size=20,
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0
    }
)

checkpointer = AsyncPostgresSaver(pool)
await checkpointer.setup()  # First time only

graph = builder.compile(checkpointer=checkpointer)
```

**Production Recommendation**: PRIMARY choice for production deployments.

---

### 4. RedisSaver / AsyncRedisSaver

**Description**: Ultra-fast Redis-based checkpointer with <1ms latency.

**Use Cases**:
- Real-time applications requiring sub-millisecond retrieval
- High-throughput agent swarms
- Systems with frequent state updates
- Parallel subgraph patterns (fanout scenarios)

**Pros**:
- Sub-millisecond checkpoint retrieval
- Excellent for parallel workloads
- Outperforms alternatives in benchmarks
- Native JSON support for nested state
- Optional TTL for automatic expiration

**Cons**:
- Requires Redis server
- In-memory storage (higher cost at scale)
- More recent addition (less mature than Postgres)

**Installation**:
```bash
pip install langgraph-checkpoint-redis
```

**Example**:
```python
from langgraph.checkpoint.redis import RedisSaver

REDIS_URI = "redis://localhost:6379"

with RedisSaver.from_conn_string(REDIS_URI) as checkpointer:
    checkpointer.setup()
    graph = builder.compile(checkpointer=checkpointer)
```

**Performance Notes**:
- Version 0.1.0 represents complete redesign for performance
- Optimized for checkpoint creation, write tracking, and state merging
- Shines in fanout patterns (parallel subgraphs)

**Production Recommendation**: Excellent for high-performance, real-time systems. Consider Postgres for cost-effectiveness with large state volumes.

---

### 5. Additional Checkpointers

**MongoDB**: Provides checkpointing with MongoDB as backend. Performant and scalable.
```bash
pip install langgraph-checkpoint-mongodb
```

**Couchbase**: Scalability and flexible query capabilities for complex conversation states across multiple users.
```bash
pip install langgraph-checkpoint-couchbase
```

**Django**: Integrates with Django ORM for Django-based applications.
```bash
pip install langgraph-checkpoint-django
```

---

## Production Persistence Patterns

### Pattern 1: FastAPI + AsyncPostgresSaver (Recommended)

**Use Case**: Production web applications with multiple concurrent users.

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from fastapi import FastAPI

DB_URI = "postgresql://user:password@localhost:5432/langgraph"

# Global connection pool (created once at startup)
connection_pool = None
checkpointer = None

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[dict, None]:
    """Initialize connection pool and checkpointer on startup."""
    global connection_pool, checkpointer

    # Create connection pool
    connection_pool = AsyncConnectionPool(
        conninfo=DB_URI,
        min_size=5,
        max_size=20,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0
        }
    )

    # Create checkpointer
    checkpointer = AsyncPostgresSaver(connection_pool)
    await checkpointer.setup()  # Run migrations (idempotent)

    # Make available to app
    yield {"checkpointer": checkpointer}

    # Cleanup on shutdown
    await connection_pool.close()

app = FastAPI(lifespan=lifespan)

# Compile graph ONCE (reuse across requests)
from langgraph.graph import StateGraph

graph = StateGraph(MyState)
# ... add nodes and edges ...
compiled_graph = None

@app.on_event("startup")
async def compile_workflow():
    global compiled_graph
    compiled_graph = graph.compile(checkpointer=checkpointer)

@app.post("/chat")
async def chat(user_id: str, message: str):
    """Handle chat request with user-specific thread."""
    thread_id = f"user_{user_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Invoke with persistence
    result = await compiled_graph.ainvoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config
    )

    return result
```

**Key Points**:
- Create connection pool once at startup (not per request)
- Compile graph once and reuse (graphs are stateless)
- Neither graph nor checkpointer keep internal state
- Connection pool handles concurrency efficiently

---

### Pattern 2: Thread-Level Persistence for Multi-User Apps

**Use Case**: SaaS applications with isolated user conversations.

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from datetime import datetime

async def handle_user_message(user_id: str, session_id: str, message: str):
    """
    Handle message with user and session isolation.

    Each user can have multiple sessions (e.g., different job applications).
    """
    # Thread ID pattern: user_SESSION_timestamp
    thread_id = f"user_{user_id}_session_{session_id}"

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id,  # For cross-thread memory
            "session_id": session_id
        }
    }

    # Execute with persistence
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": message}]},
        config=config
    )

    return result

# Resume thread (continue previous conversation)
async def resume_conversation(user_id: str, session_id: str):
    """Resume conversation from previous checkpoint."""
    thread_id = f"user_{user_id}_session_{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Get current state
    state = await graph.aget_state(config)
    print(f"Resuming from checkpoint: {state.values}")

    return state
```

**Thread ID Naming Patterns**:
- Simple: `f"user_{user_id}"`
- Session-based: `f"user_{user_id}_session_{session_id}"`
- Timestamped: `f"workflow_{datetime.now().isoformat()}"`
- Job-specific: `f"user_{user_id}_job_{job_id}"`

---

### Pattern 3: Hybrid Checkpointer + Store Architecture

**Use Case**: Applications needing both conversation history (checkpointer) AND cross-thread memory (store).

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from langchain_openai import OpenAIEmbeddings

# Setup checkpointer (thread-level state)
checkpointer = AsyncPostgresSaver(connection_pool)
await checkpointer.setup()

# Setup store (cross-thread memory)
store = AsyncPostgresStore(
    connection_pool,
    index={
        "dims": 1536,
        "embed": OpenAIEmbeddings(model="text-embedding-3-small"),
        "fields": ["content", "summary"]  # Fields to index
    }
)
await store.setup()

# Compile with BOTH
graph = workflow.compile(checkpointer=checkpointer, store=store)

# Access in nodes via dependency injection
def agent_node(state: State, config: RunnableConfig, *, store: BaseStore):
    """Node with access to both state and cross-thread memory."""
    user_id = config["configurable"]["user_id"]

    # Read from store (cross-thread memory)
    namespace = ("users", user_id, "preferences")
    memories = store.search(namespace, query="user preferences", limit=5)

    # Use memories in agent logic
    context = "\n".join([m.value["content"] for m in memories])

    # ... process with LLM ...

    # Save new memory
    store.put(
        namespace,
        key="pref_" + str(uuid.uuid4()),
        value={"content": "User prefers dark mode", "timestamp": datetime.now()}
    )

    return {"output": result}
```

**When to Use Store vs Checkpointer**:
- **Checkpointer**: Conversation history within a single thread/session
- **Store**: Information that persists ACROSS threads (user preferences, facts, entity data)

---

## Thread Management

### Understanding Threads

A **thread** is a unique identifier (`thread_id`) that accumulates state across a sequence of graph executions. Each thread maintains its own independent execution history, like separate chat conversations.

**Key Characteristics**:
- Threads are isolated (changes in one don't affect others)
- Each thread has its own checkpoint history
- Thread IDs are user-defined strings
- Threads enable resumption after interruption

### Creating and Using Threads

```python
from datetime import datetime
import uuid

# Method 1: User-based thread
thread_id = f"user_{user_id}"
config = {"configurable": {"thread_id": thread_id}}

# Method 2: Session-based thread
thread_id = f"user_{user_id}_session_{session_id}"
config = {"configurable": {"thread_id": thread_id}}

# Method 3: Unique per conversation
thread_id = str(uuid.uuid4())
config = {"configurable": {"thread_id": thread_id}}

# Method 4: Timestamp-based
thread_id = f"conversation-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
config = {"configurable": {"thread_id": thread_id}}

# Invoke with thread
result = await graph.ainvoke(initial_state, config=config)
```

### Retrieving Thread State

```python
# Get latest state for thread
config = {"configurable": {"thread_id": "user_123"}}
state = await graph.aget_state(config)

print(f"Messages: {state.values['messages']}")
print(f"Next nodes: {state.next}")
print(f"Config: {state.config}")
print(f"Metadata: {state.metadata}")

# Get specific checkpoint
config_with_checkpoint = {
    "configurable": {
        "thread_id": "user_123",
        "checkpoint_id": "1ef4f797-8335-6428-8001-8a1503f9b875"
    }
}
state = await graph.aget_state(config_with_checkpoint)
```

### Listing Thread History

```python
# Get all checkpoints for a thread (chronologically ordered)
config = {"configurable": {"thread_id": "user_123"}}
history = [state async for state in graph.aget_state_history(config)]

print(f"Total checkpoints: {len(history)}")
for i, state in enumerate(history):
    print(f"Checkpoint {i}: {state.values}, Next: {state.next}")
```

### Time Travel (Replaying from Previous Checkpoint)

```python
# Resume execution from a previous checkpoint
config = {
    "configurable": {
        "thread_id": "user_123",
        "checkpoint_id": "abc-123-def-456"  # Previous checkpoint
    }
}

# This replays prior steps without re-executing them
result = await graph.ainvoke(None, config=config)
```

### Updating Thread State

```python
# Modify state at current or specific checkpoint
config = {"configurable": {"thread_id": "user_123"}}

# Update respects reducer functions (e.g., add_messages appends)
await graph.aupdate_state(
    config,
    {"messages": [{"role": "user", "content": "Updated message"}]}
)

# For channels with reducers, new values merge rather than replace
```

### Deleting Threads

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

checkpointer = AsyncPostgresSaver(pool)

# Delete all checkpoints for a thread
await checkpointer.adelete_thread("user_123")

# Note: Deletion is immediate and irreversible
```

### Multi-User Thread Management Best Practices

**1. Use Descriptive Thread IDs**
```python
# Good: Clear structure
thread_id = f"user_{user_id}_job_{job_id}"

# Bad: Opaque UUID
thread_id = str(uuid.uuid4())  # Hard to query/debug
```

**2. Implement Thread Metadata**
```python
config = {
    "configurable": {
        "thread_id": f"user_{user_id}",
        "user_id": user_id,
        "session_start": datetime.now().isoformat(),
        "application_type": "job_application"
    }
}
```

**3. Thread Lifecycle Management**
```python
async def create_thread(user_id: str, job_id: str) -> str:
    """Create new thread with metadata."""
    thread_id = f"user_{user_id}_job_{job_id}"

    # Initialize empty state
    config = {"configurable": {"thread_id": thread_id}}
    await graph.ainvoke({"messages": []}, config=config)

    return thread_id

async def archive_thread(thread_id: str):
    """Archive completed thread to cold storage."""
    # Export state
    state = await graph.aget_state({"configurable": {"thread_id": thread_id}})

    # Save to archive (S3, etc.)
    await save_to_archive(thread_id, state.values)

    # Delete from hot storage
    await checkpointer.adelete_thread(thread_id)
```

**4. Connection Pool Sizing for Multi-User Apps**
```python
from psycopg_pool import AsyncConnectionPool

# Calculate pool size based on concurrency
# Rule of thumb: 2x expected concurrent users
pool = AsyncConnectionPool(
    conninfo=DB_URI,
    min_size=5,          # Minimum idle connections
    max_size=20,         # Maximum connections
    max_waiting=10,      # Max waiting requests before error
    kwargs={
        "autocommit": True,
        "prepare_threshold": 0  # Disable prepared statements for pooling
    }
)
```

---

## Cross-Thread Persistence (Store Interface)

The **Store** interface enables sharing information across multiple threads, solving problems that checkpointers alone cannot.

### When to Use Store vs Checkpointer

| Feature | Checkpointer | Store |
|---------|-------------|-------|
| **Scope** | Single thread/session | Cross-thread/global |
| **Use Case** | Conversation history | User preferences, facts, entities |
| **Persistence** | Per thread_id | Namespaced keys |
| **Search** | Get state by thread | Semantic search across namespaces |
| **Example** | Chat messages in one conversation | User's preferred resume format (all conversations) |

### Available Store Implementations

1. **InMemoryStore**: Development/testing only
2. **PostgresStore**: Production-ready SQL storage with vector search
3. **RedisStore**: High-performance in-memory store with TTL support

### Basic Store Usage Pattern

```python
from langgraph.store.postgres import AsyncPostgresStore
from langchain_openai import OpenAIEmbeddings

# Setup store with semantic search
store = AsyncPostgresStore(
    connection_pool,
    index={
        "dims": 1536,
        "embed": OpenAIEmbeddings(model="text-embedding-3-small"),
        "fields": ["content", "summary"]  # Index these fields for search
    }
)
await store.setup()

# Compile graph with store
graph = workflow.compile(checkpointer=checkpointer, store=store)
```

### Namespace Organization

Namespaces are **tuples** that organize data hierarchically, like directory paths.

```python
# User-specific preferences
namespace = ("users", user_id, "preferences")

# Company-specific data
namespace = ("companies", company_name, "job_postings")

# Global facts
namespace = ("global", "resume_templates")
```

### Storing and Retrieving Data

```python
def agent_node(state: State, config: RunnableConfig, *, store: BaseStore):
    """Node with store access via dependency injection."""
    user_id = config["configurable"]["user_id"]
    namespace = ("users", user_id, "memories")

    # Store a memory
    memory_id = str(uuid.uuid4())
    await store.aput(
        namespace,
        key=memory_id,
        value={
            "content": "User prefers concise bullet points",
            "timestamp": datetime.now().isoformat(),
            "source": "resume_feedback"
        },
        ttl=None  # Persist indefinitely
    )

    # Retrieve specific memory
    memory = await store.aget(namespace, key=memory_id)
    print(f"Memory: {memory.value}")

    # Retrieve all memories for user
    all_memories = await store.asearch(namespace, limit=100)

    return {"output": result}
```

### Semantic Search

```python
# Search across memories by meaning
namespace = ("users", user_id, "preferences")
relevant_memories = await store.asearch(
    namespace,
    query="What resume format does the user prefer?",
    limit=3
)

# Build context for LLM
context = "\n".join([
    f"- {m.value['content']}"
    for m in relevant_memories
])
```

### Cross-User Search

```python
# Search across ALL users' preferences
namespace_prefix = ("users",)  # Match all users
results = await store.asearch(
    namespace_prefix,
    query="preferred resume templates",
    limit=10
)

# Results include data from multiple users
for result in results:
    print(f"User: {result.namespace[1]}, Data: {result.value}")
```

### TTL and Expiration

```python
# Store with TTL (auto-delete after X minutes)
await store.aput(
    namespace,
    key="temp_data",
    value={"data": "temporary"},
    ttl=60  # Expire after 60 minutes
)

# Refresh TTL on read
memory = await store.aget(namespace, key="temp_data", refresh_ttl=True)
```

### Store Operations Summary

| Method | Description |
|--------|-------------|
| `aput(namespace, key, value, index, ttl)` | Store/update item |
| `aget(namespace, key, refresh_ttl)` | Retrieve single item |
| `asearch(namespace_prefix, query, filter, limit, offset, refresh_ttl)` | Semantic search |
| `adelete(namespace, key)` | Remove item |
| `alist_namespaces(match_conditions, max_depth, limit, offset)` | List available namespaces |
| `abatch(ops)` | Execute multiple operations atomically |

---

## Complete Code Examples

### Example 1: Production FastAPI + PostgreSQL

```python
#!/usr/bin/env python3
"""
Production-ready LangGraph Resume Agent with PostgreSQL persistence.
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TypedDict, Annotated
from datetime import datetime
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import OpenAIEmbeddings
from psycopg_pool import AsyncConnectionPool

# Configuration
DB_URI = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/langgraph")
POOL_MIN_SIZE = 5
POOL_MAX_SIZE = 20

# Global resources
connection_pool = None
checkpointer = None
store = None
compiled_graph = None

# State Schema
class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    job_id: str | None

# Agent Node
async def chat_node(state: ConversationState, config, *, store):
    """Process message with LLM, using cross-thread memory."""
    user_id = config["configurable"]["user_id"]
    namespace = ("users", user_id, "preferences")

    # Retrieve user preferences from store (cross-thread)
    memories = await store.asearch(
        namespace,
        query="resume preferences and feedback",
        limit=5
    )

    context = "\n".join([m.value["content"] for m in memories])

    # Call LLM (simplified)
    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = await client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=f"You are a resume agent. User preferences:\n{context}",
        messages=[
            {"role": m.type, "content": m.content}
            for m in state["messages"]
        ]
    )

    assistant_message = response.content[0].text

    return {
        "messages": [AIMessage(content=assistant_message)]
    }

# Build Graph
def build_graph():
    """Build conversation graph."""
    graph = StateGraph(ConversationState)
    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    return graph

# FastAPI Lifespan
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[dict, None]:
    """Initialize database resources on startup."""
    global connection_pool, checkpointer, store, compiled_graph

    print("Initializing database connection pool...")
    connection_pool = AsyncConnectionPool(
        conninfo=DB_URI,
        min_size=POOL_MIN_SIZE,
        max_size=POOL_MAX_SIZE,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0
        }
    )

    print("Setting up checkpointer...")
    checkpointer = AsyncPostgresSaver(connection_pool)
    await checkpointer.setup()

    print("Setting up store...")
    store = AsyncPostgresStore(
        connection_pool,
        index={
            "dims": 1536,
            "embed": OpenAIEmbeddings(model="text-embedding-3-small"),
            "fields": ["content"]
        }
    )
    await store.setup()

    print("Compiling graph...")
    graph = build_graph()
    compiled_graph = graph.compile(checkpointer=checkpointer, store=store)

    print("Application ready!")
    yield {"checkpointer": checkpointer, "store": store}

    print("Shutting down...")
    await connection_pool.close()

app = FastAPI(lifespan=lifespan)

# API Models
class ChatRequest(BaseModel):
    user_id: str
    message: str
    job_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str

# Endpoints
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat message with persistence."""
    # Thread ID: user_JOB or just user
    if request.job_id:
        thread_id = f"user_{request.user_id}_job_{request.job_id}"
    else:
        thread_id = f"user_{request.user_id}"

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": request.user_id
        }
    }

    # Invoke graph
    try:
        result = await compiled_graph.ainvoke(
            {
                "messages": [HumanMessage(content=request.message)],
                "user_id": request.user_id,
                "job_id": request.job_id
            },
            config=config
        )

        # Extract assistant message
        last_message = result["messages"][-1]

        return ChatResponse(
            response=last_message.content,
            thread_id=thread_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{thread_id}")
async def get_history(thread_id: str):
    """Retrieve conversation history for a thread."""
    config = {"configurable": {"thread_id": thread_id}}

    try:
        state = await compiled_graph.aget_state(config)
        return {
            "thread_id": thread_id,
            "messages": [
                {"role": m.type, "content": m.content}
                for m in state.values.get("messages", [])
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Thread not found")

@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete all checkpoints for a thread."""
    try:
        await checkpointer.adelete_thread(thread_id)
        return {"status": "deleted", "thread_id": thread_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

### Example 2: SQLite Development Setup

```python
#!/usr/bin/env python3
"""
Development setup with SQLite persistence.
"""
import sqlite3
from typing import TypedDict, Annotated
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Setup SQLite checkpointer
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "checkpoints.db"

# Create connection with threading support
conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)

# Initialize checkpointer
checkpointer = SqliteSaver(conn)
checkpointer.setup()  # Create tables

# State Schema
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Simple chat node
def chat_node(state: State):
    """Process message."""
    last_message = state["messages"][-1].content
    response = f"Echo: {last_message}"
    return {"messages": [AIMessage(content=response)]}

# Build graph
graph = StateGraph(State)
graph.add_node("chat", chat_node)
graph.add_edge(START, "chat")
graph.add_edge("chat", END)

# Compile with SQLite checkpointer
app = graph.compile(checkpointer=checkpointer)

# CLI Interface
def main():
    """Interactive CLI with persistence."""
    print("SQLite Checkpointer Demo")
    print("=" * 60)

    thread_id = input("Enter thread ID (or 'new' for new thread): ").strip()
    if thread_id == "new":
        from datetime import datetime
        thread_id = f"thread-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    config = {"configurable": {"thread_id": thread_id}}

    # Show existing history
    try:
        state = app.get_state(config)
        if state.values.get("messages"):
            print(f"\nResuming thread: {thread_id}")
            print("History:")
            for msg in state.values["messages"]:
                role = "User" if msg.type == "human" else "Assistant"
                print(f"  {role}: {msg.content}")
        else:
            print(f"\nStarting new thread: {thread_id}")
    except:
        print(f"\nStarting new thread: {thread_id}")

    print("\nType 'exit' to quit\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        # Invoke with persistence
        result = app.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=config
        )

        # Display response
        last_message = result["messages"][-1]
        print(f"Assistant: {last_message.content}\n")

if __name__ == "__main__":
    main()
```

---

### Example 3: Resume Agent with Store and Checkpointer

```python
#!/usr/bin/env python3
"""
Resume Agent with hybrid persistence: checkpointer + store.
"""
from typing import TypedDict, Annotated
from datetime import datetime
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import OpenAIEmbeddings

# State Schema
class ResumeAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    job_analysis: dict | None
    tailored_resume: dict | None

# Initialize checkpointer and store
checkpointer = MemorySaver()
store = InMemoryStore(
    index={
        "embed": OpenAIEmbeddings(model="text-embedding-3-small"),
        "dims": 1536,
        "fields": ["content"]
    }
)

# Nodes
def analyze_job_node(state: ResumeAgentState, config, *, store):
    """Analyze job posting and save to store."""
    user_id = config["configurable"]["user_id"]
    last_message = state["messages"][-1].content

    # Simulate job analysis
    job_analysis = {
        "company": "Example Corp",
        "title": "Senior Engineer",
        "requirements": ["Python", "FastAPI", "PostgreSQL"]
    }

    # Save to store (cross-thread memory)
    namespace = ("users", user_id, "job_analyses")
    job_id = str(uuid.uuid4())
    store.put(
        namespace,
        key=job_id,
        value={
            "content": f"Job at {job_analysis['company']} - {job_analysis['title']}",
            "analysis": job_analysis,
            "timestamp": datetime.now().isoformat()
        }
    )

    return {
        "messages": [AIMessage(content=f"Analyzed job: {job_analysis['title']}")],
        "job_analysis": job_analysis
    }

def tailor_resume_node(state: ResumeAgentState, config, *, store):
    """Tailor resume using job analysis and user history."""
    user_id = config["configurable"]["user_id"]

    # Retrieve previous job analyses from store
    namespace = ("users", user_id, "job_analyses")
    previous_jobs = store.search(namespace, limit=5)

    context = f"User has applied to {len(previous_jobs)} jobs previously"

    # Simulate resume tailoring
    tailored_resume = {
        "summary": "Tailored for " + state["job_analysis"]["title"],
        "context": context
    }

    return {
        "messages": [AIMessage(content="Resume tailored!")],
        "tailored_resume": tailored_resume
    }

# Router
def route_after_analyze(state: ResumeAgentState):
    """Route to resume tailoring if job analysis succeeded."""
    if state.get("job_analysis"):
        return "tailor_resume"
    return END

# Build Graph
graph = StateGraph(ResumeAgentState)
graph.add_node("analyze_job", analyze_job_node)
graph.add_node("tailor_resume", tailor_resume_node)

graph.add_edge(START, "analyze_job")
graph.add_conditional_edges(
    "analyze_job",
    route_after_analyze,
    {
        "tailor_resume": "tailor_resume",
        END: END
    }
)
graph.add_edge("tailor_resume", END)

# Compile with BOTH checkpointer and store
app = graph.compile(checkpointer=checkpointer, store=store)

# Example Usage
if __name__ == "__main__":
    user_id = "user_123"
    thread_id = f"user_{user_id}_job_application_1"

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id
        }
    }

    # First invocation
    result = app.invoke(
        {
            "messages": [HumanMessage(content="Analyze this job posting")],
            "user_id": user_id
        },
        config=config
    )

    print("Result:", result)

    # Check store (cross-thread memory)
    namespace = ("users", user_id, "job_analyses")
    analyses = store.search(namespace)
    print(f"\nUser has {len(analyses)} job analyses stored")
```

---

## Performance Considerations

### 1. Checkpointer Performance Comparison

| Checkpointer | Read Latency | Write Latency | Use Case | Concurrency | Cost |
|-------------|-------------|---------------|----------|-------------|------|
| **MemorySaver** | Nanoseconds | Nanoseconds | Dev/Test | Single process | Free |
| **SqliteSaver** | Milliseconds | Milliseconds (poor under load) | Dev/Demos | Single thread | Free |
| **PostgresSaver** | Low milliseconds | Low milliseconds | Production | Excellent | Moderate |
| **RedisSaver** | <1ms | <1ms | Real-time | Excellent | Higher (memory) |
| **MongoDB** | Low milliseconds | Low milliseconds | Production | Excellent | Moderate |

**Benchmark Notes** (Redis Blog):
- Redis 0.1.0 consistently outperforms alternatives in fanout benchmarks
- Sub-millisecond checkpoint retrieval for real-time applications
- Optimized for parallel subgraph patterns (agent swarms)

### 2. Connection Pool Sizing

**Rule of Thumb**: `max_size = 2 × expected_concurrent_users`

```python
from psycopg_pool import AsyncConnectionPool

# For 10 concurrent users
pool = AsyncConnectionPool(
    conninfo=DB_URI,
    min_size=5,          # Keep 5 idle connections warm
    max_size=20,         # Allow up to 20 concurrent connections
    max_waiting=10,      # Queue up to 10 requests before failing
    timeout=30.0,        # Wait 30s for available connection
    kwargs={
        "autocommit": True,          # Don't open transactions
        "prepare_threshold": 0       # Disable prepared statements
    }
)
```

**Why `autocommit=True`?** Checkpointers write frequently; explicit transactions add overhead.

**Why `prepare_threshold=0`?** Prepared statements can cause issues with connection pooling.

### 3. State Size Optimization

**Problem**: Large states increase serialization/deserialization overhead and database storage.

**Solutions**:

**a) Minimize State Schema**
```python
# Bad: Storing large blobs in state
class State(TypedDict):
    messages: list[BaseMessage]
    full_resume_text: str  # 50KB blob
    all_job_postings: list[dict]  # 500KB blob

# Good: Store only references
class State(TypedDict):
    messages: list[BaseMessage]
    resume_id: str  # Reference to store
    job_id: str     # Reference to store
```

**b) Use Store for Large Data**
```python
# Store large data in store, not state
namespace = ("users", user_id, "resumes")
store.put(namespace, key=resume_id, value=large_resume_dict)

# Keep only ID in state
return {"resume_id": resume_id}
```

**c) Prune Conversation History**
```python
from langchain_core.messages import trim_messages

def trim_history_node(state: State):
    """Keep only last N messages."""
    trimmed = trim_messages(
        state["messages"],
        max_tokens=4000,
        strategy="last",
        token_counter=len  # Or use tiktoken
    )
    return {"messages": trimmed}
```

**d) Summarize Old Messages**
```python
def summarize_node(state: State):
    """Summarize old messages, keep only summary + recent."""
    if len(state["messages"]) > 20:
        old_messages = state["messages"][:-10]
        recent_messages = state["messages"][-10:]

        # Summarize old messages with LLM
        summary = await llm.summarize(old_messages)

        # Replace with summary message
        summary_msg = AIMessage(content=f"[Summary]: {summary}")
        return {"messages": [summary_msg] + recent_messages}

    return {}
```

### 4. Database Optimization

**PostgreSQL Configuration**:
```sql
-- Increase connection limit (default 100)
ALTER SYSTEM SET max_connections = 200;

-- Tune for write-heavy workloads
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- Restart PostgreSQL
```

**Redis Configuration**:
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru  # Evict least recently used
save ""  # Disable RDB snapshots for performance (optional)
```

### 5. Monitoring and Observability

**Metrics to Track**:
- Checkpoint read/write latency (p50, p95, p99)
- Connection pool utilization
- Database size growth
- Thread count growth
- Average state size per checkpoint

**Example Instrumentation**:
```python
import time
from prometheus_client import Counter, Histogram

checkpoint_read_duration = Histogram(
    'checkpoint_read_seconds',
    'Time to read checkpoint'
)
checkpoint_write_duration = Histogram(
    'checkpoint_write_seconds',
    'Time to write checkpoint'
)

async def instrumented_invoke(graph, state, config):
    """Invoke graph with metrics."""
    start = time.time()

    try:
        result = await graph.ainvoke(state, config)

        # Record success
        duration = time.time() - start
        checkpoint_write_duration.observe(duration)

        return result
    except Exception as e:
        # Record failure
        checkpoint_errors.inc()
        raise
```

### 6. Caching Strategies

**Problem**: Repeated operations waste compute and API calls.

**Solution**: Cache results in state or store.

```python
def caching_node(state: State, config, *, store):
    """Check cache before expensive operation."""
    job_url = state["job_url"]

    # Check store for cached result
    namespace = ("cache", "job_analyses")
    cached = store.get(namespace, key=job_url)

    if cached:
        return {
            "job_analysis": cached.value["analysis"],
            "cached": True
        }

    # Expensive operation
    analysis = await analyze_job_expensive(job_url)

    # Cache result
    store.put(
        namespace,
        key=job_url,
        value={"analysis": analysis},
        ttl=60 * 24  # Cache for 24 hours
    )

    return {
        "job_analysis": analysis,
        "cached": False
    }
```

### 7. Serialization Optimization

**Default Serialization**: `JsonPlusSerializer` handles most types.

**For Complex Objects**:
```python
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

# Enable pickle fallback for unsupported types
serde = JsonPlusSerializer(pickle_fallback=True)
checkpointer = PostgresSaver(pool, serde=serde)
```

**For Security-Critical Data**:
```python
from langgraph.checkpoint.serde.encrypted import EncryptedSerializer

# Encrypt checkpoints (reads LANGGRAPH_AES_KEY env var)
serde = EncryptedSerializer.from_pycryptodome_aes()
checkpointer = PostgresSaver(pool, serde=serde)
```

---

## Maintenance and Operations

### 1. Checkpoint Cleanup and Pruning

**Problem**: Checkpoints accumulate over time, growing database size.

**Current State**: LangGraph does not provide built-in cleanup mechanisms.

**Solutions**:

**a) Manual Thread Deletion**
```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def cleanup_old_threads(checkpointer: AsyncPostgresSaver, days: int = 30):
    """Delete threads older than N days."""
    from datetime import datetime, timedelta

    cutoff = datetime.now() - timedelta(days=days)

    # Query threads (requires custom SQL)
    async with checkpointer.conn.cursor() as cur:
        await cur.execute("""
            SELECT DISTINCT thread_id
            FROM checkpoints
            WHERE created_at < %s
        """, (cutoff,))

        old_threads = await cur.fetchall()

    # Delete each thread
    for (thread_id,) in old_threads:
        await checkpointer.adelete_thread(thread_id)
        print(f"Deleted thread: {thread_id}")
```

**b) Database Vacuum (PostgreSQL)**
```sql
-- Reclaim space from deleted rows
VACUUM FULL checkpoints;
VACUUM FULL checkpoint_blobs;
VACUUM FULL checkpoint_writes;

-- Schedule regular vacuuming
CREATE EXTENSION IF NOT EXISTS pg_cron;
SELECT cron.schedule('vacuum-checkpoints', '0 2 * * *', 'VACUUM checkpoints');
```

**c) Archival Strategy**
```python
async def archive_and_prune(checkpointer, thread_id: str, archive_store):
    """Archive thread to cold storage, then delete."""
    # Export all checkpoints
    config = {"configurable": {"thread_id": thread_id}}
    history = [
        state async for state in checkpointer.aget_state_history(config)
    ]

    # Save to archive (S3, GCS, etc.)
    await archive_store.save(thread_id, history)

    # Delete from hot storage
    await checkpointer.adelete_thread(thread_id)
```

### 2. TTL-Based Expiration (Store Interface)

**For cross-thread data**, use TTL:

```python
# Store with automatic expiration
await store.aput(
    namespace=("cache", "job_analyses"),
    key=job_url,
    value=analysis,
    ttl=60 * 24  # Expire after 24 hours
)

# Start background sweeper (PostgresStore)
await store.start_ttl_sweeper(interval_minutes=60)
```

### 3. Monitoring Database Growth

**PostgreSQL Size Query**:
```sql
-- Total size of checkpointing tables
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE tablename IN ('checkpoints', 'checkpoint_blobs', 'checkpoint_writes')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Thread count
SELECT COUNT(DISTINCT thread_id) FROM checkpoints;

-- Average checkpoint size
SELECT AVG(length(checkpoint_data)) FROM checkpoints;
```

### 4. Backup and Restore

**PostgreSQL Backup**:
```bash
# Backup entire database
pg_dump -U postgres -d langgraph -Fc -f langgraph_backup.dump

# Backup only checkpoint tables
pg_dump -U postgres -d langgraph -t checkpoints -t checkpoint_blobs -t checkpoint_writes -Fc -f checkpoints.dump

# Restore
pg_restore -U postgres -d langgraph -Fc langgraph_backup.dump
```

**SQLite Backup**:
```python
import sqlite3
import shutil

# File-based backup
shutil.copy("checkpoints.db", "checkpoints_backup.db")

# Or use SQLite backup API
src = sqlite3.connect("checkpoints.db")
dst = sqlite3.connect("checkpoints_backup.db")
src.backup(dst)
dst.close()
src.close()
```

### 5. Migration Between Checkpointers

**SQLite to PostgreSQL Migration**:
```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def migrate_sqlite_to_postgres():
    """Migrate checkpoints from SQLite to PostgreSQL."""
    # Connect to both
    sqlite_saver = SqliteSaver.from_conn_string("sqlite:///checkpoints.db")
    postgres_saver = AsyncPostgresSaver.from_conn_string(
        "postgresql://user:pass@localhost/langgraph"
    )
    await postgres_saver.setup()

    # Get all threads from SQLite
    sqlite_conn = sqlite3.connect("checkpoints.db")
    cursor = sqlite_conn.execute("SELECT DISTINCT thread_id FROM checkpoints")
    threads = [row[0] for row in cursor.fetchall()]

    # Migrate each thread
    for thread_id in threads:
        config = {"configurable": {"thread_id": thread_id}}

        # Get all checkpoints for thread
        checkpoints = list(sqlite_saver.list(config))

        # Write to PostgreSQL
        for checkpoint in checkpoints:
            await postgres_saver.aput(
                config,
                checkpoint,
                metadata=checkpoint.metadata
            )

        print(f"Migrated thread: {thread_id}")
```

### 6. Health Checks

```python
from fastapi import FastAPI

@app.get("/health")
async def health_check():
    """Check database connectivity."""
    try:
        # Test connection
        async with connection_pool.connection() as conn:
            await conn.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "pool_size": connection_pool.get_stats()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }, 503
```

---

## State Size Optimization

### 1. Sliding Window for Messages

```python
from langchain_core.messages import trim_messages

def trim_messages_node(state: State):
    """Keep only last N messages to prevent unbounded growth."""
    MAX_MESSAGES = 20

    if len(state["messages"]) > MAX_MESSAGES:
        # Keep last N messages
        trimmed = trim_messages(
            state["messages"],
            max_tokens=4000,
            strategy="last"
        )
        return {"messages": trimmed}

    return {}
```

### 2. Message Summarization

```python
async def summarize_history_node(state: State):
    """Summarize old messages when history grows too large."""
    if len(state["messages"]) > 30:
        # Split: old (to summarize) + recent (keep verbatim)
        old_messages = state["messages"][:20]
        recent_messages = state["messages"][20:]

        # Summarize old messages
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        response = await client.messages.create(
            model="claude-haiku-3.5",  # Fast model for summarization
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"Summarize this conversation:\n\n{format_messages(old_messages)}"
            }]
        )

        summary = response.content[0].text

        # Replace old messages with summary
        summary_message = AIMessage(
            content=f"[Conversation Summary]: {summary}"
        )

        return {"messages": [summary_message] + recent_messages}

    return {}
```

### 3. Offload Large Data to Store

```python
def process_large_document_node(state: State, config, *, store):
    """Process large document without bloating state."""
    document = state["large_document"]  # 1MB PDF

    # Process document
    analysis = analyze_document(document)

    # Store document in store, not state
    namespace = ("documents",)
    doc_id = str(uuid.uuid4())
    store.put(
        namespace,
        key=doc_id,
        value={"document": document, "analysis": analysis}
    )

    # Return only reference in state
    return {
        "document_id": doc_id,
        "large_document": None  # Clear from state
    }
```

### 4. Periodic Cleanup

```python
def cleanup_state_node(state: State):
    """Remove stale or temporary data from state."""
    return {
        "temp_data": None,
        "cached_results": None,
        "intermediate_outputs": None
    }
```

---

## Sources

### Official Documentation
- [LangGraph Persistence Concepts](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [LangGraph Checkpointers Reference](https://langchain-ai.github.io/langgraph/reference/checkpoints/)
- [LangGraph Store Reference](https://langchain-ai.github.io/langgraph/reference/store/)
- [LangGraph How-To: Add Memory](https://langchain-ai.github.io/langgraph/how-tos/memory/add-memory/)
- [LangGraph How-To: Cross-Thread Persistence](https://langchain-ai.github.io/langgraph/how-tos/cross-thread-persistence-functional/)

### Package Documentation
- [langgraph-checkpoint PyPI](https://pypi.org/project/langgraph-checkpoint/)
- [langgraph-checkpoint-sqlite PyPI](https://pypi.org/project/langgraph-checkpoint-sqlite/)
- [langgraph-checkpoint-postgres PyPI](https://pypi.org/project/langgraph-checkpoint-postgres/)

### Blog Posts and Articles
- [LangGraph v0.2: Checkpointer Libraries](https://blog.langchain.com/langgraph-v0-2/)
- [Redis Checkpointer 0.1.0](https://redis.io/blog/langgraph-redis-checkpoint-010/)
- [LangGraph & Redis: Memory & Persistence](https://redis.io/blog/langgraph-redis-build-smarter-ai-agents-with-memory-persistence/)
- [Launching Long-Term Memory Support](https://blog.langchain.com/launching-long-term-memory-support-in-langgraph/)

### Community Discussions
- [GitHub Discussion #1357: Web Framework Checkpointer Usage](https://github.com/langchain-ai/langgraph/discussions/1357)
- [GitHub Discussion #894: PostgreSQL Persistence](https://github.com/langchain-ai/langgraph/discussions/894)
- [GitHub Discussion #2086: Cross-Thread Persistence](https://github.com/langchain-ai/langgraph/discussions/2086)

### Example Implementations
- [GitHub: langgraph-redis](https://github.com/redis-developer/langgraph-redis)
- [Medium: FastAPI + AsyncSqliteSaver](https://medium.com/@devwithll/simple-langgraph-implementation-with-memory-asyncsqlitesaver-checkpointer-fastapi-54f4e4879a2e)
- [Medium: Customizing Memory in LangGraph](https://focused.io/lab/customizing-memory-in-langgraph-agents-for-better-conversations)

---

## Recommendations for Resume Agent

Based on this research, here are recommendations for the LangGraph Resume Agent:

### Development Phase
- Use **SqliteSaver** for local development and testing
- File-based storage: `data/checkpoints.db`
- Simple setup, no external dependencies

### Production Phase
- Use **AsyncPostgresSaver** as primary checkpointer
- Connection pool: 5-20 connections depending on load
- Thread ID pattern: `f"user_{user_id}_job_{job_id}"`

### Cross-Thread Memory
- Use **PostgresStore** for user preferences and job history
- Enable semantic search with OpenAI embeddings
- Namespace pattern: `("users", user_id, "memories")`

### Performance Optimization
- Trim message history after 20 messages
- Cache job analyses in store (24-hour TTL)
- Monitor checkpoint size and growth rate

### Maintenance
- Implement monthly checkpoint cleanup (delete threads > 30 days old)
- Add health checks for database connectivity
- Set up monitoring for pool utilization

### Migration Path
1. Start with SqliteSaver in development
2. Test with PostgresSaver locally (Docker)
3. Deploy to production with managed PostgreSQL
4. Consider Redis for future high-performance needs

---

**End of Research Document**
