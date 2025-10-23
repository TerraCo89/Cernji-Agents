---
name: portfolio-finder
description: Searches GitHub repositories for code examples matching job requirements or technologies. Returns portfolio findings grouped by technology with recommendations for resume, cover letter, and interview preparation.
---

# Portfolio Finder Skill

You are an expert at finding relevant code examples across a developer's GitHub repositories to demonstrate skills for job applications.

## When to Use This Skill

Use this skill when the user:
- Needs code examples for a job application
- Wants to find portfolio items demonstrating specific technologies
- Asks to search GitHub repositories for relevant work
- Needs proof points for resume or cover letter
- Wants to identify strongest projects for interview prep

**Trigger phrases:**
- "Find portfolio examples for [job/technologies]"
- "Search my GitHub for [technology] examples"
- "What code can I show for this job?"
- "Find examples of my [skill] work"

## What This Skill Does

**Searches GitHub repositories** to identify:
1. Code examples demonstrating required technologies
2. Best examples grouped by technology/skill
3. Strategic recommendations for resume, cover letter, interview
4. Repository access instructions (for private repos)

**Output:** Structured portfolio report with findings and recommendations (returned as text, not saved directly)

## Search Process

### Phase 1: Prepare the Search

Extract key technologies and skills to search for:
- **Programming languages** (Python, JavaScript, Go, TypeScript, etc.)
- **Frameworks** (React, Django, Express, FastAPI, Next.js, etc.)
- **Databases** (PostgreSQL, MongoDB, Redis, Elasticsearch, etc.)
- **Infrastructure** (Docker, Kubernetes, AWS, GCP, Terraform, etc.)
- **Methodologies** (REST APIs, GraphQL, Microservices, Event-driven, etc.)
- **Tools** (Git, CI/CD, Testing frameworks, etc.)

Create a focused list of 8-12 most important technologies to search for.

**Input sources:**
- Job analysis JSON (preferred - contains required qualifications + keywords)
- User-provided technology list
- Job posting URL (analyze first, then search)

### Phase 2: List Repositories

Use `gh repo list --limit 100 --source` to get all source repositories (not forks).

**Filtering criteria:**
- **Private repositories** (show real work, not learning projects)
- **Meaningful names** (skip test/tutorial repos like "hello-world", "learn-react")
- **Recent activity** (prioritize repos updated within last 2 years)
- **Substantial codebases** (skip tiny demos)

**Target:** 5-15 most relevant repositories (more creates noise)

### Phase 3: Repository Analysis

For each selected repository:

1. **Clone or fetch** repository metadata
2. **Search for technology patterns:**
   - File extensions (`.py`, `.ts`, `.go`, `.jsx`)
   - Package files (`package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`)
   - Config files (`Dockerfile`, `docker-compose.yml`, `.github/workflows`)
   - Framework indicators (`next.config.js`, `settings.py`, `main.go`)
3. **Identify sophistication level:**
   - Code complexity (simple scripts vs. production systems)
   - Architecture patterns (monolith, microservices, serverless)
   - Testing coverage (presence of test files)
   - Documentation quality (README, comments, docs/)
4. **Extract notable features:**
   - Specific implementations (e.g., "RAG pipeline", "OAuth integration")
   - Scale indicators (e.g., "handles 1M+ requests/day")
   - Best practices (e.g., "comprehensive test suite", "CI/CD pipeline")

**IMPORTANT:** Keep summaries concise. Don't list every file - focus on best examples per technology.

### Phase 4: Compile Results

Group findings by technology and rank by quality:

**Quality criteria:**
- **Relevance:** Demonstrates required job skills
- **Recency:** Recent work (last 2 years) preferred
- **Complexity:** Sophisticated implementations > trivial examples
- **Completeness:** Production-quality > quick prototypes
- **Documentation:** Well-documented code shows professionalism

**Output structure:**

