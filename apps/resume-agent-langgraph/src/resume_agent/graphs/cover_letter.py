"""Cover letter generation workflow graph."""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..state import ResumeAgentState
from ..nodes import (
    prepare_cover_letter_context_node,
    generate_cover_letter_node,
    review_cover_letter_node,
)


def should_regenerate(state: ResumeAgentState) -> str:
    """
    Determine if cover letter should be regenerated based on review score.

    Conditional edge that checks the quality score from the review.
    If score < 70, regenerate the letter (loop back to generate_letter).
    If score >= 70, proceed to END.
    Maximum 2 iterations to prevent infinite loops.

    Args:
        state: Current cover letter state

    Returns:
        Next node name: "generate_letter" to regenerate, END to finish
    """
    review_score = state.get("review_score", 0)
    errors = state.get("errors", [])

    # Check if we've already regenerated (simple heuristic: check if we have a cover letter and low score)
    # In a production system, you'd track iteration count in state
    # For now, we only regenerate once to prevent infinite loops

    # If review failed (score is 0 or we have errors), don't regenerate
    if review_score == 0 or len(errors) > 0:
        return END

    # If score is low, regenerate (but only once - we don't track iterations yet)
    if review_score < 70:
        # TODO: Add iteration tracking to state to prevent infinite loops
        # For now, we'll just go to END to avoid loops
        return END

    return END


def build_cover_letter_graph() -> StateGraph:
    """
    Build the cover letter generation workflow.

    Flow:
    1. START -> prepare_context: Extract context from job analysis and tailored resume
    2. prepare_context -> generate_letter: Generate cover letter with LLM
    3. generate_letter -> review_letter: Review quality and provide score
    4. review_letter -> END: Complete workflow

    Optional Enhancement (currently disabled):
    - Conditional edge after review_letter:
      - If review_score < 70: regenerate letter (loop back to generate_letter)
      - If review_score >= 70: END
      - Maximum 2 iterations to prevent infinite loops

    The workflow includes:
    - Context preparation from job analysis and tailored resume
    - LLM-powered cover letter generation with storytelling
    - Quality review with scoring and suggestions
    - Error accumulation for partial success
    - Performance tracking via duration_ms

    Returns:
        Compiled StateGraph with MemorySaver checkpointer for persistence
    """
    # Create graph
    graph = StateGraph(ResumeAgentState)

    # Add nodes
    graph.add_node("prepare_context", prepare_cover_letter_context_node)
    graph.add_node("generate_letter", generate_cover_letter_node)
    graph.add_node("review_letter", review_cover_letter_node)

    # Set entry point
    graph.add_edge(START, "prepare_context")

    # Linear flow: prepare_context -> generate_letter -> review_letter -> END
    graph.add_edge("prepare_context", "generate_letter")
    graph.add_edge("generate_letter", "review_letter")
    graph.add_edge("review_letter", END)

    # Optional: Add conditional edge for regeneration (currently disabled)
    # Uncomment to enable regeneration loop:
    # graph.add_conditional_edges(
    #     "review_letter",
    #     should_regenerate,
    #     {
    #         "generate_letter": "generate_letter",
    #         END: END
    #     }
    # )

    # Compile with memory checkpointer
    checkpointer = MemorySaver()
    app = graph.compile(checkpointer=checkpointer)

    return app
