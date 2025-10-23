# Schema Examples: Pydantic Data Models

This document shows complete examples of all Pydantic schemas used by the data-access skill for validation.

---

## JobAnalysis Schema

**Purpose:** Structured job posting data extracted by job-analyzer skill

**Source:** `apps/resume-agent/resume_agent.py` (lines 147-160)

**Pydantic Definition:**
```python
class JobAnalysis(BaseModel):
    url: str
    fetched_at: str  # ISO timestamp
    company: str
    job_title: str
    location: str
    salary_range: Optional[str] = None
    required_qualifications: List[str] = Field(default_factory=list)
    preferred_qualifications: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    candidate_profile: str
    raw_description: str
```

**Example JSON:**
```json
{
  "url": "https://japan-dev.com/jobs/cookpad/conversational-ai-engineer",
  "fetched_at": "2025-10-23T11:30:00Z",
  "company": "Cookpad",
  "job_title": "Conversational AI Engineer",
  "location": "Tokyo, Japan",
  "salary_range": "¥10M ~ ¥25M /yr",
  "required_qualifications": [
    "5+ years software engineering experience",
    "Strong proficiency in Python and ML frameworks",
    "Experience with LLMs (GPT, Claude, etc.)",
    "Experience building production AI systems",
    "Strong understanding of RAG architecture"
  ],
  "preferred_qualifications": [
    "Experience with LangChain or similar frameworks",
    "Vector database experience (Pinecone, Weaviate)",
    "MLOps and model deployment experience",
    "Japanese language proficiency (N2 or higher)"
  ],
  "responsibilities": [
    "Design and implement conversational AI systems",
    "Build RAG pipelines for context-aware responses",
    "Collaborate with product team on AI features",
    "Optimize LLM performance and cost",
    "Mentor engineers on AI best practices"
  ],
  "keywords": [
    "Python", "LLM", "GPT", "Claude", "RAG",
    "Vector Database", "LangChain", "MLOps",
    "Conversational AI", "Machine Learning"
  ],
  "candidate_profile": "We're looking for an experienced AI engineer passionate about building production systems with LLMs and RAG architectures.",
  "raw_description": "[Full HTML content omitted]"
}
```

**Validation Rules:**
- `required_qualifications`: Must contain ≥1 item
- `responsibilities`: Must contain ≥1 item
- `keywords`: Must contain ≥1 item (ideally 10-15)
- `company`, `job_title`, `location`, `candidate_profile`: Must be non-empty strings
- `fetched_at`: ISO 8601 timestamp format
- `salary_range`, `preferred_qualifications`: Optional (can be null or empty array)

---

## MasterResume Schema

**Purpose:** Complete master resume data structure

**Source:** `apps/resume-agent/resume_agent.py` (lines 132-137)

**Pydantic Definition:**
```python
class PersonalInfo(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    linkedin: Optional[str] = None
    title: Optional[str] = None

class Technology(BaseModel):
    name: str

class Achievement(BaseModel):
    description: str
    metric: Optional[str] = None

class Employment(BaseModel):
    company: str
    position: Optional[str] = None
    title: Optional[str] = None
    employment_type: Optional[str] = None
    start_date: str
    end_date: Optional[str] = None
    description: str
    technologies: List[str] = Field(default_factory=list)
    achievements: Optional[List[Achievement]] = None

class MasterResume(BaseModel):
    personal_info: PersonalInfo
    about_me: Optional[str] = None
    professional_summary: Optional[str] = None
    employment_history: List[Employment] = Field(default_factory=list)
```

