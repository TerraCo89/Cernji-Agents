"""
State schemas for the Resume Agent.

All state definitions use TypedDict with Annotated for proper type checking
and state reduction strategies.
"""

from typing import TypedDict, Annotated, Literal
from operator import add


class ResumeState(TypedDict):
    """Main state for resume optimization workflow."""
    
    # Input
    resume_text: str
    job_posting_url: str
    
    # Job Analysis
    job_title: str
    job_requirements: list[str]
    job_skills: list[str]
    ats_keywords: list[str]
    
    # Resume Analysis
    current_skills: list[str]
    experience_summary: str
    skill_gaps: list[str]
    
    # Optimization
    optimized_sections: Annotated[list[dict], add]  # Append-only
    ats_score: int
    optimization_suggestions: list[str]
    
    # Control Flow
    needs_manual_review: bool
    reviewer_approved: bool
    iteration_count: int
    max_iterations: int
    
    # Output
    final_resume: str
    cover_letter: str


class JobAnalysisState(TypedDict):
    """Subgraph state for job posting analysis."""
    
    url: str
    raw_html: str
    company_name: str
    job_title: str
    requirements: list[str]
    skills: list[str]
    keywords: list[str]
    salary_range: str
    location: str


class SectionOptimizationState(TypedDict):
    """Subgraph state for optimizing individual resume sections."""
    
    section_name: Literal["summary", "experience", "skills", "education"]
    original_text: str
    target_keywords: list[str]
    optimized_text: str
    ats_improvement: int


class ValidationState(TypedDict):
    """State for resume validation checks."""
    
    resume_text: str
    validation_errors: Annotated[list[str], add]
    validation_warnings: Annotated[list[str], add]
    is_valid: bool
