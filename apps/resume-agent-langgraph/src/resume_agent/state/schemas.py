"""State schemas for Resume Agent workflows."""

from typing import TypedDict, Annotated
from operator import add


class ConversationState(TypedDict):
    """State for conversational agent."""
    messages: Annotated[list[dict], add]  # Append-only chat history
    should_continue: bool                 # Whether to continue conversation


class JobAnalysisState(TypedDict):
    """State for job analysis workflow."""
    job_url: str                         # Input: Job posting URL
    job_content: str | None              # Intermediate: Fetched job content
    job_analysis: dict | None            # Output: Structured analysis
    cached: bool                         # Whether result was cached
    errors: list[str]                    # Error accumulation
    duration_ms: float | None            # Performance tracking


class ResumeTailoringState(TypedDict):
    """State for resume tailoring workflow."""
    job_url: str                         # Input: Job posting URL
    master_resume: dict | None           # Input: Master resume data
    job_analysis: dict | None            # Dependency: Job analysis
    initial_ats_score: dict | None       # Intermediate: Initial ATS score
    tailored_resume: str | None          # Output: Tailored resume
    final_ats_score: dict | None         # Output: Final ATS score
    keywords_integrated: list[str]       # Output: Keywords used
    errors: list[str]                    # Error accumulation
    duration_ms: float | None            # Performance tracking


class CoverLetterState(TypedDict):
    """State for cover letter generation workflow."""
    job_url: str                         # Input: Job posting URL
    job_analysis: dict | None            # Dependency: Job analysis
    tailored_resume: str | None          # Dependency: Tailored resume
    context: dict | None                 # Intermediate: Prepared context
    cover_letter: str | None             # Output: Generated cover letter
    review_score: int | None             # Output: Quality score (0-100)
    suggestions: list[str]               # Output: Improvement suggestions
    errors: list[str]                    # Error accumulation
    duration_ms: float | None            # Performance tracking
