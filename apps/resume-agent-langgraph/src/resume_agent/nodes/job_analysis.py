"""Job analysis nodes for LangGraph workflows.

This module provides nodes for fetching, analyzing, and caching job postings.
Each node returns a partial state update dict following LangGraph conventions.

Author: Claude (Anthropic)
License: Experimental
"""

import json
import time
from datetime import datetime

from ..state import JobAnalysisState
from ..llm import call_llm
from ..prompts import JOB_ANALYSIS_PROMPT


# In-memory cache for job analyses (simple implementation for MVP)
# In production, this would use the DAL and database
_job_cache: dict[str, dict] = {}


def check_cache_node(state: JobAnalysisState) -> dict:
    """
    Check if job analysis is already cached.

    This node checks if the job URL has been analyzed before. If found in cache,
    it sets the cached flag and returns the cached analysis, allowing the workflow
    to skip expensive LLM calls.

    Args:
        state: Current job analysis state containing job_url

    Returns:
        Partial state update with:
        - cached: True if found in cache, False otherwise
        - job_analysis: Cached data if available, None otherwise
    """
    job_url = state["job_url"]

    # Check in-memory cache
    if job_url in _job_cache:
        print(f"\n✓ Cache hit for {job_url}")
        return {
            "cached": True,
            "job_analysis": _job_cache[job_url]
        }

    print(f"\n✗ Cache miss for {job_url}")
    return {
        "cached": False,
        "job_analysis": None
    }


def fetch_job_node(state: JobAnalysisState) -> dict:
    """
    Fetch job posting content from URL.

    This node simulates fetching a job posting from a URL. In a production
    implementation, this would use httpx or the web fetch MCP tool to retrieve
    actual job posting content.

    Args:
        state: Current job analysis state containing job_url

    Returns:
        Partial state update with:
        - job_content: Fetched content (placeholder for MVP)
        - errors: Updated error list if fetch fails
        - duration_ms: Time taken to fetch
    """
    start_time = time.time()
    job_url = state["job_url"]

    try:
        print(f"\n📥 Fetching job posting from {job_url}...")

        # TODO: Replace with actual web fetching using httpx or MCP tool
        # For MVP, use placeholder content
        job_content = f"""
        Job Posting from {job_url}

        Company: Example Tech Corp
        Position: Senior Software Engineer

        Requirements:
        - 5+ years of Python experience
        - Experience with LangGraph and LangChain
        - Strong understanding of AI/ML workflows
        - Experience with FastAPI and REST APIs

        Responsibilities:
        - Build and maintain AI agent applications
        - Design and implement LangGraph workflows
        - Collaborate with product team on features
        - Write clean, maintainable code

        Skills:
        Python, LangGraph, LangChain, FastAPI, PostgreSQL, Docker

        Location: Remote
        Salary: $120k - $160k
        """

        duration_ms = (time.time() - start_time) * 1000

        print(f"✓ Job content fetched in {duration_ms:.0f}ms")

        return {
            "job_content": job_content,
            "duration_ms": duration_ms
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to fetch job posting: {str(e)}"
        print(f"\n❌ {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg],
            "duration_ms": duration_ms
        }


def analyze_job_node(state: JobAnalysisState) -> dict:
    """
    Analyze job posting content using LLM.

    This node takes the fetched job content and uses an LLM to extract structured
    information including company name, job title, requirements, skills,
    responsibilities, keywords, etc.

    Args:
        state: Current job analysis state containing job_content and job_url

    Returns:
        Partial state update with:
        - job_analysis: Structured analysis dict with extracted fields
        - errors: Updated error list if analysis fails
    """
    start_time = time.time()

    try:
        print("\n🤖 Analyzing job posting with LLM...")

        job_url = state["job_url"]
        job_content = state.get("job_content", "")

        if not job_content:
            raise ValueError("No job content available to analyze")

        # Format the prompt with job data
        fetched_at = datetime.utcnow().isoformat()
        formatted_prompt = JOB_ANALYSIS_PROMPT.format(
            job_url=job_url,
            job_content=job_content,
            fetched_at=fetched_at
        )

        # Call LLM with the formatted prompt
        messages = [
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]

        # Use minimal system prompt since instructions are in user message
        system_prompt = "You are an expert job posting analyzer. Extract information and return only valid JSON."

        llm_response = call_llm(messages, system_prompt)

        # Parse JSON response
        # Remove markdown code blocks if present
        json_text = llm_response.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()

        job_analysis = json.loads(json_text)

        duration_ms = (time.time() - start_time) * 1000
        print(f"✓ Job analysis completed in {duration_ms:.0f}ms")

        # Cache the result
        _job_cache[job_url] = job_analysis

        return {
            "job_analysis": job_analysis
        }

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        print(f"\n❌ {error_msg}")
        print(f"LLM Response: {llm_response[:200]}...")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }

    except Exception as e:
        error_msg = f"Failed to analyze job posting: {str(e)}"
        print(f"\n❌ {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }
