"""
Browser Automation Tools for Job Scraping
==========================================

LangChain PlayWrightBrowserToolkit integration for scraping JavaScript-heavy
job posting websites.

Key Features:
- Async browser lifecycle management
- Site-specific scrapers (Japan Dev, Recruit, etc.)
- LLM-powered data extraction via ReAct agent
- Robust error handling with retries

Architecture:
    Browser Context Manager → Toolkit → ReAct Agent → Data Extraction

Example:
    async with create_browser_context() as browser:
        data = await scrape_japan_dev_job(browser, url)
"""

import asyncio

from typing import TypedDict, Optional, Literal
from contextlib import asynccontextmanager
from langchain_core.messages import HumanMessage
from langchain_community.agent_toolkits import PlayWrightBrowserToolkit
from langchain_community.tools.playwright.utils import (
    create_async_playwright_browser,
)
from langgraph.prebuilt import create_react_agent
from langchain_anthropic import ChatAnthropic

from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# Type Definitions
# ============================================================================


class JobPostingData(TypedDict, total=False):
    """Structured data extracted from job posting"""

    job_title: str
    company_name: str
    location: str
    job_description: str
    requirements: list[str]
    salary_range: Optional[str]
    application_url: str
    posted_date: Optional[str]
    employment_type: Optional[str]  # Full-time, Contract, etc.


# ============================================================================
# Browser Lifecycle Management
# ============================================================================


@asynccontextmanager
async def create_browser_context(headless: bool = True):
    """
    Async context manager for browser lifecycle.

    Ensures proper cleanup even if scraping fails.

    Args:
        headless: Run browser in headless mode (no GUI)

    Yields:
        Playwright browser instance

    Example:
        async with create_browser_context() as browser:
            toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
            # ... use toolkit
    """
    from playwright.async_api import async_playwright

    playwright = None
    browser = None
    try:
        # Use async_playwright directly to avoid event loop conflicts
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=headless)
        yield browser
    finally:
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


# ============================================================================
# Core Scraper Agent
# ============================================================================


async def create_scraper_agent(browser, use_checkpointing: bool = False):
    """
    Create a ReAct agent with browser tools for job scraping.

    Uses PlayWrightBrowserToolkit to provide 7 pre-built browser tools:
    - navigate_browser: Navigate to URLs with wait_until support
    - click_element: Click on page elements
    - extract_text: Extract text from specific elements
    - get_elements: Find elements matching criteria
    - extract_hyperlinks: Get all links from page
    - get_current_page: Get current page state
    - navigate_back: Go back to previous page

    The agent uses Claude Sonnet 4.5 for intelligent tool selection and
    multi-step reasoning for complex scraping workflows.

    Args:
        browser: Async Playwright browser instance from create_async_playwright_browser()
        use_checkpointing: Enable conversation memory across multiple invocations.
                          WARNING: Playwright Page objects are not serializable.
                          Only use if you're maintaining the browser instance
                          across multiple agent invocations within the same session.

    Returns:
        Compiled LangGraph ReAct agent with browser tools

    Example:
        >>> async with create_browser_context() as browser:
        ...     agent = await create_scraper_agent(browser)
        ...     result = await agent.ainvoke({
        ...         "messages": [HumanMessage(content="Navigate to example.com")]
        ...     })
    """
    # Initialize toolkit with 7 browser tools
    toolkit = PlayWrightBrowserToolkit.from_browser(async_browser=browser)
    tools = toolkit.get_tools()

    # Initialize LLM (Claude Sonnet 4.5 for best reasoning on complex scraping tasks)
    import os

    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Please set it in your .env file or environment."
        )

    llm = ChatAnthropic(
        model="claude-sonnet-4-5",
        temperature=0,  # Deterministic for reliable extraction
        api_key=api_key
    )

    # Create ReAct agent - automatically handles tool routing and execution
    # Note: Page objects are not serializable, so checkpointing should only be used
    # if browser session persists across invocations
    if use_checkpointing:
        from langgraph.checkpoint.memory import MemorySaver

        checkpointer = MemorySaver()
        agent = create_react_agent(model=llm, tools=tools, checkpointer=checkpointer)
    else:
        # Default: No checkpointing (recommended for most use cases)
        agent = create_react_agent(model=llm, tools=tools)

    return agent


# ============================================================================
# Error Handling and Retry Logic
# ============================================================================


