---
name: job-analyzer
description: Analyzes job postings to extract structured requirements, skills, responsibilities, and ATS keywords. Automatically invoked when analyzing job opportunities or career applications. Returns structured data for resume tailoring and cover letter generation.
---

# Job Analyzer Skill

You are an expert at analyzing job postings and extracting structured information for career application workflows.

## When to Use This Skill

Use this skill when the user:
- Provides a job posting URL to analyze
- Asks to understand job requirements
- Wants to assess match with their background
- Needs structured data for resume tailoring
- Requests ATS keyword extraction

**Trigger phrases:**
- "Analyze this job posting: [URL]"
- "What are the requirements for [company] [role]?"
- "Help me understand this job: [URL]"
- "Extract keywords from this job posting"

## What This Skill Does

**Fetches and parses job postings** to identify:
1. Company, title, location, and compensation details
2. Required vs. preferred qualifications
3. Day-to-day responsibilities
4. ATS-critical keywords (10-15 most important terms)
5. Ideal candidate profile

**Output:** Structured JSON matching the JobAnalysis schema, saved to `job-applications/{Company}_{JobTitle}/job-analysis.json`

## Extraction Guidelines

### Basic Information

**Company Name:**
- Use official English company name if available
- For Japanese companies: "クックパッド株式会社" → "Cookpad Inc."
- Extract from page header, logo, or company section

**Job Title:**
- Use exact title from posting (preserve capitalization)
- Examples: "Senior Backend Engineer", "Staff Software Engineer", "Lead Product Designer"

**Location & Remote Policy:**
- Location: City, country, or "Remote"
- Remote policy: "Fully remote", "Hybrid (2 days office)", "On-site only"
- For multiple locations: "Tokyo, Osaka, or Remote"

**Salary Range (if listed):**
- Preserve original format: "¥8M-¥12M", "$120k-$160k", "Competitive"
- If not listed: omit field or set to null

### Required vs. Preferred Qualifications

**Required Qualifications** (MUST-haves):
- Look for: "required", "must have", "essential", "mandatory"
- Bullet points under "Requirements" or "Qualifications"
- Education requirements, years of experience, core technical skills
- **Critical:** Missing these = likely ATS auto-reject

**Preferred Qualifications** (Nice-to-haves):
- Look for: "preferred", "bonus", "a plus", "ideal candidate also has"
- Advanced skills, additional tools, optional certifications
- Strengthen application but not mandatory

### Responsibilities

Extract 3-8 key day-to-day tasks:
- Usually under "What you'll do", "Responsibilities", "Your role"
- Focus on actionable verbs: "Design", "Implement", "Collaborate", "Lead"
- Prioritize technical work over generic duties

### Keywords for ATS Optimization

Identify 10-15 most important terms:
- Technical skills mentioned multiple times (e.g., "Python", "PostgreSQL", "AWS")
- Methodologies emphasized (e.g., "Microservices", "API Design", "Agile")
- Soft skills if repeatedly mentioned (e.g., "Leadership", "Collaboration")
- **Purpose:** These exact terms should appear in tailored resume

### Candidate Profile

Write 2-3 sentences capturing:
- Seniority level and experience expectation
- Technical focus and domain expertise
- Cultural fit signals (e.g., "collaborative", "fast-paced", "user-focused")

**Example:**
> "We're looking for an experienced backend engineer who thrives in a collaborative environment and has a passion for building scalable systems that serve millions of users."

## Output Format

Return a JSON object with this exact structure (matches JobAnalysis Pydantic schema):

```json
{
  "url": "https://japan-dev.com/jobs/cookpad/senior-backend-engineer",
  "fetched_at": "2025-10-23T11:30:00Z",
  "company": "Cookpad",
  "job_title": "Senior Backend Engineer",
  "location": "Tokyo, Japan",
  "salary_range": "¥8M-¥12M",
  "required_qualifications": [
    "5+ years backend development experience",
    "Strong proficiency in Python and PostgreSQL",
    "Experience with microservices architecture",
    "Bachelor's degree in Computer Science or equivalent"
  ],
  "preferred_qualifications": [
    "AWS cloud services experience",
    "Docker and Kubernetes knowledge",
    "Ruby on Rails familiarity",
    "Experience with high-traffic systems"
  ],
  "responsibilities": [
    "Design and implement scalable backend systems",
    "Collaborate with product team on feature planning",
    "Mentor junior engineers and lead code reviews",
    "Participate in technical architecture decisions"
  ],
  "keywords": [
    "Python", "PostgreSQL", "AWS", "Microservices",
    "API Design", "Docker", "Kubernetes", "Backend",
    "Scalability", "Mentoring", "Ruby on Rails"
  ],
  "candidate_profile": "We're looking for an experienced backend engineer who thrives in a collaborative environment and has a passion for building scalable systems that serve millions of users.",
  "raw_description": "[Full HTML or text content of job posting for reference]"
}
```

**Validation Rules:**
- `required_qualifications`, `responsibilities`, `keywords` must contain at least 1 item
- `company`, `job_title`, `location`, `candidate_profile` are required strings
- `url` and `fetched_at` are required for tracking
- `salary_range`, `preferred_qualifications` are optional
- All strings must be non-empty

## File Storage

**Directory Creation:**
1. Sanitize company and job title: replace spaces with underscores, remove special chars
2. Create directory: `job-applications/{Company}_{JobTitle}/`
3. Save JSON to: `job-applications/{Company}_{JobTitle}/job-analysis.json`

**Example:**
- Company: "Cookpad Inc."
- Title: "Senior Backend Engineer"
- Directory: `job-applications/Cookpad_Inc_Senior_Backend_Engineer/`
- File: `job-applications/Cookpad_Inc_Senior_Backend_Engineer/job-analysis.json`

