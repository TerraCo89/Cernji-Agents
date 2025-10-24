#!/usr/bin/env python3
"""
Resume Agent LangGraph - Conversational Agent

A real-time conversational agent powered by LangGraph and Claude.
This is a simplified version that demonstrates the core patterns before
adding the full resume agent functionality.

Architecture:
- StateGraph: Conversation state management
- Claude API: LLM reasoning
- Simple CLI: User interaction

Author: Claude (Anthropic)
License: Experimental
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict, Annotated

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
from resume_agent.llm.messages import convert_langgraph_messages_to_api_format

# Fix Windows console encoding for emoji support
if sys.platform == "win32":
    import codecs
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Third-party imports
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
import anthropic
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()  # Options: "claude" or "openai"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Cheaper for testing

# ==============================================================================
# State Schema
# ==============================================================================

class ConversationState(TypedDict):
    """
    State for conversational agent.

    Uses Annotated[list[BaseMessage], add_messages] for messages.
    This is the standard LangGraph pattern for chat history with proper message handling.
    """
    messages: Annotated[list[BaseMessage], add_messages]  # Chat history (append-only)
    should_continue: bool  # Whether to continue conversation


# ==============================================================================
# Agent Nodes
# ==============================================================================

def call_llm(messages: list, system_prompt: str) -> str:
    """
    Call the configured LLM provider (Claude or OpenAI).

    Args:
        messages: List of message dicts with role and content
        system_prompt: System prompt to guide the LLM

    Returns:
        Assistant's response text

    Raises:
        Exception: If LLM call fails
    """
    if LLM_PROVIDER == "openai":
        # OpenAI API
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # OpenAI format includes system message in messages array
        api_messages = [{"role": "system", "content": system_prompt}] + messages

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=api_messages,
            max_tokens=2048,
            temperature=0.7
        )

        return response.choices[0].message.content

    else:
        # Claude API (default)
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Claude uses separate system parameter
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=messages
        )

        return response.content[0].text


def chat_node(state: ConversationState) -> dict:
    """
    Main chat node: processes user input with LLM.

    This node:
    1. Takes conversation history from state
    2. Sends to LLM API for response (Claude or OpenAI based on config)
    3. Returns LLM's response (appended to messages)

    Args:
        state: Current conversation state with message history

    Returns:
        Partial state update with LLM's response
    """
    provider_name = "OpenAI" if LLM_PROVIDER == "openai" else "Claude"
    model_name = OPENAI_MODEL if LLM_PROVIDER == "openai" else CLAUDE_MODEL
    print(f"\n🤖 Thinking... ({provider_name}/{model_name})")

    try:
        # Convert LangGraph SDK message format to API format
        # This handles both {"type": "human"} and {"role": "user"} formats
        api_messages = convert_langgraph_messages_to_api_format(state["messages"])

        # System prompt: Define the agent's personality and capabilities
        system_prompt = """You are a helpful Resume Agent assistant. Right now you're in development mode,
learning to have conversations before adding advanced resume features.

Be friendly, concise, and helpful. When the user asks about your capabilities,
explain that you're currently a simple conversational agent being built on LangGraph,
and will soon have features like:
- Analyzing job postings
- Tailoring resumes
- Writing cover letters
- Finding portfolio examples

