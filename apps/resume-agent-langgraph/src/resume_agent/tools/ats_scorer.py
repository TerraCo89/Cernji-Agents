"""ATS scorer tool for evaluating resume match against job requirements."""

import re
from typing import Any


def calculate_keyword_match(resume_text: str, job_keywords: list[str]) -> dict[str, Any]:
    """
    Calculate what percentage of job keywords appear in resume.

    This function performs case-insensitive keyword matching to determine
    how well a resume matches the job requirements. It's useful for
    understanding ATS (Applicant Tracking System) compatibility.

    Args:
        resume_text: Full text content of the resume
        job_keywords: List of keywords from job analysis

    Returns:
        Dictionary containing:
        - matched_keywords: list[str] - keywords found in resume
        - missing_keywords: list[str] - keywords NOT in resume
        - match_score: float - percentage (0-100)
        - match_count: int - number of matches
        - total_keywords: int - total keywords

    Example:
        >>> result = calculate_keyword_match(
        ...     "Python developer with Django experience",
        ...     ["Python", "Django", "React"]
        ... )
        >>> result["match_score"]
        66.67
        >>> result["matched_keywords"]
        ["Python", "Django"]
    """
    if not job_keywords:
        return {
            "matched_keywords": [],
            "missing_keywords": [],
            "match_score": 0.0,
            "match_count": 0,
            "total_keywords": 0
        }

    # Normalize resume text for matching (lowercase, remove extra whitespace)
    normalized_resume = re.sub(r'\s+', ' ', resume_text.lower()).strip()

    matched_keywords: list[str] = []
    missing_keywords: list[str] = []

    for keyword in job_keywords:
        # Case-insensitive substring match
        if keyword.lower() in normalized_resume:
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    match_count = len(matched_keywords)
    total_keywords = len(job_keywords)
    match_score = (match_count / total_keywords * 100) if total_keywords > 0 else 0.0

    return {
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "match_score": round(match_score, 2),
        "match_count": match_count,
        "total_keywords": total_keywords
    }


def calculate_ats_score(resume_data: dict[str, Any], job_analysis: dict[str, Any]) -> dict[str, Any]:
    """
    Calculate overall ATS score combining multiple scoring factors.

    This function provides a comprehensive ATS compatibility score by
    evaluating keyword match, skills alignment, and experience relevance.
    The scoring is weighted to prioritize the most important factors.

    Scoring weights:
    - Keyword match: 40%
    - Skills match: 30%
    - Experience relevance: 30%

    Args:
        resume_data: Dictionary containing resume content and metadata
                     Expected keys: "content" (str), "skills" (list[str])
        job_analysis: Dictionary from job analysis tool
                      Expected keys: "keywords" (list[str]), "skills" (list[str]),
                                    "requirements" (list[str])

    Returns:
        Dictionary containing:
        - overall_score: int (0-100) - weighted average score
        - keyword_score: int (0-100) - keyword match percentage
        - skills_score: int (0-100) - skills match percentage
        - experience_score: int (0-100) - experience relevance score
        - recommendations: list[str] - improvement suggestions

    Example:
        >>> job_analysis = {
        ...     "keywords": ["Python", "Django", "REST API"],
        ...     "skills": ["Python", "Docker", "PostgreSQL"],
        ...     "requirements": ["5 years experience", "Team leadership"]
        ... }
        >>> resume = {
        ...     "content": "Python developer with Django and REST API experience...",
        ...     "skills": ["Python", "Django", "Git"]
        ... }
        >>> result = calculate_ats_score(resume, job_analysis)
        >>> result["overall_score"]
        78
    """
    # Extract resume content and skills
    resume_content = resume_data.get("content", "")
    resume_skills = resume_data.get("skills", [])

    # Extract job requirements
    job_keywords = job_analysis.get("keywords", [])
    job_skills = job_analysis.get("skills", [])
    job_requirements = job_analysis.get("requirements", [])

    # 1. Calculate keyword score (40% weight)
    keyword_match = calculate_keyword_match(resume_content, job_keywords)
    keyword_score = int(keyword_match["match_score"])

    # 2. Calculate skills score (30% weight)
    if job_skills:
        skills_match = calculate_keyword_match(
            " ".join(resume_skills),
            job_skills
        )
        skills_score = int(skills_match["match_score"])
    else:
        skills_score = 0

    # 3. Calculate experience score (30% weight)
    # Simple heuristic: check if resume mentions key requirement terms
    experience_keywords = [
        "years", "experience", "led", "managed", "developed",
        "implemented", "designed", "architected", "built"
    ]

    if job_requirements:
        # Count how many requirements have matching experience indicators
        requirements_with_evidence = 0
        for requirement in job_requirements:
            # Extract key terms from requirement
            requirement_terms = re.findall(r'\b\w+\b', requirement.lower())
            # Check if resume has evidence of this requirement
            has_evidence = any(
                term in resume_content.lower()
                for term in requirement_terms
                if len(term) > 3  # Skip short words
            )
            if has_evidence:
                requirements_with_evidence += 1

        experience_score = int(
            (requirements_with_evidence / len(job_requirements) * 100)
        )
    else:
        experience_score = 0

    # Calculate weighted overall score
    overall_score = int(
        (keyword_score * 0.4) +
        (skills_score * 0.3) +
        (experience_score * 0.3)
    )

    # Generate recommendations
    recommendations = suggest_improvements(resume_data, job_analysis, {
        "keyword_match": keyword_match,
        "skills_score": skills_score,
        "experience_score": experience_score
    })

    return {
        "overall_score": overall_score,
        "keyword_score": keyword_score,
        "skills_score": skills_score,
        "experience_score": experience_score,
        "recommendations": recommendations
    }


