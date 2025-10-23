# Example Output: JobAnalysis JSON Structure

This document shows complete examples of the JSON structure returned by the job-analyzer skill.

---

## Example 1: Backend Engineer (Cookpad)

**Source:** https://japan-dev.com/jobs/cookpad/senior-backend-engineer

**Saved to:** `job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json`

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
    "Bachelor's degree in Computer Science or equivalent",
    "Strong communication skills in English and Japanese"
  ],
  "preferred_qualifications": [
    "AWS cloud services experience (EC2, RDS, S3)",
    "Docker and Kubernetes knowledge",
    "Ruby on Rails familiarity",
    "Experience with high-traffic systems (1M+ users)",
    "Prior experience in food tech or consumer internet"
  ],
  "responsibilities": [
    "Design and implement scalable backend systems",
    "Collaborate with product team on feature planning",
    "Mentor junior engineers and lead code reviews",
    "Participate in technical architecture decisions",
    "Optimize database queries and system performance",
    "Maintain and improve CI/CD pipeline"
  ],
  "keywords": [
    "Python", "PostgreSQL", "AWS", "Microservices",
    "API Design", "Docker", "Kubernetes", "Backend",
    "Scalability", "Mentoring", "Ruby on Rails", "CI/CD"
  ],
  "candidate_profile": "We're looking for an experienced backend engineer who thrives in a collaborative environment and has a passion for building scalable systems that serve millions of users. You should be comfortable working in both English and Japanese, and have a track record of technical leadership.",
  "raw_description": "[Full HTML content omitted for brevity]"
}
```

**Field Breakdown:**

- **url**: Original job posting URL for reference
- **fetched_at**: ISO timestamp when analysis was performed
- **company**: Official company name (English)
- **job_title**: Exact title from posting
- **location**: Office location or remote status
- **salary_range**: Compensation if listed (optional)
- **required_qualifications**: MUST-have skills (5 items)
- **preferred_qualifications**: Nice-to-have skills (5 items)
- **responsibilities**: Day-to-day tasks (6 items)
- **keywords**: ATS-critical terms (12 items)
- **candidate_profile**: Ideal candidate description (2 sentences)
- **raw_description**: Original HTML/text for reference

---

## Example 2: Frontend Engineer (Remote)

**Source:** https://github.com/jobs/frontend-engineer-remote

**Saved to:** `job-applications/GitHub_Frontend_Engineer/job-analysis.json`

```json
{
  "url": "https://github.com/jobs/frontend-engineer-remote",
  "fetched_at": "2025-10-23T14:15:00Z",
  "company": "GitHub",
  "job_title": "Frontend Engineer",
  "location": "Remote",
  "salary_range": "$140k-$180k",
  "required_qualifications": [
    "3+ years professional frontend development experience",
    "Expert-level JavaScript, TypeScript, and React",
    "Strong understanding of web performance optimization",
    "Experience with modern build tools (Webpack, Vite, etc.)",
    "Proven track record of shipping production features"
  ],
  "preferred_qualifications": [
    "Open source contributions",
    "Experience with design systems",
    "Familiarity with Ruby on Rails",
    "Previous remote work experience"
  ],
  "responsibilities": [
    "Build and maintain GitHub's web interface",
    "Collaborate with designers to implement new features",
    "Optimize frontend performance and accessibility",
    "Participate in code reviews and architectural discussions",
    "Contribute to internal design system and component library"
  ],
  "keywords": [
    "JavaScript", "TypeScript", "React", "Frontend",
    "Performance", "Webpack", "Vite", "Accessibility",
    "Design Systems", "Web Development", "Ruby on Rails"
  ],
  "candidate_profile": "We're seeking a frontend engineer who is passionate about building delightful user experiences and has a strong foundation in modern web technologies. You should be comfortable working remotely in a distributed team environment.",
  "raw_description": "[Full HTML content omitted for brevity]"
}
```

**Key Differences from Example 1:**

- **location**: "Remote" (no physical office)
- **salary_range**: USD instead of JPY
- **required_qualifications**: Fewer items (5) but more specific
- **preferred_qualifications**: Shorter list (4 items)
- **keywords**: Frontend-focused instead of backend

---

## Example 3: Data Scientist (Mixed Language)

**Source:** https://recruit.legalontech.jp/data-scientist

**Saved to:** `job-applications/Legal_Tech_Corp_Data_Scientist/job-analysis.json`

```json
{
  "url": "https://recruit.legalontech.jp/data-scientist",
  "fetched_at": "2025-10-23T16:45:00Z",
  "company": "Legal Tech Corp",
  "job_title": "Data Scientist",
  "location": "Tokyo, Japan (Hybrid)",
  "salary_range": null,
  "required_qualifications": [
    "Master's degree in Computer Science, Statistics, or related field",
    "3+ years experience in machine learning and data analysis",
    "Proficiency in Python (pandas, scikit-learn, PyTorch)",
    "Strong SQL and database skills",
    "Business-level Japanese (N2 or higher)"
  ],
  "preferred_qualifications": [
    "Experience in legal tech or document processing",
    "NLP (Natural Language Processing) expertise",
    "Cloud platform experience (AWS or GCP)",
    "Publications or conference presentations"
  ],
  "responsibilities": [
    "Develop ML models for legal document analysis",
    "Collaborate with legal experts to understand requirements",
    "Build and maintain data pipelines for document processing",
    "Present findings to stakeholders in Japanese and English",
    "Research and implement cutting-edge NLP techniques"
  ],
  "keywords": [
    "Python", "Machine Learning", "NLP", "Data Science",
    "pandas", "scikit-learn", "PyTorch", "SQL", "AWS",
    "Document Processing", "Legal Tech", "Japanese"
  ],
  "candidate_profile": "We're looking for a data scientist with strong ML fundamentals and an interest in applying AI to the legal domain. You should be comfortable working with Japanese language data and communicating with legal professionals in Japanese.",
  "raw_description": "[Full HTML content omitted for brevity]"
}
```

**Key Features:**

- **salary_range**: `null` (not listed in posting)
- **location**: Hybrid model specified
- **keywords**: Includes domain-specific terms ("Legal Tech", "Document Processing")
- **candidate_profile**: Mentions Japanese language requirement

---

## Example 4: Minimal Posting (Startup)

**Source:** https://example-startup.com/careers/full-stack-engineer

**Saved to:** `job-applications/Example_Startup_Full_Stack_Engineer/job-analysis.json`

```json
{
  "url": "https://example-startup.com/careers/full-stack-engineer",
  "fetched_at": "2025-10-23T18:00:00Z",
  "company": "Example Startup",
  "job_title": "Full Stack Engineer",
  "location": "San Francisco, CA",
  "salary_range": "Competitive",
  "required_qualifications": [
    "Strong programming skills in any language",
    "Willingness to learn and work on both frontend and backend",
    "Passion for building products"
  ],
  "preferred_qualifications": [
    "Experience with React and Node.js",
    "Startup experience"
  ],
  "responsibilities": [
    "Build features across the entire stack",
    "Work directly with founders on product direction",
    "Wear multiple hats and solve problems as they arise"
  ],
  "keywords": [
    "Full Stack", "React", "Node.js", "JavaScript",
    "Startup", "Product", "Frontend", "Backend"
  ],
  "candidate_profile": "We're a small team looking for a generalist engineer who is excited about early-stage startups and comfortable with ambiguity.",
  "raw_description": "[Full HTML content omitted for brevity]"
}
```

**Characteristics of Minimal Postings:**

- Fewer, more general required qualifications
- Vague salary information ("Competitive")
- Shorter lists overall (3 required qualifications vs. 5+)
- Generic keywords (still extracted based on what's available)
- Focus on soft skills and cultural fit

---

## Schema Validation Rules

### Required Fields (Must be present)

- `url` (string): Job posting URL
- `fetched_at` (string): ISO timestamp
- `company` (string): Non-empty company name
- `job_title` (string): Non-empty job title
- `location` (string): Non-empty location or "Remote"
- `required_qualifications` (array): At least 1 item
- `responsibilities` (array): At least 1 item
- `keywords` (array): At least 1 item (ideally 10-15)
- `candidate_profile` (string): Non-empty description
- `raw_description` (string): Original content for reference

### Optional Fields (Can be null or omitted)

- `salary_range` (string or null): If not listed in posting
- `preferred_qualifications` (array): Can be empty array

### Data Types

- Strings: Always use double quotes in JSON
- Arrays: Can be empty `[]` but required fields must have ≥1 item
- Timestamps: ISO 8601 format (`YYYY-MM-DDTHH:MM:SSZ`)

### Common Mistakes to Avoid

**❌ Missing required array items:**
```json
{
  "required_qualifications": [],  // ERROR: Must have at least 1 item
  "keywords": []  // ERROR: Must have at least 1 item
}
```

**✓ Correct:**
```json
{
  "required_qualifications": ["At least one qualification"],
  "keywords": ["keyword1", "keyword2", "..."]
}
```

**❌ Invalid JSON syntax:**
```json
{
  "company": 'Cookpad',  // ERROR: Use double quotes, not single
  "keywords": ["Python", "PostgreSQL",]  // ERROR: Trailing comma
}
```

**✓ Correct:**
```json
{
  "company": "Cookpad",
  "keywords": ["Python", "PostgreSQL"]
}
```

**❌ Missing timestamp format:**
```json
{
  "fetched_at": "Oct 23, 2025"  // ERROR: Not ISO 8601
}
```

**✓ Correct:**
```json
{
  "fetched_at": "2025-10-23T11:30:00Z"
}
```

---

## Field Descriptions Reference

| Field | Type | Required | Description | Example Values |
|-------|------|----------|-------------|----------------|
| url | string | Yes | Original job posting URL | "https://japan-dev.com/jobs/..." |
| fetched_at | string | Yes | ISO timestamp of analysis | "2025-10-23T11:30:00Z" |
| company | string | Yes | Official company name | "Cookpad", "GitHub", "Legal Tech Corp" |
| job_title | string | Yes | Exact job title from posting | "Senior Backend Engineer", "Data Scientist" |
| location | string | Yes | Office location or remote status | "Tokyo, Japan", "Remote", "San Francisco, CA" |
| salary_range | string/null | No | Compensation if listed | "¥8M-¥12M", "$140k-$180k", "Competitive", null |
| required_qualifications | array | Yes | MUST-have skills/experience | ["5+ years experience", "Python proficiency"] |
| preferred_qualifications | array | No | Nice-to-have skills | ["AWS experience", "Open source contributions"] |
| responsibilities | array | Yes | Day-to-day tasks | ["Design systems", "Mentor engineers"] |
| keywords | array | Yes | ATS-critical terms (10-15 ideal) | ["Python", "AWS", "Microservices"] |
| candidate_profile | string | Yes | Ideal candidate description | "We're looking for an experienced engineer..." |
| raw_description | string | Yes | Original HTML/text content | Full posting text for reference |

---

## Usage in Career Workflow

### Step 1: Job Analysis (This Skill)

```bash
User: "Analyze this job posting: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"
→ job-analyzer skill invoked
→ Output saved to job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json
```

### Step 2: Resume Tailoring (Future: resume-writer skill)

```python
# Reads job-analysis.json
job_data = read_json("job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json")

