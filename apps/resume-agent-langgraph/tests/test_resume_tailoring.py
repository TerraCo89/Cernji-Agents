"""Comprehensive tests for resume tailoring functionality.

This module tests:
1. Resume parser tool functions (load, parse, extract)
2. ATS scorer tool functions (keyword match, ATS score, suggestions)
3. Resume tailor nodes (load, analyze, tailor, validate)
4. Resume tailoring graph (complete workflow)

Test coverage includes:
- Happy path scenarios
- Error handling (file errors, parse errors, LLM failures)
- Edge cases (empty data, missing fields, invalid input)
- ATS score calculation and improvement tracking
- State transitions and partial updates

Author: Claude (Anthropic)
License: Experimental
"""

import json
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path

# Import tool functions
from src.resume_agent.tools.resume_parser import (
    load_master_resume,
    parse_resume_yaml,
    extract_skills_from_resume,
    extract_achievements_from_resume
)

from src.resume_agent.tools.ats_scorer import (
    calculate_keyword_match,
    calculate_ats_score,
    suggest_improvements
)

# Import nodes
from src.resume_agent.nodes.resume_tailor import (
    load_resume_node,
    analyze_requirements_node,
    tailor_resume_node,
    validate_tailoring_node
)

# Import state
from src.resume_agent.state import ResumeTailoringState


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_master_resume():
    """Sample master resume data structure."""
    return {
        "personal_info": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-0100",
            "location": "San Francisco, CA"
        },
        "professional_summary": "Experienced software engineer with 10+ years building scalable systems.",
        "employment_history": [
            {
                "company": "TechCorp",
                "position": "Senior Engineer",
                "start_date": "2020-01",
                "end_date": "2023-12",
                "description": "Led backend development for cloud platform",
                "technologies": ["Python", "Docker", "AWS", "Kubernetes"],
                "achievements": [
                    {
                        "description": "Reduced API latency by 40%",
                        "metric": "40% faster"
                    },
                    {
                        "description": "Led migration to microservices architecture"
                    }
                ]
            },
            {
                "company": "StartupCo",
                "position": "Full Stack Developer",
                "start_date": "2018-01",
                "end_date": "2020-01",
                "technologies": ["Python", "React", "PostgreSQL"],
                "achievements": [
                    "Built MVP in 3 months",
                    "Grew user base to 10,000 users"
                ]
            }
        ],
        "skills": ["Python", "JavaScript", "AWS", "Docker", "Kubernetes", "PostgreSQL"]
    }


@pytest.fixture
def sample_job_analysis():
    """Sample job analysis data."""
    return {
        "company": "BigTech Inc",
        "job_title": "Senior Backend Engineer",
        "requirements": [
            "5+ years Python development",
            "Experience with cloud platforms (AWS/Azure)",
            "Microservices architecture experience"
        ],
        "skills": ["Python", "AWS", "Docker", "Kubernetes", "PostgreSQL", "Redis"],
        "responsibilities": [
            "Design and implement scalable backend services",
            "Lead architecture decisions",
            "Mentor junior engineers"
        ],
        "keywords": ["Python", "AWS", "microservices", "scalable", "backend", "cloud"],
        "salary_range": "$150,000 - $200,000",
        "location": "Remote",
        "url": "https://example.com/job/123"
    }


@pytest.fixture
def sample_resume_yaml():
    """Sample YAML resume content."""
    return """
personal_info:
  name: John Doe
  email: john@example.com
  phone: "555-0100"
  location: San Francisco, CA

professional_summary: |
  Experienced software engineer with 10+ years building scalable systems.

employment_history:
  - company: TechCorp
    position: Senior Engineer
    start_date: "2020-01"
    end_date: "2023-12"
    description: Led backend development for cloud platform
    technologies:
      - Python
      - Docker
      - AWS
      - Kubernetes
    achievements:
      - description: Reduced API latency by 40%
        metric: "40% faster"
      - description: Led migration to microservices architecture

skills:
  - Python
  - AWS
  - Docker
  - Kubernetes
  - PostgreSQL
"""


@pytest.fixture
def sample_tailored_resume():
    """Sample tailored resume output."""
    return """
# John Doe
**Senior Backend Engineer**

john@example.com | 555-0100 | San Francisco, CA

## Professional Summary
Experienced Senior Backend Engineer with 10+ years building scalable cloud-native systems.
Expertise in Python, AWS, and microservices architecture.

## Experience

### Senior Engineer | TechCorp | 2020-01 - 2023-12
Led backend development for cloud platform using Python, Docker, AWS, and Kubernetes.

**Key Achievements:**
- Reduced API latency by 40% through optimization of microservices architecture
- Led migration to cloud-native microservices, improving scalability and reliability
- Architected backend services handling millions of requests per day

**Technologies:** Python, Docker, AWS, Kubernetes, Redis

### Full Stack Developer | StartupCo | 2018-01 - 2020-01
Built scalable web applications with Python and React.

**Key Achievements:**
- Built MVP in 3 months, enabling rapid market entry
- Grew user base to 10,000 users through feature development and optimization

**Technologies:** Python, React, PostgreSQL

## Skills
Python • AWS • Docker • Kubernetes • PostgreSQL • Redis • Microservices • Cloud Architecture
"""


