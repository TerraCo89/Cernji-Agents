"""
Pytest configuration and fixtures for resume-agent-langgraph tests.

This module provides test fixtures and configuration that are shared across all tests.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, Mock

# Add the src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(autouse=True, scope="session")
def mock_external_dependencies():
    """
    Session-scoped fixture to mock external dependencies that cause import errors.

    This prevents pytest collection failures caused by:
    - Missing API keys (TAVILY_API_KEY, etc.)
    - External module imports (agent.graph from other projects)
    - MCP server initialization
    """
    # Mock the 'agent' module that's imported in the root __init__.py
    mock_agent = MagicMock()
    mock_agent.graph = Mock()
    mock_agent.graph.graph = Mock()

    sys.modules["agent"] = mock_agent
    sys.modules["agent.graph"] = mock_agent.graph

    yield

    # Cleanup
    if "agent" in sys.modules:
        del sys.modules["agent"]
    if "agent.graph" in sys.modules:
        del sys.modules["agent.graph"]


@pytest.fixture
def mock_mcp_functions():
    """
    Fixture to provide mocked MCP server data access functions.

    Returns a dictionary of mocked functions that can be customized in tests.
    """
    from unittest.mock import Mock

    return {
        "data_read_master_resume": Mock(return_value={"status": "success", "data": {}}),
        "data_read_career_history": Mock(return_value={"status": "success", "data": {}}),
        "data_read_job_analysis": Mock(return_value={"status": "not_found"}),
        "data_search_portfolio_examples": Mock(return_value={"status": "success", "examples": []}),
        "data_write_job_analysis": Mock(return_value={"status": "success", "message": "Saved"}),
        "data_write_tailored_resume": Mock(return_value={"status": "success", "message": "Saved"}),
        "data_write_cover_letter": Mock(return_value={"status": "success", "message": "Saved"}),
        "data_list_applications": Mock(return_value={"status": "success", "applications": []}),
    }


@pytest.fixture(scope="session")
def sample_resume_data():
    """Sample master resume data for tests."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "123-456-7890",
            "location": "San Francisco, CA",
        },
        "professional_summary": "Experienced software engineer with 10+ years",
        "employment_history": [
            {
                "company": "TechCorp",
                "position": "Senior Engineer",
                "start_date": "2020-01",
                "end_date": "2023-01",
                "technologies": ["Python", "Docker", "AWS"],
                "achievements": [
                    {"description": "Reduced API latency by 40%", "metric": "40%"}
                ],
            }
        ],
        "skills": ["Python", "AWS", "Docker", "Kubernetes"],
        "certifications": ["AWS Solutions Architect"],
    }


@pytest.fixture(scope="session")
def sample_job_analysis():
    """Sample job analysis data for tests."""
    return {
        "company": "ACME Corp",
        "job_title": "Senior Developer",
        "url": "https://example.com/job/123",
        "required_qualifications": ["Python", "SQL", "REST APIs"],
        "preferred_qualifications": ["AWS", "Docker"],
        "keywords": ["Python", "FastAPI", "PostgreSQL"],
        "responsibilities": [
            "Design and build scalable APIs",
            "Mentor junior developers",
        ],
        "match_score": 85,
    }


@pytest.fixture(scope="session")
def sample_portfolio_examples():
    """Sample portfolio examples for tests."""
    return [
        {
            "id": "ex1",
            "title": "FastAPI REST API",
            "content": "Built REST API with FastAPI and PostgreSQL",
            "technologies": ["Python", "FastAPI", "PostgreSQL"],
            "repo_url": "https://github.com/user/api-project",
            "created_at": "2023-01-15",
        },
        {
            "id": "ex2",
            "title": "Python Data Pipeline",
            "content": "ETL pipeline processing 1M records/day",
            "technologies": ["Python", "Pandas", "Apache Airflow"],
            "repo_url": "https://github.com/user/data-pipeline",
            "created_at": "2023-06-20",
        },
    ]