# Uses required_qualifications and keywords to tailor resume
tailored_resume = tailor_resume(
    master_resume="resumes/kris-cernjavic-resume.yaml",
    job_keywords=job_data["keywords"],
    required_skills=job_data["required_qualifications"]
)

# Saves to job-applications/Cookpad_Senior_Backend_Engineer/Resume_Cookpad.txt
```

### Step 3: Cover Letter Generation (Future: cover-letter-writer skill)

```python
# Reads job-analysis.json
job_data = read_json("job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json")

# Uses candidate_profile and responsibilities for personalization
cover_letter = generate_cover_letter(
    job_data=job_data,
    user_background="resumes/career-history.yaml",
    tone=job_data["candidate_profile"]  # Match their cultural fit signals
)

# Saves to job-applications/Cookpad_Senior_Backend_Engineer/CoverLetter_Cookpad.txt
```

### Step 4: Portfolio Matching (Future: portfolio-finder skill)

```python
# Reads job-analysis.json
job_data = read_json("job-applications/Cookpad_Senior_Backend_Engineer/job-analysis.json")

# Searches GitHub repos for matching technologies
portfolio = find_portfolio_examples(
    required_skills=job_data["required_qualifications"],
    keywords=job_data["keywords"],
    github_repos=load_user_repos()
)

# Saves to job-applications/Cookpad_Senior_Backend_Engineer/portfolio_examples.txt
```

---

**For skill documentation:** See `../SKILL.md`
**For Pydantic schema:** See `apps/resume-agent/resume_agent.py` (JobAnalysis class)
