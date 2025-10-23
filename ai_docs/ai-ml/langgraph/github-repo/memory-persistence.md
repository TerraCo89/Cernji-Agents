# LangGraph Memory and Persistence

Source: `/langchain-ai/langgraph` (GitHub Repository)

## Overview

LangGraph provides robust memory and persistence capabilities through checkpointers and stores, enabling conversational memory, state recovery, and cross-thread data sharing.

## Short-Term Memory (Checkpointing)

### In-Memory Checkpointer

```python
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.memory import InMemorySaver

model = init_chat_model(model="anthropic:claude-3-5-haiku-latest")

def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

checkpointer = InMemorySaver()
builder = StateGraph(MessagesState)
builder.add_node(call_model)
builder.add_edge(START, "call_model")
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "1"}}
graph.invoke({"messages": "hi, my name is bob"}, config)
graph.invoke({"messages": "write a short poem about cats"}, config)
graph.invoke({"messages": "now do the same but for dogs"}, config)
final_response = graph.invoke({"messages": "what's my name?"}, config)

final_response["messages"][-1].pretty_print()
```

```typescript
import { trimMessages } from "@langchain/core/messages";
import { ChatAnthropic } from "@langchain/anthropic";
import { StateGraph, START, MessagesZodState, MemorySaver } from "@langchain/langgraph";
import { z } from "zod";

const model = new ChatAnthropic({ model: "claude-3-5-sonnet-20241022" });

const callModel = async (state: z.infer<typeof MessagesZodState>) => {
  const messages = trimMessages(state.messages, {
    strategy: "last",
    maxTokens: 128,
    startOn: "human",
    endOn: ["human", "tool"],
  });
  const response = await model.invoke(messages);
  return { messages: [response] };
};

const checkpointer = new MemorySaver();
const builder = new StateGraph(MessagesZodState)
  .addNode("call_model", callModel)
  .addEdge(START, "call_model");
const graph = builder.compile({ checkpointer });

const config = { configurable: { thread_id: "1" } };
await graph.invoke({ messages: [{ role: "user", content: "hi, my name is bob" }] }, config);
await graph.invoke({ messages: [{ role: "user", content: "write a short poem about cats" }] }, config);
await graph.invoke({ messages: [{ role: "user", content: "now do the same but for dogs" }] }, config);
const finalResponse = await graph.invoke({ messages: [{ role: "user", content: "what's my name?" }] }, config);

console.log(finalResponse.messages.at(-1)?.content);
```

### PostgreSQL Checkpointer

```python
from langgraph.checkpoint.postgres import PostgresSaver

DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"

with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
    builder = StateGraph(...)
    graph = builder.compile(checkpointer=checkpointer)
```

```typescript
import { PostgresSaver } from "@langchain/langgraph-checkpoint-postgres";

const DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable";
const checkpointer = PostgresSaver.fromConnString(DB_URI);

const builder = new StateGraph(...);
const graph = builder.compile({ checkpointer });
```

### Async PostgreSQL Example

```python
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

model = init_chat_model(model="anthropic:claude-3-5-haiku-latest")

DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"
async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
    # await checkpointer.setup()  # Call once for initial setup

    async def call_model(state: MessagesState):
        response = await model.ainvoke(state["messages"])
        return {"messages": response}

    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_edge(START, "call_model")

    graph = builder.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "1"}}

    async for chunk in graph.astream(
        {"messages": [{"role": "user", "content": "hi! I'm bob"}]},
        config,
        stream_mode="values"
    ):
        chunk["messages"][-1].pretty_print()

    async for chunk in graph.astream(
        {"messages": [{"role": "user", content: "what's my name?"}]},
        config,
        stream_mode="values"
    ):
        chunk["messages"][-1].pretty_print()
```

## Long-Term Memory (Store)

### Managing Cross-Thread Memory

```python
from langchain_core.messages import RemoveMessage

async def call_model(
    state: MessagesState,
    config: RunnableConfig,
    *,
    store: BaseStore,
):
    user_id = config["configurable"]["user_id"]
    namespace = ("memories", user_id)

    # Search for relevant memories
    memories = await store.asearch(namespace, query=str(state["messages"][-1].content))
    info = "\n".join([d.value["data"] for d in memories])
    system_msg = f"You are a helpful assistant. User info: {info}"

    # Store new memories if requested
    last_message = state["messages"][-1]
    if "remember" in last_message.content.lower():
        memory = "User name is Bob"
        await store.aput(namespace, str(uuid.uuid4()), {"data": memory})

    response = await model.ainvoke(
        [{"role": "system", "content": system_msg}] + state["messages"]
    )
    return {"messages": response}

builder = StateGraph(MessagesState)
builder.add_node(call_model)
builder.add_edge(START, "call_model")

graph = builder.compile(
    checkpointer=checkpointer,
    store=store,
)

config = {
    "configurable": {
        "thread_id": "1",
        "user_id": "1",
    }
}

async for chunk in graph.astream(
    {"messages": [{"role": "user", "content": "Hi! Remember: my name is Bob"}]},
    config,
    stream_mode="values",
):
    chunk["messages"][-1].pretty_print()

# Different thread, same user
config = {
    "configurable": {
        "thread_id": "2",
        "user_id": "1",
    }
}

async for chunk in graph.astream(
    {"messages": [{"role": "user", "content": "what is my name?"}]},
    config,
    stream_mode="values",
):
    chunk["messages"][-1].pretty_print()
```

