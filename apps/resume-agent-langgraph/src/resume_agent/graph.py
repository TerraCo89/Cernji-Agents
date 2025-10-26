"""LangGraph Resume Agent - Core Graph Definition.

A conversational agent for resume tailoring and career assistance.
Built following LangGraph patterns with tool integration and human-in-the-loop support.
"""
from __future__ import annotations

import os
from typing import Annotated

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ==============================================================================
# State Schema
# ==============================================================================

class State(TypedDict):
    """The state of our resume agent.

    Contains a list of messages that will be appended to (not overwritten)
    thanks to the add_messages reducer function.
    """
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


# ==============================================================================
# Tool Definitions
# ==============================================================================

# TODO: Add resume-specific tools here
tools = []


# ==============================================================================
# LLM Configuration
# ==============================================================================

# Initialize the chat model - configured via environment variables
# Supports: "openai:gpt-4", "anthropic:claude-3-5-sonnet-latest", etc.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

# Select model based on provider
if LLM_PROVIDER.lower() == "anthropic":
    model_string = f"anthropic:{ANTHROPIC_MODEL}"
else:
    model_string = f"openai:{OPENAI_MODEL}"

llm = init_chat_model(model_string)


# ==============================================================================
# Node Functions
# ==============================================================================

def chatbot(state: State):
    """Main chatbot node that processes messages and generates responses.

    Args:
        state: Current graph state containing message history

    Returns:
        Dictionary with new messages to add to state
    """
    # If we have tools, bind them to the LLM
    if tools:
        llm_with_tools = llm.bind_tools(tools)
        message = llm_with_tools.invoke(state["messages"])
        # Disable parallel tool calling to avoid repeating invocations during interrupts
        assert len(message.tool_calls) <= 1
    else:
        message = llm.invoke(state["messages"])

    return {"messages": [message]}


# ==============================================================================
# Build Graph
# ==============================================================================

# Initialize graph builder
graph_builder = StateGraph(State)

# Add chatbot node
graph_builder.add_node("chatbot", chatbot)

# If we have tools, add tool node and routing
if tools:
    tool_node = ToolNode(tools=tools)
    graph_builder.add_node("tools", tool_node)

    # Any time a tool is called, we return to the chatbot to decide the next step
    graph_builder.add_edge("tools", "chatbot")
    graph_builder.add_conditional_edges("chatbot", tools_condition)

# Define entry point
graph_builder.add_edge(START, "chatbot")

# Compile the graph
# Note: When running via `langgraph dev`, checkpointing/persistence is handled
# automatically by the server - no need to pass a checkpointer here!
graph = graph_builder.compile()
