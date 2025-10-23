---
description: Generate a customized cover letter for a specific job
allowed-tools: mcp__resume-agent__data_read_job_analysis, mcp__resume-agent__data_read_master_resume, mcp__resume-agent__data_write_cover_letter, Task, Skill
argument-hint: [job-url]
---

# Generate Cover Letter

Job URL: $ARGUMENTS

## Workflow

**Phase 1: Gather Context**
1. Extract company and job title from the URL or arguments
2. Load job analysis and master resume from database:
```
job_analysis = mcp__resume-agent__data_read_job_analysis(company, job_title)
master_resume = mcp__resume-agent__data_read_master_resume()
```

**Note:** If job analysis doesn't exist, instruct user to run `/career:fetch-job [job-url]` first.

**Phase 2: Research the Company**
Look for clues in the job posting about:
- Company values and culture
- Recent projects or products mentioned
- Specific technologies or methodologies they emphasize
- The tone of their posting (formal, casual, innovative, traditional)

**Phase 3: Generate Cover Letter**
Invoke the cover-letter-writer skill:
```
Skill(
  command="cover-letter-writer",
  description="Generate cover letter",
  prompt="Generate a compelling cover letter based on:

  Resume: {master_resume}
  Job Analysis: {job_analysis}

  The cover letter should demonstrate understanding of both the role and the company."
)
```

**Phase 4: Save Output**
Save the generated cover letter to the database:
```
mcp__resume-agent__data_write_cover_letter(
  company=company,
  job_title=job_title,
  content=cover_letter_content,
  metadata={
    "talking_points": [...],
    "company_details_referenced": [...]
  }
)
```

**Phase 5: Review Points**
Provide me with:
- Key points emphasized in the letter
- Specific company details referenced
- Recommended ways to customize further
- Any concerns or suggestions