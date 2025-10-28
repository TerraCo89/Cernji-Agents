"""Cover letter generation nodes for LangGraph workflows.

This module provides nodes for preparing context, generating personalized cover letters,
and reviewing cover letter quality. Each node returns a partial state update dict
following LangGraph conventions.

Author: Claude (Anthropic)
License: Experimental
"""

import json
import time
import re

from ..state import ResumeAgentState
from ..llm import call_llm
from ..prompts import COVER_LETTER_PROMPT, COVER_LETTER_REVIEW_PROMPT


def prepare_cover_letter_context_node(state: ResumeAgentState) -> dict:
    """
    Prepare context for cover letter generation from job analysis and tailored resume.

    This node extracts key information needed for cover letter writing:
    - Company name, job title, and key requirements from job analysis
    - Relevant achievements and skills from tailored resume
    - Company culture/values if available
    - Skills to highlight based on job requirements

    Args:
        state: Current cover letter state containing job_analysis and tailored_resume

    Returns:
        Partial state update with:
        - context: Dict with prepared data for cover letter generation
        - errors: Updated error list if preparation fails
    """
    start_time = time.time()

    try:
        print("\n📋 Preparing cover letter context...")

        job_analysis = state.get("job_analysis")
        tailored_resume = state.get("tailored_resume")

        if not job_analysis:
            raise ValueError("No job analysis available")

        if not tailored_resume:
            raise ValueError("No tailored resume available")

        # Extract job information
        company = job_analysis.get("company", "the company")
        job_title = job_analysis.get("job_title", "this position")
        requirements = job_analysis.get("requirements", [])
        skills = job_analysis.get("skills", [])
        responsibilities = job_analysis.get("responsibilities", [])

        # Extract relevant experience from resume
        # Look for bullet points with achievements (lines starting with -, *, or •)
        achievement_pattern = r'^[\s]*[-*•]\s+(.+)$'
        achievements = []
        for line in tailored_resume.split('\n'):
            match = re.match(achievement_pattern, line)
            if match:
                achievements.append(match.group(1).strip())

        # Take most relevant achievements (first 5-7 from tailored resume)
        relevant_experience = "\n".join(f"- {ach}" for ach in achievements[:7])

        # Extract skills to highlight (top skills from job analysis)
        skills_to_highlight = ", ".join(skills[:10]) if skills else "relevant technical skills"

        # Infer company culture from job posting text (simple heuristics)
        culture_keywords = []
        job_text = " ".join([
            job_analysis.get("company", ""),
            " ".join(requirements),
            " ".join(responsibilities)
        ]).lower()

        culture_indicators = {
            "collaborative": ["collaborate", "team", "partnership"],
            "innovative": ["innovative", "cutting-edge", "pioneer"],
            "data-driven": ["data", "analytics", "metrics"],
            "fast-paced": ["fast-paced", "agile", "dynamic"],
            "customer-focused": ["customer", "user", "client"]
        }

        for culture, keywords in culture_indicators.items():
            if any(keyword in job_text for keyword in keywords):
                culture_keywords.append(culture)

        culture = ", ".join(culture_keywords) if culture_keywords else "professional and goal-oriented"

        # Prepare context dict
        context = {
            "company": company,
            "job_title": job_title,
            "requirements": "\n".join(f"- {req}" for req in requirements[:5]),  # Top 5 requirements
            "skills": ", ".join(skills[:8]),  # Top 8 skills
            "culture": culture,
            "relevant_experience": relevant_experience,
            "skills_to_highlight": skills_to_highlight
        }

        duration_ms = (time.time() - start_time) * 1000
        print(f"✓ Context prepared in {duration_ms:.0f}ms")
        print(f"  Company: {company}")
        print(f"  Role: {job_title}")
        print(f"  Achievements extracted: {len(achievements)}")
        print(f"  Culture keywords: {culture}")

        return {
            "context": context
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to prepare context: {str(e)}"
        print(f"\n❌ {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }


def generate_cover_letter_node(state: ResumeAgentState) -> dict:
    """
    Generate personalized cover letter using LLM.

    This node uses an LLM to write a compelling cover letter that:
    - Opens with a strong hook (no generic phrases)
    - Tells a story connecting experience to requirements
    - Demonstrates cultural fit and enthusiasm
    - Highlights specific achievements and value proposition
    - Closes with a clear call to action

    Args:
        state: Current cover letter state containing context

    Returns:
        Partial state update with:
        - cover_letter: Generated cover letter text
        - errors: Updated error list if generation fails
    """
    start_time = time.time()

    try:
        print("\n🤖 Generating cover letter with LLM...")

        context = state.get("context")

        if not context:
            raise ValueError("No context available for cover letter generation")

        # Format the prompt with context
        formatted_prompt = COVER_LETTER_PROMPT.format(
            company=context["company"],
            job_title=context["job_title"],
            requirements=context["requirements"],
            skills=context["skills"],
            culture=context["culture"],
            relevant_experience=context["relevant_experience"],
            skills_to_highlight=context["skills_to_highlight"]
        )

        # Call LLM with the formatted prompt
        messages = [
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]

        system_prompt = "You are an expert cover letter writer. Return only valid JSON."

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

        generation_result = json.loads(json_text)

        cover_letter = generation_result.get("cover_letter", "")
        word_count = generation_result.get("word_count", 0)
        key_themes = generation_result.get("key_themes", [])

        duration_ms = (time.time() - start_time) * 1000
        print(f"✓ Cover letter generated in {duration_ms:.0f}ms")
        print(f"  Word count: {word_count}")
        print(f"  Key themes: {', '.join(key_themes)}")

        return {
            "cover_letter": cover_letter
        }

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse LLM response as JSON: {str(e)}"
        print(f"\n❌ {error_msg}")
        print(f"LLM Response: {llm_response[:200] if 'llm_response' in locals() else 'N/A'}...")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }

    except Exception as e:
        error_msg = f"Failed to generate cover letter: {str(e)}"
        print(f"\n❌ {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }


def review_cover_letter_node(state: ResumeAgentState) -> dict:
    """
    Review generated cover letter for quality and provide suggestions.

    This node evaluates the cover letter against professional standards:
    - Appropriate length (300-500 words)
    - No generic phrases like "I am writing to apply..."
    - Specific examples and achievements
    - Demonstrates cultural fit
    - Professional tone and structure

    Scoring criteria (100 points total):
    - Length (20 points)
    - No generic phrases (20 points)
    - Specific examples (20 points)
    - Cultural fit demonstration (20 points)
    - Professional tone (20 points)

    Args:
        state: Current cover letter state containing cover_letter

    Returns:
        Partial state update with:
        - review_score: Quality score (0-100)
        - suggestions: List of improvement suggestions
        - errors: Updated error list if review fails
    """
    start_time = time.time()

    try:
        print("\n✅ Reviewing cover letter quality...")

        cover_letter = state.get("cover_letter")
        context = state.get("context")

        if not cover_letter:
            raise ValueError("No cover letter available to review")

        if not context:
            raise ValueError("No context available for review")

        # Format the review prompt
        formatted_prompt = COVER_LETTER_REVIEW_PROMPT.format(
            cover_letter=cover_letter,
            job_title=context.get("job_title", "Unknown Position"),
            company=context.get("company", "Unknown Company")
        )

        # Call LLM for review
        messages = [
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]

        system_prompt = "You are an expert career coach. Return only valid JSON."

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

        review_result = json.loads(json_text)

        review_score = review_result.get("review_score", 0)
        word_count = review_result.get("word_count", 0)
        strengths = review_result.get("strengths", [])
        suggestions = review_result.get("suggestions", [])
        has_generic_phrases = review_result.get("has_generic_phrases", False)
        has_specific_examples = review_result.get("has_specific_examples", True)
        demonstrates_cultural_fit = review_result.get("demonstrates_cultural_fit", True)
        professional_tone = review_result.get("professional_tone", True)

        duration_ms = (time.time() - start_time) * 1000
        print(f"✓ Review completed in {duration_ms:.0f}ms")
        print(f"  Quality score: {review_score}/100")
        print(f"  Word count: {word_count}")
        print(f"  Generic phrases: {'Yes' if has_generic_phrases else 'No'}")
        print(f"  Specific examples: {'Yes' if has_specific_examples else 'No'}")
        print(f"  Strengths: {len(strengths)}")
        print(f"  Suggestions: {len(suggestions)}")

        return {
            "review_score": review_score,
            "suggestions": suggestions
        }

    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse review response as JSON: {str(e)}"
        print(f"\n❌ {error_msg}")
        print(f"LLM Response: {llm_response[:200] if 'llm_response' in locals() else 'N/A'}...")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }

    except Exception as e:
        error_msg = f"Failed to review cover letter: {str(e)}"
        print(f"\n❌ {error_msg}")

        return {
            "errors": state.get("errors", []) + [error_msg]
        }