**Example YAML (from file):**
```yaml
personal_info:
  name: "Kris Cernjavic"
  phone: "+1-555-123-4567"
  email: "kris.cernjavic@example.com"
  linkedin: "https://linkedin.com/in/kriscernjavic"
  title: "Senior Software Engineer"

professional_summary: |
  10+ years of software engineering experience specializing in C#, .NET, Azure,
  and AI-driven automation. Led development of multi-agent systems achieving
  95% cost reduction through LLM orchestration.

employment_history:
  - company: "Aryza"
    title: "Senior Software Engineer"
    employment_type: "Full-time"
    start_date: "2023-01"
    end_date: "Present"
    description: |
      Led AI-driven automation initiatives using Claude Code and multi-agent systems.
    technologies:
      - "C#"
      - ".NET"
      - "Azure"
      - "Claude Code"
      - "AI/ML"
    achievements:
      - description: "Reduced operational costs by 95% through AI agent automation"
        metric: "95% cost reduction"
      - description: "Built multi-agent system for automated code review"
        metric: "3x faster code review cycle"

  - company: "D&D Worldwide Logistics"
    title: "Senior Software Engineer"
    employment_type: "Full-time"
    start_date: "2020-06"
    end_date: "2023-01"
    description: |
      Developed customer matching RAG pipeline using Redis and Supabase.
    technologies:
      - "C#"
      - ".NET Core"
      - "Redis"
      - "Supabase"
      - "RAG"
    achievements:
      - description: "Implemented semantic search for customer matching"
        metric: "40% improvement in match accuracy"
```

**Validation Rules:**
- `personal_info`: Required (must contain `name` at minimum)
- `employment_history`: Array of Employment objects
- `about_me`, `professional_summary`: Optional strings
- Each Employment must have: `company`, `start_date`, `description`
- `end_date`: Optional (use "Present" for current position)
- `technologies`: Array of strings (can be empty)
- `achievements`: Optional array of Achievement objects

---

## CareerHistory Schema

**Purpose:** Extended career history with detailed achievements

**Source:** `apps/resume-agent/resume_agent.py` (lines 140-144)

**Pydantic Definition:**
```python
class CareerHistory(BaseModel):
    personal_info: PersonalInfo
    professional_summary: Optional[str] = None
    employment_history: List[Employment] = Field(default_factory=list)
```

**Example YAML:**
```yaml
personal_info:
  name: "Kris Cernjavic"
  email: "kris.cernjavic@example.com"
  title: "Senior Software Engineer"

professional_summary: |
  10+ years of software engineering experience with expertise in
  AI/ML, cloud architecture, and full-stack development.

employment_history:
  - company: "Aryza"
    title: "Senior Software Engineer"
    start_date: "2023-01"
    end_date: "Present"
    description: "Leading AI-driven automation initiatives"
    technologies: ["C#", ".NET", "Azure", "Claude Code"]
    achievements:
      - description: "Built multi-agent system for automated workflows"
        metric: "95% cost reduction, $500k annual savings"
      - description: "Developed RAG pipeline for document processing"
        metric: "10x faster retrieval, 2s average response time"
      - description: "Implemented LLM orchestration with Claude 3.5 Sonnet"
        metric: "Processed 1M+ tokens/month with 99.9% uptime"
```

**Validation Rules:**
- Same as MasterResume schema
- Typically contains more detailed achievements with metrics
- Used for cover letter generation (more storytelling context)

---

## TailoredResume Schema

**Purpose:** Tailored resume content and metadata

**Source:** `apps/resume-agent/resume_agent.py` (lines 163-170)

**Pydantic Definition:**
```python
class TailoredResume(BaseModel):
    company: str
    job_title: str
    content: str
    created_at: str  # ISO timestamp
    keywords_used: List[str] = Field(default_factory=list)
    changes_from_master: List[str] = Field(default_factory=list)
```

**Example (Metadata in header comment):**
```
# Tailored Resume Metadata
# Company: Cookpad
# Job Title: Conversational AI Engineer
# Created: 2025-10-23T14:30:00Z
# Keywords Used: Python, LLM, RAG, Vector Database, LangChain
# Changes from Master: Emphasized AI/ML projects, Added Claude Code experience, Highlighted RAG pipeline work

Kris Cernjavic
Senior Software Engineer | AI/ML Specialist
kris.cernjavic@example.com | +1-555-123-4567
https://linkedin.com/in/kriscernjavic

PROFESSIONAL SUMMARY
10+ years of software engineering experience specializing in AI-driven automation,
LLM orchestration, and RAG architectures. Led development of multi-agent systems
achieving 95% cost reduction through Claude Code and Python-based AI workflows.

TECHNICAL SKILLS
Languages: Python, C#, TypeScript, SQL
AI/ML: LLM orchestration, RAG pipelines, Vector databases, LangChain
Cloud: Azure, AWS, Supabase, Redis
Frameworks: .NET, FastAPI, React

EMPLOYMENT HISTORY

Senior Software Engineer | Aryza | 2023-01 - Present
- Built multi-agent system using Claude Code and Python for automated workflows
  → Achieved 95% cost reduction ($500k annual savings)
- Developed RAG pipeline with vector database for document retrieval
  → 10x faster retrieval, 2s average response time
- Implemented LLM orchestration with Claude 3.5 Sonnet and GPT-4
  → Processed 1M+ tokens/month with 99.9% uptime

[Additional employment history...]
```

