#!/usr/bin/env python3
"""
Graph Registry - Central registry for all LangGraph agents

This module provides a centralized way to register and retrieve LangGraph graphs.
Each graph is identified by an assistant_id that matches the Agent Chat UI configuration.
"""

from typing import Dict, Callable, Any


# Graph builder functions registry
# Maps assistant_id -> graph builder function
GRAPH_BUILDERS: Dict[str, Callable[[], Any]] = {}


def register_graph(assistant_id: str):
    """
    Decorator to register a graph builder function.

    Usage:
        @register_graph("resume_agent")
        def build_resume_agent():
            return graph.compile(checkpointer=checkpointer)
    """
    def decorator(builder_func: Callable[[], Any]) -> Callable[[], Any]:
        GRAPH_BUILDERS[assistant_id] = builder_func
        return builder_func
    return decorator


def get_graph(assistant_id: str) -> Any:
    """
    Get a compiled graph by assistant_id.

    Args:
        assistant_id: The graph identifier (e.g., "resume_agent", "minimal_agent")

    Returns:
        Compiled LangGraph graph

    Raises:
        ValueError: If assistant_id is not registered
    """
    builder = GRAPH_BUILDERS.get(assistant_id)
    if not builder:
        available = ", ".join(GRAPH_BUILDERS.keys())
        raise ValueError(
            f"Unknown assistant_id: '{assistant_id}'. "
            f"Available graphs: {available}"
        )

    # Build and return the graph
    return builder()


def list_graphs() -> list[str]:
    """
    List all registered graph IDs.

    Returns:
        List of assistant_ids
    """
    return list(GRAPH_BUILDERS.keys())


# Import and register all graphs
# This happens when the module is imported
from resume_agent_langgraph import build_web_conversation_graph
from minimal_agent import build_graph


# Register graphs with their assistant_ids
@register_graph("resume_agent")
def _build_resume_agent():
    """Build the Minimal Agent graph (working example)"""
    return build_graph()


@register_graph("minimal_agent")
def _build_minimal_agent():
    """Build the Minimal Agent graph (for testing)"""
    return build_graph()


# Future graphs can be registered here:
# @register_graph("japanese_tutor")
# def _build_japanese_tutor():
#     from japanese_tutor import build_graph
#     return build_graph()
