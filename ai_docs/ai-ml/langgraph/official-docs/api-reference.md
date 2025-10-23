# LangGraph API Reference

Source: https://langchain-ai.github.io/langgraph

## Core Modules

### langgraph.graph

Main graph construction and execution module.

```python
from langgraph.graph import (
    # Core graph classes
    Graph,
    StateGraph,
    CompiledGraph,
    CompiledStateGraph,

    # Execution engine
    Pregel,
    PregelNode,

    # Special nodes
    START,
    END,
    INTERRUPT,

    # State management
    Annotation,
    AnnotationRoot,
    StateDefinition,
    StateGraphArgs,
    StateSnapshot,

    # Control flow
    Command,
    ParentCommand,
    Send,

    # Channels
    BaseChannel,
    BinaryOperatorAggregate,

    # Errors
    BaseLangGraphError,
    GraphBubbleUp,
    GraphInterrupt,
    GraphRecursionError,
    GraphValueError,
    EmptyChannelError,
    EmptyInputError,
    InvalidUpdateError,
    MultipleSubgraphsError,
    NodeInterrupt,
    UnreachableNodeError,
    RemoteException,

    # Configuration
    LangGraphRunnableConfig,
    PregelOptions,
    Runtime,
    StateType,
    StreamMode,
    TaskOptions,
    WaitForNames,
)
```

### langgraph.graph.message

Message handling utilities.

```python
from langgraph.graph.message import (
    add_messages,
    Messages,
    MessagesAnnotation,
    MessagesZodMeta,
    MessagesZodState,
    REMOVE_ALL_MESSAGES,
    messagesStateReducer,
)
```

### langgraph.checkpoint

Checkpointing and persistence.

```python
from langgraph.checkpoint import (
    # Core checkpoint classes
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ReadonlyCheckpoint,

    # Checkpoint savers
    BaseCheckpointSaver,
    MemorySaver,

    # Storage
    BaseStore,
    BaseCache,
    InMemoryStore,
    InMemoryCache,
    MemoryStore,
    AsyncBatchedStore,

    # Operations
    GetOperation,
    PutOperation,
    SearchOperation,
    ListNamespacesOperation,
    Operation,
    OperationResults,

    # Data structures
    Item,
    SearchItem,
    MatchCondition,
    NameSpacePath,
    NamespaceMatchType,
    IndexConfig,

    # Pending writes
    CheckpointPendingWrite,
    PendingWrite,
    PendingWriteValue,

    # Protocols
    ChannelProtocol,
    SendProtocol,
    SerializerProtocol,

    # Versioning
    ChannelVersions,
    All,
    CacheFullKey,
    CacheNamespace,
    CheckpointListOptions,

    # Constants
    ERROR,
    INTERRUPT,
    RESUME,
    SCHEDULED,
    TASKS,
    WRITES_IDX_MAP,

    # Utilities
    compareChannelVersions,
    deepCopy,
    getCheckpointId,
    getTextAtPath,
    maxChannelVersion,
    tokenizePath,
    uuid5,
    uuid6,
)
```

### langgraph.prebuilt

Pre-built components and utilities.

```python
from langgraph.prebuilt import (
    # Tools
    ToolExecutor,
    ToolNode,
    ToolExecutorArgs,
    ToolInvocationInterface,
    ToolNodeOptions,

    # Agent components
    ActionRequest,
    AgentState,
    AgentNameMode,

    # Human-in-the-loop
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,

    # Agent builders
    CreateReactAgentParams,
    FunctionCallingExecutorState,

    # Functions
    create_function_calling_executor,
    create_react_agent,
    create_react_agent_annotation,
    tools_condition,
    with_agent_name,
)
```

## Functional API

### Entrypoints and Tasks

```python
from langgraph import (
    entrypoint,
    task,
    typedNode,
)

# Helper functions
from langgraph import (
    getConfig,
    getCurrentTaskInput,
    getPreviousState,
    getStore,
    getSubgraphsSeenSet,
    getWriter,
    interrupt,
)

# Type guards
from langgraph import (
    isCommand,
    isGraphBubbleUp,
    isGraphInterrupt,
    isInterrupted,
    isParentCommand,
)
```

## TypeScript/JavaScript API

### Core Graph

```typescript
import {
  StateGraph,
  Graph,
  CompiledGraph,
  CompiledStateGraph,
  START,
  END,
  INTERRUPT,
  Command,
  Send,
  Annotation,
  AnnotationRoot,
} from "@langchain/langgraph";
```

### Messages

```typescript
import {
  MessagesZodState,
  MessagesAnnotation,
  addMessages,
  messagesStateReducer,
  REMOVE_ALL_MESSAGES,
} from "@langchain/langgraph";
```

### Checkpointing

```typescript
import {
  MemorySaver,
  Checkpoint,
  CheckpointMetadata,
  CheckpointTuple,
} from "@langchain/langgraph";

import {
  PostgresSaver,
} from "@langchain/langgraph-checkpoint-postgres";
```

