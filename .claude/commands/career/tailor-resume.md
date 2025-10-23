---
description: Tailor your resume for a specific job posting
allowed-tools: SlashCommand, Task, Skill
argument-hint: [job-url]
---

# Tailor Resume for Job

Job URL: $ARGUMENTS

## Workflow

**Phase 1: Ensure Job Data is Cached**
1. Run `/career:fetch-job $ARGUMENTS` to fetch and cache the job posting data
2. This ensures we have clean, structured job data to work with
3. The fetch-job command will extract company and job title from the URL

**Phase 2: Load Required Data**
Use the Task tool with subagent_type="data-access-agent" to load both datasets:

1. First request: "Read job analysis for {Company}, {Job Title}"
   - Returns: structured job posting data with requirements, keywords, responsibilities

2. Second request: "Read master resume"
   - Returns: your complete career background with skills, experience, achievements

The data-access-agent handles all file I/O and data validation.

**Phase 3: Create Tailored Resume**
Invoke the resume-writer skill using Skill(resume-writer).

Provide the resume-writer skill with:
- Your complete master resume data (from Phase 2)
- Structured job requirements from the job analysis (from Phase 2)
- List of ATS keywords to incorporate
- Company and role details

The resume writer should:
- Emphasize relevant experience and skills
- Incorporate ATS keywords naturally
- Reorder or highlight projects that match job requirements
- Optimize formatting for ATS systems
- Return ONLY the resume content (no file operations)

**Phase 4: Save Output via Data Access Agent**
Use the Task tool with subagent_type="data-access-agent" to save the resume:

Request: "Save tailored resume for {Company}, {Job Title}: {resume_content}"

Optional: Include metadata about keywords used and changes from master resume

The data-access-agent will:
- Create the application directory if needed
- Save the resume file
- Optionally save metadata for future reference

**Phase 5: Summary**
Provide a summary:

```
✓ RESUME TAILORED SUCCESSFULLY

Company: {Company}
Role: {Job Title}

KEY CHANGES FROM MASTER RESUME
-------------------------------
- [List 3-5 significant changes made]

ATS OPTIMIZATION
----------------
- Keywords incorporated: [count]
- Skills emphasized: [list key skills]
- Projects highlighted: [list relevant projects]

MATCH ASSESSMENT
----------------
- Overall match: [X]%
- Required skills coverage: [X]%
- Preferred skills coverage: [X]%

COVER LETTER RECOMMENDATIONS
----------------------------
1. [First skill/experience to emphasize]
2. [Second skill/experience to emphasize]
3. [Third skill/experience to emphasize]

Resume saved and ready for submission.
```

## Important Notes

- This command now uses the **data-access-agent** for all file operations
- The resume-writer skill is data-agnostic (receives data, returns content)
- All data is validated using Pydantic schemas before being saved
- You don't need to know about file paths or directory structures