**Validation Rules:**
- `company`, `job_title`, `content`: Required strings
- `created_at`: ISO 8601 timestamp
- `keywords_used`: Array of keywords incorporated from job analysis
- `changes_from_master`: Array describing modifications from master resume

---

## CoverLetter Schema

**Purpose:** Cover letter content and metadata

**Source:** `apps/resume-agent/resume_agent.py` (lines 173-179)

**Pydantic Definition:**
```python
class CoverLetter(BaseModel):
    company: str
    job_title: str
    content: str
    created_at: str  # ISO timestamp
    talking_points: List[str] = Field(default_factory=list)
```

**Example (Metadata in header comment):**
```
# Cover Letter Metadata
# Company: Cookpad
# Job Title: Conversational AI Engineer
# Created: 2025-10-23T15:00:00Z
# Talking Points: AI experience at Aryza, RAG expertise, Multi-agent systems, Cultural fit for Tokyo-based role

Dear Hiring Manager,

I am writing to express my strong interest in the Conversational AI Engineer position
at Cookpad. With over 10 years of software engineering experience and a proven track
record in building production AI systems, I am excited about the opportunity to
contribute to Cookpad's mission of making everyday cooking fun.

During my time at Aryza, I led the development of a multi-agent system using Claude Code
and Python that achieved a 95% reduction in operational costs. This experience has given
me deep expertise in LLM orchestration, RAG architectures, and production AI deployment—
all skills directly applicable to this role.

[Body paragraphs...]

I am particularly drawn to Cookpad's emphasis on user-centric AI features and
collaborative engineering culture. I believe my experience in building scalable AI
systems combined with my passion for food tech makes me an ideal fit for this role.

Thank you for considering my application. I look forward to discussing how I can
contribute to Cookpad's AI initiatives.

Sincerely,
Kris Cernjavic
```

**Validation Rules:**
- `company`, `job_title`, `content`: Required strings
- `created_at`: ISO 8601 timestamp
- `talking_points`: Array of key points to emphasize in cover letter

---

## PortfolioExamples Schema

**Purpose:** Portfolio code examples for job application

**Source:** `apps/resume-agent/resume_agent.py` (lines 182-187)

**Pydantic Definition:**
```python
class PortfolioExamples(BaseModel):
    company: str
    job_title: str
    examples: List[dict] = Field(default_factory=list)
    created_at: str  # ISO timestamp
```

**Example (Saved as plain text with structure):**
```
# Portfolio Examples
# Company: Cookpad
# Job Title: Conversational AI Engineer
# Created: 2025-10-23T15:30:00Z

## Example 1: RAG Pipeline - Customer Matching
**Repository:** github.com/kcernjavic/ddwl-platform
**File:** backend/services/matching.py:536-615
**Technologies:** Python, Redis, Supabase, Vector embeddings
**Description:** Semantic search pipeline for matching customer inquiries to historical data

```python
def semantic_search_customers(query: str, top_k: int = 5):
    # Generate embedding for query
    embedding = get_embedding(query)

    # Search Redis vector store
    results = redis_client.ft("customer_idx").search(
        Query(f"@embedding:[VECTOR_RANGE {top_k} $vec]")
        .return_fields("customer_id", "score")
        .sort_by("score", asc=False)
        .dialect(2),
        query_params={"vec": embedding.tobytes()}
    )

    return [{"id": r.customer_id, "score": r.score} for r in results.docs]
```

**Impact:** 40% improvement in match accuracy, 2s average query time

---

## Example 2: Multi-Agent System - Code Review Automation
**Repository:** github.com/kcernjavic/aryza-automation
**File:** agents/code_review_agent.py:1-85
**Technologies:** Claude Code, Python, Claude Agent SDK
**Description:** Automated code review using multi-agent orchestration

[Code snippet...]

**Impact:** 95% cost reduction, 3x faster review cycle
```

