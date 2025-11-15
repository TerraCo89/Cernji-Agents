# Research Avenue 4: Streaming & Real-time Updates

**Source**: https://github.com/bracesproul/gen-ui-python/tree/main/backend/gen_ui_backend

## Executive Summary

The gen-ui-python project demonstrates a full-stack streaming architecture using:
- **Backend**: FastAPI + LangServe + LangGraph for agent orchestration
- **Frontend**: Next.js 14 + React Server Components (RSC) + Vercel AI SDK
- **Streaming Pattern**: LangServe automatic streaming with custom event handlers
- **UI Streaming**: React Server Components with `createStreamableUI` and `createStreamableValue`

The architecture enables real-time streaming of both AI responses and dynamically generated UI components to the client.

---

## 1. Server Setup and Streaming Endpoints

### 1.1 FastAPI Server Configuration

**File**: `backend/gen_ui_backend/server.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from gen_ui_backend.chain import create_graph

app = FastAPI(
    title="Gen UI Backend",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
)

# CORS Configuration for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create LangGraph and wrap with types
graph = create_graph()
runnable = graph.with_types(input_type=ChatInputType, output_type=dict)

# Add streaming-enabled routes
add_routes(app, runnable, path="/chat", playground_type="chat")

# Run server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 1.2 LangServe Streaming

**Key Points**:
- `add_routes()` automatically creates streaming endpoints at `/chat/stream`
- No explicit streaming configuration needed - LangServe handles SSE automatically
- The `playground_type="chat"` enables interactive testing interface
- Streaming is enabled by default for all compatible runnables

**Auto-generated Endpoints**:
```
POST /chat/invoke       - Single invocation
POST /chat/stream       - Server-Sent Events streaming
POST /chat/batch        - Batch processing
GET  /chat/playground   - Interactive testing UI
```

### 1.3 Dependencies

**Core Streaming Stack** (`pyproject.toml`):
```toml
langgraph = "^0.0.62"           # Graph-based agent orchestration
langserve = {version = "^0.2.1", extras = ["all"]}  # Streaming deployment
fastapi = ">=0.110.2,<1"        # ASGI web framework
uvicorn = ">=0.23.2,<0.24.0"    # ASGI server
langchain-core = "^0.2.4"       # Streaming primitives
```

---

## 2. LangGraph Streaming Configuration

### 2.1 Graph Construction

**File**: `backend/gen_ui_backend/chain.py`

```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

def create_graph() -> CompiledGraph:
    workflow = StateGraph(GenerativeUIState)

    # Configure model with streaming enabled
    model = ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0,
        streaming=True  # Enable token-by-token streaming
    )

    # Define nodes
    workflow.add_node("invoke_model", invoke_model)
    workflow.add_node("invoke_tools", invoke_tools)

    # Set entry point and edges
    workflow.set_entry_point("invoke_model")
    workflow.add_conditional_edges(
        "invoke_model",
        invoke_tools_or_return,
        {
            "continue": "invoke_tools",
            "end": END,
        },
    )
    workflow.add_edge("invoke_tools", END)

    # Compile to runnable graph
    return workflow.compile()
```

### 2.2 State Management

```python
from typing import TypedDict, List, Optional

class GenerativeUIState(TypedDict, total=False):
    """State tracked throughout graph execution"""
    input: str                          # User message
    result: Optional[str]               # Plain text response
    tool_calls: Optional[List[dict]]    # Parsed tool invocations
    tool_result: Optional[dict]         # Tool execution output
```

### 2.3 Node Implementation with Streaming

```python
def invoke_model(state: GenerativeUIState, config: RunnableConfig):
    """Process user input through streaming LLM"""
    model_with_tools = model.bind_tools([
        github_repo_tool,
        invoice_parser_tool,
        weather_tool
    ])

    # Model streams tokens as they're generated
    response = model_with_tools.invoke(state["input"], config)

    # Check if tools were called
    if response.tool_calls:
        return {"tool_calls": response.tool_calls}
    else:
        return {"result": response.content}

def invoke_tools(state: GenerativeUIState, config: RunnableConfig):
    """Execute tools and return results"""
    tool_call = state["tool_calls"][0]

    # Map tool names to implementations
    tools_map = {
        "github_repo": github_repo_tool,
        "invoice_parser": invoice_parser_tool,
        "weather": weather_tool,
    }

    tool = tools_map[tool_call["name"]]
    result = tool.invoke(tool_call["args"], config)

    return {"tool_result": result}
