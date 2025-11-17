"""Portfolio Finder Agent - Self-Contained Example (~180 lines)

A complete, production-ready LangGraph agent demonstrating the progressive
disclosure pattern from /prime-agentic-systems.

This file contains EVERYTHING needed for the Portfolio Finder agent:
- State schema (TypedDict)
- Tools (embedded in this file)
- Nodes (embedded in this file)
- Graph definition and routing
- Compilation and export

This is a TEMPLATE - copy this file and adapt it for your own agents.

Usage:
    1. Add to langgraph.json:
       "portfolio_finder": "./src/resume_agent/graphs/portfolio_finder.py:graph"

    2. Test standalone:
       python -m resume_agent.graphs.portfolio_finder

    3. Use from Agent Chat UI:
       Select "Portfolio Finder" from agent dropdown
"""

from __future__ import annotations

import os
from typing import TypedDict, Annotated, Optional, List, Dict, Any

from langchain_core.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==============================================================================
# State Schema
# ==============================================================================

class PortfolioFinderState(TypedDict, total=False):
    """State for portfolio finder workflow.

    Uses TypedDict (not Pydantic) for msgpack serialization compatibility.
    """
    # Conversation
    messages: Annotated[List[BaseMessage], "Conversation history"]

    # Input
    technologies: Optional[List[str]]  # Technologies to search for
    github_username: Optional[str]     # Optional: filter by specific user

    # Results
    portfolio_examples: Optional[List[Dict[str, Any]]]
    search_complete: bool

    # Error handling
    errors: List[str]


# ==============================================================================
# Tools (Embedded in this file)
# ==============================================================================

