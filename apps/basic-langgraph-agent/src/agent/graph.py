"""LangGraph basic chatbot following the official tutorial.

Creates a chatbot that can respond to user messages using a chat model.
"""
from __future__ import annotations

import os
import json

from typing import Annotated

from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langchain_tavily import TavilySearch
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt

from typing_extensions import TypedDict

# API keys are loaded from environment variables or .env file
# The LangGraph server automatically loads .env when starting
# No need to set them explicitly here - they should be in your .env file

class State(TypedDict):
    """The state of our chatbot.
    
    Contains a list of messages that will be appended to (not overwritten)
    thanks to the add_messages reducer function.
    """
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]
    name: str
    birthday: str


@tool
# Note that because we are generating a ToolMessage for a state update, we
# generally require the ID of the corresponding tool call. We can use
# LangChain's InjectedToolCallId to signal that this argument should not
# be revealed to the model in the tool's schema.
def human_assistance(
    name: str, birthday: str, tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Request assistance from a human."""
    human_response = interrupt(
        {
            "question": "Is this correct?",
            "name": name,
            "birthday": birthday,
        },
    )

    # Handle both Studio (string) and programmatic (dict) resume formats
    if isinstance(human_response, str):
        # Studio sends plain text - treat "yes"/"y" as confirmation
        if human_response.lower().startswith("y"):
            verified_name = name
            verified_birthday = birthday
            response = "Correct"
        else:
            # For corrections via Studio, keep original values since we can't
            # parse structured data from free text easily
            verified_name = name
            verified_birthday = birthday
            response = f"Noted feedback: {human_response}"
    else:
        # Programmatic dict response (tutorial format)
        if human_response.get("correct", "").lower().startswith("y"):
            verified_name = name
            verified_birthday = birthday
            response = "Correct"
        else:
            verified_name = human_response.get("name", name)
            verified_birthday = human_response.get("birthday", birthday)
            response = f"Made a correction: {human_response}"

    # This time we explicitly update the state with a ToolMessage inside
    # the tool.
    state_update = {
        "name": verified_name,
        "birthday": verified_birthday,
        "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
    }
    # We return a Command object in the tool to update our state.
    return Command(update=state_update)


search_tool = TavilySearch(max_results=2)


tools = [search_tool, human_assistance]


# Initialize the chat model - you can change this to any supported model
# For example: "openai:gpt-4", "anthropic:claude-3-5-sonnet-latest", etc.
llm = init_chat_model("openai:gpt-4.1-mini")
llm_with_tools = llm.bind_tools(tools)

# Build the graph
graph_builder = StateGraph(State)


def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    # Because we will be interrupting during tool execution,
    # we disable parallel tool calling to avoid repeating any
    # tool invocations when we resume.
    assert len(message.tool_calls) <= 1
    return {"messages": [message]}

graph_builder.add_node("chatbot", chatbot)


# Add the chatbot node
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)

graph_builder.add_edge(START, "chatbot")

# Compile the graph
# Note: When running via `langgraph dev`, checkpointing/persistence is handled
# automatically by the server - no need to pass a checkpointer here!
graph = graph_builder.compile()