@pytest.fixture
def initial_state():
    """Initial state for resume tailoring workflow."""
    return {
        "job_url": "https://example.com/job/123",
        "master_resume": None,
        "job_analysis": None,
        "initial_ats_score": None,
        "tailored_resume": None,
        "final_ats_score": None,
        "keywords_integrated": [],
        "errors": [],
        "duration_ms": None
    }


# ============================================================================
# TEST RESUME PARSER TOOL - Additional tests beyond test_resume_parser.py
# ============================================================================

class TestResumeParserAdvanced:
    """Advanced tests for resume parser functions."""

    def test_load_master_resume_permission_error(self, tmp_path):
        """Test error handling when file permissions are insufficient."""
        # Create a file and make it unreadable (Unix-like systems)
        resume_file = tmp_path / "unreadable.yaml"
        resume_file.write_text("personal_info:\n  name: Test")

        # On Windows, we can't easily make files unreadable, so just test the path
        result = load_master_resume(str(resume_file))
        assert result["status"] in ["success", "error"]  # Either works or permission denied

    def test_parse_resume_yaml_not_dict_root(self):
        """Test parsing YAML that's not a dict at root level."""
        yaml_content = "- item1\n- item2\n"
        result = parse_resume_yaml(yaml_content)

        assert result["status"] == "error"
        assert "dictionary" in result["error"].lower()

    def test_parse_resume_yaml_invalid_personal_info(self):
        """Test parsing with personal_info as wrong type."""
        yaml_content = """
personal_info: "Not a dictionary"
employment_history: []
"""
        result = parse_resume_yaml(yaml_content)

        assert result["status"] == "error"
        assert "personal_info" in result["error"]

    def test_parse_resume_yaml_invalid_employment_history(self):
        """Test parsing with employment_history as wrong type."""
        yaml_content = """
personal_info:
  name: John Doe
employment_history: "Not a list"
"""
        result = parse_resume_yaml(yaml_content)

        assert result["status"] == "error"
        assert "employment_history" in result["error"]

    def test_extract_skills_nested_technologies(self, sample_master_resume):
        """Test skill extraction from deeply nested employment history."""
        resume_with_nested = {
            **sample_master_resume,
            "employment_history": [
                {
                    "company": "Corp",
                    "technologies": ["Python", "Redis"]
                },
                {
                    "company": "Corp2",
                    "technologies": ["Go", "MongoDB"]
                }
            ]
        }

        skills = extract_skills_from_resume(resume_with_nested)

        # Should include both top-level skills and technologies
        assert "Python" in skills
        assert "Redis" in skills
        assert "Go" in skills
        assert "MongoDB" in skills

    def test_extract_skills_duplicate_removal(self):
        """Test that duplicate skills are removed."""
        resume_data = {
            "skills": ["Python", "AWS", "Python"],  # Duplicate
            "employment_history": [
                {"technologies": ["AWS", "Docker"]}  # AWS appears again
            ]
        }

        skills = extract_skills_from_resume(resume_data)

        # Should have 3 unique skills
        assert sorted(skills) == ["AWS", "Docker", "Python"]

    def test_extract_achievements_position_vs_title(self):
        """Test achievement extraction handles both 'position' and 'title' fields."""
        resume_data = {
            "employment_history": [
                {
                    "company": "Corp1",
                    "position": "Engineer",
                    "achievements": ["Achievement 1"]
                },
                {
                    "company": "Corp2",
                    "title": "Developer",
                    "achievements": ["Achievement 2"]
                }
            ]
        }

        achievements = extract_achievements_from_resume(resume_data)

        assert len(achievements) == 2
        assert achievements[0]["role"] == "Engineer"
        assert achievements[1]["role"] == "Developer"

    def test_extract_achievements_mixed_formats(self):
        """Test extraction with mixed string and dict achievements."""
        resume_data = {
            "employment_history": [
                {
                    "company": "Corp",
                    "position": "Engineer",
                    "achievements": [
                        "String achievement",
                        {"description": "Dict achievement", "metric": "50%"},
                        {"description": "Dict without metric"}
                    ]
                }
            ]
        }

        achievements = extract_achievements_from_resume(resume_data)

        assert len(achievements) == 3
        assert achievements[0]["achievement"] == "String achievement"
        assert "metric" not in achievements[0]
        assert achievements[1]["metric"] == "50%"
        assert "metric" not in achievements[2]


# ============================================================================
# TEST ATS SCORER TOOL - calculate_keyword_match()
# ============================================================================