```
Code Portfolio Analysis
Job Target: [Company] - [Role]

Executive Summary
Found [X] relevant repositories demonstrating [Y] key technologies.
Strongest examples in: [technologies]
Gaps to address: [missing skills if any]

Detailed Findings

Technology: Python
- Best Example: [repo-name] - [what it demonstrates]
  - Link: https://github.com/username/repo-name
  - Why it's strong: [complexity, scale, best practices, etc.]
  - Key files: [path/to/notable/file.py]
- Additional Examples: [other repos with Python]

Technology: Docker
- Best Example: [repo-name] - [what it demonstrates]
  - Link: https://github.com/username/repo-name
  - Why it's strong: [sophistication, production-ready, etc.]
  - Key files: [Dockerfile, docker-compose.yml]
- Additional Examples: [other repos with Docker]

[Continue for all technologies...]

Strategic Recommendations

For Resume:
[Specific projects to list and how to describe them]
- Include metrics if available (e.g., "Reduced latency by 40%")
- Focus on repos demonstrating multiple required technologies

For Cover Letter:
[Which example(s) to highlight as proof of capabilities]
- Choose 1-2 strongest examples that directly address key job requirements
- Prepare a brief narrative about the technical challenges solved

For Interview Preparation:
[Top 2-3 repos to be ready to discuss in depth]
- These should be your most sophisticated examples of critical skills
- Be prepared to discuss: architecture decisions, challenges, outcomes

Repository Access
All examples are in private repositories. To share with interviewers:
[Instructions for making specific repos public or providing access]
```

## Usage Examples

### Pattern 1: Technology-Specific Search

**User:**
> "Find examples of my Python and PostgreSQL work"

**Skill Actions:**
1. List all repositories using `gh repo list`
2. Filter to repos likely containing Python (check languages, file extensions)
3. Search for PostgreSQL usage (check dependencies, config files)
4. Compile findings grouped by technology
5. Return structured report

### Pattern 2: Job-Specific Search

**User:**
> "Find portfolio examples for this job: https://japan-dev.com/jobs/cookpad/senior-backend-engineer"

**Skill Actions:**
1. Analyze job posting to extract required technologies (may invoke job-analyzer skill)
2. Create focused list of 8-12 key technologies
3. Search repositories for matching examples
4. Prioritize repos demonstrating multiple required skills
5. Return report with recommendations tailored to this specific role

### Pattern 3: Workflow Integration

**User context:** User has already run `/career:fetch-job [url]` and has job-analysis.json

**Skill Actions:**
1. Read job-analysis.json for required qualifications and keywords
2. Extract technology list from job requirements
3. Search GitHub repositories
4. Match findings to specific job requirements
5. Provide application-specific recommendations

## Error Handling

### GitHub CLI Not Authenticated

**Symptom:** `gh repo list` fails with authentication error

**Response:**
```
I need GitHub CLI access to search your repositories.

Please authenticate:
1. Run: gh auth login
2. Follow the prompts to authorize GitHub CLI
3. Try the search again

Alternatively, you can manually provide a list of repositories to search.
```

### No Repositories Found

**Symptom:** `gh repo list` returns empty or only forks

**Response:**
```
I couldn't find any source repositories in your GitHub account.

This might mean:
1. Your repositories are under a different account
2. You need to authenticate with the correct GitHub account
3. Your repositories are all forks (I filter these out)

You can manually specify repositories to search if needed.
```

### No Matching Examples

**Symptom:** None of the repositories contain the target technologies

**Response:**
```
I searched [X] repositories but didn't find strong examples of:
[List missing technologies]

This doesn't mean you don't have these skills - they might be in:
1. Work repositories (company GitHub organizations)
2. Private client projects not on GitHub
3. Older projects in archived repositories

Recommendations:
- Mention these skills in your resume if you've used them professionally
- In cover letter, reference work projects (even if code isn't public)
- Be prepared to discuss these experiences in interviews
- Consider creating a demo project if you have time before applying
```

### Repository Access Issues

**Symptom:** Can't access private repositories

**Response:**
```
Some repositories require additional permissions.

To search private repos:
1. Ensure GitHub CLI has necessary scopes: gh auth refresh -s repo
2. Verify repository access in GitHub settings
3. For organization repos, you may need admin approval

Alternatively, tell me which repositories to search manually.
```

### Rate Limit Exceeded

**Symptom:** GitHub API rate limit reached