```

### 2.4 Charts Graph Example

**File**: `backend/gen_ui_backend/charts/chain.py`

```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

def create_chart_graph():
    """Multi-step graph for generating chart specifications"""
    workflow = StateGraph(AgentExecutorState)

    # Model with structured output for filter generation
    model_with_filter = ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0,
    ).with_structured_output(FilterSchema)

    # Define processing pipeline
    workflow.add_node("generate_filter", generate_filter)
    workflow.add_node("select_chart_type", select_chart_type)
    workflow.add_node("select_display_format", select_display_format)
    workflow.add_node("filter_data", filter_data)

    # Sequential execution
    workflow.set_entry_point("generate_filter")
    workflow.add_edge("generate_filter", "select_chart_type")
    workflow.add_edge("select_chart_type", "select_display_format")
    workflow.add_edge("select_display_format", "filter_data")
    workflow.add_edge("filter_data", END)

    return workflow.compile()
```

---

## 3. Stream Event Types and Formats

### 3.1 LangChain StreamEvent Structure

LangServe emits events in this format:

```typescript
interface StreamEvent {
    event: string;           // Event type identifier
    name: string;            // Node/component name
    run_id: string;          // Unique run identifier
    data: {
        input?: any;         // Node input
        output?: any;        // Node output
        chunk?: any;         // Streaming chunk (for tokens)
    };
    metadata?: {
        langgraph_node?: string;    // Current graph node
        langgraph_step?: number;    // Execution step
    };
}
```

### 3.2 Event Types

LangGraph emits these event types during streaming:

| Event Type | Description | When Emitted |
|------------|-------------|--------------|
| `on_chain_start` | Chain execution begins | Graph invocation starts |
| `on_chain_stream` | Intermediate state updates | After each node completes |
| `on_chain_end` | Chain execution completes | Graph reaches END node |
| `on_llm_start` | LLM invocation begins | Before model call |
| `on_llm_stream` | Token chunks from LLM | Each token generated |
| `on_llm_end` | LLM completes response | After all tokens |
| `on_tool_start` | Tool execution begins | Before tool invocation |
| `on_tool_end` | Tool execution completes | After tool returns |

### 3.3 Example Event Sequence

For a query: "Get weather for San Francisco"

```javascript
// 1. Chain starts
{
    event: "on_chain_start",
    name: "graph",
    data: { input: { input: "Get weather for San Francisco" } }
}

// 2. Model node executes
{
    event: "on_chain_stream",
    name: "invoke_model",
    metadata: { langgraph_node: "invoke_model", langgraph_step: 1 },
    data: {
        output: {
            tool_calls: [{ name: "weather", args: { city: "San Francisco" } }]
        }
    }
}

// 3. Tool node executes
{
    event: "on_chain_stream",
    name: "invoke_tools",
    metadata: { langgraph_node: "invoke_tools", langgraph_step: 2 },
    data: {
        output: {
            tool_result: {
                city: "San Francisco",
                temperature: 65
            }
        }
    }
}

// 4. Chain completes
{
    event: "on_chain_end",
    name: "graph",
    data: {
        output: {
            tool_result: { city: "San Francisco", temperature: 65 }
        }
    }
}
```

---

## 4. Code Examples for Streaming Different Content Types

### 4.1 Streaming Text Responses

**Frontend** (`frontend/app/agent.tsx`):

```typescript
'use server'

import { RemoteRunnable } from "@langchain/core/runnables/remote";
import { createStreamableValue } from "ai/rsc";
import { streamRunnableUI } from "@/utils/server";

export async function agent(
  input: string,
  chatHistory: [role: string, content: string][]
) {
  const fields = {
    ui: createStreamableUI(),
    lastEvent: Promise.withResolvers(),
  };

  const remoteRunnable = new RemoteRunnable({
    url: "http://localhost:8000/chat",
  });

  // Stream with event handlers
  streamRunnableUI(
    remoteRunnable,
    {
      input: convertToLangChainMessages(chatHistory, input),
    },
    fields,
    {
      // Handler for streaming text tokens
      onChatModelStream: (event: StreamEvent, fields) => {
        const runId = event.run_id;

        // Create stream for this specific run
        if (!streams[runId]) {
          const newStream = createStreamableValue("");
          streams[runId] = newStream;

          // Append streaming text component to UI
          fields.ui.append(<Message value={newStream.value} />);
        }

        // Append each token chunk
        const chunk = event.data?.chunk?.content;
        if (chunk) {
          streams[runId].append(chunk);
        }
      },
    }
  );

  return {
    ui: fields.ui.value,
    lastEvent: await fields.lastEvent.promise,
  };
}
```

### 4.2 Streaming UI Components

**Tool Execution with Loading States**:

```typescript
'use server'