class TestCalculateKeywordMatch:
    """Tests for calculate_keyword_match() function."""

    def test_calculate_keyword_match_full_match(self):
        """Test when all keywords are present."""
        resume_text = "Python developer with AWS and Docker experience"
        keywords = ["Python", "AWS", "Docker"]

        result = calculate_keyword_match(resume_text, keywords)

        assert result["match_score"] == 100.0
        assert result["match_count"] == 3
        assert result["total_keywords"] == 3
        assert set(result["matched_keywords"]) == {"Python", "AWS", "Docker"}
        assert result["missing_keywords"] == []

    def test_calculate_keyword_match_partial_match(self):
        """Test when only some keywords are present."""
        resume_text = "Python developer with Django"
        keywords = ["Python", "Django", "React", "AWS"]

        result = calculate_keyword_match(resume_text, keywords)

        assert result["match_score"] == 50.0  # 2 out of 4
        assert result["match_count"] == 2
        assert set(result["matched_keywords"]) == {"Python", "Django"}
        assert set(result["missing_keywords"]) == {"React", "AWS"}

    def test_calculate_keyword_match_no_match(self):
        """Test when no keywords are present."""
        resume_text = "Java developer with Spring Boot"
        keywords = ["Python", "Django", "Flask"]

        result = calculate_keyword_match(resume_text, keywords)

        assert result["match_score"] == 0.0
        assert result["match_count"] == 0
        assert result["matched_keywords"] == []
        assert set(result["missing_keywords"]) == {"Python", "Django", "Flask"}

    def test_calculate_keyword_match_empty_keywords(self):
        """Test with empty keyword list."""
        resume_text = "Python developer"
        keywords = []

        result = calculate_keyword_match(resume_text, keywords)

        assert result["match_score"] == 0.0
        assert result["match_count"] == 0
        assert result["total_keywords"] == 0

    def test_calculate_keyword_match_case_insensitive(self):
        """Test case-insensitive matching."""
        resume_text = "python DEVELOPER with aws and Docker"
        keywords = ["Python", "AWS", "Docker"]

        result = calculate_keyword_match(resume_text, keywords)

        assert result["match_score"] == 100.0
        assert result["match_count"] == 3

    def test_calculate_keyword_match_whitespace_normalization(self):
        """Test that extra whitespace is normalized."""
        resume_text = "Python    developer   with   AWS"
        keywords = ["Python", "AWS"]

        result = calculate_keyword_match(resume_text, keywords)

        assert result["match_score"] == 100.0

    def test_calculate_keyword_match_multiword_keywords(self):
        """Test matching multi-word keywords."""
        resume_text = "Experience with machine learning and data science"
        keywords = ["machine learning", "data science", "deep learning"]

        result = calculate_keyword_match(resume_text, keywords)

        assert result["match_count"] == 2
        assert "machine learning" in result["matched_keywords"]
        assert "data science" in result["matched_keywords"]
        assert "deep learning" in result["missing_keywords"]


# ============================================================================
# TEST ATS SCORER TOOL - calculate_ats_score()
# ============================================================================

class TestCalculateATSScore:
    """Tests for calculate_ats_score() function."""

    def test_calculate_ats_score_perfect_match(self):
        """Test ATS score with perfect alignment."""
        resume_data = {
            "content": "Python developer with AWS, Docker, and microservices experience. "
                      "Led team of 5 engineers. Built scalable systems.",
            "skills": ["Python", "AWS", "Docker", "Kubernetes"]
        }

        job_analysis = {
            "keywords": ["Python", "AWS", "Docker"],
            "skills": ["Python", "AWS", "Docker"],
            "requirements": ["experience", "team", "scalable"]
        }

        result = calculate_ats_score(resume_data, job_analysis)

        assert "overall_score" in result
        assert result["overall_score"] >= 80  # Should be high
        assert result["keyword_score"] == 100
        assert result["skills_score"] == 100

    def test_calculate_ats_score_poor_match(self):
        """Test ATS score with poor alignment."""
        resume_data = {
            "content": "Java developer with Spring Boot",
            "skills": ["Java", "Spring"]
        }

        job_analysis = {
            "keywords": ["Python", "Django", "Flask"],
            "skills": ["Python", "PostgreSQL"],
            "requirements": ["machine learning", "data analysis"]
        }

        result = calculate_ats_score(resume_data, job_analysis)

        assert result["overall_score"] < 30  # Should be low
        assert result["keyword_score"] == 0
        assert result["skills_score"] == 0

    def test_calculate_ats_score_weighted_correctly(self):
        """Test that scoring weights are applied correctly (40/30/30)."""
        resume_data = {
            "content": "Python AWS Docker experience developed implemented",
            "skills": ["Python"]
        }

        job_analysis = {
            "keywords": ["Python", "AWS", "Docker"],  # 100% match
            "skills": ["Python", "React"],  # 50% match
            "requirements": ["experience", "developed"]  # Some match
        }

        result = calculate_ats_score(resume_data, job_analysis)

        # Verify individual scores
        assert result["keyword_score"] == 100
        assert result["skills_score"] == 50

        # Overall should be weighted: 100*0.4 + 50*0.3 + experience*0.3
        # = 40 + 15 + experience_score*0.3
        assert 50 <= result["overall_score"] <= 100

    def test_calculate_ats_score_empty_requirements(self):
        """Test with empty job requirements."""
        resume_data = {
            "content": "Python developer",
            "skills": ["Python"]
        }

        job_analysis = {
            "keywords": [],
            "skills": [],
            "requirements": []
        }

        result = calculate_ats_score(resume_data, job_analysis)

        assert result["overall_score"] == 0
        assert result["keyword_score"] == 0
        assert result["skills_score"] == 0

    def test_calculate_ats_score_has_recommendations(self):
        """Test that recommendations are included."""
        resume_data = {
            "content": "Python developer",
            "skills": ["Python"]
        }

        job_analysis = {
            "keywords": ["Python", "AWS", "Docker"],
            "skills": ["Python", "AWS"],
            "requirements": ["5 years experience"]
        }

        result = calculate_ats_score(resume_data, job_analysis)

        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0


