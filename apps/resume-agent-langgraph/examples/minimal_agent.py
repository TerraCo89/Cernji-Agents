#!/usr/bin/env python3
"""
Minimal Working LangGraph Agent for Agent Chat UI

This is the simplest possible working example that demonstrates the correct
message format for LangGraph SDK integration with Agent Chat UI.

Key Pattern:
- State uses `add_messages` reducer for message handling
- Messages are BaseMessage objects (HumanMessage, AIMessage)
- Nodes return AIMessage objects, NOT dictionaries
- No input node (messages come from HTTP requests)
"""

import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ==============================================================================
# State Schema - CRITICAL: Use add_messages reducer
# ==============================================================================

class State(TypedDict):
    """
    State for conversational agent.

    IMPORTANT: The messages field MUST use the add_messages reducer.
    This is required for proper LangGraph SDK message handling.
    """
    messages: Annotated[list[BaseMessage], add_messages]


# ==============================================================================
# Agent Node - CRITICAL: Return AIMessage objects
# ==============================================================================

def chat(state: State) -> dict:
    """
    Process user message and return AI response.

    IMPORTANT: This function MUST return a dict with "messages" key
    containing a list of AIMessage objects, NOT plain dicts.

    Args:
        state: Current conversation state with message history

    Returns:
        Partial state update with AI response
    """
    try:
        print(f"\n[DEBUG] chat() called with {len(state['messages'])} messages")

        # Get the last message from the user
        last_message = state["messages"][-1]
        user_input = last_message.content
        print(f"[DEBUG] User input: {user_input}")

        # Generate a simple response (echo for now)
        response_text = f"Echo: {user_input}"
        print(f"[DEBUG] Generating response: {response_text}")

        # CRITICAL: Return AIMessage object, NOT a dict like {"role": "assistant", "content": ...}
        # The add_messages reducer expects BaseMessage objects
        ai_message = AIMessage(content=response_text)
        print(f"[DEBUG] Created AIMessage: {type(ai_message)}")
        print(f"[DEBUG] AIMessage dict: {ai_message.model_dump()}")

        result = {"messages": [ai_message]}
        print(f"[DEBUG] Returning: {result}")
        return result

    except Exception as e:
        print(f"\n[ERROR] Exception in chat(): {e}")
        import traceback
        traceback.print_exc()
        raise


# ==============================================================================
# Build Graph - For Web Use (No Input Node)
# ==============================================================================

def build_graph():
    """
    Build the minimal conversational agent graph.

    This is designed for web use where messages come from HTTP requests,
    so there's no CLI input node.

    Flow:
    1. START -> chat: Process incoming message
    2. chat -> END: Return response

    Returns:
        Compiled StateGraph with memory checkpointer
    """
    # Create graph with State schema
    graph = StateGraph(State)

    # Add the chat node
    graph.add_node("chat", chat)

    # Simple flow: START -> chat -> END
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # Compile WITH MemorySaver checkpointer (in-memory, no file I/O)
    # This avoids Windows OSError from file-based checkpointers
    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)

    return app


# ==============================================================================
# Main Entry Point (for local testing)
# ==============================================================================

def main():
    """
    Test the minimal agent locally.

    This is for debugging only. In production, the graph is exposed
    via LangGraph server.
    """
    print("\n" + "="*60)
    print("Minimal LangGraph Agent - Local Test")
    print("="*60)
    print("\nType 'exit' to quit\n")

    # Build graph
    app = build_graph()

    # Test conversation
    thread_id = "test-conversation"
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        # Get user input
        user_input = input("You: ").strip()

        if user_input.lower() in ['exit', 'quit']:
            print("\nGoodbye!\n")
            break

        # Create state with user message
        # IMPORTANT: Use HumanMessage object, not dict
        state = {
            "messages": [HumanMessage(content=user_input)]
        }

        # Invoke graph
        result = app.invoke(state, config=config)

        # Display response
        last_message = result["messages"][-1]
        print(f"Bot: {last_message.content}\n")


if __name__ == "__main__":
    main()
