# Data Model: Job Analyzer Skill

**Feature**: Decompose MCP Server to Claude Skills (MVP)
**Scope**: Job Analysis entity only
**Date**: 2025-10-23

---

## Job Analysis Entity

**Purpose**: Structured representation of a job posting's requirements, responsibilities, and keywords extracted by the job-analyzer skill.

**Source**: Existing `JobAnalysis` Pydantic model from `apps/resume-agent/resume_agent.py` (lines ~700-750)

### Fields

| Field Name | Type | Required | Description | Example |
|------------|------|----------|-------------|---------|
| company | string | Yes | Company name | "Cookpad" |
| job_title | string | Yes | Exact job title from posting | "Senior Backend Engineer" |
| role_type | string | No | Employment type | "Full-time", "Contract", "Part-time" |
| location | string | Yes | Office location or remote status | "Tokyo, Japan", "Remote", "Hybrid" |
| remote_policy | string | No | Remote work policy | "Fully remote", "Hybrid (2 days office)", "On-site only" |
| required_skills | List[string] | Yes | MUST-have qualifications | ["Python", "PostgreSQL", "5+ years experience"] |
| preferred_skills | List[string] | No | Nice-to-have qualifications | ["AWS", "Docker", "Kubernetes"] |
| requirements | List[string] | Yes | All listed requirements | ["Bachelor's degree in CS", "Strong communication skills"] |
| responsibilities | List[string] | Yes | Day-to-day tasks | ["Design scalable backend systems", "Mentor junior engineers"] |
| keywords | List[string] | Yes | ATS-critical terms (10-15 most important) | ["Python", "Microservices", "API Design", "PostgreSQL"] |
| salary_range | string | No | Compensation information | "¥8M-¥12M", "$120k-$160k", "Competitive" |
| experience_level | string | No | Seniority expected | "Senior", "Mid-level", "5-8 years" |
| candidate_profile | string | No | 2-3 sentence ideal candidate description | "We're looking for an experienced backend engineer who..." |

### Validation Rules

**From Existing Pydantic Schema**:

```python
# Reference: apps/resume-agent/resume_agent.py

class JobAnalysis(BaseModel):
    company: str
    job_title: str
    role_type: Optional[str] = None
    location: str
    remote_policy: Optional[str] = None
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = []
    requirements: List[str]
    responsibilities: List[str]
    keywords: List[str]
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    candidate_profile: Optional[str] = None
```

**Validation Constraints**:
- Required lists MUST contain at least 1 item (required_skills, requirements, responsibilities, keywords)
- Optional lists default to empty list [] if not provided
- Strings MUST be non-empty for required fields
- No maximum length constraints (job postings vary widely)

### Storage Format

**File Location**:
```
job-applications/{Company}_{JobTitle}/job-analysis.json
```

**Directory Creation**:
- Directory name: Sanitize company and job title (replace spaces with underscores, remove special chars)
- Example: "Cookpad" + "Senior Backend Engineer" → `Cookpad_Senior_Backend_Engineer/`

**JSON Structure**:
```json
{
  "company": "Cookpad",
  "job_title": "Senior Backend Engineer",
  "role_type": "Full-time",
  "location": "Tokyo, Japan",
  "remote_policy": "Hybrid (2 days office)",
  "required_skills": [
    "Python",
    "PostgreSQL",
    "5+ years backend development"
  ],
  "preferred_skills": [
    "AWS",
    "Docker",
    "Kubernetes"
  ],
  "requirements": [
    "Bachelor's degree in Computer Science or equivalent",
    "Strong communication skills in English and Japanese",
    "Experience with microservices architecture"
  ],
  "responsibilities": [
    "Design and implement scalable backend systems",
    "Collaborate with product team on feature planning",
    "Mentor junior engineers"
  ],
  "keywords": [
    "Python",
    "PostgreSQL",
    "AWS",
    "Microservices",
    "API Design",
    "Docker",
    "Kubernetes",
    "Backend",
    "Scalability",
    "Mentoring"
  ],
  "salary_range": "¥8M-¥12M",
  "experience_level": "Senior (5-8 years)",
  "candidate_profile": "We're looking for an experienced backend engineer who thrives in a collaborative environment and has a passion for building scalable systems that serve millions of users."
}
```

### Relationships

**Current (MVP)**:
- One job posting URL → One JobAnalysis entity
- Stored as standalone JSON file

**Future (Full Implementation)**:
- One JobAnalysis → One TailoredResume (resume-writer skill)
- One JobAnalysis → One CoverLetter (cover-letter-writer skill)
- One JobAnalysis → Many PortfolioExamples (portfolio-finder skill)
- One JobAnalysis → Many RAGChunks (if job posting processed by website-rag skill)

### Data Flow

```
Job Posting URL
  ↓
[WebFetch or Playwright] → HTML content
  ↓
[job-analyzer skill] → Parse + Extract
  ↓
JobAnalysis dictionary (matches Pydantic schema)
  ↓
Write to job-applications/{Company}_{JobTitle}/job-analysis.json
  ↓
Available for:
  - Resume tailoring (resume-writer skill)
  - Cover letter generation (cover-letter-writer skill)
  - Portfolio matching (portfolio-finder skill)
  - MCP tools (existing resume_agent.py server)
```

### Backward Compatibility

**With Existing MCP Server**:

✓ **100% Compatible**:
- JSON structure matches JobAnalysis Pydantic model exactly
- File location matches existing data_write_job_analysis() MCP tool expectations
- MCP server can read job-analysis.json files created by skill
- Skills can read job-analysis.json files created by MCP server

**Migration Path**:
- No data migration needed
- Both architectures (MCP + skills) can coexist
- Same data files, different access methods

### Edge Cases

| Scenario | Handling | Example |
|----------|----------|---------|
| Missing salary info | salary_range: null | Many Japanese companies don't publish salaries |
| Remote-only role | location: "Remote", remote_policy: "Fully remote" | Distinguish from office location |
| Vague requirements | Extract what's listed, note in candidate_profile | "Must be passionate" → candidate_profile |
| Japanese company names | Use official English name if available | "クックパッド株式会社" → "Cookpad Inc." |
| Multiple locations | Comma-separated string | "Tokyo, Osaka, or Remote" |
| Non-standard job boards | Adapt parsing logic if site structure differs | Skill may need per-site parsing strategies |

### Performance Considerations

**File Size**: Typically 1-3 KB per job analysis (JSON is compact)

**Read/Write Operations**:
- Write: Once per job posting analysis (<1s)
- Read: Multiple times (resume tailoring, cover letter, portfolio search)
- Concurrent access: File-based storage doesn't support locking (future: migrate to SQLite)

**Indexing** (Future Enhancement):
- Current: No indexing (file-based storage)
- Future: SQLite table with FTS5 for keyword search across all analyzed jobs

---

## Summary

- **Entity**: JobAnalysis (matches existing Pydantic schema)
- **Storage**: job-applications/{Company}_{JobTitle}/job-analysis.json
- **Validation**: Pydantic model (in future, loose validation in MVP)
- **Compatibility**: 100% backward compatible with existing MCP server
- **Relationships**: Foundation for resume-writer, cover-letter-writer, portfolio-finder skills

**Ready for**: Contract definition (skill inputs/outputs)
