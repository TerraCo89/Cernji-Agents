"""
State schemas for the Resume Agent LangGraph implementation.

This module defines the state structure using TypedDict and custom reducers.
The state persists across conversation turns via checkpointing.

Based on Pydantic models from apps/resume-agent/resume_agent.py
"""

from typing import TypedDict, Annotated, Optional, List, Dict, Any, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# ============================================================================
# STATE REDUCERS
# ============================================================================

def append_unique_examples(existing: List[Dict], new: List[Dict]) -> List[Dict]:
    """
    Custom reducer for portfolio_examples field.

    Appends only new unique examples (based on 'id' or 'title' field).
    This prevents duplicate portfolio entries in the state.

    Args:
        existing: Current list of portfolio examples
        new: New portfolio examples to add

    Returns:
        Combined list with only unique examples
    """
    if not existing:
        return new if new else []

    if not new:
        return existing

    # Build set of existing IDs/titles
    existing_ids = set()
    for ex in existing:
        # Try multiple unique identifiers
        if 'id' in ex and ex['id']:
            existing_ids.add(('id', ex['id']))
        elif 'example_id' in ex and ex['example_id']:
            existing_ids.add(('example_id', ex['example_id']))
        elif 'title' in ex and ex['title']:
            existing_ids.add(('title', ex['title']))

    # Filter new examples
    unique_new = []
    for ex in new:
        is_unique = True

        # Check against existing IDs
        if 'id' in ex and ('id', ex['id']) in existing_ids:
            is_unique = False
        elif 'example_id' in ex and ('example_id', ex['example_id']) in existing_ids:
            is_unique = False
        elif 'title' in ex and ('title', ex['title']) in existing_ids:
            is_unique = False

        if is_unique:
            unique_new.append(ex)

    return existing + unique_new


def replace_with_latest(existing: Optional[Dict], new: Optional[Dict]) -> Optional[Dict]:
    """
    Custom reducer that replaces existing value with new value.

    Used for fields like job_analysis where we always want the latest value.

    Args:
        existing: Current value (ignored)
        new: New value to replace with

    Returns:
        The new value
    """
    return new if new is not None else existing


# ============================================================================
# DATA STRUCTURE TYPEDDICTS
# ============================================================================

class PersonalInfoDict(TypedDict, total=False):
    """Personal contact information."""
    name: str
    phone: Optional[str]
    email: Optional[str]
    linkedin: Optional[str]
    title: Optional[str]


class AchievementDict(TypedDict, total=False):
    """Achievement with optional metrics."""
    description: str
    metric: Optional[str]


class EmploymentDict(TypedDict, total=False):
    """Employment history entry."""
    company: str
    position: Optional[str]
    title: Optional[str]
    employment_type: Optional[str]
    start_date: str
    end_date: Optional[str]
    description: str
    technologies: List[str]
    achievements: Optional[List[AchievementDict]]


class MasterResumeDict(TypedDict, total=False):
    """Master resume data structure."""
    personal_info: PersonalInfoDict
    about_me: Optional[str]
    professional_summary: Optional[str]
    employment_history: List[EmploymentDict]


class JobAnalysisDict(TypedDict, total=False):
    """Structured job posting analysis data."""
    url: str
    fetched_at: str  # ISO timestamp
    company: str
    job_title: str
    location: str
    salary_range: Optional[str]
    required_qualifications: List[str]
    preferred_qualifications: List[str]
    responsibilities: List[str]
    keywords: List[str]
    candidate_profile: str
    raw_description: str


class TailoredResumeDict(TypedDict, total=False):
    """Tailored resume content and metadata."""
    company: str
    job_title: str
    content: str
    created_at: str  # ISO timestamp
    keywords_used: List[str]
    changes_from_master: List[str]


class CoverLetterDict(TypedDict, total=False):
    """Cover letter content and metadata."""
    company: str
    job_title: str
    content: str
    created_at: str  # ISO timestamp
    talking_points: List[str]


class PortfolioExampleDict(TypedDict, total=False):
    """Portfolio code example metadata."""
    id: Optional[int]
    example_id: Optional[int]
    title: str
    content: str
    company: Optional[str]
    project: Optional[str]
    description: Optional[str]
    technologies: Optional[List[str]]
    file_paths: Optional[List[str]]
    source_repo: Optional[str]
    repo_url: Optional[str]
    created_at: Optional[str]


# ============================================================================
# WORKFLOW CONTROL TYPES
# ============================================================================

class WorkflowIntent(TypedDict, total=False):
    """User intent classification for workflow routing."""
    intent_type: Literal[
        "analyze_job",
        "tailor_resume",
        "write_cover_letter",
        "find_portfolio",
        "process_website",
        "query_websites",
        "general_chat",
        "full_workflow"
    ]
    confidence: float  # 0.0 to 1.0
    extracted_params: Dict[str, Any]  # e.g., {"job_url": "https://..."}


class WorkflowProgress(TypedDict, total=False):
    """Track progress through multi-step workflows."""
    workflow_type: str  # "full_application", "resume_only", etc.
    steps_completed: List[str]  # ["analyze_job", "tailor_resume", ...]
    steps_remaining: List[str]
    current_step: Optional[str]
    errors: List[str]


# ============================================================================
# MAIN STATE SCHEMA
# ============================================================================

