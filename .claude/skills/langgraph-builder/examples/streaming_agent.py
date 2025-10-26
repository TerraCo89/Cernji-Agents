#!/usr/bin/env python3
"""
Streaming LangGraph Agent Example

Demonstrates streaming responses from a LangGraph agent using:
- Token-level streaming (real-time LLM output)
- Server-Sent Events (SSE) for web frontends
- Message-level streaming (complete messages)

Usage:
    python streaming_agent.py --server

Then test with:
    curl -X POST http://localhost:8080/stream \
      -H "Content-Type: application/json" \
      -d '{"message": "Tell me a story", "thread_id": "test"}'
"""

from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import anthropic
import os

# ============================================================================
# Configuration
# ============================================================================

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# ============================================================================
# State Schema
# ============================================================================

class ConversationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ============================================================================
# Helper Functions
# ============================================================================

def convert_to_api_format(messages: list[BaseMessage]) -> list[dict]:
    """Convert LangGraph messages to API format"""
    api_messages = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        api_messages.append({"role": role, "content": msg.content})
    return api_messages


# ============================================================================
# Graph Nodes
# ============================================================================

def chat_node(state: ConversationState) -> dict:
    """Chat node with LLM call"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    api_messages = convert_to_api_format(state["messages"])

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system="You are a helpful assistant.",
        messages=api_messages
    )

    return {"messages": [AIMessage(content=response.content[0].text)]}


# ============================================================================
# Build Graph
# ============================================================================

def build_graph():
    """Build conversation graph"""
    graph = StateGraph(ConversationState)
    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# ============================================================================
# FastAPI Server with Streaming
# ============================================================================

def create_fastapi_server():
    """Create FastAPI server with streaming support"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    import json

    app = FastAPI(title="Streaming LangGraph Agent")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    graph = build_graph()

    class ChatRequest(BaseModel):
        message: str
        thread_id: str = "default"

    # ========================================================================
    # Pattern 1: Token Streaming (Real-time)
    # ========================================================================

    @app.post("/stream")
    async def stream_tokens(request: ChatRequest):
        """
        Stream individual tokens using Server-Sent Events.

        Best for: Real-time chat interfaces
        """
        async def event_generator():
            config = {"configurable": {"thread_id": request.thread_id}}

            async for event in graph.astream_events(
                {"messages": [HumanMessage(content=request.message)]},
                config=config,
                version="v2"
            ):
                # Filter for LLM token chunks
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        data = json.dumps({"content": chunk.content})
                        yield f"data: {data}\n\n"

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

    # ========================================================================
    # Pattern 2: Message Streaming (Complete Messages)
    # ========================================================================

    @app.post("/stream/messages")
    async def stream_messages(request: ChatRequest):
        """
        Stream complete messages as nodes finish.

        Best for: Showing agent workflow steps
        """
        async def message_generator():
            config = {"configurable": {"thread_id": request.thread_id}}

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

            yield "data: [DONE]\n\n"

        return StreamingResponse(
            message_generator(),
            media_type="text/event-stream"
        )

    # ========================================================================
    # Pattern 3: Non-Streaming (Traditional)
    # ========================================================================

    @app.post("/chat")
    async def chat(request: ChatRequest):
        """
        Non-streaming endpoint.

        Best for: Simple integrations, testing
        """
        config = {"configurable": {"thread_id": request.thread_id}}

        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )

        return {
            "response": result["messages"][-1].content,
            "thread_id": request.thread_id
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


# ============================================================================
# Test Client
# ============================================================================

def test_streaming():
    """Test streaming with a simple client"""
    import httpx

    print("🧪 Testing streaming endpoint...\n")

    with httpx.Client() as client:
        with client.stream(
            "POST",
            "http://localhost:8080/stream",
            json={"message": "Count to 5", "thread_id": "test"},
            timeout=None
        ) as response:
            print("Response stream:")
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    print(data, end="", flush=True)
            print("\n\n✅ Streaming test complete!")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        import uvicorn
        app = create_fastapi_server()
        print("🚀 Starting streaming server on http://localhost:8080")
        print("\n📝 Test endpoints:")
        print("   Token streaming: curl -X POST http://localhost:8080/stream -H 'Content-Type: application/json' -d '{\"message\": \"Hello!\"}'")
        print("   Message streaming: curl -X POST http://localhost:8080/stream/messages -H 'Content-Type: application/json' -d '{\"message\": \"Hello!\"}'")
        print("   Non-streaming: curl -X POST http://localhost:8080/chat -H 'Content-Type: application/json' -d '{\"message\": \"Hello!\"}'")
        uvicorn.run(app, host="0.0.0.0", port=8080)
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_streaming()
    else:
        print("Usage:")
        print("  python streaming_agent.py --server    Start server")
        print("  python streaming_agent.py --test      Test streaming")
