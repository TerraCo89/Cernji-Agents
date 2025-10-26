#!/usr/bin/env python3
"""
FastAPI Server for LangGraph - Agent Chat UI Compatible

This server wraps the LangGraph implementation and provides
compatibility with Agent Chat UI by implementing the LangGraph SDK API format.

This bypasses the problematic LangGraph server (which has issues on Windows)
by providing a direct FastAPI SSE streaming endpoint.

Architecture:
- FastAPI: Web server with SSE streaming
- LangGraph: The working LangGraph conversation graph
- LangGraph SDK API format: Compatible with Agent Chat UI

"""

import os
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from dotenv import load_dotenv

# Import the working graph
from graph_registry import get_graph, list_graphs

# Load environment variables
load_dotenv()

# ==============================================================================
# FastAPI App Setup
# ==============================================================================

app = FastAPI(
    title="Resume Agent LangGraph API",
    description="FastAPI server compatible with Agent Chat UI - Multi-Agent Support",
    version="0.2.0"
)

# Enable CORS for Agent Chat UI (runs on localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Graphs are loaded dynamically from registry - no global graph needed

# ==============================================================================
# Request/Response Models (LangGraph SDK API Format)
# ==============================================================================

class Message(BaseModel):
    """Message in LangGraph SDK format."""
    role: str | None = Field(None, description="Message role: user, assistant, system")
    content: str | list = Field(..., description="Message content - can be string or array of content blocks")
    type: str | None = Field(None, description="Message type field (human, ai)")
    id: str | None = Field(None, description="Message ID")

    class Config:
        extra = "allow"  # Allow additional fields


class StreamInput(BaseModel):
    """Input format for streaming endpoint."""
    messages: list[Message] = Field(..., description="List of messages")


class StreamConfig(BaseModel):
    """Configuration for the stream."""
    configurable: dict[str, Any] = Field(default_factory=dict)


class StreamRequest(BaseModel):
    """Request body for /runs/stream endpoint."""
    assistant_id: str = Field(..., description="Assistant/graph ID")
    input: StreamInput = Field(..., description="Input messages")
    config: StreamConfig | None = Field(None, description="Optional configuration")
    stream_mode: str | list[str] = Field(default="values", description="Streaming mode")


class ThreadInfo(BaseModel):
    """Thread information for threads endpoint."""
    thread_id: str
    created_at: str
    updated_at: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# ==============================================================================
# Message Format Conversion
# ==============================================================================

def convert_to_langgraph_messages(messages: list[Message]) -> list[BaseMessage]:
    """
    Convert request messages to LangGraph messages.

    Handles both formats:
    1. Role-based: {"role": "user", "content": "Hello"}
    2. Type-based: {"type": "human", "content": [{"type": "text", "text": "Hello"}]}

    Args:
        messages: List of messages in either format

    Returns:
        List of LangGraph BaseMessage objects
    """
    langgraph_messages = []

    for msg in messages:
        # Extract content - handle both string and array format
        content = msg.content
        if isinstance(content, list):
            # Extract text from content blocks
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            content = " ".join(text_parts) if text_parts else ""
        
        # Determine message type from role or type field
        msg_type = msg.role or msg.type
        
        if msg_type in ["user", "human"]:
            langgraph_messages.append(HumanMessage(content=content))
        elif msg_type in ["assistant", "ai"]:
            langgraph_messages.append(AIMessage(content=content))
        # Skip system messages (not supported in conversation state)

    return langgraph_messages

def convert_from_langgraph_messages(messages: list[BaseMessage]) -> list[dict]:
    """
    Convert LangGraph messages to response format.

    LangGraph returns: HumanMessage(content="Hello")
    Agent Chat UI expects: {"type": "human", "content": "Hello"}

    Args:
        messages: List of LangGraph BaseMessage objects

    Returns:
        List of messages in LangGraph SDK format (with type field)
    """
    result = []

    for msg in messages:
        msg_dict = {
            "type": msg.type,  # "human" or "ai"
            "content": msg.content,
            "id": getattr(msg, "id", str(uuid.uuid4())),
        }
        result.append(msg_dict)

    return result

# ==============================================================================
# SSE Streaming Helper
# ==============================================================================

async def sse_generator(
    graph,
    thread_id: str,
    input_messages: list[BaseMessage],
    run_id: str
) -> AsyncGenerator[str, None]:
    """
    Generate Server-Sent Events (SSE) for streaming response.

    LangGraph SDK expects this event format:
    1. event: metadata -> Initial metadata with run_id
    2. event: values -> State updates with messages
    3. event: end -> Completion signal

    Args:
        graph: Compiled LangGraph graph to execute
        thread_id: Thread ID for conversation persistence
        input_messages: User messages to process
        run_id: Unique run identifier

    Yields:
        SSE formatted strings
    """
    try:
        # Send initial metadata event
        metadata = {
            "run_id": run_id,
            "thread_id": thread_id,
        }
        yield f"event: metadata\n"
        yield f"data: {json.dumps(metadata)}\n\n"

        # Prepare state for graph execution
        state = {
            "messages": input_messages,
            "should_continue": True
        }

        # Execute graph with checkpointing
        config = {"configurable": {"thread_id": thread_id}}
        result = await asyncio.to_thread(
            graph.invoke,
            state,
            config=config
        )

        # Convert messages to SDK format
        response_messages = convert_from_langgraph_messages(result["messages"])

        # Send values event with updated state
        values_data = {
            "messages": response_messages
        }
        yield f"event: values\n"
        yield f"data: {json.dumps(values_data)}\n\n"

        # Send end event
        yield f"event: end\n"
        yield f"data: \n\n"

    except Exception as e:
        # Send error event
        error_data = {
            "error": str(e),
            "type": "error"
        }
        yield f"event: error\n"
        yield f"data: {json.dumps(error_data)}\n\n"

