"""Resume tailoring workflow graph."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..state import ResumeTailoringState
from ..nodes import (
    load_resume_node,
    analyze_requirements_node,
    tailor_resume_node,
    validate_tailoring_node,
)


def build_resume_tailoring_graph() -> StateGraph:
    """
    Build the resume tailoring workflow.

    Flow:
    1. START -> load_resume: Load master resume from default location
    2. load_resume -> analyze_requirements: Extract keywords and calculate initial ATS score
    3. analyze_requirements -> tailor_resume: Use LLM to optimize resume for job
    4. tailor_resume -> validate_tailoring: Calculate final ATS score and validate improvements
    5. validate_tailoring -> END: Complete workflow

    The workflow includes:
    - Master resume loading from shared YAML file
    - Initial ATS score calculation to establish baseline
    - LLM-powered resume tailoring with keyword integration
    - Final ATS score validation to measure improvement
    - Error accumulation for partial success
    - Performance tracking via duration_ms

    All nodes run sequentially without conditional routing (MVP pattern).
    Each node returns partial state updates following LangGraph conventions.

    Returns:
        Compiled StateGraph with MemorySaver checkpointer for persistence
    """
    # Create graph
    graph = StateGraph(ResumeTailoringState)

    # Add nodes
    graph.add_node("load_resume", load_resume_node)
    graph.add_node("analyze_requirements", analyze_requirements_node)
    graph.add_node("tailor_resume", tailor_resume_node)
    graph.add_node("validate_tailoring", validate_tailoring_node)

    # Set entry point
    graph.add_edge(START, "load_resume")

    # Linear flow: load_resume -> analyze_requirements -> tailor_resume -> validate_tailoring -> END
    graph.add_edge("load_resume", "analyze_requirements")
    graph.add_edge("analyze_requirements", "tailor_resume")
    graph.add_edge("tailor_resume", "validate_tailoring")
    graph.add_edge("validate_tailoring", END)

    # Compile with memory checkpointer
    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)

    return app
