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

# Third-party imports
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_tavily import TavilySearch
from langgraph.prebuilt import ToolNode, tools_condition

import anthropic
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM Provider Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()  # Options: "claude" or "openai"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")  # Cheaper for testing
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# ==============================================================================
# State Schema
# ==============================================================================

class State(TypedDict):
    """
    State for conversational agent.

    Uses Annotated[list[BaseMessage], add_messages] for messages.
    This is the standard LangGraph pattern for chat history with proper message handling.
    """
    messages: Annotated[list, add_messages]

# ==============================================================================
# Tool Definitions
# ==============================================================================

search_tool = TavilySearch(max_results=2)

tools = [search_tool]

tool_node = ToolNode(tools=tools)

# ==============================================================================
# LLM Initialization
# ==============================================================================

llm_with_tools = init_chat_model(OPENAI_MODEL).bind_tools(tools)

def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    # Because we will be interrupting during tool execution,
    # we disable parallel tool calling to avoid repeating any
    # tool invocations when we resume.
    assert len(message.tool_calls) <= 1
    return {"messages": [message]}


# ==============================================================================
# Build Workflow Graph
# ==============================================================================

graph_builder = StateGraph(State)

# Add only the chat node (no get_input!)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)

# Simple flow: START -> chatbot -> END
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Compile the graph
resume_agent_langgraph = graph_builder.compile()