async def retry_with_exponential_backoff(
    func, max_retries: int = 3, initial_delay: float = 1.0, *args, **kwargs
):
    """
    Retry async function with exponential backoff.

    Handles transient failures (network issues, page load timeouts, etc.)
    with increasing delays between attempts.

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles each retry)
        *args, **kwargs: Arguments to pass to func

    Returns:
        Result from successful func() call

    Raises:
        Last exception if all retries fail

    Example:
        data = await retry_with_exponential_backoff(
            scrape_japan_dev_job,
            max_retries=3,
            url="https://japan-dev.com/jobs/123"
        )
    """
    import asyncio

    last_exception = None

    for attempt in range(max_retries):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = initial_delay * (2**attempt)  # Exponential backoff
                print(
                    f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. Retrying in {delay}s..."
                )
                await asyncio.sleep(delay)
            else:
                print(f"All {max_retries} attempts failed. Last error: {str(e)}")

    raise last_exception  # type: ignore


# ============================================================================
# Response Parsing Utilities
# ============================================================================


def _parse_job_posting_response(llm_response: str) -> JobPostingData:
    """
    Parse LLM's structured response into JobPostingData dictionary.

    Expected format:
        JOB_TITLE: Software Engineer
        COMPANY: Example Corp
        LOCATION: Tokyo, Japan
        DESCRIPTION: We are looking for...
        REQUIREMENTS:
        - Python 3+ years
        - Django experience
        SALARY: ¥5M - ¥8M
        APPLICATION_URL: https://example.com/apply
        POSTED_DATE: 2025-10-20
        EMPLOYMENT_TYPE: Full-time

    Args:
        llm_response: Raw LLM response text

    Returns:
        Structured JobPostingData dict

    Note:
        This uses simple regex parsing. For production, consider using
        LLM-powered structured output (e.g., instructor library with Pydantic).
    """
    import re

    job_data: JobPostingData = {}

    # Extract single-line fields using regex
    patterns = {
        "job_title": r"JOB_TITLE:\s*(.+?)(?:\n|$)",
        "company_name": r"COMPANY:\s*(.+?)(?:\n|$)",
        "location": r"LOCATION:\s*(.+?)(?:\n|$)",
        "salary_range": r"SALARY:\s*(.+?)(?:\n|$)",
        "application_url": r"APPLICATION_URL:\s*(.+?)(?:\n|$)",
        "posted_date": r"POSTED_DATE:\s*(.+?)(?:\n|$)",
        "employment_type": r"EMPLOYMENT_TYPE:\s*(.+?)(?:\n|$)",
    }

    for field, pattern in patterns.items():
        match = re.search(pattern, llm_response, re.IGNORECASE)
        if match:
            value = match.group(1).strip()
            # Handle "Not specified" values
            if value.lower() != "not specified":
                job_data[field] = value  # type: ignore

    # Extract multi-line description
    desc_match = re.search(
        r"DESCRIPTION:\s*(.+?)(?=REQUIREMENTS:|SALARY:|$)", llm_response, re.DOTALL | re.IGNORECASE
    )
    if desc_match:
        job_data["job_description"] = desc_match.group(1).strip()

    # Extract requirements list
    req_match = re.search(
        r"REQUIREMENTS:\s*(.+?)(?=SALARY:|APPLICATION_URL:|POSTED_DATE:|EMPLOYMENT_TYPE:|$)",
        llm_response,
        re.DOTALL | re.IGNORECASE,
    )
    if req_match:
        # Parse bullet points
        requirements_text = req_match.group(1).strip()
        requirements = []
        for line in requirements_text.split("\n"):
            line = line.strip()
            if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                # Remove bullet point and add to list
                req = line.lstrip("-•*").strip()
                if req:
                    requirements.append(req)
        if requirements:
            job_data["requirements"] = requirements

    return job_data


# ============================================================================
# Site-Specific Scrapers
# ============================================================================


