# LangGraph Checkpointing

Source: https://langchain-ai.github.io/langgraph

## Overview

Checkpointing enables persistence and time-travel debugging in LangGraph applications. It allows you to save graph state at any point and resume from that state later.

## Core Checkpoint Components

### Checkpoint Structure

```python
from langgraph.checkpoint import Checkpoint, CheckpointMetadata, CheckpointTuple

checkpoint = {
    "v": 4,
    "ts": "2024-07-31T20:14:19.804150+00:00",
    "id": "1ef4f797-8335-6428-8001-8a1503f9b875",
    "channel_values": {
        "my_key": "meow",
        "node": "node"
    },
    "channel_versions": {
        "__start__": 2,
        "my_key": 3,
        "start:node": 3,
        "node": 3
    },
    "versions_seen": {
        "__input__": {},
        "__start__": {"__start__": 1},
        "node": {"start:node": 2}
    },
}
```

### CheckpointTuple

Contains checkpoint data along with metadata:

```python
from langgraph.checkpoint import CheckpointTuple

# Components of a checkpoint tuple
checkpoint_tuple = CheckpointTuple(
    config=None,
    ts=None,
    parent_ts=None,
    thread_ts=None,
    id=None,
    persisted_keys=None
)
```

### CheckpointMetadata

```python
from langgraph.checkpoint import CheckpointMetadata

metadata = CheckpointMetadata(
    run_id="run-123",
    name="my_graph"
)
```

## Checkpoint Savers

### Base Checkpoint Saver

Protocol for implementing custom checkpointers:

```python
from langgraph.checkpoint import BaseCheckpointSaver

class CustomCheckpointer(BaseCheckpointSaver):
    def get(self, config):
        """Retrieve a checkpoint"""
        pass

    def put(self, config, checkpoint, metadata, new_versions):
        """Store a checkpoint"""
        pass

    def list(self, config):
        """List checkpoints"""
        pass
```

### Memory Saver

In-memory checkpointing for development:

```python
from langgraph.checkpoint import MemorySaver

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

### PostgreSQL Saver

Production-grade persistence:

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
```

### SQLite Saver

File-based persistence:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Example initialization
# sqlite_saver = SqliteSaver.from_conn_str("sqlite:///checkpoints.db")
```

## Checkpoint Operations

### Storing Checkpoints

```python
write_config = {"configurable": {"thread_id": "1", "checkpoint_ns": ""}}

checkpointer.put(write_config, checkpoint, {}, {})
```

### Retrieving Checkpoints

```python
read_config = {"configurable": {"thread_id": "1"}}

checkpoint = checkpointer.get(read_config)
```

### Listing Checkpoints

```python
checkpoints = list(checkpointer.list(read_config))
```

## State Snapshots

### StateSnapshot Structure

```python
from langgraph.graph import StateSnapshot

snapshot = StateSnapshot(values={"key": "value"})
```

### Example State with Metadata

```json
{
  "values": {
    "messages": [
      "[Object]",
      {
        "id": "chatcmpl-A3FGhKzOZs0GYZ2yalNOCQZyPgbcp",
        "content": "",
        "additional_kwargs": {
          "tool_calls": [{
            "id": "call_OsKnTv2psf879eeJ9vx5GeoY",
            "type": "function",
            "function": "[Object]"
          }]
        }
      }
    ]
  },
  "next": ["agent"],
  "tasks": [{
    "id": "612efffa-3b16-530f-8a39-fd01c31e7b8b",
    "name": "agent",
    "interrupts": []
  }],
  "metadata": {
    "source": "loop",
    "writes": {"tools": "[Object]"},
    "step": 2
  },
  "config": {
    "configurable": {
      "thread_id": "conversation-num-1",
      "checkpoint_ns": "",
      "checkpoint_id": "1ef69ab6-9516-6200-8002-43d2c6dc603f"
    }
  },
  "createdAt": "2024-09-03T04:17:19.904Z",
  "parentConfig": {
    "configurable": {
      "thread_id": "conversation-num-1",
      "checkpoint_ns": "",
      "checkpoint_id": "1ef69ab6-9455-6410-8001-1c78a97f63e6"
    }
  }
}
```

## Update State

Edit graph state at specific checkpoints:

```python
# Update current state
config = {"configurable": {"thread_id": "1"}}
graph.update_state(config=config)

# Fork from a specific checkpoint
config = {
    "configurable": {
        "thread_id": "1",
        "checkpoint_id": "some-checkpoint-id"
    }
}
graph.update_state(config=config)
```

## Checkpoint Utilities

### Channel Versions

```python
from langgraph.checkpoint import (
    ChannelVersions,
    compareChannelVersions,
    maxChannelVersion,
)

