---
description: Analyze a job posting to understand requirements and assess match with your background
allowed-tools: SlashCommand, Task
argument-hint: [job-url]
---

# Analyze Job Posting

Job URL: $ARGUMENTS

## Purpose
Assesses how well your background matches a job posting by comparing the structured job requirements against your master resume.

## Process

**Step 1: Ensure Job Data is Cached**
1. Run `/career:fetch-job $ARGUMENTS` to fetch and cache the job posting data
2. This is idempotent - if already cached, it will reuse existing data
3. The fetch-job command will parse the URL to extract company and job title

**Step 2: Load Job Data and Master Resume**
Use the Task tool with subagent_type="data-access-agent" to load both datasets:

1. First request: "Read job analysis for {Company}, {Job Title}"
   - This returns the structured job posting data
   - Includes: required_qualifications, preferred_qualifications, responsibilities, keywords, candidate_profile

2. Second request: "Read master resume"
   - This returns your complete career background
   - Includes: skills, work experience, achievements, education

Both requests use the data-access-agent which handles all file I/O and validation.

**Step 3: Perform Match Assessment**
Compare your background to the job requirements and provide:

**Match Score (1-10):**
- Provide a numerical score with clear reasoning
- Consider: required skills coverage, experience level, domain knowledge

**Skills Match Analysis:**
- ✓ Required skills you have (list each with evidence from your resume)
- ✓ Preferred skills you have (list each with evidence)
- ⚠ Skills mentioned in the job that you should emphasize (even if not directly listed)
- ✗ Gaps you should address or work around in your application

**Experience Match:**
- How your past roles/projects align with the responsibilities
- Specific examples from your resume that demonstrate relevant experience

**Keyword Coverage:**
- Which ATS keywords from the job you already have in your background
- Which keywords you should incorporate into your tailored resume

**Application Strategy:**
- Should you apply? (Yes/No/Maybe with reasoning)
- Key talking points for your cover letter
- How to position yourself (what angle to emphasize)
- Any concerns to address proactively

## Output Format

Present a clear, actionable summary:

```
MATCH ASSESSMENT
================

Company: {company}
Role: {job_title}
Match Score: {score}/10

STRENGTHS
---------
✓ [List your matching qualifications with evidence]

GAPS
----
✗ [List any missing requirements and mitigation strategies]

RECOMMENDATION
--------------
[Should apply? Why or why not?]

POSITIONING STRATEGY
-------------------
[How to angle your application]

KEY TALKING POINTS
------------------
1. [First talking point for cover letter]
2. [Second talking point]
3. [Third talking point]
```