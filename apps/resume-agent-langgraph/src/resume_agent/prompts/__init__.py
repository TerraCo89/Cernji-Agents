"""Prompt templates for Resume Agent LangGraph.

This package contains all system prompts and prompt templates used throughout
the application. Importing from this package provides access to all prompts
via a clean, centralized interface.

Example:
    from resume_agent.prompts import SYSTEM_RESUME_AGENT, JOB_ANALYSIS_PROMPT
"""

from .templates import (
    SYSTEM_RESUME_AGENT,
    SYSTEM_JOB_ANALYZER,
    SYSTEM_RESUME_EXPERT,
    CONVERSATION_SYSTEM,
    JOB_ANALYSIS_PROMPT,
    RESUME_TAILORING_PROMPT,
    COVER_LETTER_PROMPT,
    COVER_LETTER_REVIEW_PROMPT,
)

__all__ = [
    "SYSTEM_RESUME_AGENT",
    "SYSTEM_JOB_ANALYZER",
    "SYSTEM_RESUME_EXPERT",
    "CONVERSATION_SYSTEM",
    "JOB_ANALYSIS_PROMPT",
    "RESUME_TAILORING_PROMPT",
    "COVER_LETTER_PROMPT",
    "COVER_LETTER_REVIEW_PROMPT",
]
