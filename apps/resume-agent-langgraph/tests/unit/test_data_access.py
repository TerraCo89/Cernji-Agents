"""
Unit tests for data access wrapper module.

Tests the wrapper functions that interface with the MCP server data access layer.
All MCP server functions are mocked to avoid actual database operations.

Note: We patch the imported MCP functions at their usage location within the access module.
"""

import pytest
from unittest.mock import patch, MagicMock


# ============================================================================
# TEST LOAD_MASTER_RESUME
# ============================================================================


@patch("resume_agent.data_read_master_resume")
def test_load_master_resume_success(mock_read):
    """Test successful load of master resume."""
    # Import after patching to use the mocked MCP function
    from src.resume_agent.data.access import load_master_resume

    # Mock successful response from MCP server
    mock_read.return_value = {
        "status": "success",
        "data": {
            "personal_info": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "123-456-7890",
                "location": "San Francisco, CA",
            },
            "professional_summary": "Experienced software engineer",
            "employment_history": [
                {
                    "company": "TechCorp",
                    "position": "Senior Engineer",
                    "start_date": "2020-01",
                    "end_date": "2023-01",
                }
            ],
            "skills": ["Python", "AWS", "Docker"],
        },
    }

    result = load_master_resume()

    # Verify the MCP function was called
    mock_read.assert_called_once()

    # Verify the result contains expected data
    assert result["personal_info"]["name"] == "John Doe"
    assert result["personal_info"]["email"] == "john@example.com"
    assert len(result["employment_history"]) == 1
    assert "Python" in result["skills"]


@patch("resume_agent.data_read_master_resume")
def test_load_master_resume_error(mock_read):
    """Test error handling when master resume cannot be loaded."""
    from src.resume_agent.data.access import load_master_resume

    # Mock error response from MCP server
    mock_read.return_value = {
        "status": "error",
        "message": "Master resume not found in database",
    }

    # Should raise ValueError on error
    with pytest.raises(ValueError, match="Failed to load master resume"):
        load_master_resume()

    mock_read.assert_called_once()


@patch("resume_agent.data_read_master_resume")
def test_load_master_resume_empty_data(mock_read):
    """Test handling of empty data field in response."""
    from src.resume_agent.data.access import load_master_resume

    # Mock response with no data field
    mock_read.return_value = {"status": "success"}

    result = load_master_resume()

    # Should return empty dict when no data field
    assert result == {}


# ============================================================================
# TEST LOAD_CAREER_HISTORY
# ============================================================================


@patch("resume_agent.data_read_career_history")
def test_load_career_history_success(mock_read):
    """Test successful load of career history."""
    from src.resume_agent.data.access import load_career_history

    # Mock successful response
    mock_read.return_value = {
        "status": "success",
        "data": {
            "employment_history": [
                {
                    "company": "TechCorp",
                    "title": "Senior Engineer",
                    "start_date": "2020-01",
                    "end_date": "2023-01",
                    "achievements": [
                        {"description": "Reduced latency by 40%", "metric": "40% faster"}
                    ],
                }
            ],
            "skills": ["Python", "AWS", "Docker"],
            "certifications": ["AWS Solutions Architect"],
        },
    }

    result = load_career_history()

    mock_read.assert_called_once()

    assert len(result["employment_history"]) == 1
    assert result["employment_history"][0]["company"] == "TechCorp"
    assert "Python" in result["skills"]
    assert "AWS Solutions Architect" in result["certifications"]


@patch("resume_agent.data_read_career_history")
def test_load_career_history_error(mock_read):
    """Test error handling when career history cannot be loaded."""
    from src.resume_agent.data.access import load_career_history

    mock_read.return_value = {
        "status": "error",
        "message": "Database connection failed",
    }

    with pytest.raises(ValueError, match="Failed to load career history"):
        load_career_history()

    mock_read.assert_called_once()


@patch("resume_agent.data_read_career_history")
def test_load_career_history_minimal_data(mock_read):
    """Test loading career history with minimal data."""
    from src.resume_agent.data.access import load_career_history

    mock_read.return_value = {
        "status": "success",
        "data": {
            "employment_history": [],
            "skills": [],
        },
    }

    result = load_career_history()

    assert result["employment_history"] == []
    assert result["skills"] == []


