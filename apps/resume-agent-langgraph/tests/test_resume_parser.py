"""Tests for resume parser tool."""

import pytest
from src.resume_agent.tools.resume_parser import (
    load_master_resume,
    parse_resume_yaml,
    extract_skills_from_resume,
    extract_achievements_from_resume,
)


def test_parse_resume_yaml_valid():
    """Test parsing valid YAML resume."""
    yaml_content = """
personal_info:
  name: John Doe
  email: john@example.com
  phone: "123-456-7890"
  location: San Francisco, CA

professional_summary: |
  Experienced software engineer with 10+ years building scalable systems.

employment_history:
  - company: TechCorp
    position: Senior Engineer
    start_date: "2020-01"
    end_date: "2023-01"
    description: Led backend development
    technologies:
      - Python
      - Docker
      - AWS
    achievements:
      - description: Reduced API latency by 40%
        metric: "40% faster"
      - description: Led migration to microservices

skills:
  - Python
  - AWS
  - Docker
  - Kubernetes
"""

    result = parse_resume_yaml(yaml_content)

    assert result["status"] == "success"
    assert "data" in result

    data = result["data"]
    assert data["personal_info"]["name"] == "John Doe"
    assert data["personal_info"]["email"] == "john@example.com"
    assert len(data["employment_history"]) == 1
    assert data["employment_history"][0]["company"] == "TechCorp"


def test_parse_resume_yaml_missing_required_field():
    """Test parsing YAML without required fields."""
    yaml_content = """
employment_history: []
skills:
  - Python
"""

    result = parse_resume_yaml(yaml_content)

    assert result["status"] == "error"
    assert "personal_info" in result["error"]


def test_parse_resume_yaml_invalid_yaml():
    """Test parsing invalid YAML syntax."""
    yaml_content = """
personal_info:
  name: John Doe
  invalid: [unclosed
"""

    result = parse_resume_yaml(yaml_content)

    assert result["status"] == "error"
    assert "YAML" in result["error"]


def test_parse_resume_yaml_empty_employment_history():
    """Test parsing resume with no employment history (defaults to empty list)."""
    yaml_content = """
personal_info:
  name: John Doe
  email: john@example.com
"""

    result = parse_resume_yaml(yaml_content)

    assert result["status"] == "success"
    assert result["data"]["employment_history"] == []


def test_extract_skills_from_resume_with_list():
    """Test extracting skills from resume with list format."""
    resume_data = {
        "skills": ["Python", "AWS", "Docker"],
        "employment_history": [
            {"company": "TechCorp", "technologies": ["Kubernetes", "Python"]}
        ],
    }

    skills = extract_skills_from_resume(resume_data)

    assert sorted(skills) == ["AWS", "Docker", "Kubernetes", "Python"]
    assert len(skills) == 4  # Python should be deduplicated


def test_extract_skills_from_resume_with_dict():
    """Test extracting skills from resume with structured skills."""
    resume_data = {
        "skills": {"technical": ["Python", "AWS"], "soft": ["Leadership", "Communication"]},
        "employment_history": [{"company": "TechCorp", "technologies": ["Docker"]}],
    }

    skills = extract_skills_from_resume(resume_data)

    assert sorted(skills) == ["AWS", "Communication", "Docker", "Leadership", "Python"]


def test_extract_skills_from_resume_empty():
    """Test extracting skills from resume with no skills."""
    resume_data = {"personal_info": {"name": "John Doe"}, "employment_history": []}

    skills = extract_skills_from_resume(resume_data)

    assert skills == []


def test_extract_achievements_from_resume():
    """Test extracting achievements from employment history."""
    resume_data = {
        "employment_history": [
            {
                "company": "TechCorp",
                "position": "Senior Engineer",
                "start_date": "2020-01",
                "end_date": "2023-01",
                "achievements": [
                    {"description": "Reduced latency by 40%", "metric": "40% faster"},
                    {"description": "Led migration to microservices"},
                ],
            },
            {
                "company": "StartupCo",
                "title": "Lead Developer",
                "start_date": "2018-01",
                "end_date": "2020-01",
                "achievements": ["Built MVP in 3 months", "Grew team from 2 to 10"],
            },
        ]
    }

    achievements = extract_achievements_from_resume(resume_data)

    assert len(achievements) == 4

    # Check first achievement (structured with metric)
    assert achievements[0]["company"] == "TechCorp"
    assert achievements[0]["role"] == "Senior Engineer"
    assert "40%" in achievements[0]["achievement"]
    assert achievements[0]["metric"] == "40% faster"
    assert achievements[0]["period"] == "2020-01 - 2023-01"

    # Check third achievement (string format)
    assert achievements[2]["company"] == "StartupCo"
    assert achievements[2]["role"] == "Lead Developer"
    assert "MVP" in achievements[2]["achievement"]


def test_extract_achievements_from_resume_no_achievements():
    """Test extracting achievements when none exist."""
    resume_data = {
        "employment_history": [
            {
                "company": "TechCorp",
                "position": "Engineer",
                "start_date": "2020-01",
                "end_date": "2023-01",
            }
        ]
    }

    achievements = extract_achievements_from_resume(resume_data)

    assert achievements == []


def test_load_master_resume_file_not_found():
    """Test loading non-existent resume file."""
    result = load_master_resume("/nonexistent/path/resume.yaml")

    assert result["status"] == "error"
    assert "not found" in result["error"]


def test_load_master_resume_integration(tmp_path):
    """Integration test for loading resume from file."""
    # Create temporary resume file
    resume_file = tmp_path / "test_resume.yaml"
    resume_content = """
personal_info:
  name: Jane Smith
  email: jane@example.com

employment_history:
  - company: DataCorp
    position: Data Engineer
    start_date: "2021-01"
    end_date: Present
    technologies:
      - Python
      - Spark
    achievements:
      - description: Built data pipeline processing 1M records/day
"""

    resume_file.write_text(resume_content, encoding="utf-8")

    # Load resume
    result = load_master_resume(str(resume_file))

    assert result["status"] == "success"
    assert result["data"]["personal_info"]["name"] == "Jane Smith"
    assert len(result["data"]["employment_history"]) == 1
    assert result["data"]["employment_history"][0]["company"] == "DataCorp"
