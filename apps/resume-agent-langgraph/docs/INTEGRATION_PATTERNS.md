# LangGraph Web Framework Integration Patterns

**Research Report: Production-Ready Integration Patterns for LangGraph with Web Frameworks**

This document compiles production-ready integration patterns for LangGraph with FastAPI, Flask, Django, React, and Next.js, focusing on streaming responses, error handling, and real-time chat interfaces.

---

## FastAPI Integration

### Complete Streaming Implementation

FastAPI is the most popular choice for LangGraph integration due to its async support and built-in SSE streaming capabilities.

#### Basic Setup

```bash
pip install fastapi uvicorn "langchain-openai" "langchain-anthropic" langgraph python-dotenv
```

#### Production-Ready FastAPI Server with SSE Streaming

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import AsyncGenerator, Any
import json
import uuid
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

app = FastAPI(
    title="LangGraph Agent API",
    description="Production-ready LangGraph streaming API",
    version="1.0.0"
)

# CORS for web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class Message(BaseModel):
    role: str = Field(..., description="user, assistant, or system")
    content: str = Field(..., description="Message content")

class StreamRequest(BaseModel):
    messages: list[Message]
    thread_id: str | None = None
    stream_mode: str = "values"

# SSE Event Generator
async def sse_generator(
    graph,
    messages: list[BaseMessage],
    thread_id: str,
    run_id: str
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events for streaming LangGraph execution.

    Event Format:
    - event: metadata -> Initial run metadata
    - event: values -> State updates
    - event: messages -> LLM token streaming (optional)
    - event: error -> Error information
    - event: end -> Completion signal
    """
    try:
        # Send metadata event
        metadata = {
            "run_id": run_id,
            "thread_id": thread_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        yield f"event: metadata\n"
        yield f"data: {json.dumps(metadata)}\n\n"

        # Execute graph with streaming
        state = {"messages": messages}
        config = {"configurable": {"thread_id": thread_id}}

        # Stream using astream() for async execution
        async for chunk in graph.astream(state, config=config):
            # Send state update event
            yield f"event: values\n"
            yield f"data: {json.dumps(chunk, default=str)}\n\n"

        # Send completion event
        yield f"event: end\n"
        yield f"data: \n\n"

    except Exception as e:
        # Send error event (don't close stream)
        error_data = {
            "error": str(e),
            "type": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat()
        }
        yield f"event: error\n"
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/runs/stream")
async def stream_run(request: StreamRequest):
    """
    Main streaming endpoint compatible with LangGraph SDK format.

    Accepts messages, executes graph, and streams results via SSE.
    """
    try:
        # Generate IDs
        thread_id = request.thread_id or f"thread-{uuid.uuid4()}"
        run_id = f"run-{uuid.uuid4()}"

        # Convert to LangGraph messages
        langgraph_messages = []
        for msg in request.messages:
            if msg.role == "user":
                langgraph_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langgraph_messages.append(AIMessage(content=msg.content))

        # Return SSE stream
        return StreamingResponse(
            sse_generator(graph, langgraph_messages, thread_id, run_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### Advanced: astream_events() for Granular Streaming

For more detailed event tracking (tool calls, LLM tokens, agent reasoning):

```python
async def detailed_sse_generator(
    graph,
    messages: list[BaseMessage],
    thread_id: str
) -> AsyncGenerator[str, None]:
    """
    Stream detailed events using astream_events() API.

    Provides granular events for:
    - LLM token streaming (on_chat_model_stream)
    - Tool invocations (on_tool_start, on_tool_end)
    - Agent reasoning steps
    """
    try:
        state = {"messages": messages}
        config = {"configurable": {"thread_id": thread_id}}

        # Use astream_events for detailed event stream
        async for event in graph.astream_events(state, config=config, version="v2"):
            event_type = event["event"]

            # LLM token streaming
            if event_type == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield f"event: llm_stream\n"
                    yield f"data: {json.dumps({'content': content})}\n\n"

            # Tool execution
            elif event_type == "on_tool_start":
                tool_data = {
                    "tool": event["name"],
                    "inputs": event["data"].get("input")
                }
                yield f"event: tool_start\n"
                yield f"data: {json.dumps(tool_data)}\n\n"

            elif event_type == "on_tool_end":
                tool_data = {
                    "tool": event["name"],
                    "output": event["data"].get("output")
                }
                yield f"event: tool_end\n"
                yield f"data: {json.dumps(tool_data)}\n\n"

        # Completion
        yield f"event: end\n"
        yield f"data: \n\n"

    except Exception as e:
        yield f"event: error\n"
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
```

#### Error Handling and Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ErrorAccumulatingNode:
    """Node that accumulates errors instead of raising exceptions."""

    @staticmethod
    def safe_execute(state: dict) -> dict:
        """Execute with error accumulation pattern."""
        errors = state.get("errors", [])

        try:
            result = risky_operation(state["input"])
            return {"output": result}
        except Exception as e:
            # Add error but allow workflow to continue
            errors.append({
                "node": "safe_execute",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            return {"errors": errors}

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def retry_llm_call(messages: list):
    """Retry LLM calls with exponential backoff."""
    # Your LLM call here
    pass

# Conditional routing based on errors
def should_retry(state: dict) -> str:
    """Route to retry node or continue based on error type."""
    errors = state.get("errors", [])

    if not errors:
        return "continue"

    # Check if errors are retryable
    last_error = errors[-1]
    if "rate limit" in last_error.get("error", "").lower():
        return "retry"

    return "fallback"
```

#### Background Task Processing

For long-running agent operations:

```python
from fastapi import BackgroundTasks
import asyncio

# Store for task status
task_store = {}

class TaskStatus(BaseModel):
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    result: Any = None
    error: str | None = None

@app.post("/runs/background")
async def create_background_run(
    request: StreamRequest,
    background_tasks: BackgroundTasks
):
    """Start agent execution in background."""
    task_id = f"task-{uuid.uuid4()}"

    # Initialize task status
    task_store[task_id] = TaskStatus(
        task_id=task_id,
        status="pending"
    )

    # Add to background tasks
    background_tasks.add_task(
        execute_graph_background,
        task_id,
        request.messages
    )

    return {"task_id": task_id}

async def execute_graph_background(task_id: str, messages: list):
    """Execute graph in background."""
    try:
        task_store[task_id].status = "running"

        # Execute graph
        result = await graph.ainvoke({"messages": messages})

        task_store[task_id].status = "completed"
        task_store[task_id].result = result

    except Exception as e:
        task_store[task_id].status = "failed"
        task_store[task_id].error = str(e)

@app.get("/runs/{task_id}")
async def get_task_status(task_id: str):
    """Poll task status."""
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_store[task_id]
```

---

## Flask Integration Patterns

Flask integration follows similar patterns but uses synchronous streaming:

```python
from flask import Flask, Response, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

def flask_sse_generator(graph, messages, thread_id):
    """Flask streaming generator (synchronous)."""
    try:
        # Send metadata
        metadata = {"thread_id": thread_id, "timestamp": datetime.utcnow().isoformat()}
        yield f"event: metadata\n"
        yield f"data: {json.dumps(metadata)}\n\n"

        # Execute graph (sync)
        state = {"messages": messages}
        config = {"configurable": {"thread_id": thread_id}}

        # Use .stream() for synchronous execution
        for chunk in graph.stream(state, config=config):
            yield f"event: values\n"
            yield f"data: {json.dumps(chunk, default=str)}\n\n"

        yield f"event: end\n"
        yield f"data: \n\n"

    except Exception as e:
        yield f"event: error\n"
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.route("/runs/stream", methods=["POST"])
def stream_run():
    """Flask streaming endpoint."""
    data = request.get_json()
    messages = data.get("messages", [])
    thread_id = data.get("thread_id", f"thread-{uuid.uuid4()}")

    # Convert messages to LangGraph format
    langgraph_messages = [
        HumanMessage(content=msg["content"]) if msg["role"] == "user"
        else AIMessage(content=msg["content"])
        for msg in messages
    ]

    return Response(
        flask_sse_generator(graph, langgraph_messages, thread_id),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
```

---

## Django Integration Patterns

### Django with LangGraph Checkpoint Persistence

Django provides excellent database integration through the official `langgraph-checkpoint-django` package:

```bash
pip install langgraph-checkpoint-django
```

#### Django Settings Configuration

```python
# settings.py
INSTALLED_APPS = [
    'langgraph.checkpoint.django.checkpoint',
    # ... other apps
]

# Database configuration (PostgreSQL recommended for production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'langgraph_db',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

#### Run Migrations

```bash
python manage.py migrate
```

#### Django View with Checkpoint Persistence

```python
# views.py
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from langgraph.checkpoint.django import DjangoSaver, AsyncDjangoSaver
import json

# Initialize checkpoint saver
checkpointer = DjangoSaver()  # or AsyncDjangoSaver() for async

# Build graph with Django persistence
graph = StateGraph(ConversationState)
# ... add nodes and edges ...
app = graph.compile(checkpointer=checkpointer)

def django_sse_generator(messages, thread_id):
    """Django SSE generator with checkpoint persistence."""
    try:
        state = {"messages": messages}
        config = {"configurable": {"thread_id": thread_id}}

        # Stream from graph (checkpoints saved to Django DB)
        for chunk in app.stream(state, config=config):
            yield f"event: values\n"
            yield f"data: {json.dumps(chunk, default=str)}\n\n"

        yield f"event: end\n"
        yield f"data: \n\n"

    except Exception as e:
        yield f"event: error\n"
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@csrf_exempt
def stream_chat(request):
    """Django streaming chat endpoint."""
    if request.method == "POST":
        data = json.loads(request.body)
        messages = data.get("messages", [])
        thread_id = data.get("thread_id", f"thread-{uuid.uuid4()}")

        # Convert messages
        langgraph_messages = [
            HumanMessage(content=msg["content"]) if msg["role"] == "user"
            else AIMessage(content=msg["content"])
            for msg in messages
        ]

        return StreamingHttpResponse(
            django_sse_generator(langgraph_messages, thread_id),
            content_type="text/event-stream"
        )

    return JsonResponse({"error": "Method not allowed"}, status=405)
```

#### Async Django View (Django 4.1+)

```python
from django.http import StreamingHttpResponse
from asgiref.sync import sync_to_async

async def async_sse_generator(messages, thread_id):
    """Async Django SSE generator."""
    checkpointer = AsyncDjangoSaver()

    # Build async graph
    graph = StateGraph(ConversationState)
    # ... add nodes ...
    app = graph.compile(checkpointer=checkpointer)

    state = {"messages": messages}
    config = {"configurable": {"thread_id": thread_id}}

    async for chunk in app.astream(state, config=config):
        yield f"event: values\n"
        yield f"data: {json.dumps(chunk, default=str)}\n\n"

    yield f"event: end\n"
    yield f"data: \n\n"

async def async_stream_chat(request):
    """Async Django streaming endpoint."""
    data = json.loads(request.body)
    messages = data.get("messages", [])
    thread_id = data.get("thread_id", f"thread-{uuid.uuid4()}")

    langgraph_messages = [
        HumanMessage(content=msg["content"]) if msg["role"] == "user"
        else AIMessage(content=msg["content"])
        for msg in messages
    ]

    return StreamingHttpResponse(
        async_sse_generator(langgraph_messages, thread_id),
        content_type="text/event-stream"
    )
```

---

## WebSocket Streaming

For bidirectional real-time communication (alternative to SSE):

### FastAPI WebSocket Implementation

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

# Track active connections
active_connections: Set[WebSocket] = set()

@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """WebSocket endpoint for real-time bidirectional streaming."""
    await websocket.accept()
    active_connections.add(websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            messages = data.get("messages", [])

            # Convert to LangGraph format
            langgraph_messages = [
                HumanMessage(content=msg["content"]) if msg["role"] == "user"
                else AIMessage(content=msg["content"])
                for msg in messages
            ]

            # Stream response
            state = {"messages": langgraph_messages}
            config = {"configurable": {"thread_id": thread_id}}

            async for chunk in graph.astream(state, config=config):
                # Send chunk to client
                await websocket.send_json({
                    "type": "chunk",
                    "data": chunk
                })

            # Send completion
            await websocket.send_json({"type": "complete"})

    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "error": str(e)
        })
        active_connections.remove(websocket)
```

---

## React Integration with useStream Hook

### Official LangGraph SDK Integration

The LangGraph SDK provides a `useStream()` React hook for seamless integration:

```bash
npm install @langchain/langgraph-sdk @langchain/core
```

### Complete React Component

```typescript
"use client";

import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState } from "react";

interface ChatMessage {
  type: "human" | "ai";
  content: string;
}

export default function ChatComponent() {
  const [input, setInput] = useState("");

  // Initialize useStream hook
  const stream = useStream<{ messages: ChatMessage[] }>({
    apiUrl: "http://localhost:2024",  // Your FastAPI server
    assistantId: "resume_agent",
    messagesKey: "messages",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim()) return;

    // Submit message to LangGraph
    stream.submit({
      messages: [{ type: "human", content: input }],
    });

    setInput("");
  };

  return (
    <div className="chat-container">
      {/* Message List */}
      <div className="messages">
        {stream.messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.type === "human" ? "user" : "assistant"}`}
          >
            <div className="message-content">
              {message.content as string}
            </div>
          </div>
        ))}

        {/* Loading Indicator */}
        {stream.isLoading && (
          <div className="message assistant">
            <div className="typing-indicator">Thinking...</div>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={stream.isLoading}
        />

        {stream.isLoading ? (
          <button type="button" onClick={() => stream.stop()}>
            Stop
          </button>
        ) : (
          <button type="submit">Send</button>
        )}
      </form>

      {/* Error Display */}
      {stream.error && (
        <div className="error">
          Error: {stream.error.message}
        </div>
      )}
    </div>
  );
}
```

### Advanced: Optimistic Thread Creation

```typescript
import { useState } from "react";
import { useStream } from "@langchain/langgraph-sdk/react";

export default function OptimisticChat() {
  const [threadId, setThreadId] = useState<string | null>(null);
  const [optimisticThreadId] = useState(() => crypto.randomUUID());

  const stream = useStream({
    apiUrl: "http://localhost:2024",
    assistantId: "resume_agent",
    threadId,
    onThreadId: setThreadId,  // Update threadId when confirmed
    messagesKey: "messages",
  });

  const handleSubmit = (text: string) => {
    // Update URL optimistically
    window.history.pushState({}, "", `/chat/${optimisticThreadId}`);

    // Submit with optimistic thread ID
    stream.submit(
      { messages: [{ type: "human", content: text }] },
      { threadId: optimisticThreadId }
    );
  };

  return (
    <div>
      <p>Thread: {threadId ?? optimisticThreadId}</p>
      {/* Rest of component */}
    </div>
  );
}
```

### Manual SSE Integration (Without SDK)

For custom streaming logic:

```typescript
import { useEffect, useState } from "react";
import { fetchEventSource } from "@microsoft/fetch-event-source";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export function useManualStream(apiUrl: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const sendMessage = async (content: string, threadId?: string) => {
    setIsLoading(true);
    setError(null);

    // Add user message
    const userMessage: Message = { role: "user", content };
    setMessages(prev => [...prev, userMessage]);

    try {
      await fetchEventSource(`${apiUrl}/runs/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          assistant_id: "resume_agent",
          input: {
            messages: [...messages, userMessage].map(m => ({
              role: m.role,
              content: m.content
            }))
          },
          config: {
            configurable: { thread_id: threadId || crypto.randomUUID() }
          }
        }),

        onmessage(event) {
          if (event.event === "values") {
            const data = JSON.parse(event.data);

            // Extract messages from response
            if (data.messages) {
              const apiMessages = data.messages;
              const lastMessage = apiMessages[apiMessages.length - 1];

              if (lastMessage.type === "ai") {
                setMessages(prev => [
                  ...prev,
                  { role: "assistant", content: lastMessage.content }
                ]);
              }
            }
          } else if (event.event === "error") {
            const errorData = JSON.parse(event.data);
            setError(new Error(errorData.error));
          } else if (event.event === "end") {
            setIsLoading(false);
          }
        },

        onerror(err) {
          setError(err);
          setIsLoading(false);
          throw err;  // Stop reconnection
        }
      });
    } catch (err) {
      setError(err as Error);
      setIsLoading(false);
    }
  };

  return { messages, isLoading, error, sendMessage };
}
```

---

## Next.js Integration Patterns

### Next.js API Route with LangGraph

Since LangGraph is Python-based, Next.js requires a backend API layer:

```typescript
// app/api/chat/route.ts (Next.js 13+ App Router)
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const { messages, threadId } = await request.json();

  // Proxy to FastAPI backend
  const response = await fetch("http://localhost:2024/runs/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      assistant_id: "resume_agent",
      input: { messages },
      config: {
        configurable: { thread_id: threadId || crypto.randomUUID() }
      }
    })
  });

  // Stream response back to client
  return new NextResponse(response.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "Connection": "keep-alive"
    }
  });
}
```

### Next.js Client Component

```typescript
// app/chat/page.tsx
"use client";

import { useStream } from "@langchain/langgraph-sdk/react";

export default function ChatPage() {
  const stream = useStream({
    apiUrl: "/api",  // Use Next.js API route
    assistantId: "resume_agent",
    messagesKey: "messages",
  });

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Resume Agent Chat</h1>

      <div className="messages space-y-4">
        {stream.messages.map((msg, i) => (
          <div key={i} className={`message ${msg.type}`}>
            {msg.content}
          </div>
        ))}
      </div>

      <form onSubmit={(e) => {
        e.preventDefault();
        const input = new FormData(e.currentTarget).get("message") as string;
        stream.submit({ messages: [{ type: "human", content: input }] });
        e.currentTarget.reset();
      }}>
        <input
          name="message"
          type="text"
          className="border p-2 w-full"
          placeholder="Type your message..."
        />
        <button type="submit" className="mt-2 bg-blue-500 text-white px-4 py-2">
          {stream.isLoading ? "Sending..." : "Send"}
        </button>
      </form>
    </div>
  );
}
```

---

## REST API Design Best Practices

### Core Endpoints

Following LangGraph Server API conventions:

```python
# Standard LangGraph-compatible endpoints

@app.get("/info")
async def get_info():
    """Server info endpoint."""
    return {
        "assistant_id": "resume_agent",
        "version": "1.0.0",
        "capabilities": ["streaming", "checkpointing", "tools"]
    }

@app.post("/runs/stream")
async def stream_run(request: StreamRequest):
    """Main streaming endpoint (SSE)."""
    # Implementation shown above
    pass

@app.post("/runs/invoke")
async def invoke_run(request: InvokeRequest):
    """Non-streaming invocation."""
    result = await graph.ainvoke(
        {"messages": request.messages},
        config={"configurable": {"thread_id": request.thread_id}}
    )
    return {"result": result}

@app.post("/threads/search")
async def search_threads(request: SearchRequest):
    """List available threads."""
    # Query checkpoint database
    threads = await checkpointer.list_threads(
        limit=request.limit,
        offset=request.offset
    )
    return {"threads": threads}

@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """Get current state of a thread."""
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)
    return {"state": state.values}

@app.get("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str, limit: int = 10):
    """Get thread history (all checkpoints)."""
    config = {"configurable": {"thread_id": thread_id}}
    history = []

    async for checkpoint in graph.aget_state_history(config, limit=limit):
        history.append({
            "checkpoint_id": checkpoint.config["configurable"]["checkpoint_id"],
            "values": checkpoint.values,
            "created_at": checkpoint.created_at
        })

    return {"history": history}

@app.post("/threads/{thread_id}/update")
async def update_thread_state(thread_id: str, request: UpdateRequest):
    """Update thread state (for human-in-the-loop)."""
    config = {"configurable": {"thread_id": thread_id}}

    # Update state
    await graph.aupdate_state(
        config,
        request.values,
        as_node=request.as_node
    )

    return {"status": "updated"}

@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete thread and all checkpoints."""
    # Implementation depends on checkpointer
    await checkpointer.delete_thread(thread_id)
    return {"status": "deleted"}
```

### Error Response Format

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global error handler with consistent format."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )

# Custom exceptions
class GraphExecutionError(Exception):
    """Raised when graph execution fails."""
    pass

class CheckpointNotFoundError(Exception):
    """Raised when checkpoint doesn't exist."""
    pass
```

---

## Production Code Examples

### Complete Agent Service Toolkit Pattern

Based on the `agent-service-toolkit` repository structure:

```
project/
├── src/
│   ├── agents/           # LangGraph agent definitions
│   │   ├── __init__.py
│   │   └── resume_agent.py
│   ├── api/              # FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── routes.py     # Endpoint definitions
│   │   └── models.py     # Pydantic models
│   ├── core/             # Configuration
│   │   ├── config.py
│   │   └── llm.py
│   ├── client/           # Client SDK
│   │   └── agent_client.py
│   └── service/          # FastAPI app
│       └── main.py
├── tests/
│   ├── test_agents.py
│   ├── test_api.py
│   └── test_client.py
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

#### Agent Definition

```python
# src/agents/resume_agent.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: list[BaseMessage]
    metadata: dict

def build_resume_agent(checkpointer):
    """Build resume agent graph."""
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("analyze", analyze_job_node)
    graph.add_node("tailor", tailor_resume_node)
    graph.add_node("generate", generate_cover_letter_node)

    # Add edges
    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "tailor")
    graph.add_edge("tailor", "generate")
    graph.add_edge("generate", END)

    return graph.compile(checkpointer=checkpointer)