# ============================================================================
# TEST GET_JOB_ANALYSIS
# ============================================================================


@patch("resume_agent.data_read_job_analysis")
def test_get_job_analysis_found(mock_read):
    """Test retrieving existing job analysis."""
    from src.resume_agent.data.access import get_job_analysis

    mock_read.return_value = {
        "status": "success",
        "data": {
            "company": "ACME Corp",
            "job_title": "Senior Developer",
            "url": "https://example.com/job/123",
            "required_qualifications": ["Python", "SQL", "REST APIs"],
            "preferred_qualifications": ["AWS", "Docker"],
            "keywords": ["Python", "FastAPI", "PostgreSQL"],
            "match_score": 85,
        },
    }

    result = get_job_analysis("ACME Corp", "Senior Developer")

    mock_read.assert_called_once_with(company="ACME Corp", job_title="Senior Developer")

    assert result is not None
    assert result["company"] == "ACME Corp"
    assert result["match_score"] == 85
    assert "Python" in result["required_qualifications"]


@patch("resume_agent.data_read_job_analysis")
def test_get_job_analysis_not_found(mock_read):
    """Test when job analysis is not found (should return None)."""
    from src.resume_agent.data.access import get_job_analysis

    mock_read.return_value = {"status": "not_found"}

    result = get_job_analysis("Unknown Company", "Unknown Role")

    mock_read.assert_called_once_with(company="Unknown Company", job_title="Unknown Role")

    # Should return None for not_found status
    assert result is None


@patch("resume_agent.data_read_job_analysis")
def test_get_job_analysis_error(mock_read):
    """Test error handling when database query fails."""
    from src.resume_agent.data.access import get_job_analysis

    mock_read.return_value = {
        "status": "error",
        "message": "Database query failed",
    }

    # Should raise ValueError on error status
    with pytest.raises(ValueError, match="Failed to read job analysis"):
        get_job_analysis("ACME Corp", "Developer")

    mock_read.assert_called_once()


@patch("resume_agent.data_read_job_analysis")
def test_get_job_analysis_case_insensitive(mock_read):
    """Test that case-insensitive matching works."""
    from src.resume_agent.data.access import get_job_analysis

    mock_read.return_value = {
        "status": "success",
        "data": {
            "company": "acme corp",
            "job_title": "senior developer",
        },
    }

    result = get_job_analysis("ACME CORP", "SENIOR DEVELOPER")

    # MCP server handles case-insensitive matching
    mock_read.assert_called_once_with(company="ACME CORP", job_title="SENIOR DEVELOPER")
    assert result["company"] == "acme corp"


# ============================================================================
# TEST SEARCH_PORTFOLIO_BY_TECH
# ============================================================================


@patch("resume_agent.data_search_portfolio_examples")
def test_search_portfolio_by_tech_with_results(mock_search):
    """Test searching portfolio with results."""
    from src.resume_agent.data.access import search_portfolio_by_tech

    mock_search.return_value = {
        "status": "success",
        "examples": [
            {
                "id": "ex1",
                "title": "FastAPI REST API",
                "content": "Built REST API with FastAPI and PostgreSQL",
                "technologies": ["Python", "FastAPI", "PostgreSQL"],
                "repo_url": "https://github.com/user/api-project",
            },
            {
                "id": "ex2",
                "title": "Python Data Pipeline",
                "content": "ETL pipeline processing 1M records/day",
                "technologies": ["Python", "Pandas", "Apache Airflow"],
                "repo_url": "https://github.com/user/data-pipeline",
            },
        ],
    }

    results = search_portfolio_by_tech("Python", limit=10)

    mock_search.assert_called_once_with(query="Python", technologies=["Python"])

    assert len(results) == 2
    assert results[0]["title"] == "FastAPI REST API"
    assert "Python" in results[0]["technologies"]
    assert results[1]["title"] == "Python Data Pipeline"


