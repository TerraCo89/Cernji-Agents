"""
Main Resume Agent graph definition.

Orchestrates the complete resume optimization workflow.
"""

from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from ..state import ResumeState
from ..nodes import (
    analyze_job_posting,
    analyze_resume,
    optimize_resume_sections,
    score_resume,
    validate_resume,
    await_reviewer_approval,
    finalize_resume,
)
from ..config import get_settings


def should_iterate(state: ResumeState) -> Literal["optimize", "validate"]:
    """
    Decide if we should iterate on optimization or move to validation.
    
    Args:
        state: Current state
        
    Returns:
        Next node name
    """
    settings = get_settings()
    
    # Check if we've reached max iterations
    if state['iteration_count'] >= state['max_iterations']:
        return "validate"
    
    # Check if ATS score is good enough
    if state.get('ats_score', 0) >= settings.ats_score_threshold:
        return "validate"
    
    # Otherwise, iterate
    return "optimize"


def should_review(state: ResumeState) -> Literal["await_approval", "finalize"]:
    """
    Decide if manual review is needed.
    
    Args:
        state: Current state
        
    Returns:
        Next node name
    """
    settings = get_settings()
    
    if settings.require_manual_review or state.get('needs_manual_review', False):
        return "await_approval"
    
    return "finalize"


def increment_iteration(state: ResumeState) -> dict:
    """Helper node to increment iteration counter."""
    return {"iteration_count": state.get('iteration_count', 0) + 1}


def create_resume_agent_graph() -> StateGraph:
    """
    Create the main Resume Agent graph.
    
    Returns:
        Compiled LangGraph application
    """
    # Initialize graph
    graph = StateGraph(ResumeState)
    
    # Add all nodes
    graph.add_node("analyze_job", analyze_job_posting)
    graph.add_node("analyze_resume", analyze_resume)
    graph.add_node("optimize", optimize_resume_sections)
    graph.add_node("score", score_resume)
    graph.add_node("increment_iteration", increment_iteration)
    graph.add_node("validate", validate_resume)
    graph.add_node("await_approval", await_reviewer_approval)
    graph.add_node("finalize", finalize_resume)
    
    # Define the flow
    graph.add_edge(START, "analyze_job")
    graph.add_edge("analyze_job", "analyze_resume")
    graph.add_edge("analyze_resume", "optimize")
    graph.add_edge("optimize", "score")
    graph.add_edge("score", "increment_iteration")
    
    # Conditional: iterate or validate?
    graph.add_conditional_edges(
        "increment_iteration",
        should_iterate,
        {
            "optimize": "optimize",  # Loop back
            "validate": "validate",
        }
    )
    
    # Conditional: manual review needed?
    graph.add_conditional_edges(
        "validate",
        should_review,
        {
            "await_approval": "await_approval",
            "finalize": "finalize",
        }
    )
    
    graph.add_edge("await_approval", "finalize")
    graph.add_edge("finalize", END)
    
    return graph


def compile_resume_agent(checkpointing: bool = True):
    """
    Compile the Resume Agent graph with optional checkpointing.
    
    Args:
        checkpointing: Whether to enable state persistence
        
    Returns:
        Compiled graph application
    """
    graph = create_resume_agent_graph()
    
    if checkpointing:
        checkpointer = MemorySaver()
        return graph.compile(
            checkpointer=checkpointer,
            interrupt_before=["await_approval"]  # Pause for human review
        )
    
    return graph.compile()


# Convenience function for direct execution
def run_resume_agent(
    resume_text: str,
    job_posting_url: str,
    thread_id: str = "default",
    max_iterations: int = 3,
) -> dict:
    """
    Run the resume agent end-to-end.
    
    Args:
        resume_text: The original resume content
        job_posting_url: URL of the job posting
        thread_id: Unique identifier for this session
        max_iterations: Maximum optimization iterations
        
    Returns:
        Final state after processing
    """
    app = compile_resume_agent(checkpointing=True)
    
    # Initial state
    initial_state = {
        "resume_text": resume_text,
        "job_posting_url": job_posting_url,
        "job_title": "",
        "job_requirements": [],
        "job_skills": [],
        "ats_keywords": [],
        "current_skills": [],
        "experience_summary": "",
        "skill_gaps": [],
        "optimized_sections": [],
        "ats_score": 0,
        "optimization_suggestions": [],
        "needs_manual_review": False,
        "reviewer_approved": False,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "final_resume": "",
        "cover_letter": "",
    }
    
    # Execute until checkpoint (manual review)
    config = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(initial_state, config=config)
    
    print("\n" + "="*60)
    print("⏸️  Execution paused for manual review")
    print(f"   Thread ID: {thread_id}")
    print("   To continue: app.invoke(None, config={'configurable': {'thread_id': 'YOUR_THREAD_ID'}})")
    print("="*60)
    
    return result


def resume_from_checkpoint(thread_id: str) -> dict:
    """
    Resume execution from a checkpoint.
    
    Args:
        thread_id: The thread ID to resume
        
    Returns:
        Final state after completion
    """
    app = compile_resume_agent(checkpointing=True)
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"\n▶️  Resuming execution for thread: {thread_id}")
    result = app.invoke(None, config=config)
    
    print("\n" + "="*60)
    print("✅ Resume optimization complete!")
    print(f"   Final ATS Score: {result['ats_score']}/100")
    print("="*60)
    
    return result