def suggest_improvements(
    resume_data: dict[str, Any],
    job_analysis: dict[str, Any],
    ats_score: dict[str, Any]
) -> list[str]:
    """
    Analyze gaps between resume and job requirements and suggest improvements.

    This function provides actionable, specific recommendations for improving
    resume ATS compatibility and job match. It focuses on the most impactful
    changes based on the scoring analysis.

    Args:
        resume_data: Dictionary containing resume content and metadata
        job_analysis: Dictionary from job analysis tool
        ats_score: Dictionary from calculate_ats_score with detailed scores

    Returns:
        List of actionable improvement suggestions, ordered by priority

    Example:
        >>> suggestions = suggest_improvements(resume, job_analysis, ats_score)
        >>> suggestions[0]
        "Add missing keywords: Docker, Kubernetes, CI/CD"
    """
    recommendations: list[str] = []

    # Get keyword match data
    keyword_match = ats_score.get("keyword_match", {})
    missing_keywords = keyword_match.get("missing_keywords", [])

    # Get scores for prioritization
    keyword_score = ats_score.get("keyword_score", 0)
    skills_score = ats_score.get("skills_score", 0)
    experience_score = ats_score.get("experience_score", 0)

    # Priority 1: Critical keyword gaps (< 50% match)
    if keyword_score < 50 and missing_keywords:
        # Show top 5 most critical missing keywords
        top_missing = missing_keywords[:5]
        recommendations.append(
            f"Add missing keywords: {', '.join(top_missing)}"
        )

    # Priority 2: Moderate keyword gaps (50-75% match)
    elif keyword_score < 75 and missing_keywords:
        top_missing = missing_keywords[:3]
        recommendations.append(
            f"Consider adding these keywords: {', '.join(top_missing)}"
        )

    # Priority 3: Skills gaps
    if skills_score < 70:
        job_skills = job_analysis.get("skills", [])
        resume_skills = resume_data.get("skills", [])

        # Find skills in job but not in resume
        resume_skills_lower = [s.lower() for s in resume_skills]
        missing_skills = [
            skill for skill in job_skills
            if skill.lower() not in resume_skills_lower
        ]

        if missing_skills:
            top_skills = missing_skills[:3]
            recommendations.append(
                f"Highlight experience with: {', '.join(top_skills)}"
            )

    # Priority 4: Experience relevance
    if experience_score < 60:
        recommendations.append(
            "Quantify achievements with specific metrics (e.g., 'increased performance by 40%')"
        )
        recommendations.append(
            "Add more specific examples of projects matching the job requirements"
        )

    # Priority 5: General improvements
    job_responsibilities = job_analysis.get("responsibilities", [])
    if job_responsibilities:
        # Check if resume mentions leadership/management if job requires it
        resume_content = resume_data.get("content", "").lower()
        has_leadership_keywords = any(
            keyword in resume_content
            for keyword in ["led", "managed", "mentored", "supervised", "coordinated"]
        )

        needs_leadership = any(
            keyword in " ".join(job_responsibilities).lower()
            for keyword in ["lead", "manage", "mentor", "supervise", "coordinate"]
        )

        if needs_leadership and not has_leadership_keywords:
            recommendations.append(
                "Add examples of leadership or team collaboration experience"
            )

    # If all scores are good, provide optimization suggestions
    if keyword_score >= 75 and skills_score >= 70 and experience_score >= 60:
        recommendations.append(
            "Strong match! Consider tailoring the summary section to emphasize top skills"
        )

    # Ensure we always have at least one recommendation
    if not recommendations:
        recommendations.append(
            "Resume looks good! Review job posting for any additional requirements to highlight"
        )

    return recommendations