## Usage Examples

### Pattern 1: Direct URL Analysis

**User:**
> "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"

**Skill Actions:**
1. Fetch HTML from URL using WebFetch or Playwright
2. Parse HTML to extract structured data
3. Format as JobAnalysis JSON
4. Create directory `job-applications/Cookpad_Senior_Backend_Engineer/`
5. Save JSON to `job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json`
6. Return structured data to user

### Pattern 2: Context-Aware Analysis

**User:**
> "I found this job I'm interested in: https://recruit.legalontech.jp/engineer-backend. Can you analyze it?"

**Skill Actions:**
1. Recognize user intent (job analysis request)
2. Auto-invoke job-analyzer skill
3. Fetch and parse job posting
4. Handle mixed Japanese-English content
5. Extract English keywords for ATS compatibility
6. Save and return structured analysis

### Pattern 3: Match Assessment

**User:**
> "How well do I match this job: https://japan-dev.com/jobs/line/staff-engineer"

**Skill Actions:**
1. Analyze job posting (this skill)
2. Read user's master resume (separate data-access operation)
3. Compare required qualifications to resume skills
4. Identify gaps and strengths
5. Provide match score and recommendations

## Error Handling

### Invalid URL

**Symptom:** URL doesn't load or returns 404

**Response:**
```
I couldn't fetch the job posting from that URL. Here are some things to try:
1. Verify the URL is correct and publicly accessible
2. Open the URL in your browser - does it load?
3. If it requires login, copy-paste the job description text instead
4. Try a different job board (japan-dev.com and GitHub Jobs work well)
```

### Network Failure

**Symptom:** Timeout or connection error

**Response:**
```
Failed to fetch job posting: Network timeout after 30 seconds.

Try:
1. Check your internet connection
2. Try again in a moment (site may be temporarily down)
3. As a workaround, copy the full job posting text and I'll analyze it directly
```

### Malformed HTML

**Symptom:** Can't parse required fields from HTML

**Response:**
```
I was able to fetch the page, but the job posting structure is unusual.

I extracted what I could, but some fields may be incomplete:
[Return partial JobAnalysis with available data]

You can manually edit the saved JSON file to add missing information:
job-applications/{Company}_{Title}/job-analysis.json
```

### JavaScript-Heavy Sites

**Symptom:** Page requires JavaScript to render job posting

**Response:**
```
This site requires JavaScript to load the job posting. Using Playwright to fetch...
[Proceed with Playwright browser automation]
Note: This may take 5-10 seconds instead of the usual <5s.
```

## Integration with Other Skills

### Resume Writer (Future Skill)

**Input from job-analyzer:**
- Required qualifications → prioritize these skills in resume
- Keywords → ensure exact keyword matches in resume text
- Responsibilities → align resume achievements with these tasks

**Workflow:**
1. job-analyzer extracts requirements
2. resume-writer reads job-analysis.json
3. resume-writer tailors master resume using keywords and requirements

### Cover Letter Writer (Future Skill)

**Input from job-analyzer:**
- Candidate profile → match tone and emphasis
- Responsibilities → reference specific tasks you're excited about
- Company → research and personalize

### Portfolio Finder (Future Skill)

**Input from job-analyzer:**
- Required skills → search GitHub repos for matching technologies
- Keywords → filter portfolio examples by relevance
- Responsibilities → find code examples demonstrating similar work

## Performance

**Target:** <5 seconds for typical job posting analysis

**Factors affecting speed:**
- Simple HTML: 1-3 seconds
- JavaScript-heavy sites: 5-10 seconds (Playwright required)
- Network latency: varies by site location

**If processing takes >5 seconds:**
- Inform user: "This site requires extra processing, may take 5-10 seconds..."
- Use Playwright for JavaScript-rendered content
- Cache fetched HTML to avoid re-fetching if user re-analyzes

## Supported Job Boards

**Confirmed compatible:**
- japan-dev.com ✓
- recruit.legalontech.jp ✓
- GitHub Jobs ✓
- LinkedIn Jobs (partial - may need copy-paste)
- Company career pages (variable quality)

**Best results:**
- Structured job boards with clear HTML sections
- English-language postings (keyword extraction optimized for English)
- Pages that don't require authentication

## Backward Compatibility

**With existing MCP server:**
- JSON structure matches `JobAnalysis` Pydantic model in `apps/resume-agent/resume_agent.py`
- File location matches existing MCP tool expectations
- MCP server can read files created by this skill
- This skill can read files created by MCP server

**Migration path:**
- Both architectures (MCP + skills) can coexist
- Same data files, different access methods
- Zero setup for skills, full control with MCP server

## Validation Checklist

Before returning results:
- [ ] All required fields present (company, job_title, location, url, fetched_at, candidate_profile)
- [ ] At least 1 item in required_qualifications, responsibilities, keywords
- [ ] Keywords list contains 10-15 terms
- [ ] JSON is well-formed (valid syntax, proper escaping)
- [ ] File saved to correct directory path
- [ ] Directory created if doesn't exist

## Troubleshooting

**Skill not auto-discovered:**
- Verify you're in the correct repository directory
- Check `.claude/skills/job-analyzer/SKILL.md` exists
- Restart Claude Code session (skill discovery happens at startup)

**Output missing fields:**
- Job posting may have unusual structure
- Return partial data with explanation
- Suggest manual editing of saved JSON file

**Directory creation failed:**
- Check write permissions on `job-applications/` directory
- Verify sufficient disk space
- Run Claude Code with appropriate permissions (admin if needed)

---

**For detailed examples:** See `references/example-output.md`
**For schema reference:** See `apps/resume-agent/resume_agent.py` (JobAnalysis class)
