# Serving LangGraph Agents via FastAPI - Research Results

## Solution Description

FastAPI (version 0.115.0+) provides a robust alternative to the LangGraph dev server for deploying LangGraph agents in production. This integration leverages:

1. **FastAPI's async capabilities** - Native support for async/await enables efficient streaming responses
2. **Server-Sent Events (SSE)** - Using `StreamingResponse` with `media_type="text/event-stream"` for real-time updates
3. **Pydantic validation** - Type-safe request/response models with automatic validation
4. **CORS middleware** - Easy configuration for web UI integration
5. **LangGraph checkpointers** - Persistent conversation memory using PostgreSQL or SQLite

### Key Integration Patterns

**Non-Streaming Pattern:**
- Use `graph.invoke(state, config)` for synchronous execution
- Return complete response as JSON
- Best for simple request/response workflows

**Streaming Pattern:**
- Use `graph.astream(state, config, stream_mode="...")` for state updates
- Use `graph.astream_events(state, config, version="v2")` for granular events
- Return `StreamingResponse` with SSE format
- Best for real-time chat interfaces and long-running operations

**Memory Persistence:**
- Development: `MemorySaver()` checkpointer (in-memory, volatile)
- Production: `AsyncPostgresSaver()` or `AsyncSQLiteSaver()` with FastAPI lifespan
- Thread-based isolation using `{"configurable": {"thread_id": thread_id}}`

---

## Working Code Examples

### Example 1: Basic FastAPI Server with LangGraph (Non-Streaming)

```python
from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.graph import StateGraph
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

class EmailRequest(BaseModel):
    tone: str
    ai_model: str
    language: str
    context: str

def generate_email_graph(ai_model: str, tone: str, language: str, context: str):
    """Build and compile a LangGraph workflow."""
    def email_generation_fn(state):
        if ai_model == "gemini":
            email = generate_email_gemini(language, tone, context)
        else:
            email = "Invalid AI model selected!"
        return {"email": email}

    graph = StateGraph(dict)
    graph.add_node("generate_email", email_generation_fn)
    graph.set_entry_point("generate_email")

    return graph.compile()

@app.get("/")
def read_root():
    return {"message": "LangGraph FastAPI Server"}

@app.post("/generate_email")
async def generate_email(request: EmailRequest):
    """Generate an AI-crafted email using LangGraph workflow."""
    graph = generate_email_graph(
        request.ai_model, request.tone, request.language, request.context
    )
    response = graph.invoke({})
    return response
```

**Key Points:**
- Simple `invoke()` pattern for synchronous execution
- Pydantic models for request validation
- Graph compiled per-request (rebuild if needed)

---

### Example 2: Streaming with Server-Sent Events (SSE)

```python
from fastapi import FastAPI, Body
from fastapi.responses import StreamingResponse
from typing import Annotated
from langchain_core.messages import HumanMessage, ToolMessage

app = FastAPI()

def event_stream(query: str):
    """Generate SSE events from LangGraph stream."""
    initial_state = {"messages": [HumanMessage(content=query)]}

    for output in graph.stream(initial_state):
        for node_name, node_results in output.items():
            chunk_messages = node_results.get("messages", [])

            for message in chunk_messages:
                if not message.content:
                    continue

                # Determine event type
                event_str = (
                    "event: tool_event"
                    if isinstance(message, ToolMessage)
                    else "event: ai_event"
                )
                data_str = f"data: {message.content}"

                # SSE format: event + data + double newline
                yield f"{event_str}\n{data_str}\n\n"

@app.post("/stream")
async def stream(query: Annotated[str, Body(embed=True)]):
    return StreamingResponse(
        event_stream(query),
        media_type="text/event-stream"
    )
```

**Key Points:**
- SSE format: `event: <name>\ndata: <payload>\n\n`
- `graph.stream()` yields state updates per node
- Filter messages to avoid empty content
- Distinguish event types (tool vs AI responses)

---

### Example 3: Advanced Streaming with `astream_events()`