@patch("resume_agent.data_search_portfolio_examples")
def test_search_portfolio_by_tech_no_results(mock_search):
    """Test searching portfolio with no results."""
    from src.resume_agent.data.access import search_portfolio_by_tech

    mock_search.return_value = {
        "status": "success",
        "examples": [],
    }

    results = search_portfolio_by_tech("Obscure-Tech", limit=10)

    assert results == []


@patch("resume_agent.data_search_portfolio_examples")
def test_search_portfolio_by_tech_with_limit(mock_search):
    """Test that limit parameter works correctly."""
    from src.resume_agent.data.access import search_portfolio_by_tech

    # Return 15 examples
    mock_search.return_value = {
        "status": "success",
        "examples": [{"id": f"ex{i}", "title": f"Example {i}"} for i in range(15)],
    }

    results = search_portfolio_by_tech("Python", limit=5)

    # Should only return 5 examples
    assert len(results) == 5
    assert results[0]["id"] == "ex0"
    assert results[4]["id"] == "ex4"


@patch("resume_agent.data_search_portfolio_examples")
def test_search_portfolio_by_tech_error(mock_search):
    """Test error handling during portfolio search (should return empty list)."""
    from src.resume_agent.data.access import search_portfolio_by_tech

    mock_search.return_value = {
        "status": "error",
        "message": "Vector search failed",
    }

    # Should return empty list on error (graceful degradation)
    results = search_portfolio_by_tech("Python")

    assert results == []


@patch("resume_agent.data_search_portfolio_examples")
def test_search_portfolio_by_tech_missing_examples_field(mock_search):
    """Test handling when examples field is missing."""
    from src.resume_agent.data.access import search_portfolio_by_tech

    mock_search.return_value = {"status": "success"}

    results = search_portfolio_by_tech("Python")

    # Should return empty list when examples field is missing
    assert results == []


# ============================================================================
# TEST SAVE_JOB_ANALYSIS
# ============================================================================


@patch("resume_agent.data_write_job_analysis")
def test_save_job_analysis_success(mock_write):
    """Test successful save of job analysis."""
    from src.resume_agent.data.access import save_job_analysis

    mock_write.return_value = {
        "status": "success",
        "message": "Job analysis saved successfully",
    }

    job_data = {
        "url": "https://example.com/job",
        "company": "ACME Corp",
        "job_title": "Senior Developer",
        "required_qualifications": ["Python", "SQL"],
        "keywords": ["Python", "FastAPI", "PostgreSQL"],
    }

    result = save_job_analysis("ACME Corp", "Senior Developer", job_data)

    mock_write.assert_called_once_with(
        company="ACME Corp", job_title="Senior Developer", job_data=job_data
    )

    assert result["status"] == "success"
    assert "saved successfully" in result["message"]


@patch("resume_agent.data_write_job_analysis")
def test_save_job_analysis_error(mock_write):
    """Test error handling when save fails."""
    from src.resume_agent.data.access import save_job_analysis

    mock_write.return_value = {
        "status": "error",
        "message": "Database write failed",
    }

    job_data = {"company": "ACME", "job_title": "Developer"}

    with pytest.raises(ValueError, match="Failed to save job analysis"):
        save_job_analysis("ACME", "Developer", job_data)


# ============================================================================
# TEST SAVE_TAILORED_RESUME
# ============================================================================


@patch("resume_agent.data_write_tailored_resume")
def test_save_tailored_resume_success(mock_write):
    """Test successful save of tailored resume."""
    from src.resume_agent.data.access import save_tailored_resume

    mock_write.return_value = {
        "status": "success",
        "message": "Tailored resume saved",
        "file_path": "/path/to/resumes/acme_developer.yaml",
    }

    content = "# John Doe\n\n## Experience\n..."
    metadata = {"keywords_used": ["Python", "FastAPI"], "format": "markdown"}

    result = save_tailored_resume("ACME", "Developer", content, metadata)

    mock_write.assert_called_once_with(
        company="ACME", job_title="Developer", content=content, metadata=metadata
    )

    assert result["status"] == "success"
    assert "file_path" in result