# Compare versions
is_newer = compareChannelVersions(version1, version2)

# Get maximum version
max_version = maxChannelVersion(versions)
```

### Checkpoint IDs

```python
from langgraph.checkpoint import getCheckpointId, uuid5, uuid6

# Generate checkpoint IDs
checkpoint_id = getCheckpointId()

# UUID utilities
id_v5 = uuid5(namespace, name)
id_v6 = uuid6()
```

### Path Utilities

```python
from langgraph.checkpoint import (
    NameSpacePath,
    tokenizePath,
    getTextAtPath,
)

# Tokenize namespace path
tokens = tokenizePath(path)

# Extract text at path
text = getTextAtPath(data, path)
```

## Checkpoint Constants

```python
from langgraph.checkpoint import (
    ERROR,
    INTERRUPT,
    RESUME,
    SCHEDULED,
    TASKS,
    WRITES_IDX_MAP,
)
```

## Checkpoint Subgraph Propagation

Checkpointers automatically propagate to subgraphs:

```python
from langgraph.graph import START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from typing import TypedDict

class State(TypedDict):
    foo: str

# Subgraph
def subgraph_node_1(state: State):
    return {"foo": state["foo"] + "bar"}

subgraph_builder = StateGraph(State)
subgraph_builder.add_node(subgraph_node_1)
subgraph_builder.add_edge(START, "subgraph_node_1")
subgraph = subgraph_builder.compile()

# Parent graph
builder = StateGraph(State)
builder.add_node("node_1", subgraph)
builder.add_edge(START, "node_1")

checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)
```

## Pending Writes

### CheckpointPendingWrite

Tracks writes that haven't been committed:

```python
from langgraph.checkpoint import (
    CheckpointPendingWrite,
    PendingWrite,
    PendingWriteValue,
)
```

## Storage Backends

### In-Memory Storage

```python
from langgraph.checkpoint import InMemoryStore, InMemoryCache

store = InMemoryStore()
cache = InMemoryCache()
```

### Base Store Protocol

```python
from langgraph.checkpoint import BaseStore, BaseCache

class CustomStore(BaseStore):
    def get(self, key):
        pass

    def put(self, key, value):
        pass

    def delete(self, key):
        pass
```

## Async Batched Store

For high-performance async operations:

```python
from langgraph.checkpoint import AsyncBatchedStore

store = AsyncBatchedStore()
```

## Checkpoint List Options

```python
from langgraph.checkpoint import CheckpointListOptions

options = CheckpointListOptions(
    limit=10,
    before=None,
    metadata=None,
)

checkpoints = list(checkpointer.list(config, **options))
```

## Store Operations

### Get Operation

```python
from langgraph.checkpoint import GetOperation

op = GetOperation(namespace="memories", key="user_123")
```

### Put Operation

```python
from langgraph.checkpoint import PutOperation

op = PutOperation(
    namespace="memories",
    key="user_123",
    value={"name": "John"}
)
```

### Search Operation

```python
from langgraph.checkpoint import SearchOperation, MatchCondition

op = SearchOperation(
    namespace="memories",
    match_conditions=[
        MatchCondition(field="type", value="user")
    ]
)
```

### List Namespaces Operation

```python
from langgraph.checkpoint import (
    ListNamespacesOperation,
    NamespaceMatchType,
)

op = ListNamespacesOperation(
    match_type=NamespaceMatchType.PREFIX,
    path=["memories"]
)
```

## Best Practices

1. **Choose the right checkpointer**:
   - Development: MemorySaver
   - Production: PostgresSaver or custom implementation

2. **Manage checkpoint lifecycle**:
   - Implement retention policies
   - Clean up old checkpoints
   - Monitor storage usage

3. **Thread management**:
   - Use meaningful thread IDs
   - Implement thread cleanup logic
   - Consider partitioning strategies

4. **Error handling**:
   - Handle checkpoint failures gracefully
   - Implement retry logic
   - Monitor checkpoint operations

5. **Performance**:
   - Use async operations for I/O-bound workloads
   - Batch checkpoint operations when possible
   - Index checkpoint metadata for fast queries

## Advanced Features

### Deep Copy Utility

```python
from langgraph.checkpoint import deepCopy

copied_checkpoint = deepCopy(original_checkpoint)
```

### Serialization Protocols

```python
from langgraph.checkpoint import (
    SerializerProtocol,
    ChannelProtocol,
    SendProtocol,
)
```

## Next Steps

- Implement custom checkpointers for your storage backend
- Explore time-travel debugging with checkpoints
- Build resumable workflows with checkpointing
- Optimize checkpoint performance for production