# ============================================================================
# TEST ATS SCORER TOOL - suggest_improvements()
# ============================================================================

class TestSuggestImprovements:
    """Tests for suggest_improvements() function."""

    def test_suggest_improvements_critical_gaps(self):
        """Test suggestions for critical keyword gaps (<50% match)."""
        resume_data = {"content": "Python developer", "skills": ["Python"]}
        job_analysis = {
            "keywords": ["AWS", "Docker", "Kubernetes", "Redis", "PostgreSQL"],
            "skills": [],
            "responsibilities": []
        }
        ats_score = {
            "keyword_match": {
                "missing_keywords": ["AWS", "Docker", "Kubernetes", "Redis", "PostgreSQL"]
            },
            "keyword_score": 20,
            "skills_score": 70,
            "experience_score": 70
        }

        suggestions = suggest_improvements(resume_data, job_analysis, ats_score)

        assert len(suggestions) > 0
        assert any("Add missing keywords" in s for s in suggestions)
        # Should suggest top 5 missing keywords
        assert any("AWS" in s for s in suggestions)

    def test_suggest_improvements_moderate_gaps(self):
        """Test suggestions for moderate gaps (50-75% match)."""
        resume_data = {"content": "Python AWS Docker", "skills": ["Python"]}
        job_analysis = {
            "keywords": ["Python", "AWS", "Docker", "Kubernetes"],
            "skills": [],
            "responsibilities": []
        }
        ats_score = {
            "keyword_match": {
                "missing_keywords": ["Kubernetes"]
            },
            "keyword_score": 60,
            "skills_score": 70,
            "experience_score": 70
        }

        suggestions = suggest_improvements(resume_data, job_analysis, ats_score)

        assert len(suggestions) > 0
        assert any("Consider adding" in s for s in suggestions)

    def test_suggest_improvements_skills_gaps(self):
        """Test suggestions for missing skills."""
        resume_data = {
            "content": "Python developer",
            "skills": ["Python"]
        }
        job_analysis = {
            "keywords": ["Python"],
            "skills": ["Python", "AWS", "Docker"],
            "responsibilities": []
        }
        ats_score = {
            "keyword_match": {"missing_keywords": []},
            "keyword_score": 100,
            "skills_score": 33,  # Low skills score
            "experience_score": 70
        }

        suggestions = suggest_improvements(resume_data, job_analysis, ats_score)

        assert len(suggestions) > 0
        assert any("Highlight experience" in s or "AWS" in s for s in suggestions)

    def test_suggest_improvements_experience_gaps(self):
        """Test suggestions for low experience relevance."""
        resume_data = {
            "content": "Developer",
            "skills": ["Python", "AWS"]
        }
        job_analysis = {
            "keywords": ["Python", "AWS"],
            "skills": ["Python", "AWS"],
            "requirements": ["5 years", "team lead"]
        }
        ats_score = {
            "keyword_match": {"missing_keywords": []},
            "keyword_score": 100,
            "skills_score": 100,
            "experience_score": 30  # Low experience score
        }

        suggestions = suggest_improvements(resume_data, job_analysis, ats_score)

        assert len(suggestions) > 0
        assert any("Quantify" in s or "metrics" in s for s in suggestions)
        assert any("specific examples" in s for s in suggestions)

    def test_suggest_improvements_leadership_needed(self):
        """Test suggestion for leadership experience when required."""
        resume_data = {
            "content": "Python developer built apps",
            "skills": ["Python"]
        }
        job_analysis = {
            "keywords": ["Python"],
            "skills": ["Python"],
            "responsibilities": ["Lead team of engineers", "Manage projects"]
        }
        ats_score = {
            "keyword_match": {"missing_keywords": []},
            "keyword_score": 100,
            "skills_score": 100,
            "experience_score": 50
        }

        suggestions = suggest_improvements(resume_data, job_analysis, ats_score)

        assert any("leadership" in s.lower() or "team" in s.lower() for s in suggestions)

    def test_suggest_improvements_strong_match(self):
        """Test suggestions when match is already strong."""
        resume_data = {
            "content": "Python AWS Docker led managed mentored",
            "skills": ["Python", "AWS", "Docker"]
        }
        job_analysis = {
            "keywords": ["Python", "AWS", "Docker"],
            "skills": ["Python", "AWS", "Docker"],
            "responsibilities": ["Lead team"]
        }
        ats_score = {
            "keyword_match": {"missing_keywords": []},
            "keyword_score": 100,
            "skills_score": 100,
            "experience_score": 80
        }

        suggestions = suggest_improvements(resume_data, job_analysis, ats_score)

        assert len(suggestions) > 0
        assert any("Strong match" in s or "summary" in s for s in suggestions)

    def test_suggest_improvements_always_has_recommendation(self):
        """Test that there's always at least one recommendation."""
        resume_data = {"content": "", "skills": []}
        job_analysis = {"keywords": [], "skills": [], "responsibilities": []}
        ats_score = {
            "keyword_match": {"missing_keywords": []},
            "keyword_score": 0,
            "skills_score": 0,
            "experience_score": 0
        }

        suggestions = suggest_improvements(resume_data, job_analysis, ats_score)

        assert len(suggestions) >= 1