export async function agent(input: string, chatHistory: [string, string][]) {
  const fields = {
    ui: createStreamableUI(),
    lastEvent: Promise.withResolvers(),
  };

  const streams: Record<string, ReturnType<typeof createStreamableValue>> = {};

  streamRunnableUI(
    remoteRunnable,
    { input: convertToLangChainMessages(chatHistory, input) },
    fields,
    {
      // Handler for tool invocation
      onCustomEvent: (event: StreamEvent, fields) => {
        // Detect tool calls from model
        if (
          event.name === "invoke_model" &&
          event.event === "on_chain_stream" &&
          event.data?.output?.tool_calls
        ) {
          const toolCalls = event.data.output.tool_calls;

          toolCalls.forEach((toolCall: any) => {
            const toolName = toolCall.name;

            // Show loading UI immediately
            if (toolName === "github_repo") {
              const stream = createStreamableUI(
                <div>Loading repository data...</div>
              );
              fields.ui.append(stream.value);

              // Store for later update
              streams[`tool_${toolCall.id}`] = stream;
            }
          });
        }

        // Update with final result
        if (
          event.name === "invoke_tools" &&
          event.event === "on_chain_stream" &&
          event.data?.output?.tool_result
        ) {
          const result = event.data.output.tool_result;

          // Find corresponding loading UI
          const toolStream = streams[`tool_${event.run_id}`];
          if (toolStream) {
            // Update to final component
            toolStream.done(
              <RepositoryCard
                owner={result.owner}
                repo={result.repo}
                description={result.description}
                stars={result.stars}
                language={result.language}
              />
            );
          }
        }
      },
    }
  );

  return {
    ui: fields.ui.value,
    lastEvent: await fields.lastEvent.promise,
  };
}
```

### 4.3 Streaming Chart Data

**Charts Graph** (`frontend/app/charts/page.tsx`):

```typescript
'use client'

export default function ChartsPage() {
  const [chartType, setChartType] = useState<ChartType>("bar");
  const [orders, setOrders] = useState<Order[]>([]);

  async function handleSmartFilter(input: string) {
    // Call server action with streaming
    const { ui, lastEvent } = await actions.filterGraph(
      input,
      orders,
      displayFormats
    );

    // lastEvent contains the final state after streaming
    const finalState = await lastEvent;

    // Update local state with streamed results
    if (finalState?.filter_data?.props) {
      const { chartType, displayFormat, filteredOrders } =
        finalState.filter_data.props;

      setChartType(chartType);
      setSelectedDisplayFormat(displayFormat);
      setFilteredOrders(filteredOrders);
    }
  }

  return (
    <div>
      <SmartFilter onSubmit={handleSmartFilter} />

      {/* Charts render with streamed data */}
      <Suspense fallback={<div>Loading chart...</div>}>
        {chartType === "bar" && <BarChart data={filteredOrders} />}
        {chartType === "pie" && <PieChart data={filteredOrders} />}
        {chartType === "line" && <LineChart data={filteredOrders} />}
      </Suspense>
    </div>
  );
}
```

### 4.4 Multiple Concurrent Streams

```typescript
export async function agent(input: string) {
  const fields = {
    ui: createStreamableUI(),
    lastEvent: Promise.withResolvers(),
  };

  // Track multiple concurrent streams
  const textStreams: Record<string, ReturnType<typeof createStreamableValue>> = {};
  const uiStreams: Record<string, ReturnType<typeof createStreamableUI>> = {};

  streamRunnableUI(
    remoteRunnable,
    { input },
    fields,
    {
      onChatModelStream: (event, fields) => {
        // Stream text for AI responses
        const runId = event.run_id;
        if (!textStreams[runId]) {
          textStreams[runId] = createStreamableValue("");
          fields.ui.append(<Message value={textStreams[runId].value} />);
        }
        textStreams[runId].append(event.data?.chunk?.content);
      },

      onCustomEvent: (event, fields) => {
        // Stream UI components for tool results
        if (event.name === "invoke_tools" && event.data?.output) {
          const toolId = event.run_id;

          if (!uiStreams[toolId]) {
            uiStreams[toolId] = createStreamableUI(<LoadingSpinner />);
            fields.ui.append(uiStreams[toolId].value);
          }

          // Update with final component
          uiStreams[toolId].done(<ToolResultCard data={event.data.output} />);
        }
      },
    }
  );

  return {
    ui: fields.ui.value,
    lastEvent: await fields.lastEvent.promise,
  };
}
```

---

## 5. Error Handling During Streaming

### 5.1 Current Implementation Gaps

**Analysis**: The gen-ui-python implementation **lacks explicit error handling** in several areas:

1. **No try-catch blocks** in event handlers
2. **No error events** captured from stream
3. **Silent failures** when tools are missing
4. **No timeout handling** for long-running operations

### 5.2 Recommended Error Handling Pattern

**Server-side** (Enhanced `chain.py`):

```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class GenerativeUIState(TypedDict, total=False):
    input: str
    result: Optional[str]
    tool_calls: Optional[List[dict]]
    tool_result: Optional[dict]
    error: Optional[dict]  # Add error tracking

