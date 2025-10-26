# FastAPI + LangGraph Integration Patterns

Production-ready patterns for serving LangGraph agents via FastAPI with streaming support.

## Table of Contents

- [Basic FastAPI Setup](#basic-fastapi-setup)
- [Streaming Patterns](#streaming-patterns)
- [Production Features](#production-features)
- [Deployment](#deployment)

---

## Basic FastAPI Setup

### Pattern 1: Simple Invoke Endpoint

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint"""
    thread_id = request.thread_id or "default"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )

        return ChatResponse(
            response=result["messages"][-1].content,
            thread_id=thread_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Streaming Patterns

### Pattern 1: Server-Sent Events (SSE)

**Best for:** Real-time token streaming to web frontends

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessageChunk
import json

@app.post("/stream")
async def stream_chat(request: ChatRequest):
    """Stream responses using Server-Sent Events"""

    async def event_generator():
        config = {"configurable": {"thread_id": request.thread_id or "default"}}

        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            version="v2"
        ):
            # Filter for LLM token chunks
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"

            # Signal completion
            elif event["event"] == "on_chat_model_end":
                yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

### Pattern 2: Message-Based Streaming

**Best for:** Streaming complete messages (not tokens)

```python
@app.post("/stream/messages")
async def stream_messages(request: ChatRequest):
    """Stream complete messages as they're generated"""

    async def message_generator():
        config = {"configurable": {"thread_id": request.thread_id or "default"}}

        async for chunk in graph.astream(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            stream_mode="updates"
        ):
            for node_name, node_output in chunk.items():
                messages = node_output.get("messages", [])

                for message in messages:
                    event_data = {
                        "node": node_name,
                        "role": message.type,
                        "content": message.content
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"

        # End signal
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        message_generator(),
        media_type="text/event-stream"
    )
```

### Pattern 3: Tool Call Streaming

**Best for:** Showing tool execution in real-time

```python
@app.post("/stream/tools")
async def stream_with_tools(request: ChatRequest):
    """Stream with tool call visibility"""

    async def tool_event_generator():
        config = {"configurable": {"thread_id": request.thread_id or "default"}}

        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            version="v2"
        ):
            # Tool start
            if event["event"] == "on_tool_start":
                yield f"event: tool_start\n"
                yield f"data: {json.dumps({'tool': event['name']})}\n\n"

            # Tool end
            elif event["event"] == "on_tool_end":
                yield f"event: tool_end\n"
                yield f"data: {json.dumps({'result': str(event['data']['output'])})}\n\n"

            # LLM tokens
            elif event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"event: token\n"
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"

    return StreamingResponse(
        tool_event_generator(),
        media_type="text/event-stream"
    )
```

---

## Production Features

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
)
```

### Authentication Middleware

```python
from fastapi import Depends, HTTPException, Header
from typing import Annotated

async def verify_api_key(x_api_key: Annotated[str, Header()]):
    """Verify API key from headers"""
    if x_api_key != os.getenv("API_SECRET"):
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.post("/chat")
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """Protected endpoint"""
    # ... chat logic
```

### Error Handling

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global error handler"""
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": str(exc),
            "path": str(request.url)
        }
    )
```

### Health Check Endpoint

```python
from datetime import datetime

@app.get("/health")
async def health_check():
    """Health check for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

### Metrics Endpoint

```python
from collections import defaultdict
from datetime import datetime

# Simple in-memory metrics
metrics = {
    "requests": defaultdict(int),
    "errors": defaultdict(int),
    "start_time": datetime.utcnow()
}

@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Track request metrics"""
    path = request.url.path
    metrics["requests"][path] += 1

    try:
        response = await call_next(request)
        return response
    except Exception as e:
        metrics["errors"][path] += 1
        raise

@app.get("/metrics")
async def get_metrics():
    """Expose metrics"""
    return {
        "requests": dict(metrics["requests"]),
        "errors": dict(metrics["errors"]),
        "uptime_seconds": (datetime.utcnow() - metrics["start_time"]).total_seconds()
    }
```

### Rate Limiting

```python
from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta

# Simple in-memory rate limiter
rate_limit_store = defaultdict(list)

async def rate_limit(request: Request, limit: int = 10, window: int = 60):
    """Rate limit by IP address"""
    client_ip = request.client.host
    now = datetime.utcnow()

    # Clean old requests
    rate_limit_store[client_ip] = [
        timestamp for timestamp in rate_limit_store[client_ip]
        if now - timestamp < timedelta(seconds=window)
    ]

    # Check limit
    if len(rate_limit_store[client_ip]) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded: {limit} requests per {window} seconds"
        )

    # Record request
    rate_limit_store[client_ip].append(now)

@app.post("/chat")
async def chat(
    request: ChatRequest,
    _: None = Depends(lambda r: rate_limit(r, limit=10, window=60))
):
    """Rate-limited chat endpoint"""
    # ... chat logic
```

### Connection Pool Management

```python
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Global variables
connection_pool = None
checkpointer = None
compiled_graph = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage resources during app lifetime"""
    global connection_pool, checkpointer, compiled_graph

    # Startup
    print("🚀 Initializing connection pool...")
    connection_pool = AsyncConnectionPool(
        conninfo=os.getenv("DATABASE_URL"),
        min_size=5,
        max_size=20,
        kwargs={"autocommit": True, "prepare_threshold": 0}
    )

    print("💾 Setting up checkpointer...")
    checkpointer = AsyncPostgresSaver(connection_pool)
    await checkpointer.setup()

    print("📊 Compiling graph...")
    compiled_graph = build_graph().compile(checkpointer=checkpointer)

    print("✅ Application ready!")
    yield

    # Shutdown
    print("🔒 Shutting down...")
    await connection_pool.close()

app = FastAPI(lifespan=lifespan)
```

---

## Deployment

### Docker Configuration

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8080

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: agent_db
      POSTGRES_USER: agent_user
      POSTGRES_PASSWORD: agent_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://agent_user:agent_pass@postgres:5432/agent_db
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  postgres_data:
```

### Environment Variables

**.env:**
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/agent_db

# LLM Providers
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Application
API_SECRET=your-secret-key
LOG_LEVEL=INFO
WORKERS=4
```

### Systemd Service

**/etc/systemd/system/langraph-api.service:**
```ini
[Unit]
Description=LangGraph FastAPI Service
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/langraph-api
Environment="PATH=/opt/langraph-api/venv/bin"
EnvironmentFile=/opt/langraph-api/.env
ExecStart=/opt/langraph-api/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

**/etc/nginx/sites-available/langraph-api:**
```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;

        # SSE support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Disable buffering for SSE
        proxy_buffering off;
        proxy_cache off;

        # Timeouts
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

---

## Complete Production Example

```python
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.messages import HumanMessage
import os
import json
from datetime import datetime

# Global resources
connection_pool = None
checkpointer = None
compiled_graph = None

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    global connection_pool, checkpointer, compiled_graph

    connection_pool = AsyncConnectionPool(
        conninfo=os.getenv("DATABASE_URL"),
        min_size=5,
        max_size=20
    )
    checkpointer = AsyncPostgresSaver(connection_pool)
    await checkpointer.setup()
    compiled_graph = build_graph().compile(checkpointer=checkpointer)

    yield

    await connection_pool.close()

# App
app = FastAPI(lifespan=lifespan, title="LangGraph API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    message: str
    thread_id: str | None = None

# Endpoints
@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/stream")
async def stream(request: ChatRequest):
    async def event_generator():
        config = {"configurable": {"thread_id": request.thread_id or "default"}}

        async for event in compiled_graph.astream_events(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
            version="v2"
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

---

## Quick Reference

### Start Development Server
```bash
uvicorn main:app --reload --port 8080
```

### Test Streaming Endpoint
```bash
curl -X POST http://localhost:8080/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "thread_id": "test-123"}'
```

### Production Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f api

# Scale workers
docker-compose up -d --scale api=3
```

---

## See Also

- **LangGraph Dev Server**: Alternative using `langgraph dev` command
- **Agent Chat UI**: Frontend integration patterns
- **Checkpointing**: PostgreSQL vs SQLite persistence