```

#### FastAPI Service

```python
# src/service/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from langgraph.checkpoint.postgres import PostgresSaver
import os

# Global graph instance
graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for app startup/shutdown."""
    global graph

    # Startup: Initialize graph with checkpointer
    checkpointer = PostgresSaver.from_conn_string(
        os.getenv("DATABASE_URL")
    )
    graph = build_resume_agent(checkpointer)

    yield

    # Shutdown: Cleanup
    if checkpointer:
        await checkpointer.close()

app = FastAPI(lifespan=lifespan)

# Include routers
from api.routes import router
app.include_router(router)
```

#### Client SDK

```python
# src/client/agent_client.py
import httpx
from typing import AsyncGenerator

class AgentClient:
    """Client for interacting with agent service."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()

    async def stream(
        self,
        messages: list[dict],
        thread_id: str | None = None
    ) -> AsyncGenerator[dict, None]:
        """Stream agent responses."""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/runs/stream",
            json={
                "messages": messages,
                "thread_id": thread_id
            },
            headers={"Accept": "text/event-stream"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield json.loads(line[6:])

    async def invoke(
        self,
        messages: list[dict],
        thread_id: str | None = None
    ) -> dict:
        """Invoke agent (non-streaming)."""
        response = await self.client.post(
            f"{self.base_url}/runs/invoke",
            json={"messages": messages, "thread_id": thread_id}
        )
        return response.json()
```

---

## Performance and Monitoring

### Request/Response Timing

```python
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add timing headers to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response

# Metrics
request_count = Counter(
    "langgraph_requests_total",
    "Total requests",
    ["method", "endpoint"]
)

request_duration = Histogram(
    "langgraph_request_duration_seconds",
    "Request duration",
    ["method", "endpoint"]
)

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

---

## Testing Patterns

### Integration Tests

```python
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_stream_endpoint():
    """Test streaming endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/runs/stream",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "thread_id": "test-thread"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

        # Verify SSE format
        events = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        assert len(events) > 0
        assert events[-1]["event"] == "end"
```

### Unit Tests

```python
def test_message_conversion():
    """Test message format conversion."""
    input_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]

    langgraph_messages = convert_to_langgraph_messages(input_messages)

    assert len(langgraph_messages) == 2
    assert isinstance(langgraph_messages[0], HumanMessage)
    assert isinstance(langgraph_messages[1], AIMessage)
```

---

## Sources

### Official Documentation
- LangGraph Docs: https://langchain-ai.github.io/langgraph/
- LangGraph Streaming: https://langchain-ai.github.io/langgraph/concepts/streaming/
- LangGraph Server API: https://docs.langchain.com/langgraph-platform/langgraph-server
- LangGraph React Integration: https://docs.langchain.com/langgraph-platform/use-stream-react

### GitHub Repositories
- **agent-service-toolkit**: https://github.com/JoshuaC215/agent-service-toolkit
  - Complete FastAPI + LangGraph service with Streamlit UI
  - Token and message-based streaming
  - PostgreSQL checkpointing

- **LangGraph-FastAPI-Streamlit**: https://github.com/yigit353/LangGraph-FastAPI-Streamlit
  - SSE streaming implementation
  - FastAPI bridge pattern

- **assistant-ui-langgraph-fastapi**: https://github.com/Yonom/assistant-ui-langgraph-fastapi
  - Next.js + LangGraph integration
  - Assistant-UI component library

- **fastapi-langgraph-agent-production-ready-template**: https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template
  - Production architecture
  - Authentication, rate limiting
  - Observability stack

- **LangGraph_Streaming**: https://github.com/sheikhhanif/LangGraph_Streaming
  - WebSocket streaming
  - Real-time token delivery

### Articles and Tutorials
- "Building Real-Time AI Apps with LangGraph, FastAPI & Streamlit": https://medium.com/@dharamai2024/building-real-time-ai-apps-with-langgraph-fastapi-streamlit-streaming-llm-responses-like-04d252d4d763
- "Server-Sent Events with FastAPI and React": https://www.softgrade.org/sse-with-fastapi-react-langgraph/
- "LangGraph & Next.js Integration": https://www.akveo.com/blog/langgraph-and-nextjs-how-to-integrate-ai-agents-in-a-modern-web-stack
- "Building a Conversational AI App with Django and LangGraph": https://www.analyticsvidhya.com/blog/2025/07/build-a-chatbot-from-scratch/
- "Mastering Error Handling in LangGraph": https://procodebase.com/article/mastering-error-handling-in-langgraph

### PyPI Packages
- `langgraph`: Core LangGraph library
- `langgraph-checkpoint-django`: Django persistence
- `@langchain/langgraph-sdk`: TypeScript/JavaScript SDK
- `@microsoft/fetch-event-source`: SSE client library

---

## Summary

**Key Takeaways:**

1. **FastAPI is the primary choice** for LangGraph integration due to async support and SSE streaming capabilities
2. **Server-Sent Events (SSE)** are simpler than WebSockets for unidirectional streaming from agent to client
3. **LangGraph SDK's useStream() hook** provides seamless React integration with automatic state management
4. **Django checkpointer** enables production-grade conversation persistence
5. **Error accumulation pattern** (vs raising exceptions) allows partial success workflows
6. **Production patterns** include: retry logic, background tasks, metrics, comprehensive error handling
7. **Next.js requires a backend API layer** since LangGraph is Python-based

This research provides production-ready patterns for all major web frameworks and frontend integrations with LangGraph.