def invoke_model(state: GenerativeUIState, config: RunnableConfig):
    """Invoke model with error handling"""
    try:
        model_with_tools = model.bind_tools([
            github_repo_tool,
            invoice_parser_tool,
            weather_tool
        ])

        response = model_with_tools.invoke(state["input"], config)

        if response.tool_calls:
            return {"tool_calls": response.tool_calls}
        else:
            return {"result": response.content}

    except Exception as e:
        logger.error(f"Model invocation failed: {e}")
        return {
            "error": {
                "node": "invoke_model",
                "message": str(e),
                "type": type(e).__name__
            }
        }

def invoke_tools(state: GenerativeUIState, config: RunnableConfig):
    """Execute tools with error handling"""
    try:
        tool_call = state["tool_calls"][0]

        tools_map = {
            "github_repo": github_repo_tool,
            "invoice_parser": invoice_parser_tool,
            "weather": weather_tool,
        }

        if tool_call["name"] not in tools_map:
            raise ValueError(f"Unknown tool: {tool_call['name']}")

        tool = tools_map[tool_call["name"]]
        result = tool.invoke(tool_call["args"], config)

        return {"tool_result": result}

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return {
            "error": {
                "node": "invoke_tools",
                "message": str(e),
                "type": type(e).__name__,
                "tool": tool_call.get("name", "unknown")
            }
        }
```

**Client-side** (Enhanced `agent.tsx`):

```typescript
'use server'

export async function agent(input: string, chatHistory: [string, string][]) {
  const fields = {
    ui: createStreamableUI(),
    lastEvent: Promise.withResolvers(),
    error: null as Error | null,
  };

  try {
    streamRunnableUI(
      remoteRunnable,
      { input: convertToLangChainMessages(chatHistory, input) },
      fields,
      {
        onChatModelStream: (event, fields) => {
          try {
            // Stream handling logic
            const runId = event.run_id;
            if (!streams[runId]) {
              streams[runId] = createStreamableValue("");
              fields.ui.append(<Message value={streams[runId].value} />);
            }
            streams[runId].append(event.data?.chunk?.content);
          } catch (err) {
            console.error("Stream handling error:", err);
            fields.ui.append(
              <ErrorMessage message="Failed to process stream chunk" />
            );
          }
        },

        onCustomEvent: (event, fields) => {
          // Check for error events from backend
          if (event.data?.output?.error) {
            const error = event.data.output.error;
            fields.ui.append(
              <ErrorCard
                title={`Error in ${error.node}`}
                message={error.message}
                type={error.type}
              />
            );
            return;
          }

          // Normal event processing
          try {
            // Tool execution handling
            if (event.name === "invoke_tools" && event.data?.output?.tool_result) {
              // Process tool result
            }
          } catch (err) {
            console.error("Event processing error:", err);
            fields.ui.append(
              <ErrorMessage message="Failed to process tool result" />
            );
          }
        },

        onError: (error) => {
          // Stream-level error handler
          console.error("Stream error:", error);
          fields.error = error;
          fields.ui.append(
            <ErrorCard
              title="Stream Error"
              message={error.message}
              type="StreamingError"
            />
          );
          fields.lastEvent.reject(error);
        },
      }
    );
  } catch (error) {
    // Top-level error handling
    console.error("Agent execution error:", error);
    fields.ui.append(
      <ErrorCard
        title="Agent Error"
        message={error instanceof Error ? error.message : "Unknown error"}
        type="AgentExecutionError"
      />
    );
    fields.lastEvent.reject(error);
  }

  return {
    ui: fields.ui.value,
    lastEvent: await fields.lastEvent.promise.catch(err => ({
      error: err.message
    })),
    error: fields.error,
  };
}
```

### 5.3 Timeout Handling

```typescript
import { withTimeout } from "@/utils/timeout";

