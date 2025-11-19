"""Career Assistant - Conversational agent with job analysis tool.

A chatbot that can help with career questions and analyze job postings.
"""

import os
from typing import Dict, Any

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv

# Use absolute imports (required for LangGraph server)
from resume_agent.state import ResumeAgentState
from resume_agent.tools import (
    analyze_job_posting,
    load_master_resume,
    extract_skills_from_resume,
    calculate_ats_score,
)

load_dotenv()

# ==============================================================================
# LLM Configuration
# ==============================================================================

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

if LLM_PROVIDER.lower() == "anthropic":
    model_string = f"anthropic:{ANTHROPIC_MODEL}"
else:
    model_string = f"openai:{OPENAI_MODEL}"

llm = init_chat_model(model_string)

# ==============================================================================
# Tools
# ==============================================================================

tools = [
    analyze_job_posting,           # Analyze job postings from URLs
    load_master_resume,            # Load user's resume
    extract_skills_from_resume,    # Extract skills from resume
    calculate_ats_score,           # Calculate ATS compatibility
]

# ==============================================================================
# Nodes
# ==============================================================================

def chatbot_node(state: ResumeAgentState) -> Dict[str, Any]:
    """Main chatbot node with tool calling.

    Args:
        state: Current conversation state

    Returns:
        Dictionary with new messages to add to state
    """
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Add system message if this is the first message
    messages = state["messages"]

    # Invoke LLM
    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def route_after_chatbot(state: ResumeAgentState) -> str:
    """Route to tools or end conversation.

    Args:
        state: Current state

    Returns:
        Next node: 'tools' or END
    """
    last_message = state["messages"][-1]

    # If LLM called tools, route to tool node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return END

# ==============================================================================
# Graph Construction
# ==============================================================================

def build_career_assistant_graph():
    """Build conversational career assistant with tools.

    Flow:
        START → chatbot → [has tools?] → tools → chatbot
                       → [no tools?] → END
    """
    graph = StateGraph(ResumeAgentState)

    # Add nodes
    graph.add_node("chatbot", chatbot_node)
    graph.add_node("tools", ToolNode(tools=tools))

    # Define flow
    graph.add_edge(START, "chatbot")

    graph.add_conditional_edges(
        "chatbot",
        route_after_chatbot,
        {
            "tools": "tools",
            END: END
        }
    )

    # After tools, go back to chatbot
    graph.add_edge("tools", "chatbot")

    # Compile (LangGraph server provides automatic persistence)
    return graph.compile()


# ==============================================================================
# Export (Required for LangGraph Server)
# ==============================================================================

# Export compiled graph for langgraph.json to discover this agent
graph = build_career_assistant_graph()
