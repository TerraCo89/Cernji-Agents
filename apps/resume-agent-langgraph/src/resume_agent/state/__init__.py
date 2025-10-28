"""
State module for Resume Agent LangGraph implementation.

Exports:
    - ResumeAgentState: Main state schema
    - Data structure TypedDicts
    - Custom reducers
    - Helper functions
"""

from .schemas import (
    # Main state
    ResumeAgentState,

    # Data structures
    PersonalInfoDict,
    AchievementDict,
    EmploymentDict,
    MasterResumeDict,
    JobAnalysisDict,
    TailoredResumeDict,
    CoverLetterDict,
    PortfolioExampleDict,

    # Workflow control
    WorkflowIntent,
    WorkflowProgress,
    JobAnalysisState,

    # Reducers
    append_unique_examples,
    replace_with_latest,

    # Helpers
    create_initial_state,
    update_state,

    # Validators
    validate_job_analysis_exists,
    validate_master_resume_exists,
    validate_can_tailor_resume,
    validate_can_write_cover_letter,
)

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
    "JobAnalysisState",

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
