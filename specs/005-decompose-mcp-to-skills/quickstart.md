# Quickstart: Job Analyzer Skill (MVP)

**Time to complete**: ~5 minutes
**Prerequisites**: Claude Code 0.4.0+, internet connection, job posting URL

---

## Overview

The job-analyzer skill extracts structured information from job postings automatically. You provide a URL, and Claude analyzes the posting to identify requirements, skills, responsibilities, and ATS-critical keywords.

**What this skill does**:
- Fetches job posting from URL
- Extracts company, title, location, requirements
- Identifies required vs. preferred qualifications
- Generates ATS keyword list
- Saves structured data for resume tailoring

**What this skill doesn't do** (yet):
- Tailor resumes (use resume-writer skill - future work)
- Generate cover letters (use cover-letter-writer skill - future work)
- Find portfolio examples (use portfolio-finder skill - future work)

---

## Step 1: Verify Skill Installation

The job-analyzer skill should be automatically discovered when Claude Code loads this repository.

**Test discovery**:
```
You: "What career-related skills are available?"
Claude: "I can help with job analysis using the job-analyzer skill..."
```

If skill isn't discovered:
1. Verify you're in the `D:\source\Cernji-Agents` directory
2. Check `.claude/skills/career/job-analyzer/SKILL.md` exists
3. Restart Claude Code session

---

## Step 2: Analyze Your First Job Posting

