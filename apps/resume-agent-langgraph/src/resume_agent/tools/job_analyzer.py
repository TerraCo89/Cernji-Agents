"""Job analyzer tool for fetching and parsing job postings."""

import re
from datetime import datetime
from typing import Any

import httpx


def fetch_job_posting(job_url: str) -> str:
    """
    Fetch HTML content from a job posting URL.

    Args:
        job_url: URL of the job posting to fetch

    Returns:
        HTML content as string, or error message if fetch fails

    Raises:
        Does not raise - returns error message as string on failure
    """
    try:
        response = httpx.get(
            job_url,
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        response.raise_for_status()
        return response.text
    except httpx.TimeoutException:
        return f"Error: Request timeout after 30 seconds for URL: {job_url}"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} for URL: {job_url}"
    except httpx.RequestError as e:
        return f"Error: Failed to fetch URL: {job_url} - {str(e)}"
    except Exception as e:
        return f"Error: Unexpected error fetching URL: {job_url} - {str(e)}"


def parse_job_posting(job_content: str) -> dict[str, Any]:
    """
    Extract structured data from job posting HTML content.

    This function uses simple text parsing to extract common job posting fields.
    It looks for patterns commonly found in job postings across various platforms.

    Args:
        job_content: HTML content of the job posting

    Returns:
        Dictionary with extracted job information:
        - company: Company name (str | None)
        - job_title: Job title (str | None)
        - requirements: List of job requirements (list[str])
        - skills: List of required skills (list[str])
        - responsibilities: List of responsibilities (list[str])
        - salary_range: Salary range if found (str | None)
        - location: Job location (str | None)
    """
    # Remove HTML tags for easier text parsing
    text = re.sub(r'<[^>]+>', ' ', job_content)
    text = re.sub(r'\s+', ' ', text).strip()

    result: dict[str, Any] = {
        "company": None,
        "job_title": None,
        "requirements": [],
        "skills": [],
        "responsibilities": [],
        "salary_range": None,
        "location": None
    }

    # Extract company name (look for common patterns)
    company_patterns = [
        r'company[:\s]+([^,.\n]+)',
        r'employer[:\s]+([^,.\n]+)',
        r'organization[:\s]+([^,.\n]+)',
    ]
    for pattern in company_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["company"] = match.group(1).strip()
            break

    # Extract job title (look for title patterns)
    title_patterns = [
        r'job title[:\s]+([^,.\n]+)',
        r'position[:\s]+([^,.\n]+)',
        r'role[:\s]+([^,.\n]+)',
    ]
    for pattern in title_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["job_title"] = match.group(1).strip()
            break

    # Extract location
    location_patterns = [
        r'location[:\s]+([^,.\n]+)',
        r'based in[:\s]+([^,.\n]+)',
        r'office[:\s]+([^,.\n]+)',
    ]
    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["location"] = match.group(1).strip()
            break

    # Extract salary range
    salary_patterns = [
        r'\$[\d,]+\s*-\s*\$[\d,]+',
        r'salary[:\s]+\$[\d,]+\s*-\s*\$[\d,]+',
        r'compensation[:\s]+\$[\d,]+\s*-\s*\$[\d,]+',
    ]
    for pattern in salary_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["salary_range"] = match.group(0).strip()
            break

    # Extract requirements (look for bulleted/numbered lists after "requirements")
    requirements_section = re.search(
        r'requirements?[:\s]+(.*?)(?:responsibilities|qualifications|skills|experience|$)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if requirements_section:
        section_text = requirements_section.group(1)
        # Extract bullet points or numbered items
        items = re.findall(r'[•\-\*\d+\.]\s*([^\n•\-\*]+)', section_text)
        result["requirements"] = [item.strip() for item in items if len(item.strip()) > 10]

    # Extract skills (look for common skill keywords)
    skills_section = re.search(
        r'skills?[:\s]+(.*?)(?:requirements|responsibilities|qualifications|experience|$)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if skills_section:
        section_text = skills_section.group(1)
        items = re.findall(r'[•\-\*\d+\.]\s*([^\n•\-\*]+)', section_text)
        result["skills"] = [item.strip() for item in items if len(item.strip()) > 2]

    # Extract responsibilities
    responsibilities_section = re.search(
        r'responsibilities[:\s]+(.*?)(?:requirements|qualifications|skills|experience|$)',
        text,
        re.IGNORECASE | re.DOTALL
    )
    if responsibilities_section:
        section_text = responsibilities_section.group(1)
        items = re.findall(r'[•\-\*\d+\.]\s*([^\n•\-\*]+)', section_text)
        result["responsibilities"] = [item.strip() for item in items if len(item.strip()) > 10]

    return result


def analyze_job_posting(job_url: str) -> dict[str, Any]:
    """
    Fetch and analyze a job posting from a URL.

    This is the main entry point that combines fetching and parsing.
    It handles errors gracefully and returns all job information plus metadata.

    Args:
        job_url: URL of the job posting to analyze

    Returns:
        Dictionary containing:
        - All fields from parse_job_posting()
        - url: Original job URL
        - fetched_at: ISO 8601 timestamp
        - errors: List of error messages (empty if successful)

    Example:
        >>> result = analyze_job_posting("https://example.com/job/123")
        >>> print(result["company"])
        "Example Corp"
        >>> print(result["errors"])
        []
    """
    errors: list[str] = []

    # Fetch job posting
    job_content = fetch_job_posting(job_url)

    # Check if fetch returned an error
    if job_content.startswith("Error:"):
        errors.append(job_content)
        parsed_data = {
            "company": None,
            "job_title": None,
            "requirements": [],
            "skills": [],
            "responsibilities": [],
            "salary_range": None,
            "location": None
        }
    else:
        # Parse the content
        try:
            parsed_data = parse_job_posting(job_content)
        except Exception as e:
            errors.append(f"Error parsing job content: {str(e)}")
            parsed_data = {
                "company": None,
                "job_title": None,
                "requirements": [],
                "skills": [],
                "responsibilities": [],
                "salary_range": None,
                "location": None
            }

    # Combine parsed data with metadata
    result = {
        **parsed_data,
        "url": job_url,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "errors": errors
    }

    return result