# ==============================================================================
# API Endpoints
# ==============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "LangGraph API - Multi-Agent",
        "version": "0.2.0",
        "available_agents": list_graphs()
    }


@app.get("/info")
async def info():
    """
    Graph info endpoint (required by Agent Chat UI).

    This endpoint is checked by the UI to verify the server is running.
    Returns list of available agents/graphs.
    """
    return {
        "status": "ready",
        "available_agents": list_graphs(),
        "default_agent": "resume_agent"
    }


@app.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str):
    """
    Get assistant details (LangGraph SDK format).
    
    Required by Agent Chat UI SDK.
    """
    try:
        # Verify the assistant exists
        available = list_graphs()
        if assistant_id not in available:
            raise HTTPException(status_code=404, detail=f"Assistant {assistant_id} not found")
        
        return {
            "assistant_id": assistant_id,
            "graph_id": assistant_id,
            "config": {},
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "type": "agent"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assistants/search")
async def search_assistants():
    """
    Search/list assistants (LangGraph SDK format).
    
    Required by Agent Chat UI SDK.
    """
    available = list_graphs()
    return [
        {
            "assistant_id": aid,
            "graph_id": aid,
            "config": {},
            "metadata": {"type": "agent"}
        }
        for aid in available
    ]


@app.post("/threads")
async def create_thread(request: Request):
    """
    Create a new thread (LangGraph SDK format).
    
    Required by Agent Chat UI SDK when starting a new conversation.
    """
    try:
        # Generate unique thread ID
        thread_id = f"thread-{uuid.uuid4()}"
        
        # Parse request body for optional metadata
        try:
            body = await request.json()
            metadata = body.get("metadata", {})
        except:
            metadata = {}
        
        return {
            "thread_id": thread_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata,
            "values": {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/threads/{thread_id}/runs/stream")
async def stream_run(thread_id: str, request: StreamRequest):
    """
    Main streaming endpoint compatible with LangGraph SDK.

    This endpoint:
    1. Receives messages from Agent Chat UI
    2. Converts to LangGraph format
    3. Executes the graph
    4. Streams results back in SSE format

    Args:
        request: Stream request with messages and config

    Returns:
        StreamingResponse with SSE events
    """
    try:
        # Get graph from registry based on assistant_id
        try:
            graph = get_graph(request.assistant_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

        # Use thread_id from path parameter

        # Generate unique run ID
        run_id = f"run-{uuid.uuid4()}"

        # Convert messages to LangGraph format
        langgraph_messages = convert_to_langgraph_messages(request.input.messages)

        # Return SSE streaming response
        return StreamingResponse(
            sse_generator(graph, thread_id, langgraph_messages, run_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable buffering for nginx
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/threads/search")
async def search_threads(request: Request):
    """
    Thread search endpoint (basic implementation).

    Agent Chat UI uses this to list available threads.
    For now, returns empty list (threads stored in memory checkpointer).
    """
    return []


@app.get("/threads/{thread_id}")
async def get_thread(thread_id: str):
    """
    Get thread by ID.

    Returns basic thread info.
    """
    return {
        "thread_id": thread_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "graph_id": "resume_agent"
        }
    }


@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """
    Get thread state (conversation history).

    This retrieves the conversation history for a thread.
    """
    # Try to get state from checkpointer
    config = {"configurable": {"thread_id": thread_id}}

    try:
        # Get state from graph's checkpointer
        state = graph.get_state(config)

        if state and state.values:
            messages = convert_from_langgraph_messages(state.values.get("messages", []))
            return {
                "values": {
                    "messages": messages
                }
            }
    except Exception:
        pass

    # Return empty state if not found
    return {
        "values": {
            "messages": []
        }
    }


@app.get("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str):
    """
    Get thread history (all state snapshots) - GET method.

    Returns conversation history for the thread.
    """
    return []


@app.post("/threads/{thread_id}/history")
async def get_thread_history_post(thread_id: str):
    """
    Get thread history (all state snapshots) - POST method.

    LangGraph SDK may use POST for this endpoint.
    Returns conversation history for the thread.
    """
    return []


# ==============================================================================
# Main Entry Point
# ==============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("🚀 Resume Agent LangGraph API - FastAPI Server")
    print("="*60)
    print("\n💡 Starting server on http://127.0.0.1:2024")
    print("💡 Compatible with Agent Chat UI")
    print("💡 Press Ctrl+C to stop\n")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=2024,
        log_level="info"
    )
