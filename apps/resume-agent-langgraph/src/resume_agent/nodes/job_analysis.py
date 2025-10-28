"""Job analysis nodes for LangGraph workflows.

This module provides nodes for fetching, analyzing, and caching job postings.
Each node returns a partial state update dict following LangGraph conventions.

Author: Claude (Anthropic)
License: Experimental
"""

import json
import time
import asyncio
from datetime import datetime

from ..state import JobAnalysisState
from ..llm import call_llm
from ..prompts import JOB_ANALYSIS_PROMPT
from ..tools.browser_automation import scrape_job_posting


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
        print(f"\n[OK] Cache hit for {job_url}")
        return {
            "cached": True,
            "job_analysis": _job_cache[job_url]
        }

    print(f"\n[MISS] Cache miss for {job_url}")
    return {
        "cached": False,
        "job_analysis": None
    }


async def fetch_job_node(state: JobAnalysisState) -> dict:
    """
    Fetch job posting content from URL using browser automation.

    Uses Playwright-based browser automation to scrape job postings from
    JavaScript-heavy websites. Automatically detects site type (japan-dev,
    recruit, or generic) and uses appropriate scraper.

    IMPORTANT: On Windows, runs browser automation in thread pool to avoid
    asyncio subprocess limitations (NotImplementedError with ProactorEventLoop).

    Args:
        state: Current job analysis state containing job_url

    Returns:
        Partial state update with:
        - job_content: Fetched and structured content
        - errors: Updated error list if fetch fails
        - duration_ms: Time taken to fetch
    """
    start_time = time.time()
    job_url = state["job_url"]

    try:
        print(f"\n[FETCH] Fetching job posting from {job_url}...")

        # Detect site type from URL
        if "japan-dev.com" in job_url:
            site_type = "japan-dev"
        elif "recruit.legalontech.jp" in job_url:
            site_type = "recruit"
        else:
            site_type = "generic"

        # Run browser automation in thread pool (Windows workaround)
        # Windows ProactorEventLoop doesn't support subprocess pipes
        import sys
        if sys.platform == "win32":
            # Windows: Run in thread pool with its own event loop
            job_data = await asyncio.to_thread(
                _scrape_job_sync,
                job_url,
                site_type,
                max_retries=3,
                timeout_seconds=60
            )
        else:
            # Unix: Can use async directly
            job_data = await scrape_job_posting(
                job_url,
                site_type=site_type,
                max_retries=3,
                timeout_seconds=60
            )

        # Format structured data into text for LLM analysis
        job_content = _format_job_data_as_text(job_data, job_url)

        duration_ms = (time.time() - start_time) * 1000
        print(f"[OK] Job content fetched in {duration_ms:.0f}ms")

        return {
            "job_content": job_content,
            "duration_ms": duration_ms
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to fetch job posting: {str(e)}"
        print(f"\n[ERROR] {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg],
            "duration_ms": duration_ms
        }


def _scrape_job_sync(url: str, site_type: str, max_retries: int = 3, timeout_seconds: int = 60):
    """
    Synchronous wrapper for browser scraping (thread pool execution on Windows).

    Creates a new event loop in the thread to run async Playwright operations,
    avoiding Windows asyncio subprocess limitations with ProactorEventLoop.

    Args:
        url: Job posting URL
        site_type: Site identifier (japan-dev, recruit, generic)
        max_retries: Maximum retry attempts
        timeout_seconds: Timeout per attempt in seconds

    Returns:
        Structured job data dictionary (JobPostingData)
    """
    # Create dedicated event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # Run async scraper in this thread's event loop
        return loop.run_until_complete(
            scrape_job_posting(
                url,
                site_type=site_type,
                max_retries=max_retries,
                timeout_seconds=timeout_seconds
            )
        )
    finally:
        loop.close()


def _format_job_data_as_text(job_data: dict, job_url: str) -> str:
    """
    Format structured job data into text for LLM analysis.

    Args:
        job_data: Structured job data from browser scraper
        job_url: Original job URL

    Returns:
        Formatted text representation of job posting
    """
    # Build formatted text from structured data
    parts = [f"Job Posting from {job_url}\n"]

    if job_data.get("company_name"):
        parts.append(f"Company: {job_data['company_name']}")

    if job_data.get("job_title"):
        parts.append(f"Position: {job_data['job_title']}")

    if job_data.get("location"):
        parts.append(f"Location: {job_data['location']}")

    if job_data.get("employment_type"):
        parts.append(f"Employment Type: {job_data['employment_type']}")

    if job_data.get("salary_range"):
        parts.append(f"Salary: {job_data['salary_range']}")

    if job_data.get("job_description"):
        parts.append(f"\nDescription:\n{job_data['job_description']}")

    if job_data.get("requirements"):
        parts.append("\nRequirements:")
        for req in job_data["requirements"]:
            parts.append(f"- {req}")

    if job_data.get("application_url"):
        parts.append(f"\nApplication: {job_data['application_url']}")

    if job_data.get("posted_date"):
        parts.append(f"Posted: {job_data['posted_date']}")

    return "\n".join(parts)


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
        print(f"[OK] Job analysis completed in {duration_ms:.0f}ms")

        # Cache the result
        _job_cache[job_url] = job_analysis

        return {
            "job_analysis": job_analysis
        }

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        print(f"\n[ERROR] {error_msg}")
        print(f"LLM Response: {llm_response[:200]}...")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }

    except Exception as e:
        error_msg = f"Failed to analyze job posting: {str(e)}"
        print(f"\n[ERROR] {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }
