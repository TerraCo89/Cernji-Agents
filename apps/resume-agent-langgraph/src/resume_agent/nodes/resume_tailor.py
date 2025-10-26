"""Resume tailoring nodes for LangGraph workflows.

This module provides nodes for loading master resumes, analyzing requirements,
tailoring resumes for specific jobs, and validating ATS optimization.
Each node returns a partial state update dict following LangGraph conventions.

Author: Claude (Anthropic)
License: Experimental
"""

import json
import time
from pathlib import Path

from ..state import ResumeTailoringState
from ..llm import call_llm
from ..prompts import RESUME_TAILORING_PROMPT
from ..tools import load_master_resume, calculate_keyword_match, calculate_ats_score


# Default master resume location (shared with original resume-agent)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent
RESUMES_DIR = PROJECT_ROOT / "resumes"
MASTER_RESUME = RESUMES_DIR / "kris-cernjavic-resume.yaml"


def load_resume_node(state: ResumeTailoringState) -> dict:
    """
    Load master resume from default location.

    This node loads the master resume YAML file and parses it into a structured
    dictionary. It uses the resume_parser tool to handle file I/O and validation.

    Args:
        state: Current resume tailoring state

    Returns:
        Partial state update with:
        - master_resume: Loaded resume data dict if successful
        - errors: Updated error list if load fails
    """
    start_time = time.time()

    try:
        print(f"\n📄 Loading master resume from {MASTER_RESUME}...")

        # Use the resume_parser tool to load the master resume
        result = load_master_resume(str(MASTER_RESUME))

        if result.get("status") == "error":
            error_msg = result.get("error", "Unknown error loading master resume")
            print(f"\n❌ {error_msg}")
            return {
                "errors": state.get("errors", []) + [error_msg]
            }

        # Extract the resume data
        master_resume = result.get("data", {})

        duration_ms = (time.time() - start_time) * 1000
        print(f"✓ Master resume loaded in {duration_ms:.0f}ms")

        return {
            "master_resume": master_resume
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to load master resume: {str(e)}"
        print(f"\n❌ {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }


def analyze_requirements_node(state: ResumeTailoringState) -> dict:
    """
    Analyze job requirements and calculate initial ATS score.

    This node extracts key requirements and keywords from the job analysis
    and calculates an initial ATS score to establish a baseline before tailoring.

    Args:
        state: Current resume tailoring state containing job_analysis and master_resume

    Returns:
        Partial state update with:
        - initial_ats_score: ATS score dict with keyword matching metrics
        - errors: Updated error list if analysis fails
    """
    start_time = time.time()

    try:
        print("\n🔍 Analyzing job requirements and calculating initial ATS score...")

        job_analysis = state.get("job_analysis")
        master_resume = state.get("master_resume")

        if not job_analysis:
            raise ValueError("No job analysis available")

        if not master_resume:
            raise ValueError("No master resume available")

        # Extract keywords from job analysis
        keywords = job_analysis.get("keywords", [])
        skills = job_analysis.get("skills", [])
        all_keywords = list(set(keywords + skills))  # Combine and deduplicate

        # Convert master resume to text for keyword matching
        # Simple text extraction - just concatenate all string values
        resume_text_parts = []

        def extract_text(obj, depth=0):
            """Recursively extract text from nested dict/list structures."""
            if depth > 10:  # Prevent infinite recursion
                return

            if isinstance(obj, dict):
                for value in obj.values():
                    extract_text(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    extract_text(item, depth + 1)
            elif isinstance(obj, str):
                resume_text_parts.append(obj)

        extract_text(master_resume)
        resume_text = " ".join(resume_text_parts)

        # Calculate keyword match
        keyword_match = calculate_keyword_match(resume_text, all_keywords)

        # Calculate overall ATS score
        # Prepare resume data dict for ATS scorer
        resume_data_for_ats = {
            "content": resume_text,
            "skills": master_resume.get("skills", [])
        }
        ats_score = calculate_ats_score(
            resume_data=resume_data_for_ats,
            job_analysis=job_analysis
        )

        initial_score = {
            "keyword_match": keyword_match,
            "ats_score": ats_score,
            "total_keywords": len(all_keywords),
            "matched_count": keyword_match.get("match_count", 0),
            "match_percentage": keyword_match.get("match_score", 0.0)
        }

        duration_ms = (time.time() - start_time) * 1000
        print(f"✓ Initial ATS score: {initial_score['match_percentage']:.1f}% ({initial_score['matched_count']}/{initial_score['total_keywords']} keywords)")
        print(f"  Analysis completed in {duration_ms:.0f}ms")

        return {
            "initial_ats_score": initial_score
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to analyze requirements: {str(e)}"
        print(f"\n❌ {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }


def tailor_resume_node(state: ResumeTailoringState) -> dict:
    """
    Tailor resume content for specific job using LLM.

    This node uses an LLM to optimize the master resume for the target job.
    It rewrites achievements to match requirements, integrates keywords naturally,
    and highlights relevant experience while maintaining authenticity.

    Args:
        state: Current resume tailoring state containing master_resume and job_analysis

    Returns:
        Partial state update with:
        - tailored_resume: Optimized resume text in markdown format
        - keywords_integrated: List of keywords successfully integrated
        - errors: Updated error list if tailoring fails
    """
    start_time = time.time()

    try:
        print("\n🤖 Tailoring resume with LLM...")

        master_resume = state.get("master_resume")
        job_analysis = state.get("job_analysis")

        if not master_resume:
            raise ValueError("No master resume available to tailor")

        if not job_analysis:
            raise ValueError("No job analysis available")

        # Format master resume as readable text for the LLM
        master_resume_text = json.dumps(master_resume, indent=2)

        # Extract job analysis fields
        company = job_analysis.get("company", "Unknown Company")
        job_title = job_analysis.get("job_title", "Unknown Position")
        requirements = "\n".join(f"- {req}" for req in job_analysis.get("requirements", []))
        skills = ", ".join(job_analysis.get("skills", []))
        responsibilities = "\n".join(f"- {resp}" for resp in job_analysis.get("responsibilities", []))
        keywords = ", ".join(job_analysis.get("keywords", []))

        # Format the prompt with job data
        formatted_prompt = RESUME_TAILORING_PROMPT.format(
            master_resume=master_resume_text,
            company=company,
            job_title=job_title,
            requirements=requirements,
            skills=skills,
            responsibilities=responsibilities,
            keywords=keywords
        )

        # Call LLM with the formatted prompt
        messages = [
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]

        system_prompt = "You are an expert resume writer specializing in ATS optimization. Return only valid JSON."

        llm_response = call_llm(messages, system_prompt)

        # Parse JSON response
        # Remove markdown code blocks if present
        json_text = llm_response.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:]
        if json_text.startswith("```"):
            json_text = json_text[3:]
        if json_text.endswith("```"):
            json_text = json_text[:-3]
        json_text = json_text.strip()

        tailoring_result = json.loads(json_text)

        tailored_resume = tailoring_result.get("tailored_resume", "")
        keywords_integrated = tailoring_result.get("keywords_integrated", [])

        duration_ms = (time.time() - start_time) * 1000
        print(f"✓ Resume tailored in {duration_ms:.0f}ms")
        print(f"  Integrated {len(keywords_integrated)} keywords")

        return {
            "tailored_resume": tailored_resume,
            "keywords_integrated": keywords_integrated
        }

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        print(f"\n❌ {error_msg}")
        print(f"LLM Response: {llm_response[:200] if 'llm_response' in locals() else 'N/A'}...")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }

    except Exception as e:
        error_msg = f"Failed to tailor resume: {str(e)}"
        print(f"\n❌ {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }


def validate_tailoring_node(state: ResumeTailoringState) -> dict:
    """
    Validate tailored resume by calculating final ATS score.

    This node calculates the ATS score for the tailored resume and compares
    it with the initial score to measure improvement. This validates that
    the tailoring process successfully integrated keywords and optimized content.

    Args:
        state: Current resume tailoring state containing tailored_resume and job_analysis

    Returns:
        Partial state update with:
        - final_ats_score: ATS score dict with comparison to initial score
        - errors: Updated error list if validation fails
    """
    start_time = time.time()

    try:
        print("\n✅ Validating tailored resume...")

        tailored_resume = state.get("tailored_resume")
        job_analysis = state.get("job_analysis")
        initial_score = state.get("initial_ats_score")

        if not tailored_resume:
            raise ValueError("No tailored resume available to validate")

        if not job_analysis:
            raise ValueError("No job analysis available")

        # Extract keywords from job analysis
        keywords = job_analysis.get("keywords", [])
        skills = job_analysis.get("skills", [])
        all_keywords = list(set(keywords + skills))

        # Calculate keyword match for tailored resume
        keyword_match = calculate_keyword_match(tailored_resume, all_keywords)

        # Calculate overall ATS score
        # Prepare resume data dict for ATS scorer
        # Extract skills from tailored resume text (simplified - just use keywords integrated)
        keywords_integrated = state.get("keywords_integrated", [])
        resume_data_for_ats = {
            "content": tailored_resume,
            "skills": keywords_integrated
        }
        ats_score = calculate_ats_score(
            resume_data=resume_data_for_ats,
            job_analysis=job_analysis
        )

        final_score = {
            "keyword_match": keyword_match,
            "ats_score": ats_score,
            "total_keywords": len(all_keywords),
            "matched_count": keyword_match.get("match_count", 0),
            "match_percentage": keyword_match.get("match_score", 0.0)
        }

        # Calculate improvement
        if initial_score:
            initial_percentage = initial_score.get("match_percentage", 0.0)
            final_percentage = final_score["match_percentage"]
            improvement = final_percentage - initial_percentage

            print(f"✓ Final ATS score: {final_percentage:.1f}% ({final_score['matched_count']}/{final_score['total_keywords']} keywords)")
            print(f"  Improvement: {improvement:+.1f}% (from {initial_percentage:.1f}%)")
        else:
            print(f"✓ Final ATS score: {final_score['match_percentage']:.1f}% ({final_score['matched_count']}/{final_score['total_keywords']} keywords)")

        duration_ms = (time.time() - start_time) * 1000
        print(f"  Validation completed in {duration_ms:.0f}ms")

        return {
            "final_ats_score": final_score
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to validate tailoring: {str(e)}"
        print(f"\n❌ {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }
