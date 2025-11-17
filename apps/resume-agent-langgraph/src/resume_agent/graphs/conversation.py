"""Conversational agent graph."""

from langgraph.graph import StateGraph, START, END

# Use absolute imports (required for LangGraph server)
from resume_agent.state import ResumeAgentState
from resume_agent.nodes import chat_node, get_user_input_node


def should_continue(state: ResumeAgentState) -> str:
    """
    Determine if conversation should continue.

    Args:
        state: Current conversation state

    Returns:
        Next node name: "chat" to continue, END to stop
    """
    if state.get("should_continue", True):
        return "chat"
    return END


def build_conversation_graph() -> StateGraph:
    """
    Build the conversational agent workflow.

    Flow:
    1. START -> get_input: Get user message
    2. get_input -> chat: Process with LLM (conditional: continue if not exit)
    3. chat -> get_input: Loop back for next message

    Returns:
        Compiled StateGraph with checkpointer
    """
    # Create graph
    graph = StateGraph(ResumeAgentState)

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

    # Compile (LangGraph server provides automatic persistence)
    app = graph.compile()

    return app


# ==============================================================================
# Export (Required for LangGraph Server)
# ==============================================================================

# Export compiled graph for langgraph.json to discover this agent
graph = build_conversation_graph()