export async function agent(input: string, chatHistory: [string, string][]) {
  const fields = {
    ui: createStreamableUI(),
    lastEvent: Promise.withResolvers(),
  };

  try {
    // Add timeout wrapper
    await withTimeout(
      streamRunnableUI(
        remoteRunnable,
        { input: convertToLangChainMessages(chatHistory, input) },
        fields,
        eventHandlers
      ),
      30000 // 30 second timeout
    );
  } catch (error) {
    if (error.name === "TimeoutError") {
      fields.ui.append(
        <ErrorCard
          title="Request Timeout"
          message="The operation took too long to complete. Please try again."
          type="TimeoutError"
        />
      );
    }
  }

  return {
    ui: fields.ui.value,
    lastEvent: await fields.lastEvent.promise,
  };
}
```

### 5.4 Retry Logic

```typescript
async function agentWithRetry(
  input: string,
  chatHistory: [string, string][],
  maxRetries = 3
) {
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await agent(input, chatHistory);
    } catch (error) {
      lastError = error as Error;
      console.warn(`Attempt ${attempt} failed:`, error);

      if (attempt < maxRetries) {
        // Exponential backoff
        await new Promise(resolve =>
          setTimeout(resolve, Math.pow(2, attempt) * 1000)
        );
      }
    }
  }

  // All retries failed
  throw new Error(
    `Agent failed after ${maxRetries} attempts: ${lastError?.message}`
  );
}
```

---

## 6. Frontend Integration Patterns

### 6.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Client Components                        │  │
│  │  (Chat UI, Forms, Display Components)                 │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │ useActions()                     │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │           Server Actions (agent.tsx)                  │  │
│  │  - Create streamable UI/values                        │  │
│  │  - Handle LangServe stream events                     │  │
│  │  - Return streaming components                        │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │ RemoteRunnable                   │
└──────────────────────────┼───────────────────────────────────┘
                           │ HTTP/SSE
┌──────────────────────────▼───────────────────────────────────┐
│                      Backend                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              LangServe Server                         │  │
│  │  - FastAPI endpoints                                  │  │
│  │  - SSE streaming (/chat/stream)                       │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                  │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │           LangGraph Compiled Graph                    │  │
│  │  - State management                                   │  │
│  │  - Node execution                                     │  │
│  │  - Event emission                                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Client Component Pattern

**File**: `frontend/components/prebuilt/chat.tsx`

```typescript
'use client'

import { useActions } from "@/utils/client";
import { EndpointsContext } from "@/app/agent";
import { useState } from "react";

