"""
Tests for tool implementations.
"""

import pytest
from resume_agent.tools import (
    ats_analyzer,
    analyze_resume_ats,
    calculate_keyword_match,
    extract_skills_from_text,
)


class TestATSAnalyzer:
    """Tests for ATS analyzer tool."""
    
    def test_analyze_ats_compatibility_basic(self):
        """Test basic ATS compatibility analysis."""
        resume = """
        John Doe
        john@example.com | (555) 123-4567
        
        EXPERIENCE
        Senior Software Engineer at Tech Corp
        - Developed Python applications
        - Led team of 5 engineers
        
        EDUCATION
        BS Computer Science
        
        SKILLS
        Python, Django, PostgreSQL
        """
        
        result = analyze_resume_ats(resume)
        
        assert "ats_score" in result
        assert "issues" in result
        assert "warnings" in result
        assert 0 <= result["ats_score"] <= 100
    
    def test_detect_missing_contact_info(self):
        """Test detection of missing contact information."""
        resume = "Just some text without contact info"
        
        result = analyze_resume_ats(resume)
        
        assert result["ats_score"] < 100
        assert any("email" in issue.lower() for issue in result["issues"])
    
    def test_detect_missing_sections(self):
        """Test detection of missing standard sections."""
        resume = "Random text without proper sections"
        
        result = analyze_resume_ats(resume)
        
        assert len(result["found_sections"]) < 3
        assert result["ats_score"] < 100


class TestKeywordMatching:
    """Tests for keyword matching functionality."""
    
    def test_calculate_keyword_match_perfect(self):
        """Test perfect keyword match."""
        resume = "I have experience with Python, Django, and PostgreSQL"
        keywords = ["Python", "Django", "PostgreSQL"]
        
        result = calculate_keyword_match(resume, keywords)
        
        assert result["match_percentage"] == 100.0
        assert len(result["matched_keywords"]) == 3
        assert len(result["missing_keywords"]) == 0
    
    def test_calculate_keyword_match_partial(self):
        """Test partial keyword match."""
        resume = "I have experience with Python and Django"
        keywords = ["Python", "Django", "PostgreSQL", "Docker"]
        
        result = calculate_keyword_match(resume, keywords)
        
        assert result["match_percentage"] == 50.0
        assert len(result["matched_keywords"]) == 2
        assert len(result["missing_keywords"]) == 2
    
    def test_keyword_matching_case_insensitive(self):
        """Test that keyword matching is case insensitive."""
        resume = "python DJANGO postgresql"
        keywords = ["Python", "Django", "PostgreSQL"]
        
        result = calculate_keyword_match(resume, keywords)
        
        assert result["match_percentage"] == 100.0


class TestSkillExtraction:
    """Tests for skill extraction."""
    
    def test_extract_programming_languages(self):
        """Test extraction of programming languages."""
        text = "Proficient in Python, JavaScript, and Go"
        
        skills = extract_skills_from_text(text)
        
        assert "Python" in skills or "python" in [s.lower() for s in skills]
        assert "JavaScript" in skills or "javascript" in [s.lower() for s in skills]
    
    def test_extract_frameworks(self):
        """Test extraction of frameworks."""
        text = "Experience with React, Django, and FastAPI"
        
        skills = extract_skills_from_text(text)
        
        assert len(skills) > 0
        # Check for any framework
        frameworks = ["React", "Django", "FastAPI"]
        assert any(fw in skills or fw.lower() in [s.lower() for s in skills] 
                  for fw in frameworks)
    
    def test_extract_cloud_platforms(self):
        """Test extraction of cloud platforms."""
        text = "Deployed on AWS and used Docker for containerization"
        
        skills = extract_skills_from_text(text)
        
        assert any(skill.upper() in ["AWS", "DOCKER"] for skill in skills)


# Integration tests
class TestToolIntegration:
    """Integration tests for tools."""
    
    def test_full_ats_analysis_pipeline(self):
        """Test complete ATS analysis pipeline."""
        resume = """
        Jane Smith
        jane@example.com | (555) 987-6543
        
        PROFESSIONAL EXPERIENCE
        Senior Python Developer at StartupXYZ
        - Built REST APIs using Django and FastAPI
        - Managed PostgreSQL databases
        - Deployed on AWS with Docker
        
        EDUCATION
        MS Computer Science, MIT
        
        SKILLS
        Python, Django, FastAPI, PostgreSQL, AWS, Docker, React
        """
        
        keywords = ["Python", "Django", "FastAPI", "PostgreSQL", "AWS", "Docker"]
        
        # Run ATS analysis
        ats_result = analyze_resume_ats(resume)
        
        # Run keyword matching
        keyword_result = calculate_keyword_match(resume, keywords)
        
        # Extract skills
        skills = extract_skills_from_text(resume)
        
        # Assertions
        assert ats_result["ats_score"] > 70  # Should score well
        assert keyword_result["match_percentage"] > 80  # High keyword match
        assert len(skills) > 5  # Should extract multiple skills
        assert ats_result["has_contact_info"] is True