**Find a job posting** from a supported site:
- [japan-dev.com](https://japan-dev.com) - English-language Japan tech jobs
- [recruit.legalontech.jp](https://recruit.legalontech.jp) - Legal tech jobs (mixed JP/EN)
- GitHub Jobs, LinkedIn, or any job board with structured HTML

**Example job posting** (for testing):
```
https://japan-dev.com/jobs/cookpad/senior-backend-engineer
```

**Analyze it**:
```
You: "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
Claude: [Automatically invokes job-analyzer skill]
```

**Expected output** (within 5 seconds):
```json
{
  "company": "Cookpad",
  "job_title": "Senior Backend Engineer",
  "location": "Tokyo, Japan",
  "remote_policy": "Hybrid (2 days office)",
  "required_skills": [
    "Python",
    "PostgreSQL",
    "5+ years backend development",
    "Microservices architecture experience"
  ],
  "preferred_skills": [
    "AWS",
    "Docker",
    "Kubernetes",
    "Ruby on Rails"
  ],
  "responsibilities": [
    "Design and implement scalable backend systems",
    "Collaborate with product team on feature planning",
    "Mentor junior engineers",
    "Participate in technical architecture decisions"
  ],
  "keywords": [
    "Python", "PostgreSQL", "AWS", "Microservices",
    "API Design", "Docker", "Kubernetes", "Backend",
    "Scalability", "Mentoring", "Ruby", "Rails"
  ],
  "salary_range": "¥8M-¥12M",
  "experience_level": "Senior (5-8 years)"
}
```

---

## Step 3: Review Stored Data

After analysis, Claude saves the structured data to your local filesystem.

**Location**:
```
job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json
```

**Verify the file**:

**Option 1: Command line**
```bash
cat "job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json"
```

**Option 2: File explorer**
Navigate to `D:\source\Cernji-Agents\job-applications\` and open the company folder.

**Why this matters**:
- Resume-writer skill will read this data to tailor your resume
- Cover-letter-writer skill will reference it for personalization
- Portfolio-finder skill will match your code examples to required skills
- You can review the analysis before starting your application

---

## Step 4: Test with Your Own Job Posting

Now try analyzing a job you're actually interested in:

```
You: "Analyze this job posting: [YOUR JOB URL]"
Claude: [Invokes skill automatically]
```

**Tips for best results**:
- Use job postings from structured job boards (better HTML parsing)
- English-language postings work best (keyword extraction optimized for English)
- If posting requires JavaScript to load, skill will use Playwright (may take 5-10s)

**Supported job boards** (confirmed compatible):
- japan-dev.com ✓
- recruit.legalontech.jp ✓
- GitHub Jobs ✓
- LinkedIn Jobs ✓
- Company career pages (variable quality)

---

## Common Issues & Solutions

### Issue 1: Skill not found

**Symptoms**:
```
You: "Analyze this job posting: [URL]"
Claude: "I don't have a specific skill for that..."
```

**Solutions**:
1. **Verify directory**: Ensure you're in `D:\source\Cernji-Agents`
2. **Check skill file**: Confirm `ai_docs/claude-skills/career/job-analyzer/SKILL.md` exists
3. **Explicit invocation**: Try "Use the job-analyzer skill to analyze [URL]"
4. **Restart Claude Code**: Skill discovery happens at session start

---

### Issue 2: Failed to fetch job posting

**Symptoms**:
```
Error: "Failed to fetch job posting: Timeout after 30 seconds"
```

**Solutions**:
1. **Verify URL**: Open URL in your browser - does it load?
2. **Check connectivity**: Test internet connection
3. **Try different URL**: Some sites block automated fetching
4. **JavaScript-heavy sites**: May require longer timeout (skill uses Playwright for these)

**Alternative**: If fetch fails repeatedly, copy the job posting text and provide it directly:
```
You: "Here's a job posting I'd like analyzed: [PASTE FULL TEXT]"
Claude: [Analyzes text directly without fetching]
```

---

### Issue 3: Malformed or incomplete output

**Symptoms**:
- Missing required fields
- Empty arrays for required_skills or responsibilities
- Generic keywords list

**Solutions**:
1. **Check job posting structure**: Is the HTML well-formatted?
2. **Try different site**: Some job boards have clearer structure
3. **Manual cleanup**: Edit the saved `job-analysis.json` to add missing info

**Note**: MVP skill uses heuristic parsing. Future versions may use more sophisticated extraction.

---

### Issue 4: Directory creation failed

**Symptoms**:
```
Error: "Failed to create directory: Permission denied"
```

**Solutions**:
1. **Check permissions**: Ensure write access to `D:\source\Cernji-Agents\job-applications\`
2. **Run as administrator** (if on Windows with restricted permissions)
3. **Verify disk space**: Ensure sufficient space for new directories

---

## Next Steps

Once you've successfully analyzed a job posting:

### 1. Review the Analysis
```
You: "Show me the job analysis for Cookpad Senior Backend Engineer"
Claude: [Reads and displays job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json]
```

### 2. Assess Your Match
```
You: "How well do I match this job based on my master resume?"
Claude: [Compares your resumes/kris-cernjavic-resume.yaml to job requirements]
```

### 3. Tailor Your Resume (Future Work)
```
You: "Tailor my resume for this Cookpad job"
Claude: [Will use resume-writer skill once implemented]
```

### 4. Generate Cover Letter (Future Work)
```
You: "Generate a cover letter for Cookpad"
Claude: [Will use cover-letter-writer skill once implemented]
```

### 5. Find Portfolio Examples (Future Work)
```
You: "Find portfolio examples that match this job's requirements"
Claude: [Will use portfolio-finder skill once implemented]
```

---

## Understanding the Output

### required_skills vs. preferred_skills

**Required**: MUST-have qualifications - if you don't have these, you may be auto-rejected by ATS.

**Preferred**: Nice-to-have qualifications - strengthen your application but not mandatory.

**Use this for prioritization**:
- Ensure your resume prominently features ALL required skills
- Include as many preferred skills as you honestly possess
- Don't claim skills you don't have (will be revealed in interviews)

### keywords Array

**Purpose**: ATS (Applicant Tracking System) optimization.

**How to use**:
- These 10-15 terms are most frequently mentioned or emphasized in the posting
- Your resume should include these exact keywords where applicable
- Don't keyword-stuff - use them naturally in context

**Example**:
If keywords include ["Python", "Microservices", "PostgreSQL"], ensure your resume mentions:
- "Designed **microservices** architecture using **Python** and **PostgreSQL**"
- Not just "Worked with databases" (too vague, misses keywords)

### candidate_profile

**Purpose**: Understand the "culture fit" they're seeking.

**Example**:
> "We're looking for an experienced backend engineer who thrives in a collaborative environment and has a passion for building scalable systems that serve millions of users."

**Key themes**: Collaboration, scalability, user impact

**Use this for**:
- Cover letter tone and emphasis
- Interview talking points
- Assessing cultural alignment

---

## Testing Checklist

Before relying on this skill for real job applications, validate it works:

- [ ] Skill auto-discovered by Claude Code
- [ ] Successfully analyzed a test job posting (japan-dev.com)
- [ ] JSON file created in job-applications directory
- [ ] All required fields present (company, job_title, required_skills, responsibilities, keywords)
- [ ] Keywords list contains 10-15 relevant terms
- [ ] Graceful error handling when URL is invalid

If all checks pass ✓, you're ready to use the job-analyzer skill for real applications!

---

## FAQ

**Q: Can I analyze multiple jobs in one session?**
A: Yes! Each analysis creates a separate directory. Analyze as many as you want.

**Q: What if the job posting is in Japanese?**
A: MVP skill works best with English postings. Japanese support planned for future versions.

**Q: Can I edit the job-analysis.json file manually?**
A: Yes! It's just a JSON file. Edit as needed to correct parsing errors or add missing info.

**Q: How do I delete an analysis?**
A: Delete the directory from `job-applications/{Company}_{JobTitle}/`

**Q: Does this work with LinkedIn jobs?**
A: Partially. LinkedIn's HTML is complex and may require copy-pasting the text instead of using the URL.

**Q: Can I use this without Claude Code?**
A: No. This skill requires Claude Code 0.4.0+ for skill discovery and code execution environment.

---

## Support & Feedback

**Issues**: If you encounter problems not covered in this quickstart, check:
1. `specs/005-decompose-mcp-to-skills/plan.md` - Implementation plan and design decisions
2. `specs/005-decompose-mcp-to-skills/research.md` - Technical research and alternatives
3. `.claude/skills/career/job-analyzer/SKILL.md` - Detailed skill instructions

**Future Enhancements**:
- Japanese job posting support
- More robust HTML parsing
- LinkedIn direct integration
- Automated ATS compatibility scoring

---

**Quickstart Complete!** You're now ready to analyze job postings with the job-analyzer skill.

**Recommended first use**: Analyze 2-3 real job postings you're interested in, review the output quality, and get comfortable with the workflow before relying on it for serious applications.
