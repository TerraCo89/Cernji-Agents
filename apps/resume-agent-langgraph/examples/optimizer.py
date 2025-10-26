"""
Resume optimization node.

Optimizes resume content for ATS and target job requirements.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import ResumeState
from ..config import get_settings
from ..prompts import (
    RESUME_ANALYSIS_PROMPT,
    SECTION_OPTIMIZATION_PROMPT,
    ATS_SCORING_PROMPT,
    SYSTEM_RESUME_EXPERT,
)
from ..tools import analyze_resume_ats, calculate_keyword_match


def analyze_resume(state: ResumeState) -> dict:
    """
    Analyze resume against job requirements.
    
    Identifies:
    - Current skills in resume
    - Experience summary
    - Skill gaps
    
    Args:
        state: Current resume agent state
        
    Returns:
        State updates with resume analysis
    """
    print("\n📊 Analyzing current resume...")
    
    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.model_name,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
    )
    
    # Prepare prompt
    prompt = RESUME_ANALYSIS_PROMPT.format(
        resume_text=state['resume_text'],
        requirements='\n'.join(f"- {req}" for req in state['job_requirements']),
        skills='\n'.join(f"- {skill}" for skill in state['job_skills'])
    )
    
    # Analyze with LLM
    response = llm.invoke([
        SystemMessage(content=SYSTEM_RESUME_EXPERT),
        HumanMessage(content=prompt)
    ])
    
    analysis = response.content
    
    # Extract structured information (simplified - use structured outputs in production)
    current_skills = _extract_skills_from_analysis(analysis)
    experience_summary = _extract_summary(analysis)
    skill_gaps = _extract_gaps(analysis, state['job_skills'], current_skills)
    
    print(f"   ✓ Identified {len(current_skills)} current skills")
    print(f"   ✓ Found {len(skill_gaps)} skill gaps")
    
    return {
        "current_skills": current_skills,
        "experience_summary": experience_summary,
        "skill_gaps": skill_gaps,
    }


def optimize_resume_sections(state: ResumeState) -> dict:
    """
    Optimize individual resume sections for ATS and readability.
    
    Args:
        state: Current resume agent state
        
    Returns:
        State updates with optimized sections
    """
    print("\n✨ Optimizing resume sections...")
    
    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.model_name,
        temperature=0.3,  # Slightly higher for more creative rewrites
        max_tokens=settings.max_tokens,
    )
    
    # For demo, let's optimize the full resume
    # In production, you'd split into sections
    
    prompt = SECTION_OPTIMIZATION_PROMPT.format(
        section_name="Full Resume",
        original_text=state['resume_text'],
        keywords=', '.join(state['ats_keywords'][:15]),  # Top 15 keywords
        job_context=f"Job Title: {state['job_title']}\n" + 
                    f"Key Requirements: {', '.join(state['job_requirements'][:5])}"
    )
    
    print("   🤖 Generating optimized version with Claude...")
    response = llm.invoke([
        SystemMessage(content=SYSTEM_RESUME_EXPERT),
        HumanMessage(content=prompt)
    ])
    
    optimized = response.content.strip()
    
    # Calculate improvement
    original_ats = analyze_resume_ats(state['resume_text'])
    optimized_ats = analyze_resume_ats(optimized)
    
    improvement = optimized_ats['ats_score'] - original_ats['ats_score']
    
    print(f"   ✓ ATS Score: {original_ats['ats_score']} → {optimized_ats['ats_score']} ({improvement:+d})")
    
    return {
        "optimized_sections": [{
            "section": "full_resume",
            "original_score": original_ats['ats_score'],
            "optimized_score": optimized_ats['ats_score'],
            "content": optimized,
        }],
        "ats_score": optimized_ats['ats_score'],
    }


def score_resume(state: ResumeState) -> dict:
    """
    Score the resume using ATS analysis and keyword matching.
    
    Args:
        state: Current resume agent state
        
    Returns:
        State updates with scoring and suggestions
    """
    print("\n🎯 Scoring resume against job requirements...")
    
    # Get the resume to score (optimized if available)
    resume_text = state['resume_text']
    if state.get('optimized_sections'):
        resume_text = state['optimized_sections'][-1]['content']
    
    # Run ATS analysis
    ats_results = analyze_resume_ats(resume_text)
    
    # Calculate keyword match
    keyword_match = calculate_keyword_match(resume_text, state['ats_keywords'])
    
    # Generate suggestions
    suggestions = []
    
    if ats_results['issues']:
        suggestions.append(f"Critical: {', '.join(ats_results['issues'])}")
    
    if keyword_match['match_percentage'] < 60:
        missing = keyword_match['missing_keywords'][:5]
        suggestions.append(f"Add keywords: {', '.join(missing)}")
    
    if ats_results['warnings']:
        suggestions.extend(ats_results['warnings'])
    
    # Determine if manual review needed
    needs_review = (
        ats_results['ats_score'] < settings.ats_score_threshold or
        len(ats_results['issues']) > 0 or
        keyword_match['match_percentage'] < 50
    )
    
    print(f"   ✓ ATS Score: {ats_results['ats_score']}/100")
    print(f"   ✓ Keyword Match: {keyword_match['match_percentage']:.1f}%")
    print(f"   ✓ Manual Review Needed: {needs_review}")
    
    return {
        "ats_score": ats_results['ats_score'],
        "optimization_suggestions": suggestions,
        "needs_manual_review": needs_review,
    }


# Helper functions
def _extract_skills_from_analysis(analysis: str) -> list[str]:
    """Extract skills list from analysis text."""
    # Simple extraction - look for lines with skills
    skills = []
    for line in analysis.split('\n'):
        if 'skill' in line.lower() and (':' in line or '-' in line):
            # Extract items after colon or dash
            parts = line.split(':' if ':' in line else '-', 1)
            if len(parts) > 1:
                items = parts[1].split(',')
                skills.extend([s.strip().strip('*-•') for s in items if s.strip()])
    return skills[:15]  # Limit to top 15


def _extract_summary(analysis: str) -> str:
    """Extract experience summary from analysis."""
    # Look for summary section
    for line in analysis.split('\n'):
        if 'summary' in line.lower() and ':' in line:
            return line.split(':', 1)[1].strip()
    
    # Fallback: return first few sentences
    sentences = [s.strip() for s in analysis.split('.') if len(s.strip()) > 20]
    return '. '.join(sentences[:2]) + '.' if sentences else "Experienced professional"


def _extract_gaps(analysis: str, job_skills: list[str], current_skills: list[str]) -> list[str]:
    """Identify skill gaps."""
    current_lower = [s.lower() for s in current_skills]
    gaps = []
    
    for skill in job_skills:
        if skill.lower() not in current_lower:
            gaps.append(skill)
    
    return gaps[:10]  # Top 10 gaps
