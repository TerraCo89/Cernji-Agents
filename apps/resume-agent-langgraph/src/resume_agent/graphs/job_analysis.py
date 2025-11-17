"""Job analysis workflow graph."""

from langgraph.graph import StateGraph, START, END

# Use absolute imports (required for LangGraph server)
from resume_agent.state import JobAnalysisState
from resume_agent.nodes import check_cache_node, fetch_job_node, analyze_job_node


def should_fetch(state: JobAnalysisState) -> str:
    """
    Determine if job content should be fetched.

    Conditional edge that checks whether the job analysis is already cached.
    If cached, skip directly to END. Otherwise, proceed to fetch_job.

    Args:
        state: Current job analysis state

    Returns:
        Next node name: "fetch_job" to fetch and analyze, END to skip
    """
    if state.get("cached", False):
        return END
    return "fetch_job"


def build_job_analysis_graph() -> StateGraph:
    """
    Build the job analysis workflow.

    Flow:
    1. START -> check_cache: Check for cached job analysis
    2. check_cache -> (conditional):
       - If cached: go to END (skip analysis)
       - If not cached: go to fetch_job
    3. fetch_job -> analyze_job: Fetch job posting and analyze
    4. analyze_job -> END: Complete workflow

    The workflow includes:
    - Cache lookup to avoid redundant API calls
    - Job content fetching from URL
    - Claude-powered analysis to extract structured job requirements
    - Error accumulation for partial success
    - Performance tracking via duration_ms

    Returns:
        Compiled StateGraph with MemorySaver checkpointer for persistence
    """
    # Create graph
    graph = StateGraph(JobAnalysisState)

    # Add nodes
    graph.add_node("check_cache", check_cache_node)
    graph.add_node("fetch_job", fetch_job_node)
    graph.add_node("analyze_job", analyze_job_node)

    # Set entry point
    graph.add_edge(START, "check_cache")

    # Add conditional edge after check_cache
    graph.add_conditional_edges(
        "check_cache",
        should_fetch,
        {
            "fetch_job": "fetch_job",
            END: END
        }
    )

    # Linear flow: fetch_job -> analyze_job -> END
    graph.add_edge("fetch_job", "analyze_job")
    graph.add_edge("analyze_job", END)

    # Compile (LangGraph server provides automatic persistence)
    app = graph.compile()

    return app


# ==============================================================================
# Export (Required for LangGraph Server)
# ==============================================================================

# Export compiled graph for langgraph.json to discover this agent
graph = build_job_analysis_graph()
