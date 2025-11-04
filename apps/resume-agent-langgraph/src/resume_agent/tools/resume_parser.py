"""Resume parser tool for extracting and processing resume data.

This module provides functions to load and extract information from resume data
stored in the SQLite database. Uses the data access wrapper for single source
of truth database access.
"""

from typing import Any

from langchain_core.tools import tool
from ..data.access import load_master_resume as load_resume_from_db


@tool
def load_master_resume() -> dict[str, Any]:
    """Load master resume from database.

    Loads the master resume from the SQLite database using the data access wrapper.
    The database is the single source of truth for resume data.

    Returns:
        Dictionary with status 'success' or 'error' and corresponding data or error message.

    Example:
        >>> result = load_master_resume()
        >>> if result["status"] == "success":
        ...     print(result["data"]["personal_info"]["name"])
    """
    try:
        # Load from database using data access wrapper
        resume_data = load_resume_from_db()

        return {"status": "success", "data": resume_data}

    except ValueError as e:
        # Data access wrapper raises ValueError on database errors
        return {
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to load resume from database: {str(e)}"
        }


@tool
def extract_skills_from_resume(resume_data: dict[str, Any]) -> list[str]:
    """Extract all skills from resume data, combining skills fields and employment technologies.

    Args:
        resume_data: Parsed resume dictionary

    Returns:
        Deduplicated sorted list of skill strings.
    """
    skills_set = set()

    # Extract from top-level skills field
    if "skills" in resume_data:
        skills = resume_data["skills"]
        if isinstance(skills, list):
            skills_set.update(skill for skill in skills if isinstance(skill, str))
        elif isinstance(skills, dict):
            # Handle structured skills (e.g., {"technical": [...], "soft": [...]})
            for skill_category, skill_list in skills.items():
                if isinstance(skill_list, list):
                    skills_set.update(skill for skill in skill_list if isinstance(skill, str))

    # Extract technologies from employment history
    employment_history = resume_data.get("employment_history", [])
    if isinstance(employment_history, list):
        for employment in employment_history:
            if isinstance(employment, dict):
                technologies = employment.get("technologies", [])
                if isinstance(technologies, list):
                    skills_set.update(tech for tech in technologies if isinstance(tech, str))

    return sorted(list(skills_set))


@tool
def extract_achievements_from_resume(resume_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract achievements from all employment positions with company, role, and period context.

    Args:
        resume_data: Parsed resume dictionary

    Returns:
        List of achievement dictionaries with company, role, achievement, metric, and period fields.
    """
    achievements_list = []

    employment_history = resume_data.get("employment_history", [])
    if not isinstance(employment_history, list):
        return achievements_list

    for employment in employment_history:
        if not isinstance(employment, dict):
            continue

        company = employment.get("company", "Unknown Company")
        role = employment.get("position") or employment.get("title", "Unknown Role")
        start_date = employment.get("start_date", "")
        end_date = employment.get("end_date", "Present")

        # Format period
        period = f"{start_date} - {end_date}" if start_date else ""

        # Extract achievements
        achievements = employment.get("achievements", [])
        if isinstance(achievements, list):
            for achievement in achievements:
                if isinstance(achievement, dict):
                    # Structured achievement with description and optional metric
                    achievement_entry = {
                        "company": company,
                        "role": role,
                        "achievement": achievement.get("description", ""),
                        "period": period,
                    }

                    # Add metric if present
                    if "metric" in achievement:
                        achievement_entry["metric"] = achievement["metric"]

                    if achievement_entry["achievement"]:
                        achievements_list.append(achievement_entry)

                elif isinstance(achievement, str):
                    # Simple string achievement
                    achievements_list.append(
                        {
                            "company": company,
                            "role": role,
                            "achievement": achievement,
                            "period": period,
                        }
                    )

    return achievements_list