class ResumeAgentState(TypedDict):
    """
    Complete state for Resume Agent LangGraph implementation.

    This state persists across conversation turns via SQLite checkpointing.
    Each field can be updated independently by nodes in the graph.

    Required Fields:
        messages: Conversation history (uses add_messages reducer)

    Optional Fields (job application data):
        job_analysis: Current job being analyzed
        master_resume: User's master resume data
        tailored_resume: Job-specific tailored resume
        cover_letter: Job-specific cover letter
        portfolio_examples: Relevant code examples (append-only with dedup)

    Optional Fields (workflow control):
        current_intent: Classified user intent
        workflow_progress: Multi-step workflow tracking
        requires_user_input: Whether agent is waiting for user input
        error_message: Latest error if any

    Optional Fields (RAG pipeline):
        rag_query_results: Results from website semantic search
        processed_websites: List of processed website metadata
    """

    # ========== REQUIRED FIELDS ==========

    # Conversation history (LangGraph requirement for chat agents)
    # Uses add_messages reducer to append new messages and deduplicate by ID
    messages: Annotated[List[BaseMessage], add_messages]

    # ========== JOB APPLICATION DATA ==========

    # Current job analysis (replace with latest)
    job_analysis: Annotated[
        Optional[JobAnalysisDict],
        replace_with_latest
    ]

    # Master resume (replace with latest)
    master_resume: Annotated[
        Optional[MasterResumeDict],
        replace_with_latest
    ]

    # Tailored resume (replace with latest)
    tailored_resume: Annotated[
        Optional[TailoredResumeDict],
        replace_with_latest
    ]

    # Cover letter (replace with latest)
    cover_letter: Annotated[
        Optional[CoverLetterDict],
        replace_with_latest
    ]

    # Portfolio examples (append unique only)
    portfolio_examples: Annotated[
        List[PortfolioExampleDict],
        append_unique_examples
    ]

    # ========== WORKFLOW CONTROL ==========

    # Current user intent classification
    current_intent: Annotated[
        Optional[WorkflowIntent],
        replace_with_latest
    ]

    # Workflow progress tracking (for multi-step flows)
    workflow_progress: Annotated[
        Optional[WorkflowProgress],
        replace_with_latest
    ]

    # Whether agent needs user input to proceed
    requires_user_input: Annotated[
        bool,
        replace_with_latest
    ]

    # Latest error message (if any)
    error_message: Annotated[
        Optional[str],
        replace_with_latest
    ]

    # ========== RAG PIPELINE DATA ==========

    # Results from semantic website search
    rag_query_results: Annotated[
        Optional[List[Dict[str, Any]]],
        replace_with_latest
    ]

    # Metadata about processed websites
    processed_websites: Annotated[
        Optional[List[Dict[str, Any]]],
        replace_with_latest
    ]

    # ========== METADATA ==========

    # User ID (for multi-user support in future)
    user_id: Annotated[
        str,
        replace_with_latest
    ]


# ============================================================================
# STATE INITIALIZATION HELPERS
# ============================================================================

def create_initial_state(user_id: str = "default") -> ResumeAgentState:
    """
    Create a new initial state for a conversation.

    Args:
        user_id: User identifier (default: "default")

    Returns:
        Initial state dict with required fields populated
    """
    return {
        "messages": [],
        "job_analysis": None,
        "master_resume": None,
        "tailored_resume": None,
        "cover_letter": None,
        "portfolio_examples": [],
        "current_intent": None,
        "workflow_progress": None,
        "requires_user_input": False,
        "error_message": None,
        "rag_query_results": None,
        "processed_websites": None,
        "user_id": user_id,
    }


def update_state(
    current_state: ResumeAgentState,
    **updates: Any
) -> Dict[str, Any]:
    """
    Create a state update dict with only the specified fields.

    This is the recommended way to return state updates from nodes.
    Only include fields that you want to update.

    Args:
        current_state: Current state (for reference, not modified)
        **updates: Field names and new values

    Returns:
        Update dict to be returned from node

    Example:
        return update_state(
            state,
            job_analysis=new_analysis,
            messages=[AIMessage(content="Analysis complete!")]
        )
    """
    return {k: v for k, v in updates.items()}


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_job_analysis_exists(state: ResumeAgentState) -> bool:
    """Check if job analysis exists in state."""
    return state.get("job_analysis") is not None


def validate_master_resume_exists(state: ResumeAgentState) -> bool:
    """Check if master resume exists in state."""
    return state.get("master_resume") is not None


def validate_can_tailor_resume(state: ResumeAgentState) -> bool:
    """Check if prerequisites exist for resume tailoring."""
    return (
        validate_job_analysis_exists(state) and
        validate_master_resume_exists(state)
    )


def validate_can_write_cover_letter(state: ResumeAgentState) -> bool:
    """Check if prerequisites exist for cover letter generation."""
    return (
        validate_job_analysis_exists(state) and
        validate_master_resume_exists(state)
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Main state
    "ResumeAgentState",

    # Data structures
    "PersonalInfoDict",
    "AchievementDict",
    "EmploymentDict",
    "MasterResumeDict",
    "JobAnalysisDict",
    "TailoredResumeDict",
    "CoverLetterDict",
    "PortfolioExampleDict",

    # Workflow control
    "WorkflowIntent",
    "WorkflowProgress",

    # Reducers
    "append_unique_examples",
    "replace_with_latest",

    # Helpers
    "create_initial_state",
    "update_state",

    # Validators
    "validate_job_analysis_exists",
    "validate_master_resume_exists",
    "validate_can_tailor_resume",
    "validate_can_write_cover_letter",
]
