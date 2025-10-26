"""
Tests for node implementations.
"""

import pytest
from resume_agent.state import ResumeState
from resume_agent.nodes import (
    analyze_resume,
    score_resume,
    validate_resume,
)


@pytest.fixture
def sample_state():
    """Create a sample state for testing."""
    return {
        "resume_text": "Senior Software Engineer with 5 years experience in Python.",
        "job_posting_url": "https://example.com/job",
        "job_title": "Senior Python Developer",
        "job_requirements": [
            "5+ years Python experience",
            "Experience with Django",
            "Strong CS fundamentals"
        ],
        "job_skills": ["Python", "Django", "PostgreSQL", "Docker"],
        "ats_keywords": ["Python", "Django", "PostgreSQL", "Docker", "API"],
        "current_skills": [],
        "experience_summary": "",
        "skill_gaps": [],
        "optimized_sections": [],
        "ats_score": 0,
        "optimization_suggestions": [],
        "needs_manual_review": False,
        "reviewer_approved": False,
        "iteration_count": 0,
        "max_iterations": 3,
        "final_resume": "",
        "cover_letter": "",
    }


class TestAnalyzeResume:
    """Tests for resume analysis node."""
    
    def test_analyze_resume_extracts_skills(self, sample_state):
        """Test that resume analysis extracts skills."""
        # Note: This would fail without real API key
        # In production, mock the LLM responses
        pytest.skip("Requires API key - use mocking in real tests")
        
        result = analyze_resume(sample_state)
        
        assert "current_skills" in result
        assert "experience_summary" in result
        assert "skill_gaps" in result


class TestScoreResume:
    """Tests for resume scoring node."""
    
    def test_score_resume_calculates_ats_score(self, sample_state):
        """Test that scoring calculates ATS score."""
        result = score_resume(sample_state)
        
        assert "ats_score" in result
        assert isinstance(result["ats_score"], int)
        assert 0 <= result["ats_score"] <= 100
    
    def test_score_resume_identifies_review_needed(self, sample_state):
        """Test that low scores trigger manual review."""
        result = score_resume(sample_state)
        
        assert "needs_manual_review" in result
        assert isinstance(result["needs_manual_review"], bool)


class TestValidateResume:
    """Tests for resume validation node."""
    
    def test_validate_resume_returns_suggestions(self, sample_state):
        """Test that validation returns suggestions."""
        pytest.skip("Requires API key - use mocking in real tests")
        
        result = validate_resume(sample_state)
        
        assert "optimization_suggestions" in result
        assert isinstance(result["optimization_suggestions"], list)


# Integration test example
class TestNodeIntegration:
    """Integration tests for node workflows."""
    
    def test_full_analysis_flow(self, sample_state):
        """Test complete analysis workflow."""
        pytest.skip("Integration test - requires full setup")
        
        # This would test the full flow:
        # analyze_resume -> optimize -> score -> validate
        pass