```python
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

class AgentRequest(BaseModel):
    """Request schema for the agent endpoint."""
    session_id: str
    message: str

@app.post("/agent_stream")
async def stream_agent_response(request: AgentRequest):
    """Streams responses from LangGraph agent using Server-Sent Events."""

    async def event_generator():
        try:
            # Get session history
            session_history = get_session_history(request.session_id)
            current_messages = session_history.messages + [
                HumanMessage(content=request.message)
            ]

            # Stream events with version v2
            async for event in agent_app.astream_events(
                {"messages": current_messages},
                config={"configurable": {"session_id": request.session_id}},
                version="v2"
            ):
                event_name = event["event"]
                event_data = event["data"]

                payload = None

                # Filter for relevant events
                if event_name == "on_chat_model_stream":
                    chunk_content = event_data["chunk"].content
                    if chunk_content:
                        payload = {
                            "type": "llm_stream",
                            "content": chunk_content
                        }

                elif event_name == "on_tool_end":
                    payload = {
                        "type": "tool_end",
                        "output": str(event_data.get("output"))
                    }

                # Emit payload as SSE
                if payload:
                    yield f"event: {payload['type']}\n"
                    yield f"data: {json.dumps(payload)}\n\n"

        except Exception as e:
            # Error event
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

**Key Points:**
- `astream_events()` provides granular event stream
- Use `version="v2"` for latest event format
- Filter events by name: `on_chat_model_stream`, `on_tool_end`, etc.
- Session history integration for conversation memory
- Error handling within the generator

---

### Example 4: CORS Configuration

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configure CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://example.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security note: When allow_credentials=True,
# allow_origins cannot be ["*"] - must be explicit
```

**Key Points:**
- Must be added before route definitions
- Explicit origins required when `allow_credentials=True`
- Use `["*"]` for development only (not production)
- Headers must include `Content-Type`, `Authorization`, etc.

---

### Example 5: PostgreSQL Checkpointer with FastAPI Lifespan

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

DB_URI = "postgresql://postgres:postgres@localhost:5432/postgres"

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[dict[str, AsyncPostgresSaver], None]:
    """Manage PostgreSQL connection pool and checkpointer lifecycle."""
    # Startup: Create connection pool
    async with AsyncConnectionPool(conninfo=DB_URI) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()  # Initialize database schema

        # Yield checkpointer to app state
        yield {"checkpointer": checkpointer}

    # Shutdown: Pool cleanup handled by context manager

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(request: Request, message: str, thread_id: str):
    """Chat endpoint with persistent memory."""
    # Access checkpointer from app state
    checkpointer = request.state.checkpointer

    # Compile graph with checkpointer
    graph = build_graph().compile(checkpointer=checkpointer)

    # Execute with thread-based memory
    config = {"configurable": {"thread_id": thread_id}}

    async for event in graph.astream({"messages": [message]}, config):
        # Process streaming response
        for node_name, node_data in event.items():
            yield node_data
