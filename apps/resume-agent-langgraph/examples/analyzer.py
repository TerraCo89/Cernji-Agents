"""
Job analysis node.

Fetches and analyzes job postings to extract requirements and keywords.
"""

import json
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import ResumeState
from ..config import get_settings
from ..prompts import JOB_ANALYSIS_PROMPT, SYSTEM_JOB_ANALYZER
from ..tools import scrape_job_posting


def analyze_job_posting(state: ResumeState) -> dict:
    """
    Analyze job posting to extract requirements and keywords.
    
    This node:
    1. Fetches the job posting content
    2. Uses LLM to extract structured information
    3. Updates state with job analysis results
    
    Args:
        state: Current resume agent state
        
    Returns:
        State updates with job analysis
    """
    print(f"\n📋 Analyzing job posting: {state['job_posting_url']}")
    
    # Fetch job posting
    try:
        job_data = scrape_job_posting(state['job_posting_url'])
        print(f"   ✓ Fetched job from {job_data['source']}")
    except Exception as e:
        print(f"   ✗ Failed to fetch job posting: {e}")
        return {
            "job_title": "Unknown",
            "job_requirements": ["Failed to fetch job posting"],
            "job_skills": [],
            "ats_keywords": [],
        }
    
    # Initialize LLM
    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.model_name,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )
    
    # Prepare prompt
    prompt = JOB_ANALYSIS_PROMPT.format(
        url=state['job_posting_url'],
        content=job_data['cleaned_text'][:4000]  # Limit to avoid token limits
    )
    
    # Analyze with LLM
    print("   🤖 Extracting requirements with Claude...")
    response = llm.invoke([
        SystemMessage(content=SYSTEM_JOB_ANALYZER),
        HumanMessage(content=prompt)
    ])
    
    # Parse response (in production, you'd want structured outputs)
    analysis_text = response.content
    
    # Extract structured data from response
    # For demo, using simple parsing - in production, use structured outputs
    job_title = job_data.get('title', 'Unknown')
    
    # Simple extraction (you'd improve this with structured outputs)
    requirements = _extract_bullet_points(analysis_text, "requirements")
    skills = _extract_bullet_points(analysis_text, "skills")
    keywords = _extract_bullet_points(analysis_text, "keywords")
    
    print(f"   ✓ Found {len(requirements)} requirements")
    print(f"   ✓ Found {len(skills)} skills")
    print(f"   ✓ Found {len(keywords)} ATS keywords")
    
    return {
        "job_title": job_title,
        "job_requirements": requirements,
        "job_skills": skills,
        "ats_keywords": keywords,
    }


def _extract_bullet_points(text: str, section: str) -> list[str]:
    """
    Extract bullet points from a section of text.
    
    This is a simple helper - in production, use structured outputs.
    """
    lines = text.split('\n')
    in_section = False
    bullet_points = []
    
    for line in lines:
        line = line.strip()
        
        # Check if we're entering the section
        if section.lower() in line.lower() and ':' in line:
            in_section = True
            continue
        
        # Check if we're leaving the section
        if in_section and line and not line.startswith(('-', '•', '*', '1.', '2.', '3.')):
            # If line doesn't start with bullet marker, we might be in a new section
            if ':' in line:
                break
        
        # Extract bullet point
        if in_section and line:
            # Remove bullet markers
            cleaned = line.lstrip('-•*123456789. ')
            if cleaned and len(cleaned) > 3:
                bullet_points.append(cleaned)
    
    return bullet_points[:10]  # Limit to top 10
