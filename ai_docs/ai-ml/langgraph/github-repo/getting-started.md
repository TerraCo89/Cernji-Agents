# LangGraph Getting Started

Source: `/langchain-ai/langgraph` (GitHub Repository)

## Overview

LangGraph is a low-level orchestration framework for building, managing, and deploying long-running, stateful agents and workflows with comprehensive memory, human-in-the-loop capabilities, and production-ready deployment.

## Core Components

### 1. State Management

#### Initialize StateGraph

Define a state schema using TypedDict (Python) or Zod (TypeScript) to manage the chatbot's state:

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)
```

```typescript
import { StateGraph, MessagesZodState, START } from "@langchain/langgraph";
import { z } from "zod";

const State = z.object({ messages: MessagesZodState.shape.messages });
const graph = new StateGraph(State).compile();
```

#### Subclass MessagesState (Python)

Extend the prebuilt `MessagesState` to add custom fields:

```python
from langgraph.graph import MessagesState

class State(MessagesState):
    documents: list[str]
```

### 2. Building a Basic Chatbot

Complete chatbot setup with state, LLM integration, and graph compilation:

```python
from typing import Annotated
from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

llm = init_chat_model("anthropic:claude-3-5-sonnet-latest")

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

# Add node and edges
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()
```

```typescript
import { StateGraph, START, END, MessagesZodState } from "@langchain/langgraph";
import { z } from "zod";
import { ChatOpenAI } from "@langchain/openai";

const llm = new ChatOpenAI({
  model: "gpt-4o",
  temperature: 0,
});

const State = z.object({ messages: MessagesZodState.shape.messages });

const graph = new StateGraph(State)
  .addNode("chatbot", async (state) => {
    return { messages: [await llm.invoke(state.messages)] };
  })
  .addEdge(START, "chatbot")
  .addEdge("chatbot", END)
  .compile();
```

### 3. Adding Tools

Bind tools to the LLM for enhanced capabilities:

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)
```

```typescript
import { StateGraph, MessagesZodState } from "@langchain/langgraph";
import { z } from "zod";

const State = z.object({ messages: MessagesZodState.shape.messages });

const chatbot = async (state: z.infer<typeof State>) => {
  const llmWithTools = llm.bindTools(tools);
  return { messages: [await llmWithTools.invoke(state.messages)] };
};
```

### 4. Prebuilt Components

Use LangGraph's prebuilt components for common patterns:

```python
from typing import Annotated
from langchain_tavily import TavilySearch
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

tool = TavilySearch(max_results=2)
tools = [tool]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()
```

### 5. Entry Point Definition

Specify where the graph execution begins:

```python
graph_builder.add_edge(START, "chatbot")
```

```typescript
import { StateGraph, MessagesZodState, START } from "@langchain/langgraph";
import { z } from "zod";

const State = z.object({ messages: MessagesZodState.shape.messages });

const graph = new StateGraph(State)
  .addNode("chatbot", async (state: z.infer<typeof State>) => {
    return { messages: [await llm.invoke(state.messages)] };
  })
  .addEdge(START, "chatbot")
  .compile();
```

## State Schemas

### Using TypedDict (Python)

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages

class GraphState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
```

### Multiple State Schemas

Define distinct input, output, overall, and private states:

```python
class InputState(TypedDict):
    user_input: str

class OutputState(TypedDict):
    graph_output: str

class OverallState(TypedDict):
    foo: str
    user_input: str
    graph_output: str

class PrivateState(TypedDict):
    bar: str

def node_1(state: InputState) -> OverallState:
    return {"foo": state["user_input"] + " name"}

def node_2(state: OverallState) -> PrivateState:
    return {"bar": state["foo"] + " is"}

def node_3(state: PrivateState) -> OutputState:
    return {"graph_output": state["bar"] + " Lance"}

builder = StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_2", "node_3")
builder.add_edge("node_3", END)

graph = builder.compile()
graph.invoke({"user_input": "My"})
```

### TypeScript Equivalent

```typescript
const InputState = z.object({
  userInput: z.string(),
});

const OutputState = z.object({
  graphOutput: z.string(),
});

const OverallState = z.object({
  foo: z.string(),
  userInput: z.string(),
  graphOutput: z.string(),
});

const PrivateState = z.object({
  bar: z.string(),
});

const graph = new StateGraph({
  state: OverallState,
  input: InputState,
  output: OutputState,
})
  .addNode("node1", (state) => {
    return { foo: state.userInput + " name" };
  })
  .addNode("node2", (state) => {
    return { bar: state.foo + " is" };
  })
  .addNode("node3", (state) => {
    return { graphOutput: state.bar + " Lance" };
  }, { input: PrivateState })
  .addEdge(START, "node1")
  .addEdge("node1", "node2")
  .addEdge("node2", "node3")
  .addEdge("node3", END)
  .compile();

await graph.invoke({ userInput: "My" });
// { graphOutput: 'My name is Lance' }
```

## Command Object

Use the `Command` object to combine state updates and control flow:

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

## Compilation

After defining nodes and edges, compile the graph:

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

## Next Steps

- Learn about persistence and checkpointing
- Explore memory management patterns
- Build multi-agent systems
- Deploy to production with LangGraph Cloud
