---
description: Search GitHub repositories for code examples matching job requirements
allowed-tools: Bash(gh:*), Read, web_fetch
argument-hint: [job-url]
---

# Find Portfolio Examples for Job

Job URL: $ARGUMENTS

## Workflow

**Step 1: Analyze Job Requirements**

Use the job-analyzer sub-agent to extract required technologies and skills from the job posting.

**Step 2: Search Your Portfolio**

Use the portfolio-finder sub-agent to search your GitHub repositories for examples of those technologies.

Provide the portfolio-finder with:
- List of required technologies from job analysis
- Any preferred/bonus skills that could differentiate you
- Context about the seniority level (affects what kind of examples to prioritize)

**Step 3: Generate Portfolio Report**

Save the portfolio analysis to the job's folder (create if doesn't exist):
`{Company}_{JobTitle}/portfolio_examples.txt`

This file will contain:
- Links to relevant repositories
- Specific code examples for each required technology
- Recommendations for which projects to highlight

**Step 4: Integration Recommendations**

Provide specific suggestions:

**For Your Resume:**
"Add these projects to your experience section:
- [Project Name]: [How to describe it] [Link]"

**For Your Cover Letter:**
"Mention this specific example:
[Concrete example with link that demonstrates a key requirement]"

**For Interview Prep:**
"Be ready to discuss these repositories in detail:
[Top 2-3 most impressive projects]"

**Step 5: Next Steps**

Remind about repository access:
- Which repos are currently private
- Whether to make any public before applying
- How to provide interviewer access if requested