export default function Chat() {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<[string, string][]>([]);
  const [elements, setElements] = useState<JSX.Element[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Access server actions via context
  const actions = useActions<typeof EndpointsContext>();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    // Prepare file data if present
    let fileData = null;
    if (selectedFile) {
      const arrayBuffer = await selectedFile.arrayBuffer();
      const base64 = Buffer.from(arrayBuffer).toString('base64');
      fileData = {
        data: base64,
        extension: selectedFile.name.split('.').pop()
      };
    }

    // Call server action with streaming
    const { ui, lastEvent } = await actions.agent(input, history, fileData);

    // Append streaming UI immediately
    setElements(prev => [...prev, ui]);

    // Clear input
    setInput("");
    setSelectedFile(null);

    // Wait for stream completion
    const finalEvent = await lastEvent;

    // Extract final result from stream
    const result =
      finalEvent?.invoke_model?.result ||
      finalEvent?.invoke_tools?.tool_result;

    // Update history for next request
    setHistory(prev => [
      ...prev,
      ["human", input],
      ["ai", result]
    ]);
  }

  return (
    <div>
      {/* Display all accumulated UI elements */}
      <div className="messages">
        {elements.map((element, i) => (
          <div key={i}>{element}</div>
        ))}
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type a message..."
        />
        <input
          type="file"
          onChange={e => setSelectedFile(e.target.files?.[0] || null)}
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
```

### 6.3 Message Streaming Component

**File**: `frontend/ai/message.tsx`

```typescript
'use client'

import { useStreamableValue } from "ai/rsc";
import { StreamableValue } from "ai/rsc";

interface MessageProps {
  value: StreamableValue<string>;
}

export default function Message(props: MessageProps) {
  // Hook automatically re-renders as new chunks arrive
  const [data] = useStreamableValue(props.value);

  // Don't render until data arrives
  if (!data) {
    return null;
  }

  return (
    <div className="message">
      <AIMessageText content={data} />
    </div>
  );
}
```

### 6.4 Server Action Context Provider

**File**: `frontend/utils/client.tsx`

```typescript
'use client'

import { createContext, useContext } from "react";

// Generic context for server actions
export const ActionsContext = createContext<any>(null);

// Type-safe hook to access actions
export function useActions<T>(): T {
  const actions = useContext(ActionsContext);
  if (!actions) {
    throw new Error("useActions must be used within ActionsProvider");
  }
  return actions;
}
```

**File**: `frontend/utils/server.tsx`

```typescript
'use server'

import { AIProvider } from "ai/rsc";

// Expose server actions to client components
export function exposeEndpoints<T extends Record<string, any>>(
  actions: T
) {
  return async function ActionsProvider({ children }: { children: React.ReactNode }) {
    return (
      <AIProvider actions={actions}>
        {children}
      </AIProvider>
    );
  };
}
```

### 6.5 streamRunnableUI Utility

**File**: `frontend/utils/server.tsx`

```typescript
'use server'

import { Runnable } from "@langchain/core/runnables";
import { createStreamableUI, createStreamableValue } from "ai/rsc";

interface EventHandlerFields {
  ui: ReturnType<typeof createStreamableUI>;
  onEvent?: (event: StreamEvent) => void;
}

type EventHandler = (
  event: StreamEvent,
  fields: EventHandlerFields
) => void | Promise<void>;

interface StreamHandlers {
  onChatModelStream?: EventHandler;
  onCustomEvent?: EventHandler;
  onError?: (error: Error) => void;
}

export async function streamRunnableUI(
  runnable: Runnable,
  input: any,
  fields: {
    ui: ReturnType<typeof createStreamableUI>;
    lastEvent: ReturnType<typeof Promise.withResolvers>;
  },
  handlers: StreamHandlers = {}
) {
  let lastEventValue: any = null;
  let chainEnded = false;

  try {
    // Stream events from runnable
    const stream = await runnable.streamEvents(input, {
      version: "v2"
    });

    for await (const event of stream) {
      // Stop processing after chain ends
      if (chainEnded) continue;

      // Detect chain completion
      if (event.event === "on_chain_end" && event.name === "graph") {
        chainEnded = true;
        lastEventValue = event.data?.output || event.data?.chunk?.output;
        continue;
      }

      // Handle streaming text from chat model
      if (
        event.event === "on_llm_stream" &&
        event.data?.chunk?.content
      ) {
        await handlers.onChatModelStream?.(event, fields);
      }

      // Handle custom events (tool calls, etc.)
      if (event.event === "on_chain_stream") {
        await handlers.onCustomEvent?.(event, fields);
      }
    }

    // Resolve with final state
    fields.lastEvent.resolve(lastEventValue);

  } catch (error) {
    console.error("Stream error:", error);
    handlers.onError?.(error as Error);
    fields.lastEvent.reject(error);
  } finally {
    // Mark UI as complete
    fields.ui.done();
  }
}
```

### 6.6 Complete Integration Example

**Page Component**:

```typescript
// app/page.tsx
import { Chat } from "@/components/prebuilt/chat";
import { EndpointsProvider } from "@/app/agent";

export default function Home() {
  return (
    <EndpointsProvider>
      <div className="flex h-screen flex-col items-center justify-between">
        <h1>Generative UI with LangChain Python</h1>
        <div className="min-w-[600px]">
          <Chat />
        </div>
      </div>
    </EndpointsProvider>
  );
}
```

**Server Actions**:

```typescript
// app/agent.tsx
'use server'

import { exposeEndpoints } from "@/utils/server";
import { agent } from "@/lib/agent";

// Define actions
async function agentAction(
  input: string,
  history: [string, string][],
  file?: { data: string; extension: string }
) {
  return agent(input, history, file);
}

// Export context and provider
export const EndpointsContext = {
  agent: agentAction,
};

export const EndpointsProvider = exposeEndpoints(EndpointsContext);
```

---

## 7. Key Patterns and Best Practices

### 7.1 Streaming Patterns Summary

| Pattern | Use Case | Implementation |
|---------|----------|----------------|
| **Text Streaming** | AI responses, chat messages | `createStreamableValue()` + `on_llm_stream` |
| **UI Streaming** | Dynamic components, loading states | `createStreamableUI()` + `on_chain_stream` |
| **Progressive Enhancement** | Loading → Final state transitions | `stream.update()` → `stream.done()` |
| **Concurrent Streams** | Multiple simultaneous outputs | Multiple `createStreamableValue()` instances |
| **Event-based Updates** | Tool calls, state transitions | Custom event handlers in `streamRunnableUI` |

### 7.2 Best Practices

1. **Always use streaming for LLMs**: Set `streaming=True` on model configuration
2. **Create separate streams per run**: Use `run_id` to track concurrent operations
3. **Provide immediate feedback**: Show loading UI before streaming completes
4. **Handle errors gracefully**: Implement try-catch and error UI components
5. **Clean up streams**: Call `.done()` to mark completion and prevent memory leaks
6. **Type safety**: Use TypeScript for all streaming interfaces
7. **Optimize bundle size**: Stream UI components to avoid large initial payloads

### 7.3 Performance Considerations

```typescript
// ✅ Good: Stream text progressively
const stream = createStreamableValue("");
fields.ui.append(<Message value={stream.value} />);
for (const chunk of chunks) {
  stream.append(chunk);
}
stream.done();

// ❌ Bad: Wait for complete response
const completeText = await getAllChunks();
fields.ui.append(<Message value={completeText} />);
```

```typescript
// ✅ Good: Update existing stream
const stream = createStreamableUI(<LoadingSpinner />);
fields.ui.append(stream.value);
// ... later
stream.done(<FinalComponent data={result} />);

// ❌ Bad: Create multiple UI elements
fields.ui.append(<LoadingSpinner />);
// ... later
fields.ui.append(<FinalComponent data={result} />);
```

---

## 8. Dependencies Summary

### Backend Dependencies

```toml
# Core Framework
fastapi = ">=0.110.2,<1"
uvicorn = ">=0.23.2,<0.24.0"

# LangChain Streaming
langgraph = "^0.0.62"
langgraph-cli = "^0.1.46"
langserve = {version = "^0.2.1", extras = ["all"]}
langchain = "^0.2.2"
langchain-core = "^0.2.4"
langchain-openai = "^0.1.8"
langchain-anthropic = "^0.1.16"
langchain-community = "^0.2.3"

# Data Processing
pydantic = ">=1.10.13,<2"
motor = "^3.4.0"  # Async MongoDB
pymongo = "^4.6.3"

# Utilities
python-dotenv = "^1.0.1"
typer = ">=0.9.0,<0.10.0"
rich = "^13.7.1"
```

### Frontend Dependencies

```json
{
  "dependencies": {
    // LangChain Client
    "@langchain/core": "^0.2.6",
    "@langchain/langgraph": "^0.0.22",
    "@langchain/langgraph-sdk": "^0.0.1-rc.14",

    // AI SDK for Streaming
    "ai": "^3.1.16",

    // Framework
    "next": "14.2.3",
    "react": "^18",
    "react-dom": "^18",

    // Utilities
    "uuid": "^9.0.1",
    "react-markdown": "^9.0.1"
  }
}
```

---

## 9. Comparison with Other Approaches

### 9.1 LangServe vs Direct FastAPI Streaming

| Aspect | LangServe | Direct FastAPI SSE |
|--------|-----------|-------------------|
| **Setup Complexity** | Simple (`add_routes()`) | Manual SSE implementation |
| **Event Formatting** | Automatic LangChain events | Custom event structure |
| **Type Safety** | Built-in with `with_types()` | Manual type definitions |
| **Playground** | Included | Must build separately |
| **Flexibility** | LangChain-specific | Full control |

### 9.2 RSC vs Traditional React Streaming

| Aspect | React Server Components | Traditional React |
|--------|------------------------|-------------------|
| **Bundle Size** | Smaller (server-rendered) | Larger (client-side) |
| **Streaming** | Native with Suspense | Requires custom implementation |
| **Data Fetching** | Server-side | Client-side |
| **Hydration** | Selective | Full page |
| **Complexity** | Higher learning curve | Familiar patterns |

---

## 10. Recommendations

### 10.1 For New Projects

1. **Use LangServe for LangGraph apps**: Automatic streaming with minimal setup
2. **Adopt React Server Components**: Better performance and streaming DX
3. **Implement error boundaries**: Graceful degradation during streaming failures
4. **Add request timeouts**: Prevent hanging connections
5. **Monitor stream performance**: Track latency and completion rates

### 10.2 Migration Path

For existing non-streaming applications:

1. **Phase 1**: Add `streaming=True` to LLM configurations
2. **Phase 2**: Implement basic event handlers for text streaming
3. **Phase 3**: Add UI component streaming for tool results
4. **Phase 4**: Implement progressive loading states
5. **Phase 5**: Add comprehensive error handling and retries

### 10.3 Testing Streaming

```typescript
// Test streaming behavior
describe("Agent Streaming", () => {
  it("should stream text progressively", async () => {
    const chunks: string[] = [];

    const { ui } = await agent("Hello", []);

    // Mock stream subscription
    ui.subscribe((chunk) => {
      chunks.push(chunk);
    });

    await waitForStreamCompletion();

    expect(chunks.length).toBeGreaterThan(1);
    expect(chunks.join("")).toContain("Hello");
  });

  it("should handle streaming errors", async () => {
    // Mock network failure
    server.use(
      http.post("http://localhost:8000/chat/stream", () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    const { ui, error } = await agent("Test", []);

    expect(error).toBeDefined();
    expect(ui).toContain("ErrorCard");
  });
});
```

---

## Appendix: Complete File Reference

### Backend Files

- `backend/gen_ui_backend/server.py` - FastAPI server with LangServe
- `backend/gen_ui_backend/chain.py` - Main LangGraph definition
- `backend/gen_ui_backend/types.py` - Type definitions
- `backend/gen_ui_backend/tools/github.py` - GitHub tool
- `backend/gen_ui_backend/tools/weather.py` - Weather tool
- `backend/gen_ui_backend/tools/invoice.py` - Invoice tool
- `backend/gen_ui_backend/charts/chain.py` - Charts graph
- `backend/gen_ui_backend/charts/schema.py` - Chart schemas
- `backend/pyproject.toml` - Python dependencies
- `backend/langgraph.json` - LangGraph configuration

### Frontend Files

- `frontend/app/page.tsx` - Main page
- `frontend/app/agent.tsx` - Server actions
- `frontend/app/shared.tsx` - Shared utilities
- `frontend/app/charts/page.tsx` - Charts page
- `frontend/components/prebuilt/chat.tsx` - Chat component
- `frontend/ai/message.tsx` - Message streaming component
- `frontend/utils/server.tsx` - Server streaming utilities
- `frontend/utils/client.tsx` - Client context utilities
- `frontend/package.json` - NPM dependencies

---

## Conclusion

The gen-ui-python project demonstrates a robust streaming architecture that combines:

1. **LangServe** for automatic LangGraph streaming over HTTP/SSE
2. **React Server Components** for efficient UI streaming
3. **Vercel AI SDK** for streamable UI and values
4. **Event-driven architecture** for progressive updates

Key takeaways:

- Streaming is **built-in** with LangServe - minimal configuration needed
- **Event handlers** provide fine-grained control over stream processing
- **Multiple stream types** (text, UI components) can run concurrently
- **Error handling** needs improvement in the reference implementation
- **Type safety** throughout with TypeScript and Pydantic

This architecture enables real-time, interactive AI applications with dynamic UI generation and minimal latency.
