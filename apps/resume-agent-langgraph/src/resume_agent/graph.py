"""LangGraph Resume Agent - Job Analysis Workflow.

A conversational agent for resume tailoring and career assistance.
Implements job analysis workflow with browser automation and caching.
"""
from __future__ import annotations

import os
from typing import Dict, Any

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AIMessage

from dotenv import load_dotenv

# Import state schema
from resume_agent.state.schemas import (
    ResumeAgentState,
)

# Import job analysis nodes
from resume_agent.nodes.job_analysis import (
    check_cache_node,
    fetch_job_node,
    analyze_job_node,
)

# Import resume-specific tools
from resume_agent.tools import (
    # Job analysis (triggers workflow)
    analyze_job_posting,

    # ATS scoring
    calculate_keyword_match,
    calculate_ats_score,

    # Resume parsing
    load_master_resume,
    extract_skills_from_resume,
    extract_achievements_from_resume,
)

# Load environment variables
load_dotenv()


# ==============================================================================
# State Schema
# ==============================================================================

# JobAnalysisState is imported from state.schemas
# It includes all fields needed for job analysis workflow:
# - job_url: URL of job posting to analyze
# - job_content: Fetched HTML/text content
# - job_analysis: Structured analysis result
# - cached: Whether result came from cache
# - errors: List of errors encountered
# - duration_ms: Time taken for operations


# ==============================================================================
# Tool Definitions
# ==============================================================================

# List of tools available to the LLM
tools = [
    # Job Analysis Tools (triggers browser automation workflow)
    analyze_job_posting,           # Fetch and analyze job postings from URLs

    # ATS Compatibility Tools
    calculate_keyword_match,       # Calculate keyword match percentage
    calculate_ats_score,           # Overall ATS compatibility score

    # Resume Data Tools
    load_master_resume,            # Load resume from YAML file
    extract_skills_from_resume,    # Extract all skills from resume
    extract_achievements_from_resume,  # Extract achievements with context
]


# ==============================================================================
# LLM Configuration
# ==============================================================================

# Initialize the chat model - configured via environment variables
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
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

def chatbot(state: ResumeAgentState) -> Dict[str, Any]:
    """Main chatbot node that processes messages and generates responses.

    Args:
        state: Current graph state with full ResumeAgentState schema

    Returns:
        Dictionary with new messages to add to state
    """
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)
    message = llm_with_tools.invoke(state["messages"])

    # Disable parallel tool calling to avoid repeating invocations during interrupts
    assert len(message.tool_calls) <= 1

    return {"messages": [message]}


def route_after_chatbot(state: ResumeAgentState) -> str:
    """Route after chatbot based on tool calls and state.

    If analyze_job_posting tool was called, extract job_url and route to
    job analysis workflow. Otherwise, route based on tool calls.

    Args:
        state: Current graph state

    Returns:
        Next node name or END
    """
    # Check last message for tool calls
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        # Check if analyze_job_posting was called
        for tool_call in last_message.tool_calls:
            if tool_call["name"] == "analyze_job_posting":
                # Route to job analysis workflow
                # Note: job_url will be extracted in extract_job_url_node
                return "extract_job_url"

        # Other tool calls go to normal tool node
        return "tools"

    return END


def route_after_cache_check(state: ResumeAgentState) -> str:
    """Route after cache check: fetch if miss, analyze if hit.

    Args:
        state: Current graph state with 'cached' field

    Returns:
        'fetch_job' if cache miss, 'analyze_job' if cache hit
    """
    if state.get("cached"):
        # Cache hit - skip fetch, go straight to final response
        return "format_job_analysis_response"
    else:
        # Cache miss - fetch job content
        return "fetch_job"


def route_after_fetch(state: ResumeAgentState) -> str:
    """Route after fetch: analyze if successful, end if error.

    Args:
        state: Current graph state with 'job_content' or 'errors'

    Returns:
        'analyze_job' if successful, END if error
    """
    if state.get("errors"):
        # Fetch failed - return error to user
        return "format_error_response"
    else:
        # Fetch succeeded - analyze job content
        return "analyze_job"


def route_after_analyze(state: ResumeAgentState) -> str:
    """Route after analysis: format response or handle error.

    Args:
        state: Current graph state with 'job_analysis' or 'errors'

    Returns:
        'format_job_analysis_response' if successful, 'format_error_response' if error
    """
    if state.get("errors"):
        return "format_error_response"
    else:
        return "format_job_analysis_response"