### Prebuilt

```typescript
import {
  createReactAgent,
  ToolNode,
} from "@langchain/langgraph/prebuilt";
```

## Type Definitions

### Python Type Definitions

```python
from langgraph.graph import (
    # Type aliases
    BaseLangGraphErrorFields,
    BinaryOperator,
    CommandParams,
    EntrypointOptions,
    GetStateOptions,
    Interrupt,
    MultipleChannelSubscriptionOptions,
    NodeType,
    RetryPolicy,
    SingleChannelSubscriptionOptions,
    SingleReducer,
    StreamOutputMap,
    UpdateType,
)
```

### TypeScript Type Definitions

```typescript
import type {
  StateType,
  NodeType,
  StreamMode,
  UpdateType,
  LangGraphRunnableConfig,
} from "@langchain/langgraph";
```

## Configuration Objects

### RuntimeConfig

```python
from langgraph.graph import LangGraphRunnableConfig

config = LangGraphRunnableConfig(
    recursion_limit=1000,
    configurable={
        "thread_id": "1",
        "checkpoint_ns": "",
    }
)
```

### PregelOptions

```python
from langgraph.graph import PregelOptions, TaskOptions

options = PregelOptions(
    tasks=[
        TaskOptions(name="task1", concurrency=1),
        TaskOptions(name="task2", concurrency=2),
    ]
)
```

## Error Classes

### Core Errors

```python
from langgraph.graph import (
    BaseLangGraphError,      # Base error class
    EmptyChannelError,       # Channel has no value
    EmptyInputError,         # No input provided
    GraphValueError,         # Invalid graph configuration
    GraphRecursionError,     # Recursion limit exceeded
    InvalidUpdateError,      # Invalid state update
    UnreachableNodeError,    # Node cannot be reached
    MultipleSubgraphsError,  # Multiple subgraphs conflict
    NodeInterrupt,           # Node execution interrupted
    GraphInterrupt,          # Graph execution interrupted
    GraphBubbleUp,           # Bubble up to parent graph
    RemoteException,         # Remote execution error
)
```

## Stream Modes

```python
from langgraph.graph import StreamMode

# Available modes:
# - "values": Full state after each step
# - "updates": Only updates from each node
# - "messages": Individual messages as generated
```

## Command Parameters

```python
from langgraph.graph import CommandParams

command = Command(
    update={"key": "value"},
    goto="next_node",
    graph=Command.PARENT,  # or Command.CURRENT
)
```

## Utility Functions

### State Access

```python
from langgraph import (
    getConfig,              # Get current config
    getCurrentTaskInput,    # Get current task input
    getPreviousState,       # Get previous state snapshot
    getStore,              # Get store instance
    getWriter,             # Get writer instance
    getSubgraphsSeenSet,   # Get visited subgraphs
)
```

### Type Guards

```python
from langgraph import (
    isCommand,          # Check if object is Command
    isGraphBubbleUp,    # Check if error is GraphBubbleUp
    isGraphInterrupt,   # Check if error is GraphInterrupt
    isInterrupted,      # Check if execution interrupted
    isParentCommand,    # Check if command targets parent
)
```

## Constants Reference

### Special Values

```python
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint import ERROR, INTERRUPT, RESUME, SCHEDULED, TASKS
```

## Database-Specific Extensions

### PostgreSQL Checkpoint

```python
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Synchronous
saver = PostgresSaver.from_conn_string(DB_URI)

# Asynchronous
async_saver = AsyncPostgresSaver.from_conn_string(DB_URI)
```

### SQLite Checkpoint

```python
from langgraph.checkpoint.sqlite import SqliteSaver

saver = SqliteSaver.from_conn_str("sqlite:///checkpoints.db")
```

### MongoDB (if available)

```python
# from langgraph.checkpoint.mongodb import MongoDBSaver
```

## Remote Graph Execution

```python
from langgraph.remote import RemoteGraph, RemoteGraphParams

params = RemoteGraphParams(
    url="https://api.example.com/graph",
    method="POST"
)

remote_graph = RemoteGraph(params)
```

## Web Components

```python
from langgraph.web import (
    Annotation,
    AnnotationRoot,
    # ... other web-specific components
)
```

## Best Practices

1. **Import only what you need**: Reduces memory footprint
2. **Use type hints**: Leverage Python/TypeScript type checking
3. **Check error types**: Use specific error handling
4. **Configure appropriately**: Set recursion limits and timeouts
5. **Use async when appropriate**: Better for I/O-bound operations

## Version Compatibility

- Python: 3.9+
- TypeScript/JavaScript: ES2020+
- LangChain: Compatible with latest LangChain versions

## Next Steps

- Explore specific modules in depth
- Review examples for each component
- Check changelog for version updates
- Consult TypeScript definitions for detailed typing