@patch("resume_agent.data_write_tailored_resume")
def test_save_tailored_resume_without_metadata(mock_write):
    """Test saving tailored resume without metadata."""
    from src.resume_agent.data.access import save_tailored_resume

    mock_write.return_value = {
        "status": "success",
        "message": "Tailored resume saved",
        "file_path": "/path/to/resumes/acme_developer.yaml",
    }

    content = "# John Doe\n\n## Experience\n..."

    result = save_tailored_resume("ACME", "Developer", content)

    # Should pass empty dict when metadata is None
    mock_write.assert_called_once_with(
        company="ACME", job_title="Developer", content=content, metadata={}
    )

    assert result["status"] == "success"


@patch("resume_agent.data_write_tailored_resume")
def test_save_tailored_resume_error(mock_write):
    """Test error handling when save fails."""
    from src.resume_agent.data.access import save_tailored_resume

    mock_write.return_value = {
        "status": "error",
        "message": "File write permission denied",
    }

    with pytest.raises(ValueError, match="Failed to save tailored resume"):
        save_tailored_resume("ACME", "Developer", "content")


# ============================================================================
# TEST SAVE_COVER_LETTER
# ============================================================================


@patch("resume_agent.data_write_cover_letter")
def test_save_cover_letter_success(mock_write):
    """Test successful save of cover letter."""
    from src.resume_agent.data.access import save_cover_letter

    mock_write.return_value = {
        "status": "success",
        "message": "Cover letter saved",
        "file_path": "/path/to/letters/acme_developer.md",
    }

    content = "Dear Hiring Manager,\n\n..."
    metadata = {
        "talking_points": ["React expertise", "Team leadership"],
        "tone": "professional",
    }

    result = save_cover_letter("ACME", "Developer", content, metadata)

    mock_write.assert_called_once_with(
        company="ACME", job_title="Developer", content=content, metadata=metadata
    )

    assert result["status"] == "success"
    assert "file_path" in result


@patch("resume_agent.data_write_cover_letter")
def test_save_cover_letter_without_metadata(mock_write):
    """Test saving cover letter without metadata."""
    from src.resume_agent.data.access import save_cover_letter

    mock_write.return_value = {
        "status": "success",
        "message": "Cover letter saved",
        "file_path": "/path/to/letters/acme_developer.md",
    }

    content = "Dear Hiring Manager,\n\n..."

    result = save_cover_letter("ACME", "Developer", content)

    # Should pass empty dict when metadata is None
    mock_write.assert_called_once_with(
        company="ACME", job_title="Developer", content=content, metadata={}
    )

    assert result["status"] == "success"


@patch("resume_agent.data_write_cover_letter")
def test_save_cover_letter_error(mock_write):
    """Test error handling when save fails."""
    from src.resume_agent.data.access import save_cover_letter

    mock_write.return_value = {
        "status": "error",
        "message": "Database connection lost",
    }

    with pytest.raises(ValueError, match="Failed to save cover letter"):
        save_cover_letter("ACME", "Developer", "content")


# ============================================================================
# TEST LIST_APPLICATIONS
# ============================================================================


@patch("resume_agent.data_list_applications")
def test_list_applications_success(mock_list):
    """Test successful listing of applications."""
    from src.resume_agent.data.access import list_applications

    mock_list.return_value = {
        "status": "success",
        "applications": [
            {
                "company": "ACME Corp",
                "job_title": "Senior Developer",
                "status": "applied",
                "applied_date": "2023-10-15",
                "has_tailored_resume": True,
                "has_cover_letter": True,
            },
            {
                "company": "TechCorp",
                "job_title": "Lead Engineer",
                "status": "interviewing",
                "applied_date": "2023-10-20",
                "has_tailored_resume": True,
                "has_cover_letter": False,
            },
        ],
    }

    results = list_applications(limit=10)

    mock_list.assert_called_once_with(limit=10)

    assert len(results) == 2
    assert results[0]["company"] == "ACME Corp"
    assert results[0]["has_tailored_resume"] is True
    assert results[1]["status"] == "interviewing"


