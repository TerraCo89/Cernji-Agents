#!/usr/bin/env python3
"""
Minimal LangGraph Agent Example

A complete, working example of a LangGraph agent with:
- Proper message handling (avoiding KeyError: 'role')
- Memory persistence with checkpointing
- Multi-provider LLM support (Claude/OpenAI)
- FastAPI server with streaming
- Agent Chat UI compatibility

Usage:
    python minimal_agent.py

Then test with:
    curl -X POST http://localhost:8080/chat \
      -H "Content-Type: application/json" \
      -d '{"message": "Hello!", "thread_id": "test-123"}'
"""

from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import anthropic
import openai
import os

# ============================================================================
# Configuration
# ============================================================================

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ============================================================================
# State Schema
# ============================================================================

class ConversationState(TypedDict):
    """
    State schema for conversation agent.

    IMPORTANT: Use TypedDict (not Pydantic BaseModel) to avoid msgpack errors.
    """
    messages: Annotated[list[BaseMessage], add_messages]


# ============================================================================
# Helper Functions
# ============================================================================

def convert_to_api_format(messages: list[BaseMessage]) -> list[dict]:
    """
    Convert LangGraph messages to API format.

    LangGraph: HumanMessage(content="Hello")
    API: {"role": "user", "content": "Hello"}
    """
    api_messages = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        api_messages.append({"role": role, "content": msg.content})
    return api_messages


def call_claude(messages: list[dict], system_prompt: str) -> str:
    """Call Claude API"""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system=system_prompt,
        messages=messages
    )

    return response.content[0].text


def call_openai(messages: list[dict], system_prompt: str) -> str:
    """Call OpenAI API"""
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    # OpenAI needs system message in messages array
    api_messages = [{"role": "system", "content": system_prompt}] + messages

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_messages,
        max_tokens=2048
    )

    return response.choices[0].message.content


def call_llm(messages: list[dict], system_prompt: str) -> str:
    """Unified LLM interface - switches based on LLM_PROVIDER env var"""
    if LLM_PROVIDER == "openai":
        return call_openai(messages, system_prompt)
    else:
        return call_claude(messages, system_prompt)


# ============================================================================
# Graph Nodes
# ============================================================================

def chat_node(state: ConversationState) -> dict:
    """
    Process conversation with LLM.

    IMPORTANT: Return AIMessage objects (not plain strings) to avoid
    KeyError: 'role' when using with Agent Chat UI.
    """
    # Convert LangGraph messages to API format
    api_messages = convert_to_api_format(state["messages"])

    # Call LLM
    response_text = call_llm(
        messages=api_messages,
        system_prompt="You are a helpful assistant."
    )

    # Return as AIMessage object
    return {
        "messages": [AIMessage(content=response_text)]
    }


# ============================================================================
# Build Graph
# ============================================================================

def build_graph():
    """Build conversation graph with checkpointing"""
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("chat", chat_node)

    # Define flow
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # Compile with checkpointer for persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# ============================================================================
# Test the Graph
# ============================================================================

def test_graph():
    """Test graph with multiple messages"""
    app = build_graph()

    config = {"configurable": {"thread_id": "test-conversation"}}

    # First message
    print("User: Hello, my name is Alice")
    result = app.invoke(
        {"messages": [HumanMessage(content="Hello, my name is Alice")]},
        config=config
    )
    print(f"Assistant: {result['messages'][-1].content}\n")

    # Second message (should remember name)
    print("User: What's my name?")
    result = app.invoke(
        {"messages": [HumanMessage(content="What's my name?")]},
        config=config
    )
    print(f"Assistant: {result['messages'][-1].content}\n")

    print(f"Total messages in conversation: {len(result['messages'])}")


# ============================================================================
# FastAPI Server (Optional)
# ============================================================================

def create_fastapi_server():
    """Create FastAPI server for the agent"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel

    app = FastAPI(title="Minimal LangGraph Agent")

    # CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Build graph
    graph = build_graph()

    class ChatRequest(BaseModel):
        message: str
        thread_id: str = "default"

    class ChatResponse(BaseModel):
        response: str
        thread_id: str

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """Chat endpoint"""
        config = {"configurable": {"thread_id": request.thread_id}}

        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config
        )

        return ChatResponse(
            response=result["messages"][-1].content,
            thread_id=request.thread_id
        )

    @app.get("/health")
    async def health():
        """Health check"""
        return {"status": "healthy"}

    return app


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Start FastAPI server
        import uvicorn
        app = create_fastapi_server()
        print("🚀 Starting FastAPI server on http://localhost:8080")
        print("📝 Test with: curl -X POST http://localhost:8080/chat -H 'Content-Type: application/json' -d '{\"message\": \"Hello!\"}'")
        uvicorn.run(app, host="0.0.0.0", port=8080)
    else:
        # Run test
        print("🧪 Running graph test...\n")
        test_graph()
        print("\n✅ Test complete!")
        print("\n💡 Run with --server flag to start FastAPI server:")
        print("   python minimal_agent.py --server")
