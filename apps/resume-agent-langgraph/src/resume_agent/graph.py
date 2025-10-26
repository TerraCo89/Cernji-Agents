"""LangGraph Resume Agent - Core Graph Definition.

A conversational agent for resume tailoring and career assistance.
Built following LangGraph patterns with tool integration and human-in-the-loop support.
"""
from __future__ import annotations

import os
from typing import Dict, Any

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from dotenv import load_dotenv

# Import comprehensive state schema and helpers
# Using absolute imports for compatibility with langgraph dev server
from resume_agent.state.schemas import (
    # Main state schema
    ResumeAgentState,

    # Data structure TypedDicts
    PersonalInfoDict,
    AchievementDict,
    EmploymentDict,
    MasterResumeDict,
    JobAnalysisDict,
    TailoredResumeDict,
    CoverLetterDict,
    PortfolioExampleDict,

    # Workflow control TypedDicts
    WorkflowIntent,
    WorkflowProgress,

    # Custom reducers
    append_unique_examples,
    replace_with_latest,

    # Helper functions
    create_initial_state,
    update_state,

    # Validators
    validate_job_analysis_exists,
    validate_master_resume_exists,
    validate_can_tailor_resume,
    validate_can_write_cover_letter,
)

# Load environment variables
load_dotenv()


# ==============================================================================
# State Schema
# ==============================================================================

# State schema is now imported from state.schemas module
# See: src/resume_agent/state/schemas.py for the complete ResumeAgentState definition
#
# Key state fields:
# - messages: Conversation history (required)
# - job_analysis: Current job being analyzed
# - master_resume: User's master resume data
# - tailored_resume: Job-specific tailored resume
# - cover_letter: Job-specific cover letter
# - portfolio_examples: Relevant code examples
# - current_intent: Classified user intent
# - workflow_progress: Multi-step workflow tracking
# - requires_user_input: Whether agent needs user input
# - error_message: Latest error if any
# - rag_query_results: Results from website semantic search
# - processed_websites: List of processed website metadata
# - user_id: User identifier


# ==============================================================================
# Tool Definitions
# ==============================================================================

# Import resume-specific tools
from resume_agent.tools import (
    # Job analysis
    analyze_job_posting,
    
    # ATS scoring
    calculate_keyword_match,
    calculate_ats_score,

    # Resume parsing
    load_master_resume,
    extract_skills_from_resume,
    extract_achievements_from_resume,
)

# List of tools available to the LLM
tools = [
    # Job Analysis Tools
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
# Supports: "openai:gpt-4", "anthropic:claude-3-5-sonnet-latest", etc.
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1")
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
    # If we have tools, bind them to the LLM
    if tools:
        llm_with_tools = llm.bind_tools(tools)
        message = llm_with_tools.invoke(state["messages"])
        # Disable parallel tool calling to avoid repeating invocations during interrupts
        assert len(message.tool_calls) <= 1
    else:
        message = llm.invoke(state["messages"])

    # Use update_state helper for cleaner state updates
    return update_state(state, messages=[message])


# ==============================================================================
# Build Graph
# ==============================================================================

# Initialize graph builder with ResumeAgentState schema
graph_builder = StateGraph(ResumeAgentState)

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
# The ResumeAgentState schema includes custom reducers that will be applied
# automatically during state updates (e.g., append_unique_examples for portfolio_examples)
graph = graph_builder.compile()