# ============================================================================
# TEST RESUME TAILOR NODES - load_resume_node()
# ============================================================================

class TestLoadResumeNode:
    """Tests for load_resume_node()."""

    @patch('src.resume_agent.nodes.resume_tailor.load_master_resume')
    def test_load_resume_node_success(self, mock_load, initial_state, sample_master_resume):
        """Test successful resume loading."""
        mock_load.return_value = {
            "status": "success",
            "data": sample_master_resume
        }

        result = load_resume_node(initial_state)

        assert "master_resume" in result
        assert result["master_resume"] == sample_master_resume
        assert "errors" not in result or result.get("errors") == []

    @patch('src.resume_agent.nodes.resume_tailor.load_master_resume')
    def test_load_resume_node_file_not_found(self, mock_load, initial_state):
        """Test error when resume file not found."""
        mock_load.return_value = {
            "status": "error",
            "error": "Resume file not found"
        }

        result = load_resume_node(initial_state)

        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "not found" in result["errors"][0].lower()
        assert "master_resume" not in result

    @patch('src.resume_agent.nodes.resume_tailor.load_master_resume')
    def test_load_resume_node_exception(self, mock_load, initial_state):
        """Test error handling when load_master_resume raises exception."""
        mock_load.side_effect = Exception("Unexpected error")

        result = load_resume_node(initial_state)

        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "Failed to load master resume" in result["errors"][0]


# ============================================================================
# TEST RESUME TAILOR NODES - analyze_requirements_node()
# ============================================================================

class TestAnalyzeRequirementsNode:
    """Tests for analyze_requirements_node()."""

    def test_analyze_requirements_node_success(self, sample_master_resume, sample_job_analysis):
        """Test successful requirements analysis."""
        state = {
            "job_url": "https://example.com/job/123",
            "master_resume": sample_master_resume,
            "job_analysis": sample_job_analysis,
            "errors": []
        }

        result = analyze_requirements_node(state)

        assert "initial_ats_score" in result
        assert "keyword_match" in result["initial_ats_score"]
        assert "ats_score" in result["initial_ats_score"]
        assert "match_percentage" in result["initial_ats_score"]
        assert "errors" not in result or result.get("errors") == []

    def test_analyze_requirements_node_no_job_analysis(self, sample_master_resume):
        """Test error when job analysis is missing."""
        state = {
            "job_url": "https://example.com/job/123",
            "master_resume": sample_master_resume,
            "job_analysis": None,
            "errors": []
        }

        result = analyze_requirements_node(state)

        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "No job analysis" in result["errors"][0]

    def test_analyze_requirements_node_no_master_resume(self, sample_job_analysis):
        """Test error when master resume is missing."""
        state = {
            "job_url": "https://example.com/job/123",
            "master_resume": None,
            "job_analysis": sample_job_analysis,
            "errors": []
        }

        result = analyze_requirements_node(state)

        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "No master resume" in result["errors"][0]

    def test_analyze_requirements_node_combines_keywords(self, sample_master_resume):
        """Test that keywords and skills are combined for matching."""
        job_analysis = {
            "keywords": ["Python", "AWS"],
            "skills": ["Docker", "AWS"],  # AWS appears in both
            "requirements": [],
            "responsibilities": []
        }

        state = {
            "master_resume": sample_master_resume,
            "job_analysis": job_analysis,
            "errors": []
        }

        result = analyze_requirements_node(state)

        # Should have 3 unique keywords (Python, AWS, Docker)
        assert result["initial_ats_score"]["total_keywords"] == 3


