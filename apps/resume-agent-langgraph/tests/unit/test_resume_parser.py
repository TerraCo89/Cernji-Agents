"""Tests for resume parser tool."""

import pytest
from unittest.mock import patch, MagicMock
from src.resume_agent.tools.resume_parser import (
    extract_skills_from_resume,
    extract_achievements_from_resume,
)


@patch('resume_agent.data.access._get_mcp_fn')
def test_load_master_resume_success(mock_get_mcp_fn):
    """Test loading resume from database successfully."""
    from src.resume_agent.tools.resume_parser import load_master_resume

    # Mock the MCP function to return success response
    mock_fn = MagicMock()
    mock_fn.return_value = {
        "status": "success",
        "data": {
            "personal_info": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890",
                "location": "San Francisco, CA"
            },
            "professional_summary": "Experienced software engineer with 10+ years building scalable systems.",
            "employment_history": [
                {
                    "company": "TechCorp",
                    "position": "Senior Engineer",
                    "start_date": "2020-01",
                    "end_date": "2023-01",
                    "description": "Led backend development",
                    "technologies": ["Python", "Docker", "AWS"],
                    "achievements": [
                        {"description": "Reduced API latency by 40%", "metric": "40% faster"},
                        {"description": "Led migration to microservices"}
                    ]
                }
            ],
            "skills": ["Python", "AWS", "Docker", "Kubernetes"]
        }
    }
    mock_get_mcp_fn.return_value = mock_fn

    # Call the tool (LangChain tools use .invoke())
    result = load_master_resume.invoke({})

    # Verify
    assert result["status"] == "success"
    assert "data" in result
    assert result["data"]["personal_info"]["name"] == "John Doe"
    assert len(result["data"]["employment_history"]) == 1
    mock_get_mcp_fn.assert_called_once_with("data_read_master_resume")
    mock_fn.assert_called_once()


@patch('resume_agent.data.access._get_mcp_fn')
def test_load_master_resume_database_error(mock_get_mcp_fn):
    """Test handling database error when loading resume."""
    from src.resume_agent.tools.resume_parser import load_master_resume

    # Mock the MCP function to return error response
    mock_fn = MagicMock()
    mock_fn.return_value = {
        "status": "error",
        "error": "Resume not found in database"
    }
    mock_get_mcp_fn.return_value = mock_fn

    # Call the tool (LangChain tools use .invoke())
    result = load_master_resume.invoke({})

    # Verify error handling
    assert result["status"] == "error"
    assert "Resume not found" in result["error"]
    mock_get_mcp_fn.assert_called_once_with("data_read_master_resume")


@patch('resume_agent.data.access._get_mcp_fn')
def test_load_master_resume_unexpected_error(mock_get_mcp_fn):
    """Test handling unexpected error when loading resume."""
    from src.resume_agent.tools.resume_parser import load_master_resume

    # Mock the MCP function to raise exception
    mock_fn = MagicMock()
    mock_fn.side_effect = Exception("Unexpected database error")
    mock_get_mcp_fn.return_value = mock_fn

    # Call the tool (LangChain tools use .invoke())
    result = load_master_resume.invoke({})

    # Verify error handling
    assert result["status"] == "error"
    assert "Failed to load resume from database" in result["error"]
    mock_get_mcp_fn.assert_called_once_with("data_read_master_resume")


def test_extract_skills_from_resume_with_list():
    """Test extracting skills from resume with list format."""
    resume_data = {
        "skills": ["Python", "AWS", "Docker"],
        "employment_history": [
            {"company": "TechCorp", "technologies": ["Kubernetes", "Python"]}
        ],
    }

    # LangChain tools need to be invoked with .invoke()
    skills = extract_skills_from_resume.invoke({"resume_data": resume_data})

    assert sorted(skills) == ["AWS", "Docker", "Kubernetes", "Python"]
    assert len(skills) == 4  # Python should be deduplicated


def test_extract_skills_from_resume_with_dict():
    """Test extracting skills from resume with structured skills."""
    resume_data = {
        "skills": {"technical": ["Python", "AWS"], "soft": ["Leadership", "Communication"]},
        "employment_history": [{"company": "TechCorp", "technologies": ["Docker"]}],
    }

    # LangChain tools need to be invoked with .invoke()
    skills = extract_skills_from_resume.invoke({"resume_data": resume_data})

    assert sorted(skills) == ["AWS", "Communication", "Docker", "Leadership", "Python"]


def test_extract_skills_from_resume_empty():
    """Test extracting skills from resume with no skills."""
    resume_data = {"personal_info": {"name": "John Doe"}, "employment_history": []}

    # LangChain tools need to be invoked with .invoke()
    skills = extract_skills_from_resume.invoke({"resume_data": resume_data})

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

    # LangChain tools need to be invoked with .invoke()
    achievements = extract_achievements_from_resume.invoke({"resume_data": resume_data})

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

    # LangChain tools need to be invoked with .invoke()
    achievements = extract_achievements_from_resume.invoke({"resume_data": resume_data})

    assert achievements == []