For now, just have a nice conversation!"""

        # Call LLM (Claude or OpenAI based on config)
        assistant_message = call_llm(api_messages, system_prompt)

        # Return as partial state update (will be appended to messages)
        # IMPORTANT: Use AIMessage object, not plain dict, for LangGraph SDK compatibility
        return {
            "messages": [AIMessage(content=assistant_message)]
        }

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return {
            "messages": [AIMessage(content=f"Sorry, I encountered an error: {str(e)}")]
        }


def get_user_input_node(state: ConversationState) -> dict:
    """
    Get input from user via CLI.

    This node:
    1. Displays the last assistant message (if any)
    2. Prompts user for input
    3. Handles exit commands
    4. Returns user message

    Args:
        state: Current conversation state

    Returns:
        Partial state update with user message and continue flag
    """
    # Display last assistant message
    if state["messages"]:
        last_msg = state["messages"][-1]
        # Handle both message objects and dicts (for compatibility)
        msg_type = getattr(last_msg, 'type', None) or last_msg.get("role", None)
        msg_content = getattr(last_msg, 'content', None) or last_msg.get("content", "")
        if msg_type in ["ai", "assistant"]:
            print(f"\n🤖 Assistant: {msg_content}")

    # Get user input
    print("\n" + "="*60)
    user_input = input("👤 You (type 'exit' or 'quit' to end): ").strip()

    # Check for exit command
    if user_input.lower() in ['exit', 'quit', 'bye']:
        print("\n👋 Goodbye! Thanks for chatting!\n")
        return {
            "should_continue": False,
            "messages": [HumanMessage(content=user_input)]
        }

    # Return user message
    # IMPORTANT: Use HumanMessage object, not plain dict, for LangGraph SDK compatibility
    return {
        "should_continue": True,
        "messages": [HumanMessage(content=user_input)]
    }


# ==============================================================================
# Conditional Edge Functions
# ==============================================================================

def should_continue(state: ConversationState) -> str:
    """
    Determine if conversation should continue.

    This is a conditional edge function that routes based on state.

    Args:
        state: Current conversation state

    Returns:
        Next node name: "chat" to continue, END to stop
    """
    if state.get("should_continue", True):
        return "chat"
    return END


# ==============================================================================
# Build Workflow Graph
# ==============================================================================

def build_conversation_graph() -> StateGraph:
    """
    Build the conversational agent workflow.

    Flow:
    1. START -> get_input: Get user message
    2. get_input -> chat: Process with Claude (conditional: continue if not exit)
    3. chat -> get_input: Loop back for next message

    Returns:
        Compiled StateGraph with checkpointer
    """
    # Create graph
    graph = StateGraph(ConversationState)

    # Add nodes
    graph.add_node("get_input", get_user_input_node)
    graph.add_node("chat", chat_node)

    # Set entry point
    graph.add_edge(START, "get_input")

    # Add conditional edge after get_input
    graph.add_conditional_edges(
        "get_input",
        should_continue,
        {
            "chat": "chat",
            END: END
        }
    )

    # Loop: chat back to get_input
    graph.add_edge("chat", "get_input")

    # Compile with memory checkpointer
    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)

    return app


def build_web_conversation_graph() -> StateGraph:
    """
    Build web-compatible conversational agent (no CLI input).

    Flow:
    1. START -> chat: Process incoming message
    2. chat -> END: Return response

    Messages come from HTTP requests (already in state).
    No get_input node needed.

    Returns:
        Compiled StateGraph with checkpointer
    """
    graph = StateGraph(ConversationState)

    # Add only the chat node (no get_input!)
    graph.add_node("chat", chat_node)

    # Simple flow: START -> chat -> END
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)

    # Compile with memory checkpointer
    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)

    return app


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """
    Main entry point for Resume Agent conversational interface.

    Starts an interactive chat session with the agent.
    """
    print("\n" + "="*60)
    print("🚀 Resume Agent - LangGraph Conversational Agent")
    print("="*60)

    # Show LLM provider configuration
    provider_name = "OpenAI" if LLM_PROVIDER == "openai" else "Claude"
    model_name = OPENAI_MODEL if LLM_PROVIDER == "openai" else CLAUDE_MODEL
    print(f"\n💡 LLM Provider: {provider_name}")
    print(f"💡 Model: {model_name}")

    print("\nWelcome! I'm your Resume Agent assistant.")
    print("I'm currently in development mode, learning to chat with you.")
    print("\nType 'exit', 'quit', or 'bye' to end the conversation.")
    print("="*60)

    # Check for appropriate API key based on provider
    if LLM_PROVIDER == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            print("\n❌ Error: OPENAI_API_KEY not found in environment")
            print("Please set your API key in .env file or environment variables")
            print("Or switch to Claude by setting LLM_PROVIDER=claude")
            sys.exit(1)
    else:
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("\n❌ Error: ANTHROPIC_API_KEY not found in environment")
            print("Please set your API key in .env file or environment variables")
            print("Or switch to OpenAI by setting LLM_PROVIDER=openai")
            sys.exit(1)

    try:
        # Build conversation graph
        app = build_conversation_graph()

        # Initialize conversation state
        initial_state = {
            "messages": [],
            "should_continue": True
        }

        # Run conversation loop
        # Each iteration maintains conversation history via checkpointing
        thread_id = f"conversation-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        config = {"configurable": {"thread_id": thread_id}}

        # Start the conversation
        app.invoke(initial_state, config=config)

    except KeyboardInterrupt:
        print("\n\n👋 Conversation interrupted. Goodbye!\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()


# ==============================================================================
# LangGraph API Entry Point
# ==============================================================================

def build_graph():
    """
    Entry point for LangGraph API server.
    
    This function is called by langgraph.json to build the graph.
    Returns the web-compatible conversation graph.
    """
    return build_web_conversation_graph()