async def scrape_japan_dev_job(url: str) -> JobPostingData:
    """
    Scrape job posting from Japan Dev (https://japan-dev.com).

    Japan Dev is a JavaScript-heavy site with:
    - AJAX-loaded job details
    - Dynamic "Apply" button rendering
    - Structured job information sections

    Args:
        url: Full URL to job posting (e.g., https://japan-dev.com/jobs/...)

    Returns:
        Structured job data

    Raises:
        Exception: If scraping fails after retries
    """
    async with create_browser_context(headless=True) as browser:
        agent = await create_scraper_agent(browser)

        # Construct detailed extraction prompt with step-by-step instructions
        # Note: Being explicit about steps improves extraction reliability
        extraction_prompt = f"""
You are scraping a job posting from Japan Dev. Follow these steps carefully:

**STEP 1: NAVIGATE AND WAIT**
Use the navigate_browser tool with these EXACT parameters:

```
navigate_browser(url="{url}")
```

The tool will automatically wait for the page to load. Japan Dev uses JavaScript to load job details dynamically, so be patient and wait for all content to appear.

**STEP 2: VERIFY PAGE LOADED**
After navigation, use get_elements to check that job content is visible. Look for elements containing job details.

**STEP 3: EXTRACT ALL PAGE CONTENT**
Use extract_text or get_elements to get all visible text from the page. Japan Dev job postings typically have all information visible after the page loads, including salary details.

**STEP 4: EXTRACT INFORMATION**
Look for these specific sections and extract data:

1. **Job Title**: Usually in a large heading near the top
2. **Company Name**: "Cookpad" or company logo/name
3. **Location**: Look for location icon or "Location:" label
4. **Salary/Compensation**: VERY IMPORTANT - Look carefully for:
   - Section labeled "Salary", "Compensation", "給与", or "年収"
   - Japanese format: "¥X万 - ¥Y万" or "XXX万円〜YYY万円"
   - English format: "¥X,000,000 - ¥Y,000,000" or "$XX,XXX - $YY,YYY"
   - Hourly rates, annual salary, or monthly salary
   - If you see ANY numbers with ¥ or 万円, extract them as salary
5. **Job Description**: Full text describing the role
6. **Requirements/Qualifications**: Bulleted list of skills, experience, education
7. **Application Method**: "Apply" button, application URL, or contact method
8. **Posted Date**: When the job was posted
9. **Employment Type**: Full-time, Contract, Part-time, etc.

**STEP 5: FORMAT OUTPUT**
Return the data in this EXACT format:

```
JOB_TITLE: [exact title from page]
COMPANY: [exact company name]
LOCATION: [exact location]
DESCRIPTION: [complete job description]
REQUIREMENTS:
- [requirement 1]
- [requirement 2]
- [requirement 3]
SALARY: [EXACT salary text from page - DO NOT write "Not specified" unless you truly cannot find any salary info]
APPLICATION_URL: [url or button text]
POSTED_DATE: [date or "Not specified"]
EMPLOYMENT_TYPE: [type or "Not specified"]
```

**CRITICAL**: Do not skip the salary field. If you see compensation information anywhere on the page, extract it exactly as written. Check multiple times before marking as "Not specified".
"""

        # Invoke agent with extraction prompt
        result = await agent.ainvoke({"messages": [HumanMessage(content=extraction_prompt)]})

        # Extract the LLM's final response
        # Handle both string and list responses (Anthropic returns list of content blocks)
        raw_content = result["messages"][-1].content
        if isinstance(raw_content, list):
            # Extract text from first content block
            llm_response = raw_content[0].get("text", "") if raw_content else ""
        else:
            llm_response = raw_content

        # Debug: Print raw LLM response to help diagnose extraction issues
        print("\n" + "="*80)
        print("DEBUG: Raw LLM Response from Japan Dev Scraper")
        print("="*80)
        print(llm_response)
        print("="*80 + "\n")

        # Parse structured data from LLM response
        job_data = _parse_job_posting_response(llm_response)

        # Debug: Print parsed data
        print("\n" + "="*80)
        print("DEBUG: Parsed Job Data")
        print("="*80)
        import json
        print(json.dumps(job_data, indent=2, ensure_ascii=False))
        print("="*80 + "\n")

        return job_data