```

**Key Points:**
- Use `AsyncConnectionPool` for connection pooling
- `checkpointer.setup()` creates required database tables
- Access checkpointer via `request.state.checkpointer`
- Thread ID isolates conversations
- Pool cleanup automatic with context manager

---

### Example 6: AsyncSQLite Checkpointer (Development)

```python
from fastapi import FastAPI
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage SQLite checkpointer lifecycle."""
    async with AsyncSqliteSaver.from_conn_string("checkpoints.db") as checkpointer:
        await checkpointer.setup()
        yield {"checkpointer": checkpointer}

app = FastAPI(lifespan=lifespan)

# Note: AsyncSqliteSaver is NOT recommended for production
# Use PostgreSQL for production workloads
```

**Key Points:**
- `from_conn_string()` simplifies setup
- Good for development/testing
- Limited write performance (SQLite WAL mode)
- Switch to PostgreSQL for production

---

### Example 7: Error Handling in Streaming

```python
from typing import AsyncGenerator
from openai import RateLimitError

async def stream_with_errors(
    generator: AsyncGenerator[str, None]
) -> AsyncGenerator[str, None]:
    """Wrapper to handle errors during streaming."""
    try:
        async for chunk in generator:
            yield chunk

    except RateLimitError as e:
        # Handle rate limit errors
        error_msg = e.body.get("message", "OpenAI API rate limit exceeded")
        yield f"event: error_event\ndata: {error_msg}\n\n"

    except Exception as e:
        # Generic error handler
        error_msg = "An error occurred and our developers were notified"
        yield f"event: error_event\ndata: {error_msg}\n\n"

@app.post("/stream")
async def stream(query: str):
    return StreamingResponse(
        stream_with_errors(event_stream(query)),
        media_type="text/event-stream"
    )
```

**Key Points:**
- Wrap generators for error handling
- Send error events instead of raising exceptions
- Specific handlers for API rate limits
- Generic fallback for unexpected errors

---

### Example 8: LangGraph SDK Format (Agent Chat UI Compatible)

```python
import json
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

app = FastAPI()

class Message(BaseModel):
    """Message in LangGraph SDK format."""
    role: str | None = Field(None, description="user, assistant, system")
    content: str | list = Field(..., description="String or array of blocks")
    type: str | None = Field(None, description="human, ai")
    id: str | None = None

    class Config:
        extra = "allow"

class StreamInput(BaseModel):
    messages: list[Message]

class StreamRequest(BaseModel):
    assistant_id: str
    input: StreamInput
    config: dict = Field(default_factory=dict)
    stream_mode: str | list[str] = "values"

def convert_to_langgraph_messages(messages: list[Message]) -> list[BaseMessage]:
    """Convert SDK format to LangGraph messages."""
    langgraph_messages = []

    for msg in messages:
        # Extract content - handle array format
        content = msg.content
        if isinstance(content, list):
            text_parts = [
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            content = " ".join(text_parts) if text_parts else ""

        # Determine message type
        msg_type = msg.role or msg.type

        if msg_type in ["user", "human"]:
            langgraph_messages.append(HumanMessage(content=content))
        elif msg_type in ["assistant", "ai"]:
            langgraph_messages.append(AIMessage(content=content))

    return langgraph_messages

async def sse_generator(
    graph,
    thread_id: str,
    input_messages: list[BaseMessage],
    run_id: str
):
    """Generate SSE events in LangGraph SDK format."""
    try:
        # 1. Metadata event
        metadata = {"run_id": run_id, "thread_id": thread_id}
        yield f"event: metadata\n"
        yield f"data: {json.dumps(metadata)}\n\n"

        # 2. Execute graph
        state = {"messages": input_messages}
        config = {"configurable": {"thread_id": thread_id}}
        result = graph.invoke(state, config=config)

        # 3. Values event
        response_messages = [
            {"type": msg.type, "content": msg.content, "id": str(uuid.uuid4())}
            for msg in result["messages"]
        ]
        values_data = {"messages": response_messages}
        yield f"event: values\n"
        yield f"data: {json.dumps(values_data)}\n\n"

        # 4. End event
        yield f"event: end\ndata: \n\n"

    except Exception as e:
        # Error event
        error_data = {"error": str(e), "type": "error"}
        yield f"event: error\n"
        yield f"data: {json.dumps(error_data)}\n\n"

@app.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, request: StreamRequest):
    """LangGraph SDK compatible streaming endpoint."""
    # Generate run ID
    run_id = f"run-{uuid.uuid4()}"

    # Convert messages
    langgraph_messages = convert_to_langgraph_messages(request.input.messages)

    # Get graph (from registry or build)
    graph = get_graph(request.assistant_id)

    # Stream response
    return StreamingResponse(
        sse_generator(graph, thread_id, langgraph_messages, run_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

@app.post("/threads")
async def create_thread():
    """Create new thread."""
    thread_id = f"thread-{uuid.uuid4()}"
    return {
        "thread_id": thread_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {}
    }
```

**Key Points:**
- Compatible with LangGraph SDK and Agent Chat UI
- Handles both role-based and type-based message formats
- SSE event sequence: metadata → values → end
- UUID generation for threads and runs
- Proper SSE headers to prevent buffering

---

### Example 9: Async LangChain Callback Handler Pattern

```python
import asyncio
import os
from typing import AsyncIterable, Awaitable
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from pydantic import BaseModel

app = FastAPI()

async def send_message(message: str) -> AsyncIterable[str]:
    """Stream LLM response using callback handler."""
    callback = AsyncIteratorCallbackHandler()

    model = ChatOpenAI(
        streaming=True,
        verbose=True,
        callbacks=[callback],
    )

    async def wrap_done(fn: Awaitable, event: asyncio.Event):
        """Wrap awaitable with event to signal completion."""
        try:
            await fn
        except Exception as e:
            print(f"Caught exception: {e}")
        finally:
            event.set()

    # Start generation task
    task = asyncio.create_task(
        wrap_done(
            model.agenerate(messages=[[HumanMessage(content=message)]]),
            callback.done
        ),
    )

    # Stream tokens as they arrive
    async for token in callback.aiter():
        yield f"data: {token}\n\n"

    # Wait for completion
    await task

class StreamRequest(BaseModel):
    message: str

@app.post("/stream")
def stream(body: StreamRequest):
    return StreamingResponse(
        send_message(body.message),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(host="0.0.0.0", port=8000, app=app)
```

**Key Points:**
- `AsyncIteratorCallbackHandler` for token streaming
- Event signaling for async task coordination
- Automatic cleanup on completion or error
- Works with LangChain chat models

---

## Request/Response Validation Patterns

### Pydantic Models for LangGraph State

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class JobAnalysisRequest(BaseModel):
    """Request for job analysis workflow."""
    job_url: str = Field(..., description="URL of job posting")
    session_id: str = Field(..., description="Session/thread ID")

    class Config:
        json_schema_extra = {
            "example": {
                "job_url": "https://example.com/job/123",
                "session_id": "session-abc123"
            }
        }

class JobAnalysisResponse(BaseModel):
    """Response from job analysis."""
    job_title: str
    company: str
    required_skills: List[str]
    nice_to_have: List[str]
    ats_score: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "job_title": "Senior Python Engineer",
                "company": "TechCorp",
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                "nice_to_have": ["Docker", "Kubernetes"],
                "ats_score": 85.5
            }
        }
```

**Key Points:**
- Use Pydantic v2 features (`Field`, `Config.json_schema_extra`)
- Provide examples for API documentation
- Strong typing for LangGraph state validation
- FastAPI auto-generates OpenAPI specs

---

## Comparison: LangGraph Dev Server vs FastAPI

| Feature | LangGraph Dev Server | FastAPI |
|---------|---------------------|---------|
| **Setup Complexity** | Minimal (`langgraph dev`) | Moderate (custom server) |
| **Windows Support** | Issues reported | Full support |
| **Customization** | Limited | Full control |
| **Middleware** | Basic | CORS, auth, logging, etc. |
| **Error Handling** | Basic | Custom error handlers |
| **Scaling** | Single instance | Multi-worker (gunicorn/uvicorn) |
| **Production Ready** | Development only | Yes |
| **Monitoring** | LangGraph Studio | Custom (Prometheus, etc.) |
| **Authentication** | Not built-in | Easy to add |
| **Request Validation** | Basic | Pydantic validation |

---

## Best Practices

### 1. Graph Lifecycle Management
```python
# DON'T: Rebuild graph on every request
@app.post("/chat")
async def chat(message: str):
    graph = build_graph().compile()  # ❌ Expensive
    return graph.invoke({"messages": [message]})

# DO: Compile once, reuse (stateless graphs)
graph = build_graph().compile(checkpointer=checkpointer)

@app.post("/chat")
async def chat(message: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    return graph.invoke({"messages": [message]}, config=config)
```

### 2. Checkpointer Selection
```python
# Development
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()  # In-memory, volatile

# Staging
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
async with AsyncSqliteSaver.from_conn_string("db.sqlite") as checkpointer:
    # Good for testing, limited concurrency

# Production
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool

async with AsyncConnectionPool(conninfo=DB_URI) as pool:
    checkpointer = AsyncPostgresSaver(pool)  # ✅ Production ready
```

### 3. Streaming Performance
```python
# Use stream modes strategically
await graph.astream(state, config, stream_mode="values")    # Full state
await graph.astream(state, config, stream_mode="updates")   # Only updates
await graph.astream(state, config, stream_mode="messages")  # Only messages

# For granular events
async for event in graph.astream_events(state, config, version="v2"):
    if event["event"] == "on_chat_model_stream":
        # Only process LLM tokens
        yield event["data"]["chunk"].content
```

### 4. Error Boundaries
```python
from fastapi import HTTPException

@app.post("/chat")
async def chat(message: str):
    try:
        result = graph.invoke({"messages": [message]})
        return result
    except ValueError as e:
        # Client error (4xx)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Server error (5xx)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 5. Thread Safety
```python
# Checkpointers are thread-safe
# No need for locks or global state

# ✅ Safe: Each request gets isolated state via thread_id
@app.post("/chat")
async def chat(message: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    return await graph.ainvoke({"messages": [message]}, config=config)

# ❌ Unsafe: Sharing mutable state across requests
global_state = {"counter": 0}

@app.post("/chat")
async def chat(message: str):
    global_state["counter"] += 1  # Race condition!
```

---

## Sources

### FastAPI Documentation
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/) - Official CORS configuration guide
- [FastAPI StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse) - Streaming response patterns
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) - Application lifecycle management

### LangGraph + FastAPI Examples
- [GitHub: assistant-ui-langgraph-fastapi](https://github.com/Yonom/assistant-ui-langgraph-fastapi) - Complete example with streaming
- [GitHub: fastapi-langgraph-agent-production-ready-template](https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template) - Production-ready template with auth, monitoring, PostgreSQL
- [DEV Community: How to use LangGraph within a FastAPI Backend](https://dev.to/anuragkanojiya/how-to-use-langgraph-within-a-fastapi-backend-amm) - Step-by-step tutorial
- [Medium: Building Real-Time AI Apps with LangGraph, FastAPI & Streamlit](https://medium.com/@dharamai2024/building-real-time-ai-apps-with-langgraph-fastapi-streamlit-streaming-llm-responses-like-04d252d4d763) - Streaming patterns
- [Softgrade.org: Server-Sent Events with FastAPI and React](https://www.softgrade.org/sse-with-fastapi-react-langgraph/) - SSE implementation guide
- [ORFIUM Engineering: Agentic Chatbot with FastAPI and PostgreSQL](https://www.orfium.com/engineering/how-to-build-an-agentic-chatbot-with-fastapi-and-postgresql/) - PostgreSQL checkpointer integration
- [GitHub Gist: LangChain FastAPI Streaming](https://gist.github.com/ninely/88485b2e265d852d3feb8bd115065b1a) - Minimal streaming example

### LangGraph Documentation
- [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) - Checkpointer concepts
- [LangGraph Stream Outputs](https://langchain-ai.github.io/langgraph/how-tos/streaming/) - Streaming modes guide
- [GitHub Discussion #1357: Checkpointer in Web Framework](https://github.com/langchain-ai/langgraph/discussions/1357) - Best practices for FastAPI integration
- [GitHub Discussion #894: PostgreSQL Persistence](https://github.com/langchain-ai/langgraph/discussions/894) - PostgreSQL setup guide

### Community Resources
- [Medium: Simple LangGraph Implementation with AsyncSqliteSaver](https://medium.com/@devwithll/simple-langgraph-implementation-with-memory-asyncsqlitesaver-checkpointer-fastapi-54f4e4879a2e) - SQLite checkpointer tutorial
- [Stack Overflow: RAG with LangChain and FastAPI Streaming](https://stackoverflow.com/questions/78232975/rag-with-langchain-and-fastapi-stream-generated-answer-and-return-source-docume) - RAG streaming patterns
- [MLVector: Day 25 - FastAPI for LangGraph Agents](https://mlvector.com/2025/06/30/30daysoflangchain-day-25-fastapi-for-langgraph-agents-streaming-responses/) - Complete tutorial with code

---

## Additional Patterns

### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    """Health check for load balancers."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0"
    }
```

### Metrics Endpoint (Prometheus)
```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type="text/plain")
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/chat")
@limiter.limit("5/minute")
async def chat(request: Request, message: str):
    """Rate-limited chat endpoint."""
    return {"response": "..."}
```

### Authentication Middleware
```python
from fastapi import Header, HTTPException

async def verify_token(authorization: str = Header(None)):
    """Verify JWT token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    # Verify token logic here
    return token

@app.post("/chat")
async def chat(message: str, token: str = Depends(verify_token)):
    """Protected endpoint."""
    return {"response": "..."}
```

---

## Conclusion

FastAPI provides a robust, production-ready alternative to the LangGraph dev server with:

- **Better control** over request/response handling
- **Full middleware support** for CORS, auth, rate limiting
- **Multiple streaming patterns** for different use cases
- **Persistent memory** via PostgreSQL or SQLite checkpointers
- **Production features** like health checks, metrics, error handling
- **Cross-platform support** including Windows

The existing `fastapi_server.py` in the repository already implements many of these patterns, providing a solid foundation for production deployment.