### PostgreSQL Store

```python
from langgraph.store.postgres import PostgresStore

DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable"

with PostgresStore.from_conn_string(DB_URI) as store:
    builder = StateGraph(...)
    graph = builder.compile(store=store)
```

```typescript
import { PostgresStore } from "@langchain/langgraph-checkpoint-postgres";

const DB_URI = "postgresql://postgres:postgres@localhost:5442/postgres?sslmode=disable";
const store = PostgresStore.fromConnString(DB_URI);

const builder = new StateGraph(...);
const graph = builder.compile({ store });
```

## Accessing State in Tools

Tools can access the graph's state directly:

```python
from typing import Annotated
from langgraph.prebuilt import InjectedState, create_react_agent

class CustomState(AgentState):
    user_id: str

def get_user_info(
    state: Annotated[CustomState, InjectedState]
) -> str:
    """Look up user info."""
    user_id = state["user_id"]
    return "User is John Smith" if user_id == "user_123" else "Unknown user"

agent = create_react_agent(
    model="anthropic:claude-3-7-sonnet-latest",
    tools=[get_user_info],
    state_schema=CustomState,
)

agent.invoke({
    "messages": "look up user information",
    "user_id": "user_123"
})
```

```typescript
import { tool } from "@langchain/core/tools";
import { z } from "zod";
import {
  MessagesZodState,
  LangGraphRunnableConfig,
} from "@langchain/langgraph";
import { createReactAgent } from "@langchain/langgraph/prebuilt";

const CustomState = z.object({
  messages: MessagesZodState.shape.messages,
  userId: z.string(),
});

const getUserInfo = tool(
  async (_, config: LangGraphRunnableConfig) => {
    const userId = config.configurable?.userId;
    return userId === "user_123" ? "User is John Smith" : "Unknown user";
  },
  {
    name: "get_user_info",
    description: "Look up user info.",
    schema: z.object({}),
  }
);

const agent = createReactAgent({
  llm: model,
  tools: [getUserInfo],
  stateSchema: CustomState,
});

await agent.invoke({
  messages: [{ role: "user", content: "look up user information" }],
  userId: "user_123",
});
```

## Deleting Messages

Remove specific messages from state:

```python
from langchain_core.messages import RemoveMessage

def delete_messages(state):
    messages = state["messages"]
    if len(messages) > 2:
        # Remove the earliest two messages
        return {"messages": [RemoveMessage(id=m.id) for m in messages[:2]]}
```

## Managing Checkpoints

### InMemorySaver Basic Usage

```python
from langgraph.checkpoint.memory import InMemorySaver

write_config = {"configurable": {"thread_id": "1", "checkpoint_ns": ""}}
read_config = {"configurable": {"thread_id": "1"}}

checkpointer = InMemorySaver()
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

# Store checkpoint
checkpointer.put(write_config, checkpoint, {}, {})

# Load checkpoint
checkpointer.get(read_config)

# List checkpoints
list(checkpointer.list(read_config))
```

## Threads and Pre-populated State

Create threads with initial state:

```python
from langgraph_sdk import get_client

client = get_client(url=<DEPLOYMENT_URL>)
thread = await client.threads.create(
    graph_id="agent",
    supersteps=[
        {
            "updates": [{"values": {}, "as_node": '__input__'}]
        },
        {
            "updates": [{
                "values": {
                    "messages": [{"type": 'human', "content": 'hello'}]
                },
                "as_node": '__start__'
            }]
        },
        {
            "updates": [{
                "values": {
                    "messages": [{
                        "content": 'Hello! How can I assist you today?',
                        "type": 'ai'
                    }]
                },
                "as_node": 'call_model'
            }]
        }
    ]
)

print(thread)
```

```javascript
import { Client } from "@langchain/langgraph-sdk";

const client = new Client({ apiUrl: <DEPLOYMENT_URL> });
const thread = await client.threads.create({
    graphId: 'agent',
    supersteps: [
        {
            updates: [{values: {}, asNode: '__input__'}]
        },
        {
            updates: [{
                values: {
                    messages: [{type: 'human', content: 'hello'}]
                },
                asNode: '__start__',
            }]
        },
        {
            updates: [{
                values: {
                    messages: [{
                        content: 'Hello! How can I assist you today?',
                        type: 'ai',
                    }]
                },
                asNode: 'call_model',
            }]
        }
    ],
});

console.log(thread);
```

## Summary Extension (TypeScript)

Add summary tracking to state:

```typescript
import { MessagesZodState } from "@langchain/langgraph";
import { z } from "zod";

const State = MessagesZodState.merge(z.object({
  summary: z.string().optional(),
}));
```

## Best Practices

1. **Choose the right persistence layer**: Use in-memory for development, PostgreSQL for production
2. **Manage thread IDs**: Use meaningful thread IDs to organize conversations
3. **Clean up old data**: Implement retention policies for checkpoints and memories
4. **Use stores for cross-thread data**: Leverage stores when data needs to be shared across conversations
5. **Test async flows**: If using async, ensure proper error handling and connection management
