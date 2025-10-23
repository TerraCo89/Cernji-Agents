---
name: data-access
description: Centralized data access layer for all career-related file operations. Provides validated read/write interface for master resume, career history, job analyses, tailored resumes, and cover letters using Pydantic schemas.
---

# Data Access Skill

You are the centralized data access layer for all career data operations. You provide a clean, file-system agnostic interface that validates all data using Pydantic schemas.

## When to Use This Skill

**CRITICAL:** ALL other career skills MUST use data-access for file I/O operations. Never read or write files directly.

Use this skill when:
- Reading master resume or career history
- Reading/writing job analyses
- Reading/writing tailored resumes or cover letters
- Managing application directories
- Listing applications
- Any file operation involving career data

**Integration Pattern:**
```
job-analyzer → data-access (write job analysis)
resume-writer → data-access (read master resume, read job analysis, write tailored resume)
cover-letter-writer → data-access (read career history, read job analysis, write cover letter)
```

## What This Skill Does

**Provides validated data access** for:
1. **Read Operations**: Master resume, career history, job analyses, tailored resumes, cover letters
2. **Write Operations**: Job analyses, tailored resumes, cover letters, portfolio examples
3. **Utility Operations**: Get/create application directories, list applications
4. **Validation**: All data validated against Pydantic schemas before read/write

**Key Principle:** File-system agnostic interface that makes it easy to swap storage backends later (e.g., database instead of files).

## Available Operations

### Read Operations

#### Read Master Resume
```
Tool: mcp__resume-agent__data_read_master_resume()
Returns: Complete master resume (validated via MasterResume schema)
Schema: PersonalInfo + employment_history + professional_summary
File: ./resumes/kris-cernjavic-resume.yaml
```

#### Read Career History
```
Tool: mcp__resume-agent__data_read_career_history()
Returns: Extended career history with detailed achievements (validated via CareerHistory schema)
Schema: PersonalInfo + employment_history with Achievement objects
File: ./resumes/career-history.yaml
```

#### Read Job Analysis
```
Tool: mcp__resume-agent__data_read_job_analysis(company, job_title)
Returns: Structured job posting data (validated via JobAnalysis schema)
Schema: url, company, job_title, qualifications, keywords, responsibilities, etc.
File: ./job-applications/{Company}_{JobTitle}/job-analysis.json
```

#### Read Tailored Resume
```
Tool: mcp__resume-agent__data_read_tailored_resume(company, job_title)
Returns: Previously generated tailored resume (validated via TailoredResume schema)
Schema: company, job_title, content, keywords_used, changes_from_master
File: ./job-applications/{Company}_{JobTitle}/Resume_{Company}.txt
```

#### Read Cover Letter
```
Tool: mcp__resume-agent__data_read_cover_letter(company, job_title)
Returns: Previously generated cover letter (validated via CoverLetter schema)
Schema: company, job_title, content, talking_points
File: ./job-applications/{Company}_{JobTitle}/CoverLetter_{Company}.txt
```

#### List Applications
```
Tool: mcp__resume-agent__data_list_applications(limit=10)
Returns: List of application metadata (validated via ApplicationMetadata schema)
Schema: directory, company, role, files dict, modified timestamp
Directory: ./job-applications/
```

### Write Operations

#### Save Job Analysis
```
Tool: mcp__resume-agent__data_write_job_analysis(company, job_title, job_data)
Validates: Data must match JobAnalysis schema (required fields, array lengths)
Creates: Application directory if doesn't exist
Returns: File path where data was saved
File: ./job-applications/{Company}_{JobTitle}/job-analysis.json
```

#### Save Tailored Resume
```
Tool: mcp__resume-agent__data_write_tailored_resume(company, job_title, content, metadata)
Validates: TailoredResume schema (company, job_title, content required)
Optional: metadata (keywords_used, changes_from_master)
Returns: File path where resume was saved
File: ./job-applications/{Company}_{JobTitle}/Resume_{Company}.txt
```

#### Save Cover Letter
```
Tool: mcp__resume-agent__data_write_cover_letter(company, job_title, content, metadata)
Validates: CoverLetter schema (company, job_title, content required)
Optional: metadata (talking_points)
Returns: File path where cover letter was saved
File: ./job-applications/{Company}_{JobTitle}/CoverLetter_{Company}.txt
```

#### Save Portfolio Examples
```
Tool: mcp__resume-agent__data_write_portfolio_examples(company, job_title, content)
Validates: PortfolioExamples schema
Returns: File path where examples were saved
File: ./job-applications/{Company}_{JobTitle}/portfolio_examples.txt
```

### Utility Operations