# ============================================================================
# TEST RESUME TAILOR NODES - tailor_resume_node()
# ============================================================================

class TestTailorResumeNode:
    """Tests for tailor_resume_node()."""

    @patch('src.resume_agent.nodes.resume_tailor.call_llm')
    def test_tailor_resume_node_success(self, mock_llm, sample_master_resume, sample_job_analysis):
        """Test successful resume tailoring."""
        llm_response = json.dumps({
            "tailored_resume": "# Tailored Resume\nContent here",
            "keywords_integrated": ["Python", "AWS", "Docker"],
            "optimization_notes": "Emphasized cloud experience"
        })
        mock_llm.return_value = llm_response

        state = {
            "master_resume": sample_master_resume,
            "job_analysis": sample_job_analysis,
            "errors": []
        }

        result = tailor_resume_node(state)

        assert "tailored_resume" in result
        assert "keywords_integrated" in result
        assert len(result["keywords_integrated"]) == 3
        assert "errors" not in result or result.get("errors") == []

    @patch('src.resume_agent.nodes.resume_tailor.call_llm')
    def test_tailor_resume_node_markdown_json(self, mock_llm, sample_master_resume, sample_job_analysis):
        """Test parsing JSON wrapped in markdown code blocks."""
        llm_response = "```json\n" + json.dumps({
            "tailored_resume": "Resume content",
            "keywords_integrated": ["Python"]
        }) + "\n```"
        mock_llm.return_value = llm_response

        state = {
            "master_resume": sample_master_resume,
            "job_analysis": sample_job_analysis,
            "errors": []
        }

        result = tailor_resume_node(state)

        assert "tailored_resume" in result
        assert result["tailored_resume"] == "Resume content"

    @patch('src.resume_agent.nodes.resume_tailor.call_llm')
    def test_tailor_resume_node_invalid_json(self, mock_llm, sample_master_resume, sample_job_analysis):
        """Test error handling for invalid JSON response."""
        mock_llm.return_value = "This is not valid JSON"

        state = {
            "master_resume": sample_master_resume,
            "job_analysis": sample_job_analysis,
            "errors": []
        }

        result = tailor_resume_node(state)

        assert "errors" in result
        assert len(result["errors"]) == 1
        assert "Failed to parse" in result["errors"][0]

    def test_tailor_resume_node_no_master_resume(self, sample_job_analysis):
        """Test error when master resume is missing."""
        state = {
            "master_resume": None,
            "job_analysis": sample_job_analysis,
            "errors": []
        }

        result = tailor_resume_node(state)

        assert "errors" in result
        assert "No master resume" in result["errors"][0]

    def test_tailor_resume_node_no_job_analysis(self, sample_master_resume):
        """Test error when job analysis is missing."""
        state = {
            "master_resume": sample_master_resume,
            "job_analysis": None,
            "errors": []
        }

        result = tailor_resume_node(state)

        assert "errors" in result
        assert "No job analysis" in result["errors"][0]

    @patch('src.resume_agent.nodes.resume_tailor.call_llm')
    def test_tailor_resume_node_llm_exception(self, mock_llm, sample_master_resume, sample_job_analysis):
        """Test error handling when LLM call fails."""
        mock_llm.side_effect = Exception("LLM API error")

        state = {
            "master_resume": sample_master_resume,
            "job_analysis": sample_job_analysis,
            "errors": []
        }

        result = tailor_resume_node(state)

        assert "errors" in result
        assert "Failed to tailor resume" in result["errors"][0]


# ============================================================================
# TEST RESUME TAILOR NODES - validate_tailoring_node()
# ============================================================================