async def scrape_recruit_job(url: str) -> JobPostingData:
    """
    Scrape job posting from Recruit (https://recruit.legalontech.jp).

    Recruit typically has:
    - Server-rendered content (faster loading)
    - Structured data in specific divs/sections
    - Application form links

    Args:
        url: Full URL to job posting

    Returns:
        Structured job data

    Raises:
        Exception: If scraping fails after retries
    """
    async with create_browser_context(headless=True) as browser:
        agent = await create_scraper_agent(browser)

        # Use same extraction prompt format as Japan Dev
        # The agent will adapt to the site's specific structure
        extraction_prompt = f"""
Navigate to {url} and extract job posting information from this Recruit.legalontech.jp page.

IMPORTANT: Wait for the page to fully load before extracting data.

Extract the following information and return it in this exact format:

```
JOB_TITLE: [title]
COMPANY: [company name]
LOCATION: [location]
DESCRIPTION: [full description]
REQUIREMENTS:
- [requirement 1]
- [requirement 2]
- [requirement 3]
...
SALARY: [salary range or "Not specified"]
APPLICATION_URL: [url or method to apply]
POSTED_DATE: [date or "Not specified"]
EMPLOYMENT_TYPE: [type or "Not specified"]
```

Be thorough and extract all available information.
"""

        result = await agent.ainvoke({"messages": [HumanMessage(content=extraction_prompt)]})

        # Handle both string and list responses (Anthropic returns list of content blocks)
        raw_content = result["messages"][-1].content
        if isinstance(raw_content, list):
            llm_response = raw_content[0].get("text", "") if raw_content else ""
        else:
            llm_response = raw_content

        job_data = _parse_job_posting_response(llm_response)

        return job_data


async def scrape_generic_job_posting(url: str) -> JobPostingData:
    """
    Generic job scraper using LLM-powered extraction.

    Uses ReAct agent to intelligently navigate and extract data
    from unknown job posting formats. Slower but more flexible.

    Args:
        url: Full URL to job posting

    Returns:
        Structured job data (best effort)

    Raises:
        Exception: If scraping fails after retries
    """
    async with create_browser_context(headless=True) as browser:
        agent = await create_scraper_agent(browser)

        # Generic extraction prompt works for any job site
        extraction_prompt = f"""
Navigate to {url} and extract job posting information.

IMPORTANT:
1. Wait for the page to fully load (use wait_until='networkidle')
2. Look for standard job posting sections (title, company, description, requirements)
3. If the page has multiple jobs, focus on the main job posting

Extract and return in this exact format:

```
JOB_TITLE: [title]
COMPANY: [company name]
LOCATION: [location]
DESCRIPTION: [full description]
REQUIREMENTS:
- [requirement 1]
- [requirement 2]
...
SALARY: [salary range or "Not specified"]
APPLICATION_URL: [url or "Apply button on page"]
POSTED_DATE: [date or "Not specified"]
EMPLOYMENT_TYPE: [type or "Not specified"]
```

Be thorough and extract all available information.
"""

        result = await agent.ainvoke({"messages": [HumanMessage(content=extraction_prompt)]})

        # Handle both string and list responses (Anthropic returns list of content blocks)
        raw_content = result["messages"][-1].content
        if isinstance(raw_content, list):
            llm_response = raw_content[0].get("text", "") if raw_content else ""
        else:
            llm_response = raw_content

        job_data = _parse_job_posting_response(llm_response)

        return job_data


# ============================================================================
# Main Scraper Router
# ============================================================================


async def scrape_job_posting(
    url: str,
    site_type: Literal["japan-dev", "recruit", "generic"] = "generic",
    max_retries: int = 3,
    timeout_seconds: int = 60,
) -> JobPostingData:
    """
    Route to appropriate scraper based on site type with retry logic.

    Auto-detects site if site_type='generic', or use site-specific
    scraper for better performance.

    Args:
        url: Job posting URL
        site_type: Site identifier for optimized scraping
        max_retries: Maximum retry attempts for transient failures
        timeout_seconds: Maximum time to wait for scraping (per attempt)

    Returns:
        Structured job data

    Raises:
        asyncio.TimeoutError: If scraping exceeds timeout
        Exception: If all retries fail

    Example:
        data = await scrape_job_posting(
            "https://japan-dev.com/jobs/12345",
            site_type="japan-dev",
            max_retries=3
        )
    """
    import asyncio

    # Select scraper function
    if site_type == "japan-dev":
        scraper = scrape_japan_dev_job
    elif site_type == "recruit":
        scraper = scrape_recruit_job
    else:
        scraper = scrape_generic_job_posting

    # Apply timeout and retry logic
    async def scrape_with_timeout():
        return await asyncio.wait_for(scraper(url), timeout=timeout_seconds)

    return await retry_with_exponential_backoff(scrape_with_timeout, max_retries=max_retries)


# ============================================================================
# Testing Utilities
# ============================================================================


async def test_scraper():
    """Quick test function for development"""
    test_url = "https://japan-dev.com/jobs/example"
    data = await scrape_job_posting(test_url, site_type="japan-dev")
    print(f"Scraped data: {data}")


if __name__ == "__main__":
    asyncio.run(test_scraper())
