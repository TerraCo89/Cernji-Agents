"""
Prompt templates for Resume Agent.

Centralized prompt management for consistency and easy iteration.
"""

from typing import Any


class PromptTemplate:
    """Base class for prompt templates with variable substitution."""
    
    def __init__(self, template: str):
        self.template = template
    
    def format(self, **kwargs: Any) -> str:
        """Format the template with provided variables."""
        return self.template.format(**kwargs)


# Job Analysis Prompts
JOB_ANALYSIS_PROMPT = PromptTemplate("""
You are an expert job posting analyzer. Extract structured information from this job posting.

Job Posting URL: {url}
Raw Content:
{content}

Extract and return the following information:
1. Company name
2. Job title
3. Key requirements (list)
4. Required skills and technologies (list)
5. ATS keywords that are likely important (list)
6. Salary range (if mentioned)
7. Location

Be thorough and precise. ATS keywords should include exact phrases from the posting.
""")


# Resume Analysis Prompts
RESUME_ANALYSIS_PROMPT = PromptTemplate("""
You are an expert resume analyzer. Analyze this resume against the job requirements.

Resume:
{resume_text}

Job Requirements:
{requirements}

Job Skills:
{skills}

Analyze:
1. Current skills mentioned in resume
2. Experience summary (2-3 sentences)
3. Skill gaps between resume and job requirements
4. Strengths that align with the job

Be specific and actionable in your analysis.
""")


# Section Optimization Prompts
SECTION_OPTIMIZATION_PROMPT = PromptTemplate("""
You are an expert resume writer. Optimize this resume section for ATS and hiring managers.

Section: {section_name}
Original Text:
{original_text}

Target Keywords to Incorporate:
{keywords}

Job Context:
{job_context}

Rewrite this section to:
1. Naturally incorporate target keywords
2. Use strong action verbs
3. Quantify achievements where possible
4. Maintain authenticity and readability
5. Optimize for ATS scanning

Return ONLY the optimized section text, no explanations.
""")


# ATS Scoring Prompt
ATS_SCORING_PROMPT = PromptTemplate("""
You are an ATS (Applicant Tracking System) analyzer. Score this resume against the job requirements.

Resume:
{resume_text}

Job Requirements:
{requirements}

ATS Keywords:
{keywords}

Provide:
1. ATS Score (0-100) - how well this resume would rank
2. Keyword match percentage
3. Specific missing keywords
4. Formatting issues that could hurt ATS parsing

Be strict and realistic in your scoring.
""")


# Cover Letter Generation
COVER_LETTER_PROMPT = PromptTemplate("""
You are an expert cover letter writer. Create a compelling cover letter for this job application.

Job Title: {job_title}
Company: {company_name}

Job Requirements:
{requirements}

Candidate's Experience Summary:
{experience_summary}

Key Skills to Highlight:
{skills}

Write a professional, enthusiastic cover letter that:
1. Opens with a strong hook related to the company/role
2. Highlights 2-3 key achievements that match job requirements
3. Shows genuine interest in the company
4. Closes with a clear call-to-action
5. Stays concise (300-400 words)

Tone: Professional but warm and authentic.
""")


# Validation Prompts
VALIDATION_PROMPT = PromptTemplate("""
You are a resume quality control expert. Check this resume for common errors.

Resume:
{resume_text}

Check for:
1. Typos and grammatical errors
2. Formatting inconsistencies
3. Missing critical sections (contact, experience, education)
4. Overly long sections (>1 page typically)
5. Weak action verbs or passive voice
6. Unprofessional email addresses or information

Return:
- Errors (critical issues that must be fixed)
- Warnings (suggestions for improvement)
""")


# System Prompts
SYSTEM_RESUME_EXPERT = """You are an expert resume writer and career coach with 15+ years of experience. 
You understand:
- ATS (Applicant Tracking Systems) and how they parse resumes
- What hiring managers look for in candidates
- Industry-specific resume best practices
- How to quantify achievements effectively

You provide honest, actionable advice while maintaining the candidate's authentic voice."""


SYSTEM_JOB_ANALYZER = """You are an expert at analyzing job postings and understanding employer needs.
You can:
- Extract key requirements from messy job descriptions
- Identify implicit requirements not explicitly stated
- Recognize industry-specific terminology and buzzwords
- Understand what skills are "must-haves" vs "nice-to-haves"

You provide structured, precise analysis."""
