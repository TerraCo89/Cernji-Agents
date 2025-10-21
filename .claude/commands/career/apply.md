---
description: Complete job application workflow - analyzes job, tailors resume, generates cover letter, finds portfolio examples
allowed-tools: SlashCommand, Task, Bash(gh:*)
argument-hint: [job-url]
---

# Full Job Application Workflow

Job URL: $ARGUMENTS

## Complete Process

**Phase 1: Fetch and Cache Job Data**
1. Run `/career:fetch-job $ARGUMENTS` to fetch and cache the structured job data
2. The fetch-job command creates the application directory and saves job-analysis.json
3. The cached data includes: requirements, keywords, responsibilities, company info

**Phase 2: Load and Display Job Analysis**
1. Use Task tool with subagent_type="data-access-agent"
2. Request: "Read job analysis for {Company}, {Job Title}"
3. Display a summary so you can review before proceeding:
   - Company and role
   - Required qualifications (count)
   - Preferred qualifications (count)
   - Key responsibilities
   - ATS keywords

This helps you confirm the job is worth applying to.

**Phase 3: Load Master Resume**
1. Use Task tool with subagent_type="data-access-agent"
2. Request: "Read master resume"
3. This provides your complete career background for the next phases

**Phase 4: Portfolio Search**
1. Use the Task tool with subagent_type="portfolio-finder" to search your GitHub repositories
2. Provide the portfolio-finder with:
   - Required skills from the job analysis (from Phase 2)
   - Preferred skills from the job analysis
3. The portfolio-finder should:
   - Search for code examples demonstrating the key technologies
   - Return a structured list of relevant repositories and code snippets
   - NOT perform any file operations (just return the data)

**Phase 5: Save Portfolio Examples**
1. Use Task tool with subagent_type="data-access-agent"
2. Request: "Save portfolio examples for {Company}, {Job Title}: {portfolio_content}"
3. This saves the portfolio findings for future reference

**Phase 6: Resume Tailoring**
1. Use the Task tool with subagent_type="resume-writer" to create an optimized resume
2. Provide the resume-writer with:
   - Master resume data (from Phase 3)
   - Job requirements from job analysis (from Phase 2)
   - Portfolio examples (from Phase 4)
3. The resume writer should:
   - Return ONLY the resume content (no file operations)
   - Incorporate keywords naturally
   - Emphasize relevant experience
   - Mention specific projects that demonstrate required skills

**Phase 7: Save Tailored Resume**
1. Use Task tool with subagent_type="data-access-agent"
2. Request: "Save tailored resume for {Company}, {Job Title}: {resume_content}"
3. Optional: Include metadata about keywords used and changes made

**Phase 8: Cover Letter Generation**
1. Use the Task tool with subagent_type="cover-letter-writer" to create a compelling narrative
2. Provide the cover letter writer with:
   - Master resume data (from Phase 3)
   - Job requirements from job analysis (from Phase 2)
   - Portfolio examples (from Phase 4)
3. The cover letter writer should:
   - Return ONLY the cover letter content (no file operations)
   - Tell a compelling story about why you're interested
   - Mention at least one specific project with a link
   - Demonstrate cultural fit and enthusiasm

**Phase 9: Save Cover Letter**
1. Use Task tool with subagent_type="data-access-agent"
2. Request: "Save cover letter for {Company}, {Job Title}: {cover_letter_content}"
3. Optional: Include metadata about talking points

**Phase 10: Final Organization**
The application folder now contains all necessary files:
- `job-analysis.json` - Structured job data
- `Resume_{Company}.txt` - Tailored resume
- `CoverLetter_{Company}.txt` - Personalized cover letter
- `portfolio_examples.txt` - Relevant code examples

**Phase 11: Application Readiness Report**
Provide a comprehensive summary:

```
APPLICATION PACKAGE COMPLETE
============================

Folder: ./job-applications/{Company}_{Title}/

FILES GENERATED
---------------
✓ job-analysis.json (structured requirements)
✓ Resume_{Company}.txt (tailored resume)
✓ CoverLetter_{Company}.txt (personalized letter)
✓ portfolio_examples.txt (code examples)

MATCH ASSESSMENT
----------------
Overall Score: [X]/10
Required Skills Coverage: [X]%
Preferred Skills Coverage: [X]%

TOP 3 INTERVIEW TALKING POINTS
-------------------------------
1. [Talking point with code example link]
2. [Talking point with code example link]
3. [Talking point with code example link]

PORTFOLIO HIGHLIGHTS
--------------------
- [Repo 1]: [What it demonstrates]
- [Repo 2]: [What it demonstrates]
- [Repo 3]: [What it demonstrates]

REPOSITORY ACCESS
-----------------
[Which private repos you might want to share]

RECOMMENDED NEXT STEPS
---------------------
1. [First action to take]
2. [Second action to take]
3. [Third action to take]
```

This gives you everything you need to apply confidently.

## Important Notes

**Data Access Architecture:**
- This command now uses the **data-access-agent** for ALL file operations
- All agents (resume-writer, cover-letter-writer, portfolio-finder) are data-agnostic
- They receive data as input and return content as output (no direct file I/O)
- The data-access-agent handles all reading/writing with Pydantic validation

**Benefits:**
- ✓ Type-safe: All data validated against schemas
- ✓ Centralized: Single source of truth for data operations
- ✓ Testable: Each agent can be tested independently
- ✓ Future-proof: Easy to swap file storage for database later

**Agent Responsibilities:**
- **fetch-job**: Fetches job posting → saves via data-access-agent
- **data-access-agent**: All file I/O with validation
- **portfolio-finder**: Searches GitHub → returns data (no file I/O)
- **resume-writer**: Receives data → returns resume content (no file I/O)
- **cover-letter-writer**: Receives data → returns cover letter content (no file I/O)