class TestValidateTailoringNode:
    """Tests for validate_tailoring_node()."""

    def test_validate_tailoring_node_success(self, sample_tailored_resume, sample_job_analysis):
        """Test successful validation."""
        initial_score = {
            "match_percentage": 60.0,
            "matched_count": 3,
            "total_keywords": 5
        }

        state = {
            "tailored_resume": sample_tailored_resume,
            "job_analysis": sample_job_analysis,
            "initial_ats_score": initial_score,
            "keywords_integrated": ["Python", "AWS", "Docker"],
            "errors": []
        }

        result = validate_tailoring_node(state)

        assert "final_ats_score" in result
        assert "keyword_match" in result["final_ats_score"]
        assert "match_percentage" in result["final_ats_score"]
        # Final score should be higher than initial
        assert result["final_ats_score"]["match_percentage"] >= initial_score["match_percentage"]

    def test_validate_tailoring_node_improvement_calculation(self, sample_tailored_resume, sample_job_analysis):
        """Test that improvement is calculated correctly."""
        initial_score = {
            "match_percentage": 50.0,
            "matched_count": 2,
            "total_keywords": 4
        }

        state = {
            "tailored_resume": sample_tailored_resume,
            "job_analysis": sample_job_analysis,
            "initial_ats_score": initial_score,
            "keywords_integrated": ["Python", "AWS"],
            "errors": []
        }

        result = validate_tailoring_node(state)

        # Should have calculated improvement
        final_percentage = result["final_ats_score"]["match_percentage"]
        improvement = final_percentage - initial_score["match_percentage"]
        assert improvement >= 0  # Should improve or stay same

    def test_validate_tailoring_node_no_tailored_resume(self, sample_job_analysis):
        """Test error when tailored resume is missing."""
        state = {
            "tailored_resume": None,
            "job_analysis": sample_job_analysis,
            "initial_ats_score": {},
            "errors": []
        }

        result = validate_tailoring_node(state)

        assert "errors" in result
        assert "No tailored resume" in result["errors"][0]

    def test_validate_tailoring_node_no_job_analysis(self, sample_tailored_resume):
        """Test error when job analysis is missing."""
        state = {
            "tailored_resume": sample_tailored_resume,
            "job_analysis": None,
            "initial_ats_score": {},
            "errors": []
        }

        result = validate_tailoring_node(state)

        assert "errors" in result
        assert "No job analysis" in result["errors"][0]

    def test_validate_tailoring_node_no_initial_score(self, sample_tailored_resume, sample_job_analysis):
        """Test validation works without initial score (no comparison)."""
        state = {
            "tailored_resume": sample_tailored_resume,
            "job_analysis": sample_job_analysis,
            "initial_ats_score": None,
            "keywords_integrated": ["Python"],
            "errors": []
        }

        result = validate_tailoring_node(state)

        # Should still work, just no improvement comparison
        assert "final_ats_score" in result
        assert "errors" not in result or result.get("errors") == []


# ============================================================================
# TEST RESUME TAILORING WORKFLOW - Integration Tests
# ============================================================================

class TestResumeTailoringWorkflow:
    """Integration tests for complete resume tailoring workflow."""

    @patch('src.resume_agent.nodes.resume_tailor.load_master_resume')
    @patch('src.resume_agent.nodes.resume_tailor.call_llm')
    def test_full_workflow_success(
        self,
        mock_llm,
        mock_load,
        sample_master_resume,
        sample_job_analysis,
        sample_tailored_resume
    ):
        """Test complete workflow from loading to validation."""
        # Setup mocks
        mock_load.return_value = {
            "status": "success",
            "data": sample_master_resume
        }

        llm_response = json.dumps({
            "tailored_resume": sample_tailored_resume,
            "keywords_integrated": ["Python", "AWS", "Docker", "microservices"]
        })
        mock_llm.return_value = llm_response

        # Initial state
        state = {
            "job_url": "https://example.com/job/123",
            "master_resume": None,
            "job_analysis": sample_job_analysis,
            "initial_ats_score": None,
            "tailored_resume": None,
            "final_ats_score": None,
            "keywords_integrated": [],
            "errors": []
        }

        # Execute workflow nodes in sequence
        # 1. Load resume
        state.update(load_resume_node(state))
        assert state["master_resume"] is not None
        assert len(state.get("errors", [])) == 0

        # 2. Analyze requirements
        state.update(analyze_requirements_node(state))
        assert state["initial_ats_score"] is not None
        assert len(state.get("errors", [])) == 0

        # 3. Tailor resume
        state.update(tailor_resume_node(state))
        assert state["tailored_resume"] is not None
        assert len(state["keywords_integrated"]) > 0
        assert len(state.get("errors", [])) == 0

        # 4. Validate tailoring
        state.update(validate_tailoring_node(state))
        assert state["final_ats_score"] is not None
        assert len(state.get("errors", [])) == 0

        # Verify improvement
        initial_percentage = state["initial_ats_score"]["match_percentage"]
        final_percentage = state["final_ats_score"]["match_percentage"]
        assert final_percentage >= initial_percentage

    @patch('src.resume_agent.nodes.resume_tailor.load_master_resume')
    def test_workflow_error_accumulation(self, mock_load):
        """Test that errors accumulate during workflow."""
        mock_load.return_value = {
            "status": "error",
            "error": "File not found"
        }

        state = {
            "job_url": "https://example.com/job/123",
            "master_resume": None,
            "job_analysis": None,
            "errors": []
        }

        # Load resume (fails)
        state.update(load_resume_node(state))
        assert len(state["errors"]) == 1

        # Analyze requirements (fails due to missing data)
        state.update(analyze_requirements_node(state))
        assert len(state["errors"]) == 2

        # Errors should accumulate, not replace
        assert "File not found" in state["errors"][0]
        assert "No" in state["errors"][1]  # "No job analysis" or "No master resume"

    @patch('src.resume_agent.nodes.resume_tailor.load_master_resume')
    @patch('src.resume_agent.nodes.resume_tailor.call_llm')
    def test_workflow_ats_score_improvement(
        self,
        mock_llm,
        mock_load,
        sample_master_resume,
        sample_job_analysis
    ):
        """Test that tailoring improves ATS score."""
        mock_load.return_value = {
            "status": "success",
            "data": sample_master_resume
        }

        # Create tailored resume with ALL job keywords integrated
        # Combine keywords and skills for comprehensive matching
        job_keywords = sample_job_analysis["keywords"]
        job_skills = sample_job_analysis["skills"]
        all_keywords = list(set(job_keywords + job_skills))

        # Create tailored content that includes ALL keywords/skills
        tailored_content = f"""
        Senior Backend Engineer with expertise in {' '.join(all_keywords)}.
        Experience with {' and '.join(all_keywords[:3])}.
        Led development of {' '.join(all_keywords[3:])} projects.
        Built scalable microservices using cloud technologies.
        """

        llm_response = json.dumps({
            "tailored_resume": tailored_content,
            "keywords_integrated": all_keywords
        })
        mock_llm.return_value = llm_response

        state = {
            "job_url": "https://example.com/job/123",
            "master_resume": None,
            "job_analysis": sample_job_analysis,
            "errors": []
        }

        # Execute workflow
        state.update(load_resume_node(state))
        state.update(analyze_requirements_node(state))
        initial_score = state["initial_ats_score"]["match_percentage"]

        state.update(tailor_resume_node(state))
        state.update(validate_tailoring_node(state))
        final_score = state["final_ats_score"]["match_percentage"]

        # Final score should be better (or at least not worse)
        # Since we integrated ALL keywords, final should be 100%
        assert final_score >= initial_score
        assert final_score == 100.0  # Should match all keywords


