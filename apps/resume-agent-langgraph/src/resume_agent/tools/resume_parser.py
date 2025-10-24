"""Resume parser tool for extracting and processing resume data.

This module provides functions to load, parse, and extract information from
resume files in YAML format, compatible with the existing career-history.yaml
structure used by the Resume Agent.
"""

import yaml
from pathlib import Path
from typing import Any, Optional


def load_master_resume(file_path: str) -> dict[str, Any]:
    """Load and parse master resume from YAML file.

    Reads a YAML resume file and returns the structured data as a dictionary.
    Handles file not found errors gracefully by returning error information.

    Args:
        file_path: Absolute or relative path to the YAML resume file

    Returns:
        Dictionary containing either:
        - success: {"status": "success", "data": {...}}
        - error: {"status": "error", "error": "error message", "file_path": "..."}

    Example:
        >>> result = load_master_resume("resumes/career-history.yaml")
        >>> if result["status"] == "success":
        ...     resume_data = result["data"]
        ...     print(resume_data["personal_info"]["name"])
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return {
                "status": "error",
                "error": f"Resume file not found: {file_path}",
                "file_path": str(path.absolute()),
            }

        if not path.is_file():
            return {
                "status": "error",
                "error": f"Path is not a file: {file_path}",
                "file_path": str(path.absolute()),
            }

        # Read and parse YAML
        with open(path, "r", encoding="utf-8") as f:
            yaml_content = f.read()

        # Parse YAML into dict
        resume_data = parse_resume_yaml(yaml_content)

        if resume_data["status"] == "error":
            return resume_data

        return {"status": "success", "data": resume_data["data"]}

    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to load resume: {str(e)}",
            "file_path": file_path,
        }


def parse_resume_yaml(yaml_content: str) -> dict[str, Any]:
    """Parse YAML string into structured resume dictionary.

    Parses YAML content and validates that required fields are present.
    Compatible with the career-history.yaml structure.

    Args:
        yaml_content: YAML string containing resume data

    Returns:
        Dictionary containing either:
        - success: {"status": "success", "data": {...}}
        - error: {"status": "error", "error": "error message"}

    Example:
        >>> yaml_str = '''
        ... personal_info:
        ...   name: John Doe
        ...   email: john@example.com
        ... employment_history: []
        ... '''
        >>> result = parse_resume_yaml(yaml_str)
        >>> if result["status"] == "success":
        ...     print(result["data"]["personal_info"]["name"])
    """
    try:
        # Parse YAML
        data = yaml.safe_load(yaml_content)

        if not isinstance(data, dict):
            return {
                "status": "error",
                "error": "Resume YAML must be a dictionary at root level",
            }

        # Validate required fields
        required_fields = ["personal_info"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return {
                "status": "error",
                "error": f"Missing required fields: {', '.join(missing_fields)}",
            }

        # Validate personal_info structure
        personal_info = data.get("personal_info", {})
        if not isinstance(personal_info, dict):
            return {
                "status": "error",
                "error": "personal_info must be a dictionary",
            }

        # Ensure employment_history exists (default to empty list)
        if "employment_history" not in data:
            data["employment_history"] = []
        elif not isinstance(data["employment_history"], list):
            return {
                "status": "error",
                "error": "employment_history must be a list",
            }

        return {"status": "success", "data": data}

    except yaml.YAMLError as e:
        return {
            "status": "error",
            "error": f"Invalid YAML format: {str(e)}",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to parse resume YAML: {str(e)}",
        }


def extract_skills_from_resume(resume_data: dict[str, Any]) -> list[str]:
    """Extract all skills from resume data.

    Combines technical skills, soft skills, and technologies from employment
    history into a deduplicated list of skills.

    Args:
        resume_data: Parsed resume dictionary (from load_master_resume or parse_resume_yaml)

    Returns:
        Deduplicated list of skill strings (case-sensitive)

    Example:
        >>> resume = {"skills": ["Python", "AWS"], "employment_history": [
        ...     {"technologies": ["Docker", "Python"]}
        ... ]}
        >>> skills = extract_skills_from_resume(resume)
        >>> print(sorted(skills))
        ['AWS', 'Docker', 'Python']
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


def extract_achievements_from_resume(resume_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract achievements from all employment positions.

    Returns a list of achievement dictionaries with context about the company,
    role, and achievement details.

    Args:
        resume_data: Parsed resume dictionary (from load_master_resume or parse_resume_yaml)

    Returns:
        List of achievement dictionaries, each containing:
        - company: Company name
        - role: Job title/position
        - achievement: Achievement description
        - metric: Optional metric (if available)
        - period: Employment period (start_date - end_date)

    Example:
        >>> resume = {
        ...     "employment_history": [{
        ...         "company": "TechCorp",
        ...         "position": "Engineer",
        ...         "start_date": "2020-01",
        ...         "end_date": "2023-01",
        ...         "achievements": [
        ...             {"description": "Led migration", "metric": "30% faster"}
        ...         ]
        ...     }]
        ... }
        >>> achievements = extract_achievements_from_resume(resume)
        >>> print(achievements[0]["company"])
        TechCorp
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