#### Get Application Path
```
Tool: mcp__resume-agent__data_get_application_path(company, job_title, ensure_exists)
Parameters:
  - company: Company name
  - job_title: Job title
  - ensure_exists: True to create directory if doesn't exist
Returns: Directory path and existence status
Directory: ./job-applications/{Company}_{JobTitle}/
```

## Response Format

Always use: **Status (✓/✗)** + **Summary** + **Key details** + **Data status**

**Success (Read):**
```
✓ Master resume loaded successfully
Name: Kris Cernjavic | Experience: 6 positions | Technologies: 40+ skills
[Data validated and ready for use]
```

**Success (Write):**
```
✓ Job analysis saved successfully
Company: Cookpad | Role: Conversational AI Engineer | Keywords: 30+ ✓
[Data validated and saved]
```

**Error (Not Found):**
```
✗ Job analysis not found
Company: Cookpad | Role: Conversational AI Engineer
Run /career:fetch-job {url} first to cache the job data.
```

## Validation Rules

### JobAnalysis Schema
**Required fields:**
- url (string): Job posting URL
- fetched_at (string): ISO timestamp
- company (string): Non-empty
- job_title (string): Non-empty
- location (string): Non-empty
- required_qualifications (array): ≥1 item
- responsibilities (array): ≥1 item
- keywords (array): ≥1 item
- candidate_profile (string): Non-empty
- raw_description (string): Original content

**Optional fields:**
- salary_range (string/null)
- preferred_qualifications (array)

### MasterResume Schema
**Required fields:**
- personal_info (PersonalInfo object)
- employment_history (array of Employment objects)

**Optional fields:**
- about_me (string)
- professional_summary (string)

### TailoredResume Schema
**Required fields:**
- company (string)
- job_title (string)
- content (string)
- created_at (string): ISO timestamp

**Optional fields:**
- keywords_used (array)
- changes_from_master (array)

### CoverLetter Schema
**Required fields:**
- company (string)
- job_title (string)
- content (string)
- created_at (string): ISO timestamp

**Optional fields:**
- talking_points (array)

## Usage Patterns

### Pattern 1: Read Operations (Job Analysis Workflow)

**User:**
> "Read master resume and job analysis for Cookpad, Conversational AI Engineer"

**Skill Actions:**
1. Call `data_read_master_resume()` → validate MasterResume schema
2. Call `data_read_job_analysis("Cookpad", "Conversational AI Engineer")` → validate JobAnalysis schema
3. Return combined summary with key details from both datasets

**Response:**
```
✓ Data loaded successfully

MASTER RESUME
- Name: Kris Cernjavic
- Experience: 10+ years software engineering
- Key Technologies: C#, .NET, Azure, AI/ML, Claude Code
- Recent: AI-driven automation at Aryza (95% cost reduction)

JOB ANALYSIS - Cookpad
- Role: Conversational AI Engineer
- Location: Tokyo, Japan
- Required: 5+ years, Python, LLMs, RAG, Multi-agent systems
- Preferred: LangChain, Vector DBs, MLOps

Both datasets validated and ready for analysis.
```

### Pattern 2: Write Operations (Save Job Analysis)

**User:**
> "Save job analysis for Cookpad, Conversational AI Engineer: {json_data}"

**Skill Actions:**
1. Parse company name and job title from request
2. Extract JSON data payload
3. Validate data against JobAnalysis schema
4. Call `data_write_job_analysis("Cookpad", "Conversational AI Engineer", json_data)`
5. Return confirmation with file path

**Response:**
```
✓ Job analysis saved successfully

Company: Cookpad
Role: Conversational AI Engineer

Validation:
- All required fields present ✓
- 11 required qualifications ✓
- 5 preferred qualifications ✓
- 14 key responsibilities ✓
- 30+ ATS keywords ✓
- Schema: JobAnalysis ✓

File: ./job-applications/Cookpad_Conversational_AI_Engineer/job-analysis.json
```

### Pattern 3: Validation Error Handling

**User:**
> "Save job analysis with incomplete data: {invalid_json}"

**Skill Actions:**
1. Attempt to validate data against JobAnalysis schema
2. Pydantic raises validation error (missing required fields)
3. Return detailed error with guidance

**Response:**
```
✗ Failed to save job analysis

Validation Error: JobAnalysis schema validation failed

Missing required fields:
- required_qualifications (must contain ≥1 item)
- keywords (must contain ≥1 item)
- candidate_profile (must be non-empty string)

Please ensure all required fields are present and match the schema.
See references/schema-examples.md for complete schema definition.
```

### Pattern 4: List Applications

**User:**
> "List recent applications"