@patch("resume_agent.data_list_applications")
def test_list_applications_empty(mock_list):
    """Test listing applications when none exist."""
    from src.resume_agent.data.access import list_applications

    mock_list.return_value = {"status": "success", "applications": []}

    results = list_applications()

    assert results == []


@patch("resume_agent.data_list_applications")
def test_list_applications_error(mock_list):
    """Test error handling during list operation (should return empty list)."""
    from src.resume_agent.data.access import list_applications

    mock_list.return_value = {
        "status": "error",
        "message": "Database query failed",
    }

    # Should return empty list on error (graceful degradation)
    results = list_applications(limit=5)

    assert results == []


@patch("resume_agent.data_list_applications")
def test_list_applications_default_limit(mock_list):
    """Test that default limit is 10."""
    from src.resume_agent.data.access import list_applications

    mock_list.return_value = {"status": "success", "applications": []}

    list_applications()

    # Should use default limit of 10
    mock_list.assert_called_once_with(limit=10)


# ============================================================================
# CONTRACT TESTS
# ============================================================================


def test_mcp_server_functions_importable():
    """
    Contract test: Verify MCP server functions are importable.

    This test ensures the MCP server module exists and exports
    the expected data access functions.
    """
    import sys
    from pathlib import Path

    # Add MCP server to path
    mcp_server_path = Path(__file__).parent.parent.parent / "resume-agent"
    sys.path.insert(0, str(mcp_server_path))

    try:
        from resume_agent import (
            data_read_master_resume,
            data_read_career_history,
            data_read_job_analysis,
            data_search_portfolio_examples,
            data_write_job_analysis,
            data_write_tailored_resume,
            data_write_cover_letter,
            data_list_applications,
        )

        # Verify functions are callable
        assert callable(data_read_master_resume)
        assert callable(data_read_career_history)
        assert callable(data_read_job_analysis)
        assert callable(data_search_portfolio_examples)
        assert callable(data_write_job_analysis)
        assert callable(data_write_tailored_resume)
        assert callable(data_write_cover_letter)
        assert callable(data_list_applications)

    except ImportError as e:
        pytest.fail(f"Failed to import MCP server functions: {e}")


def test_mcp_function_signatures():
    """
    Contract test: Verify MCP server function signatures match expectations.

    This ensures the wrapper functions are compatible with the MCP server API.
    """
    import inspect
    import sys
    from pathlib import Path

    mcp_server_path = Path(__file__).parent.parent.parent / "resume-agent"
    sys.path.insert(0, str(mcp_server_path))

    from resume_agent import (
        data_read_master_resume,
        data_read_job_analysis,
        data_search_portfolio_examples,
        data_write_job_analysis,
    )

    # Test data_read_master_resume signature (no parameters)
    sig = inspect.signature(data_read_master_resume)
    # Function has no required parameters (may have optional ones)
    required_params = [p for p in sig.parameters.values() if p.default == inspect.Parameter.empty]
    assert len(required_params) == 0, f"data_read_master_resume should have no required parameters, found {list(sig.parameters.keys())}"

    # Test data_read_job_analysis signature (company, job_title)
    sig = inspect.signature(data_read_job_analysis)
    assert "company" in sig.parameters, "data_read_job_analysis should have 'company' parameter"
    assert (
        "job_title" in sig.parameters
    ), "data_read_job_analysis should have 'job_title' parameter"

    # Test data_search_portfolio_examples signature (query, technologies)
    sig = inspect.signature(data_search_portfolio_examples)
    assert (
        "query" in sig.parameters
    ), "data_search_portfolio_examples should have 'query' parameter"
    # technologies may be optional

    # Test data_write_job_analysis signature (company, job_title, job_data)
    sig = inspect.signature(data_write_job_analysis)
    assert (
        "company" in sig.parameters
    ), "data_write_job_analysis should have 'company' parameter"
    assert (
        "job_title" in sig.parameters
    ), "data_write_job_analysis should have 'job_title' parameter"
    assert (
        "job_data" in sig.parameters
    ), "data_write_job_analysis should have 'job_data' parameter"