@tool
def search_github_repos(
    technologies: List[str],
    username: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Search GitHub for code examples matching technologies.

    Args:
        technologies: List of technologies/languages to search for
        username: Optional GitHub username to filter by

    Returns:
        List of portfolio examples with repo info and code snippets
    """
    # Implementation would call GitHub API
    # For this example, return mock data
    examples = []

    for tech in technologies:
        examples.append({
            "technology": tech,
            "repo_name": f"example-{tech.lower()}-project",
            "repo_url": f"https://github.com/{username or 'user'}/example-{tech.lower()}-project",
            "description": f"Production {tech} application with best practices",
            "stars": 42,
            "code_snippet": f"// Example {tech} code\nfunction main() {{\n  // Implementation\n}}",
            "relevance_score": 0.85
        })

    return examples


# ==============================================================================
# Nodes (Embedded in this file)
# ==============================================================================

def extract_search_params_node(state: PortfolioFinderState) -> Dict[str, Any]:
    """Extract search parameters from user message.

    This node analyzes the conversation to determine what technologies
    the user is looking for portfolio examples of.

    Args:
        state: Current state with messages

    Returns:
        State update with extracted technologies
    """
    # In production, this would use LLM to extract technologies
    # from the conversation. For this example, use a simple extraction.

    last_message = state["messages"][-1]
    message_text = last_message.content.lower()

    # Simple keyword extraction (replace with LLM in production)
    tech_keywords = ["python", "typescript", "react", "langgraph", "fastapi"]
    found_techs = [tech for tech in tech_keywords if tech in message_text]

    if not found_techs:
        return {
            "errors": ["Could not determine which technologies to search for. Please specify technologies explicitly."]
        }

    return {
        "technologies": found_techs,
        "errors": []
    }


def search_portfolio_node(state: PortfolioFinderState) -> Dict[str, Any]:
    """Search GitHub for portfolio examples.

    Args:
        state: State with technologies to search for

    Returns:
        State update with portfolio examples
    """
    technologies = state.get("technologies", [])

    if not technologies:
        return {
            "errors": ["No technologies specified for search"],
            "search_complete": True
        }

    try:
        # Call the search tool
        examples = search_github_repos(
            technologies=technologies,
            username=state.get("github_username")
        )

        return {
            "portfolio_examples": examples,
            "search_complete": True,
            "errors": []
        }

    except Exception as e:
        return {
            "errors": [f"Portfolio search failed: {str(e)}"],
            "search_complete": True
        }


def format_results_node(state: PortfolioFinderState) -> Dict[str, Any]:
    """Format portfolio search results as user message.

    Args:
        state: State with portfolio_examples

    Returns:
        State update with formatted message
    """
    examples = state.get("portfolio_examples", [])

    if not examples:
        message = AIMessage(
            content="No portfolio examples found matching your criteria. Try different technologies."
        )
        return {"messages": [message]}

    # Build formatted response
    response_parts = [
        f"✅ **Found {len(examples)} Portfolio Examples**\n"
    ]

    for example in examples[:5]:  # Show first 5
        response_parts.append(
            f"**{example['technology']}** - {example['repo_name']}\n"
            f"⭐ {example['stars']} stars | Relevance: {int(example['relevance_score'] * 100)}%\n"
            f"📦 {example['description']}\n"
            f"🔗 {example['repo_url']}\n"
        )

    if len(examples) > 5:
        response_parts.append(f"\n... and {len(examples) - 5} more examples")

    message = AIMessage(content="\n".join(response_parts))

    return {"messages": [message]}


def format_error_node(state: PortfolioFinderState) -> Dict[str, Any]:
    """Format error message for user.

    Args:
        state: State with errors

    Returns:
        State update with error message
    """
    errors = state.get("errors", [])
    error_text = "\n".join([f"❌ {error}" for error in errors])

    message = AIMessage(
        content=f"**Portfolio Search Failed**\n\n{error_text}\n\nPlease try again with different parameters."
    )

    return {
        "messages": [message],
        "errors": []  # Clear errors after displaying
    }


# ==============================================================================
# Routing Logic
# ==============================================================================

def route_after_extract(state: PortfolioFinderState) -> str:
    """Route after parameter extraction.

    Args:
        state: State with technologies or errors

    Returns:
        Next node: 'search' if successful, 'format_error' if failed
    """
    if state.get("errors"):
        return "format_error"
    return "search"


def route_after_search(state: PortfolioFinderState) -> str:
    """Route after portfolio search.

    Args:
        state: State with results or errors

    Returns:
        Next node: 'format_results' if successful, 'format_error' if failed
    """
    if state.get("errors"):
        return "format_error"
    return "format_results"


# ==============================================================================
# Graph Construction
# ==============================================================================

def build_portfolio_finder_graph():
    """Build portfolio finder agent graph.

    Flow:
        START
          ↓
        extract_params (extract technologies from message)
          ↓
        [conditional]
          ├─→ search (search GitHub for examples)
          │     ↓
          │   format_results (format as user message)
          │     ↓
          │   END
          │
          └─→ format_error (show error to user)
                ↓
              END

    Returns:
        Compiled StateGraph with MemorySaver checkpointer
    """
    # Initialize graph
    graph = StateGraph(PortfolioFinderState)

    # Add nodes
    graph.add_node("extract_params", extract_search_params_node)
    graph.add_node("search", search_portfolio_node)
    graph.add_node("format_results", format_results_node)
    graph.add_node("format_error", format_error_node)

    # Define flow
    graph.add_edge(START, "extract_params")

    graph.add_conditional_edges(
        "extract_params",
        route_after_extract,
        {
            "search": "search",
            "format_error": "format_error"
        }
    )

    graph.add_conditional_edges(
        "search",
        route_after_search,
        {
            "format_results": "format_results",
            "format_error": "format_error"
        }
    )

    graph.add_edge("format_results", END)
    graph.add_edge("format_error", END)

    # Compile with checkpointing for conversation persistence
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# ==============================================================================
# Export (Required for LangGraph Server)
# ==============================================================================

# This line is REQUIRED for langgraph.json to discover this agent
graph = build_portfolio_finder_graph()


# ==============================================================================
# Standalone Testing (Optional)
# ==============================================================================

if __name__ == "__main__":
    """Test the agent standalone (without LangGraph server)."""
    import sys

    # Build graph
    test_graph = build_portfolio_finder_graph()

    # Test query
    query = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "Find my Python and LangGraph portfolio examples"
    )

    # Invoke graph
    result = test_graph.invoke(
        {"messages": [HumanMessage(content=query)]},
        config={"configurable": {"thread_id": "test-thread-1"}}
    )

    # Print results
    print("\n" + "="*60)
    print("PORTFOLIO FINDER TEST")
    print("="*60)
    print(f"\nQuery: {query}\n")

    # Extract response
    last_message = result["messages"][-1]
    print(f"Response:\n{last_message.content}\n")

    if result.get("portfolio_examples"):
        print(f"\nFound {len(result['portfolio_examples'])} examples")
        for ex in result["portfolio_examples"]:
            print(f"  - {ex['technology']}: {ex['repo_url']}")

    print("\n" + "="*60)