**Skill Actions:**
1. Call `data_list_applications(limit=10)`
2. Return formatted list with metadata

**Response:**
```
✓ Recent applications retrieved

Found 3 applications:

1. Cookpad - Conversational AI Engineer
   Files: job-analysis.json ✓, Resume_Cookpad.txt ✓, CoverLetter_Cookpad.txt ✓
   Modified: 2025-10-22 14:30

2. GitHub - Senior Frontend Engineer
   Files: job-analysis.json ✓, Resume_GitHub.txt ✓
   Modified: 2025-10-20 09:15

3. Legal Tech Corp - Data Scientist
   Files: job-analysis.json ✓
   Modified: 2025-10-19 16:45
```

## Error Handling

**File Not Found:** `✗ {Resource} not found | Company: {X} | Role: {Y} | [Suggest creation command]`

**Validation Error:** `✗ Failed to save | Schema: {X} | Missing: {fields} | See references/schema-examples.md`

**Permission Error:** `✗ Directory creation failed | Check permissions, disk space, locks`

**Network Error:** `✗ MCP server timeout | Check: server running, config, restart Claude Desktop`

## File System Abstraction

**Important Design Principle:** Never expose file paths in responses unless specifically requested. Provide a clean interface that hides implementation details.

**Instead of:**
> "I'll save it to ./job-applications/Company_Title/job-analysis.json"

**Say:**
> "Saving job analysis for {Company}, {Title}"

**Why:** This abstraction allows future migration to database storage without changing how other skills interact with data-access.

**Exception:** Include file paths in validation/debugging contexts or when user explicitly asks "where is this saved?"

## Integration with Other Skills

### job-analyzer Skill

**Workflow:**
1. job-analyzer fetches and parses job posting
2. job-analyzer calls data-access to save JobAnalysis JSON
3. data-access validates against JobAnalysis schema
4. data-access creates application directory
5. data-access saves to job-applications/{Company}_{JobTitle}/job-analysis.json

**Data Flow:**
```
job-analyzer (parse job) → data-access (validate + save) → filesystem
```

### resume-writer Skill (Future)

**Workflow:**
1. resume-writer calls data-access to read master resume
2. resume-writer calls data-access to read job analysis
3. resume-writer generates tailored resume content
4. resume-writer calls data-access to save tailored resume
5. data-access validates against TailoredResume schema
6. data-access saves to job-applications/{Company}_{JobTitle}/Resume_{Company}.txt

**Data Flow:**
```
resume-writer → data-access (read master + job analysis)
resume-writer (generate) → data-access (validate + save resume) → filesystem
```

### cover-letter-writer Skill (Future)

**Workflow:**
1. cover-letter-writer calls data-access to read career history
2. cover-letter-writer calls data-access to read job analysis
3. cover-letter-writer generates cover letter content
4. cover-letter-writer calls data-access to save cover letter
5. data-access validates against CoverLetter schema
6. data-access saves to job-applications/{Company}_{JobTitle}/CoverLetter_{Company}.txt

**Data Flow:**
```
cover-letter-writer → data-access (read career history + job analysis)
cover-letter-writer (generate) → data-access (validate + save letter) → filesystem
```

## Performance

**Target Performance:**
- Read operations: <2 seconds
- Write operations: <3 seconds (includes validation)
- List operations: <1 second

**Factors Affecting Speed:**
- File size (master resume ~50KB, job analysis ~10KB)
- Validation complexity (Pydantic schema validation adds ~100ms)
- Disk I/O speed
- MCP server response time

**Optimization:**
- MCP server caches frequently accessed files (master resume, career history)
- Validation is performed in-memory before disk write
- Directory creation is idempotent (no-op if exists)

## Backward Compatibility

**With existing MCP server:**
- All tools use identical Pydantic schemas defined in `apps/resume-agent/resume_agent.py`
- File locations match existing MCP tool expectations
- MCP server reads/writes same files as this skill
- Both architectures (MCP + skills) coexist seamlessly

**Migration Path:**
- Zero setup for skills in Claude Code
- MCP server provides full control in Claude Desktop
- Same data files, different access methods
- No data migration needed

## Troubleshooting

**Skill not responding:** Check MCP server running, Claude Desktop config, restart

**Validation failing:** Review `references/schema-examples.md`, check JSON syntax, trailing commas

**Wrong location:** Verify working directory, job-applications/ exists, sanitization (spaces → underscores)

**Permission denied:** Check write permissions, disk space, process locks

---

**For schema examples:** See `references/schema-examples.md`
**For Pydantic definitions:** See `apps/resume-agent/resume_agent.py` (lines 99-197)
**For MCP server details:** See `README-MCP-SERVER.md`