def format_job_analysis_response(state: ResumeAgentState) -> Dict[str, Any]:
    """Format job analysis result as user message.

    Args:
        state: State with job_analysis field

    Returns:
        State update with formatted message
    """
    job_analysis = state.get("job_analysis", {})
    cached = state.get("cached", False)

    # Build response message
    cache_indicator = " (from cache)" if cached else ""

    response_parts = [
        f"✅ **Job Analysis Complete{cache_indicator}**\n",
        f"**Company**: {job_analysis.get('company', 'N/A')}",
        f"**Position**: {job_analysis.get('job_title', 'N/A')}",
        f"**Location**: {job_analysis.get('location', 'N/A')}\n",
    ]

    # Add required qualifications summary
    required_quals = job_analysis.get("required_qualifications", [])
    if required_quals:
        response_parts.append(f"**Required Qualifications** ({len(required_quals)}):")
        for qual in required_quals[:5]:  # Show first 5
            response_parts.append(f"  • {qual}")
        if len(required_quals) > 5:
            response_parts.append(f"  ... and {len(required_quals) - 5} more")

    # Add keywords summary
    keywords = job_analysis.get("keywords", [])
    if keywords:
        response_parts.append(f"\n**Key Technologies**: {', '.join(keywords[:10])}")

    response_message = "\n".join(response_parts)

    # Clear job_url to prevent re-triggering workflow
    return {
        "messages": [AIMessage(content=response_message)],
        "job_url": None,  # Clear to prevent loop
    }


def extract_job_url_node(state: ResumeAgentState) -> Dict[str, Any]:
    """Extract job_url from analyze_job_posting tool call.

    Args:
        state: State with tool call message

    Returns:
        State update with job_url set
    """
    last_message = state["messages"][-1]

    # Find analyze_job_posting tool call and extract job_url
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "analyze_job_posting":
            job_url = tool_call["args"].get("job_url")
            return {"job_url": job_url}

    # Should never reach here based on routing logic
    return {"errors": ["Failed to extract job_url from tool call"]}


def format_error_response(state: ResumeAgentState) -> Dict[str, Any]:
    """Format error message for user.

    Args:
        state: State with errors list

    Returns:
        State update with error message
    """
    errors = state.get("errors", [])
    error_message = "\n".join([f"❌ {error}" for error in errors])

    response = f"**Job Analysis Failed**\n\n{error_message}\n\nPlease check the URL and try again."

    # Clear job_url and errors
    return {
        "messages": [AIMessage(content=response)],
        "job_url": None,
        "errors": [],
    }


# ==============================================================================
# Build Graph
# ==============================================================================

# Initialize graph builder with ResumeAgentState schema
graph_builder = StateGraph(ResumeAgentState)

# Add chatbot node
graph_builder.add_node("chatbot", chatbot)

# Add tool node for general tools
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# Add job analysis workflow nodes
graph_builder.add_node("extract_job_url", extract_job_url_node)
graph_builder.add_node("check_cache", check_cache_node)
graph_builder.add_node("fetch_job", fetch_job_node)
graph_builder.add_node("analyze_job", analyze_job_node)
graph_builder.add_node("format_job_analysis_response", format_job_analysis_response)
graph_builder.add_node("format_error_response", format_error_response)

# Define entry point
graph_builder.add_edge(START, "chatbot")

# Route from chatbot: either to tools, job analysis workflow, or END
graph_builder.add_conditional_edges(
    "chatbot",
    route_after_chatbot,
    {
        "tools": "tools",
        "extract_job_url": "extract_job_url",
        END: END,
    }
)

# Tools return to chatbot for next turn
graph_builder.add_edge("tools", "chatbot")

# Job analysis workflow entry point - extract job_url then check cache
graph_builder.add_edge("extract_job_url", "check_cache")

# Job analysis workflow routing
graph_builder.add_conditional_edges(
    "check_cache",
    route_after_cache_check,
    {
        "fetch_job": "fetch_job",
        "format_job_analysis_response": "format_job_analysis_response",
    }
)

graph_builder.add_conditional_edges(
    "fetch_job",
    route_after_fetch,
    {
        "analyze_job": "analyze_job",
        "format_error_response": "format_error_response",
    }
)

graph_builder.add_conditional_edges(
    "analyze_job",
    route_after_analyze,
    {
        "format_job_analysis_response": "format_job_analysis_response",
        "format_error_response": "format_error_response",
    }
)

# Response formatting nodes return to chatbot for next turn
graph_builder.add_edge("format_job_analysis_response", "chatbot")
graph_builder.add_edge("format_error_response", "chatbot")

# Compile the graph
# Note: When running via `langgraph dev`, checkpointing/persistence is handled
# automatically by the server - no need to pass a checkpointer here!
graph = graph_builder.compile()
