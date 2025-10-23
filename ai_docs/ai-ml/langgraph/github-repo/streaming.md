# LangGraph Streaming

Source: `/langchain-ai/langgraph` (GitHub Repository)

## Overview

LangGraph provides powerful streaming capabilities that allow you to monitor graph execution in real-time, enabling responsive UIs and debugging.

## Stream Modes

### 1. Values Mode

Stream the complete state after each step:

```python
async for chunk in client.runs.stream(
    thread_id,
    assistant_id,
    input={"topic": "ice cream"},
    stream_mode="values"
):
    print(chunk.data)
```

```javascript
const streamResponse = client.runs.stream(
  threadID,
  assistantID,
  {
    input: { topic: "ice cream" },
    streamMode: "values"
  }
);
for await (const chunk of streamResponse) {
  console.log(chunk.data);
}
```

```bash
curl --request POST \
--url <DEPLOYMENT_URL>/threads/<THREAD_ID>/runs/stream \
--header 'Content-Type: application/json' \
--data '{
  "assistant_id": "agent",
  "input": {"topic": "ice cream"},
  "stream_mode": "values"
}'
```

### 2. Updates Mode

Stream only the updates from each node:

```python
async for chunk in client.runs.stream(
    thread_id,
    assistant_id,
    input={"topic": "ice cream"},
    stream_mode="updates"
):
    print(chunk.data)
```

### 3. Messages Mode

Stream individual messages as they're generated:

```python
async for chunk in client.runs.stream(
    thread_id,
    assistant_id,
    input={"topic": "ice cream"},
    stream_mode="messages"
):
    print(chunk.data)
```

## Basic Streaming Example

### Python

```python
from dataclasses import dataclass
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START

@dataclass
class MyState:
    topic: str
    joke: str = ""

llm = init_chat_model(model="openai:gpt-4o-mini")

def call_model(state: MyState):
    """Call the LLM to generate a joke about a topic"""
    llm_response = llm.invoke([
        {"role": "user", "content": f"Generate a joke about {state.topic}"}
    ])
    return {"joke": llm_response.content}

graph = (
    StateGraph(MyState)
    .add_node(call_model)
    .add_edge(START, "call_model")
    .compile()
)

# Stream execution
for chunk in graph.stream({"topic": "programming"}, stream_mode="values"):
    print(chunk)
```

### JavaScript/TypeScript

```typescript
import { StateGraph, START } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";
import { z } from "zod";

const State = z.object({
  topic: z.string(),
  joke: z.string().default(""),
});

const llm = new ChatOpenAI({ model: "gpt-4o-mini" });

const callModel = async (state: z.infer<typeof State>) => {
  const response = await llm.invoke([
    { role: "user", content: `Generate a joke about ${state.topic}` }
  ]);
  return { joke: response.content };
};

const graph = new StateGraph(State)
  .addNode("callModel", callModel)
  .addEdge(START, "callModel")
  .compile();

// Stream execution
for await (const chunk of await graph.stream(
  { topic: "programming" },
  { streamMode: "values" }
)) {
  console.log(chunk);
}
```

## Streaming with In-Memory State

```javascript
const builder = new StateGraph(MessagesZodState)
  .addNode("call_model", async (state) => {
    const response = await model.invoke(state.messages);
    return { messages: [response] };
  })
  .addEdge(START, "call_model");

const graph = builder.compile({ checkpointer });

const config = {
  configurable: {
    thread_id: "1"
  }
};

for await (const chunk of await graph.stream(
  { messages: [{ role: "user", content: "hi! I'm bob" }] },
  { ...config, streamMode: "values" }
)) {
  console.log(chunk.messages.at(-1)?.content);
}

for await (const chunk of await graph.stream(
  { messages: [{ role: "user", content: "what's my name?" }] },
  { ...config, streamMode: "values" }
)) {
  console.log(chunk.messages.at(-1)?.content);
}
```

## Token Streaming

For streaming individual tokens from LLM responses, you can use the LLM's native streaming:

```python
async def call_model_streaming(state: MessagesState):
    response_chunks = []
    async for chunk in llm.astream(state["messages"]):
        response_chunks.append(chunk)
        # Yield intermediate results if needed

    return {"messages": [response_chunks[-1]]}
```

```typescript
const callModelStreaming = async (state: MessagesZodState) => {
  const responseChunks = [];
  for await (const chunk of await llm.stream(state.messages)) {
    responseChunks.push(chunk);
    // Process chunk in real-time
  }
  return { messages: [responseChunks[responseChunks.length - 1]] };
};
```

## Combining Stream Modes

You can use multiple stream modes simultaneously:

```python
async for chunk in graph.astream(
    input_data,
    stream_mode=["values", "updates"],
    config=config
):
    if chunk["type"] == "values":
        print("Full state:", chunk["data"])
    elif chunk["type"] == "updates":
        print("Node update:", chunk["data"])
```

## Stream State Updates

Monitor state changes as they happen:

```python
config = {"configurable": {"thread_id": "1"}}

async for state in graph.astream(
    {"messages": [{"role": "user", "content": "Hello!"}]},
    config,
    stream_mode="values"
):
    print("Current state:", state)
```

## Best Practices

1. **Choose appropriate stream mode**:
   - Use `values` for complete state snapshots
   - Use `updates` for incremental changes
   - Use `messages` for token-level streaming

2. **Handle backpressure**: Ensure your consumer can keep up with the stream

3. **Error handling**: Wrap streaming operations in try-catch blocks

4. **UI updates**: Use streaming for real-time UI updates in chatbots

5. **Debugging**: Stream mode "updates" is excellent for debugging node execution

## Advanced: Custom Streaming

Implement custom streaming logic for specific use cases:

```python
from langgraph.graph import StateGraph

class CustomStreamingGraph(StateGraph):
    async def custom_stream(self, input_data, config):
        async for event in self.astream_events(input_data, config):
            # Custom processing
            if event["event"] == "on_chain_start":
                yield {"type": "start", "data": event}
            elif event["event"] == "on_chain_end":
                yield {"type": "end", "data": event}
```

## Streaming Examples

### Streaming with Progress Indicators

```python
import asyncio

async def stream_with_progress(graph, input_data, config):
    step_count = 0
    async for chunk in graph.astream(input_data, config, stream_mode="updates"):
        step_count += 1
        print(f"Step {step_count}: {chunk}")
        # Update progress bar or UI
```

### Streaming with Error Recovery

```python
async def stream_with_retry(graph, input_data, config, max_retries=3):
    for attempt in range(max_retries):
        try:
            async for chunk in graph.astream(input_data, config):
                yield chunk
            break
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Retry attempt {attempt + 1} due to: {e}")
            await asyncio.sleep(1)
```

## Performance Considerations

- Streaming adds minimal overhead compared to blocking invocation
- For large graphs, use `stream_mode="updates"` to reduce data transfer
- Consider buffering for UI updates to avoid flickering
- Use async streaming (`astream`) for better concurrency

## Next Steps

- Explore different stream modes for your use case
- Implement real-time UI updates with streaming
- Combine streaming with checkpointing for robust applications
- Learn about custom event handling for advanced scenarios