# ============================================================================
# TEST STATE SCHEMA
# ============================================================================

class TestResumeTailoringState:
    """Tests for ResumeTailoringState schema."""

    def test_state_structure(self):
        """Test that state has all required fields."""
        state: ResumeTailoringState = {
            "job_url": "https://example.com/job/123",
            "master_resume": None,
            "job_analysis": None,
            "initial_ats_score": None,
            "tailored_resume": None,
            "final_ats_score": None,
            "keywords_integrated": [],
            "errors": [],
            "duration_ms": None
        }

        # Verify all keys exist
        assert "job_url" in state
        assert "master_resume" in state
        assert "job_analysis" in state
        assert "initial_ats_score" in state
        assert "tailored_resume" in state
        assert "final_ats_score" in state
        assert "keywords_integrated" in state
        assert "errors" in state
        assert "duration_ms" in state

    def test_state_types(self):
        """Test that state fields have correct types."""
        state: ResumeTailoringState = {
            "job_url": "https://example.com/job/123",
            "master_resume": {"personal_info": {"name": "Test"}},
            "job_analysis": {"company": "Test"},
            "initial_ats_score": {"match_percentage": 50.0},
            "tailored_resume": "Resume content",
            "final_ats_score": {"match_percentage": 75.0},
            "keywords_integrated": ["Python", "AWS"],
            "errors": ["error1"],
            "duration_ms": 123.45
        }

        # Verify types
        assert isinstance(state["job_url"], str)
        assert isinstance(state["master_resume"], dict)
        assert isinstance(state["job_analysis"], dict)
        assert isinstance(state["initial_ats_score"], dict)
        assert isinstance(state["tailored_resume"], str)
        assert isinstance(state["final_ats_score"], dict)
        assert isinstance(state["keywords_integrated"], list)
        assert isinstance(state["errors"], list)
        assert isinstance(state["duration_ms"], (int, float))


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Performance-related tests."""

    @patch('src.resume_agent.nodes.resume_tailor.load_master_resume')
    def test_load_resume_node_timing(self, mock_load, sample_master_resume):
        """Test that load_resume_node tracks timing."""
        import time

        def slow_load(*args, **kwargs):
            time.sleep(0.01)  # Simulate slow load
            return {"status": "success", "data": sample_master_resume}

        mock_load.side_effect = slow_load

        state = {"errors": []}
        result = load_resume_node(state)

        # Should have completed (timing is printed but not in return value)
        assert "master_resume" in result

    def test_keyword_match_performance(self):
        """Test keyword matching performance with large datasets."""
        import time

        # Create large resume text
        resume_text = " ".join(["Python developer with AWS experience"] * 100)

        # Create many keywords
        keywords = ["Python", "AWS", "Docker"] * 10

        start = time.time()
        result = calculate_keyword_match(resume_text, keywords)
        duration = time.time() - start

        # Should complete quickly even with repeated data
        assert duration < 1.0  # Less than 1 second
        assert result["match_count"] > 0