**Validation Rules:**
- `company`, `job_title`: Required strings
- `examples`: Array of dictionaries with keys: repo, description, link, technologies
- `created_at`: ISO 8601 timestamp

---

## ApplicationMetadata Schema

**Purpose:** Metadata about job application directory

**Source:** `apps/resume-agent/resume_agent.py` (lines 190-196)

**Pydantic Definition:**
```python
class ApplicationMetadata(BaseModel):
    directory: str
    company: str
    role: str
    files: dict  # {resume: bool, cover_letter: bool, analysis: bool}
    modified: float  # Unix timestamp
```

**Example (returned by data_list_applications):**
```json
{
  "directory": "./job-applications/Cookpad_Conversational_AI_Engineer",
  "company": "Cookpad",
  "role": "Conversational AI Engineer",
  "files": {
    "resume": true,
    "cover_letter": true,
    "analysis": true,
    "portfolio": false
  },
  "modified": 1729681800.0
}
```

**Validation Rules:**
- `directory`: Full path to application directory
- `company`, `role`: Extracted from directory name
- `files`: Dictionary with boolean values for each file type
- `modified`: Unix timestamp (seconds since epoch)

---

## Common Validation Errors

### Error 1: Missing Required Fields

**Symptom:**
```
ValidationError: field required (type=value_error.missing)
```

**Cause:** Required field is missing or null

**Fix:**
```json
// ❌ Missing required field
{
  "company": "Cookpad",
  "job_title": "Engineer"
  // Missing: url, fetched_at, location, etc.
}

// ✓ All required fields present
{
  "url": "https://...",
  "fetched_at": "2025-10-23T11:30:00Z",
  "company": "Cookpad",
  "job_title": "Engineer",
  "location": "Tokyo",
  "required_qualifications": ["..."],
  "responsibilities": ["..."],
  "keywords": ["..."],
  "candidate_profile": "...",
  "raw_description": "..."
}
```

### Error 2: Empty Required Arrays

**Symptom:**
```
ValidationError: ensure this value has at least 1 item
```

**Cause:** Required array is empty

**Fix:**
```json
// ❌ Empty required array
{
  "required_qualifications": [],
  "keywords": []
}

// ✓ Arrays contain at least 1 item
{
  "required_qualifications": ["5+ years experience"],
  "keywords": ["Python", "AI", "LLM"]
}
```

### Error 3: Invalid Timestamp Format

**Symptom:**
```
ValidationError: invalid datetime format
```

**Cause:** Timestamp is not ISO 8601 format

**Fix:**
```json
// ❌ Invalid timestamp
{
  "fetched_at": "Oct 23, 2025",
  "created_at": "2025-10-23 11:30:00"
}

// ✓ ISO 8601 format
{
  "fetched_at": "2025-10-23T11:30:00Z",
  "created_at": "2025-10-23T14:30:00Z"
}
```

### Error 4: Wrong Data Type

**Symptom:**
```
ValidationError: str type expected
```

**Cause:** Field has wrong data type

**Fix:**
```json
// ❌ Wrong data type
{
  "company": 123,  // Should be string
  "keywords": "Python, LLM"  // Should be array
}

// ✓ Correct data types
{
  "company": "Cookpad",
  "keywords": ["Python", "LLM"]
}
```

---

## Testing Validation

You can test schema validation using Python:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

# Import schema from resume_agent.py
from resume_agent import JobAnalysis

# Test valid data
valid_data = {
    "url": "https://example.com/job",
    "fetched_at": "2025-10-23T11:30:00Z",
    "company": "Cookpad",
    "job_title": "AI Engineer",
    "location": "Tokyo",
    "required_qualifications": ["5+ years"],
    "responsibilities": ["Build AI systems"],
    "keywords": ["Python", "AI"],
    "candidate_profile": "Experienced AI engineer",
    "raw_description": "Full job posting text"
}

# Validate
try:
    job = JobAnalysis(**valid_data)
    print("✓ Validation passed")
except Exception as e:
    print(f"✗ Validation failed: {e}")
```

---

**For skill documentation:** See `../SKILL.md`
**For Pydantic source code:** See `apps/resume-agent/resume_agent.py` (lines 99-197)
**For MCP server details:** See `README-MCP-SERVER.md`
