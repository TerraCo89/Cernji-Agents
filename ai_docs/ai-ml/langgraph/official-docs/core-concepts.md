# LangGraph Core Concepts

Source: https://langchain-ai.github.io/langgraph

## Overview

LangGraph models agent workflows as graphs, with States, Nodes, and Edges as the fundamental building blocks.

## Core Components

### 1. States

States represent the application's data structure. They define what information flows through your graph.

#### Basic State Definition (Python)

```python
from typing_extensions import TypedDict

class MyState(TypedDict):
    messages: list
```

#### With Annotations

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]
```

#### TypeScript/Zod

```typescript
import { z } from "zod";

const State = z.object({
  foo: z.number(),
  bar: z.array(z.string()),
});
```

### 2. Nodes

Nodes contain the logic that processes state. They're functions that take state as input and return state updates.

```python
def add_message(state):
    return {"messages": state["messages"] + ["New message"]}
```

### 3. Edges

Edges define the flow between nodes, determining execution order.

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(MyState)
workflow.add_node("add_message_node", add_message)
workflow.add_edge("add_message_node", END)
workflow.set_entry_point("add_message_node")
```

## State Reducers

### Default Behavior (Last Write Wins)

```python
from typing_extensions import TypedDict

class State(TypedDict):
    foo: int
    bar: list[str]
```

When no reducer is specified, the latest value replaces the previous one.

### add_messages Reducer

Handles message accumulation with deduplication and updates:

```python
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict

class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

## Graph Construction

### Basic Graph

```python
from langgraph.graph import StateGraph, END

class MyState:
    messages: list

def add_message(state):
    return {"messages": state["messages"] + ["New message"]}

workflow = StateGraph(MyState)
workflow.add_node("add_message_node", add_message)
workflow.add_edge("add_message_node", END)
workflow.set_entry_point("add_message_node")

# app = workflow.compile()
```

### StateGraph with START and END

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)
builder.add_node(node)
builder.set_entry_point("node")
graph = builder.compile()
```

```typescript
import { StateGraph } from "@langchain/langgraph";

const graph = new StateGraph(State)
  .addNode("node", node)
  .addEdge("__start__", "node")
  .compile();
```

## Special Nodes

### START Node

Designates the entry point for user input:

```python
from langgraph.graph import START

graph.add_edge(START, "node_a")
```

```typescript
import { START } from "@langchain/langgraph";

graph.addEdge(START, "nodeA");
```

### END Node

Marks the termination point of the graph:

```python
from langgraph.graph import END

graph.add_edge("final_node", END)
```

## MessagesState

Pre-configured state for chat applications:

### Python

```python
from langgraph.graph import MessagesState

class State(MessagesState):
    extra_field: int
```

### TypeScript

```typescript
import { MessagesZodState } from "@langchain/langgraph";

// Messages are automatically deserialized into LangChain Message objects
const graph = new StateGraph(MessagesZodState)
  // ...
```

Supported input formats:

```json
{
  "messages": [new HumanMessage("message")]
}

// Also supported:
{
  "messages": [{ "role": "human", "content": "message" }]
}
```

## Command Object

Combine state updates with control flow:

```python
def my_node(state: State) -> Command[Literal["my_other_node"]]:
    return Command(
        update={"foo": "bar"},
        goto="my_other_node"
    )
```

```typescript
import { Command } from "@langchain/langgraph";

graph.addNode("myNode", (state) => {
  return new Command({
    update: { foo: "bar" },
    goto: "myOtherNode",
  });
});
```

### Dynamic Routing with Command

```python
def my_node(state: State) -> Command[Literal["my_other_node"]]:
    if state["foo"] == "bar":
        return Command(update={"foo": "baz"}, goto="my_other_node")
```

```typescript
import { Command } from "@langchain/langgraph";

graph.addNode("myNode", (state) => {
  if (state.foo === "bar") {
    return new Command({
      update: { foo: "baz" },
      goto: "myOtherNode",
    });
  }
});

// Specify possible endpoints for graph rendering
builder.addNode("myNode", myNode, {
  ends: ["myOtherNode", END],
});
```

## Compilation

Compile the graph before use:

```python
graph = graph_builder.compile(...)
```

```typescript
const graph = new StateGraph(StateAnnotation)
  .addNode("nodeA", nodeA)
  .addEdge(START, "nodeA")
  .addEdge("nodeA", END)
  .compile();
```

Compilation performs:
- Structural validation
- Orphaned node detection
- Runtime configuration (checkpointers, breakpoints)

## Core API Components

### Available Imports (Python)

```python
from langgraph.graph import (
    StateGraph,
    Graph,
    CompiledGraph,
    CompiledStateGraph,
    END,
    START,
    INTERRUPT,
)

from langgraph.graph.message import (
    add_messages,
    Messages,
    MessagesAnnotation,
    MessagesZodState,
    REMOVE_ALL_MESSAGES,
)

from langgraph.graph import (
    Annotation,
    AnnotationRoot,
    Command,
    Send,
)
```

### Available Imports (TypeScript)

```typescript
import {
  StateGraph,
  Graph,
  CompiledGraph,
  END,
  START,
  INTERRUPT,
  Command,
  Send,
  Annotation,
} from "@langchain/langgraph";

import {
  MessagesZodState,
  MessagesAnnotation,
  addMessages,
} from "@langchain/langgraph";
```

## Error Handling

### Base Errors

```python
from langgraph.graph import (
    BaseLangGraphError,
    GraphInterrupt,
    InvalidUpdateError,
    EmptyChannelError,
    EmptyInputError,
    GraphValueError,
    GraphRecursionError,
    NodeInterrupt,
    MultipleSubgraphsError,
    UnreachableNodeError,
)
```

## Best Practices

1. **State Design**:
   - Keep state minimal and focused
   - Use typed dictionaries for clarity
   - Choose appropriate reducers for your data

2. **Node Design**:
   - Keep nodes small and focused
   - Return only updated fields
   - Handle errors gracefully

3. **Edge Design**:
   - Use conditional edges for branching logic
   - Ensure all paths lead to END
   - Avoid circular dependencies without proper conditions

4. **Compilation**:
   - Compile once, invoke many times
   - Configure checkpointers at compile time
   - Use type hints for better IDE support

## Advanced Patterns

### Multiple State Schemas

```python
class InputState(TypedDict):
    user_input: str

class OutputState(TypedDict):
    graph_output: str

class OverallState(TypedDict):
    foo: str
    user_input: str
    graph_output: str

builder = StateGraph(
    OverallState,
    input_schema=InputState,
    output_schema=OutputState
)
```

### Subgraphs

```javascript
const builder = new StateGraph(MessagesZodState)
  .addNode("subgraphNode", async (state) => {
    const response = await subgraph.invoke({
      subgraphMessages: state.messages,
    });
    return { messages: response.subgraphMessages };
  })
  .addEdge(START, "subgraphNode");
const graph = builder.compile();
await graph.invoke({ messages: [{ role: "user", content: "hi!" }] });
```

## Next Steps

- Learn about persistence and checkpointing
- Explore conditional edges and routing
- Build multi-agent systems
- Deploy graphs to production