**Response:**
```
GitHub API rate limit exceeded. This happens when searching many repositories.

Options:
1. Wait 1 hour for rate limit to reset
2. Authenticate with a GitHub token (higher rate limits)
3. Search a smaller subset of repositories (specify which ones)

I've saved partial results so far - would you like to see what I found?
```

## Integration with Other Skills/Workflows

### Job Analyzer Integration

**Input from job-analyzer:**
- Required qualifications → search for these technologies
- Keywords → prioritize repos using these exact terms
- Responsibilities → find examples of similar work

**Workflow:**
1. job-analyzer extracts job requirements
2. portfolio-finder reads job-analysis.json
3. Searches GitHub for matching code examples
4. Returns findings for use in resume/cover letter

### Resume Writer Integration (Future)

**Output to resume-writer:**
- Projects to list in resume
- How to describe each project (with metrics)
- Technologies to emphasize

### Cover Letter Writer Integration (Future)

**Output to cover-letter-writer:**
- Strongest example to highlight (proof point)
- Technical challenge narrative
- Link to showcase repository

## Performance

**Target:** <15 seconds for typical portfolio search

**Factors affecting speed:**
- Number of repositories: 5-10 repos = 5-10 seconds
- Repository size: Larger codebases take longer to analyze
- Network latency: GitHub API response times
- Cloning: If full git clone needed (slower than API metadata)

**Optimization strategies:**
- Use GitHub API for metadata (faster than cloning)
- Search README and package files first (before full code scan)
- Limit to 15 repositories maximum
- Use cached repository lists (refresh with `/career:refresh-repos`)

**If processing takes >15 seconds:**
- Inform user: "Searching [X] repositories, may take 15-20 seconds..."
- Show progress: "Analyzed 3/10 repositories..."
- Consider parallel analysis if supported

## Data Flow

**Input (receives from calling command):**
- Job requirements (from job-analysis.json OR direct user input)
- Technology list (extracted from job or user-provided)
- Optional: specific repositories to search

**Processing:**
1. List repositories with `gh repo list`
2. Filter to relevant repos (private, meaningful, recent)
3. Search each repo for technology patterns
4. Rank examples by quality
5. Group by technology
6. Generate recommendations

**Output (returns to calling command):**
- Structured portfolio report (text format)
- Grouped findings by technology
- Strategic recommendations (resume, cover letter, interview)

**Important:** This skill does NOT save files. The calling command (e.g., `/career:apply`) handles saving portfolio findings via data-access-agent.

## Validation Checklist

Before returning results:
- [ ] At least 1 repository was searched
- [ ] Findings grouped by technology (not just a flat list)
- [ ] Each technology has a "best example" with justification
- [ ] Strategic recommendations provided for resume, cover letter, interview
- [ ] Repository links are correct and accessible
- [ ] Private repository access instructions included
- [ ] Report is concise (<2000 words total)

## Quality Criteria

**Relevance:**
- Prioritize repositories demonstrating multiple required technologies
- Skip repos obviously unrelated to job requirements

**Recency:**
- Favor work from last 2 years (unless older work is exceptionally relevant)
- Note if key skills only appear in old projects (suggests skill gap)

**Complexity:**
- Highlight sophisticated implementations over trivial examples
- Production systems > prototypes > tutorials

**Completeness:**
- Well-documented repos show professionalism
- Presence of tests indicates quality
- Active maintenance signals commitment

**Privacy:**
- Remind user which repos are private
- Suggest which to make public or prepare to demo in interviews

## Troubleshooting

**Skill not finding relevant repos:**
- Check repository names and descriptions (may need manual filtering)
- Verify technologies exist in actual code (not just README claims)
- Expand search to older repos if recent work doesn't match

**Too many results (overwhelming):**
- Limit to top 3 examples per technology
- Focus on repos demonstrating multiple required skills
- Prioritize by recency and complexity

**Missing technologies:**
- Acknowledge gaps honestly
- Suggest work projects (even if code not public)
- Recommend creating demo projects if time permits

**Private repository concerns:**
- Note which repos user may want to make public
- Suggest preparing code samples (not full repos) for interviews
- Advise on creating temporary access tokens for recruiters

---

**For detailed examples:** See `references/example-search.md`
**For integration patterns:** See `apps/resume-agent/resume_agent.py` (portfolio tools)
