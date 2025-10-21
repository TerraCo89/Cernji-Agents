---
description: Generate a technology proficiency matrix showing your skills based on GitHub portfolio
allowed-tools: Bash(gh:*), Write, Read, mcp__resume-agent__data_read_career_history, Task
---

# Portfolio Technology Matrix

## Process

**Step 1: Define Target Technologies**
Create a list of commonly requested technologies across software engineering roles:

**Languages:**
- Python, JavaScript, TypeScript, Go, Java, Ruby, C++, C#, PHP, Rust

**Frontend Frameworks:**
- React, Vue, Angular, Next.js, Svelte, Tailwind CSS

**Backend Frameworks:**
- Django, Flask, FastAPI, Express, Node.js, Spring Boot, Rails

**Databases:**
- PostgreSQL, MySQL, MongoDB, Redis, SQLite, DynamoDB

**Infrastructure & DevOps:**
- Docker, Kubernetes, AWS, GCP, Azure, Terraform, Ansible

**Tools & Practices:**
- Git, REST APIs, GraphQL, CI/CD, Testing (Jest/Pytest/etc), Microservices

**Step 2: Load Career History**
Load career history from database to cross-reference technologies:
```
career_history = mcp__resume-agent__data_read_career_history()
```

Extract all technologies listed across all employment entries. This provides context about professional (not just portfolio) experience.

**Step 3: Comprehensive Portfolio Scan**
Use the portfolio-finder sub-agent to search ALL your repositories for these technologies.

For each technology found, assess:
- **Example Count**: How many repos demonstrate this?
- **Recency**: When was the most recent use?
- **Complexity**: Beginner, Intermediate, or Advanced usage?
- **Documentation**: Are examples well-documented?
- **Project Size**: Toy projects vs production-quality code?
- **Professional Use**: Is this listed in your career history?

**Step 4: Calculate Portfolio Scores**
For each technology, calculate a score (0-5 stars) based on:

**5 stars (Expert):**
- 5+ repositories with substantial usage
- Used within last month
- Advanced/complex implementations
- Well-documented, production-quality code

**4 stars (Advanced):**
- 3-4 repositories with meaningful usage
- Used within last 3 months
- Intermediate to advanced complexity
- Good code quality

**3 stars (Intermediate):**
- 2-3 repositories
- Used within last 6 months
- Basic to intermediate implementations
- Reasonable quality

**2 stars (Beginner):**
- 1 repository with meaningful usage
- Or multiple repos with only trivial usage
- Used within last year

**1 star (Novice):**
- Only trivial usage (single import, minimal code)
- Or very old examples (1+ year ago)

**0 stars (No Evidence):**
- No examples found in portfolio

**Step 5: Generate Matrix**
Create a visual matrix document:

```
=================================================================
          TECHNOLOGY PROFICIENCY MATRIX
          Based on GitHub Portfolio Analysis
          Generated: [date]
=================================================================

PROGRAMMING LANGUAGES
─────────────────────────────────────────────────────────────────
Technology    | Repos | Latest Use | Level        | Score
─────────────────────────────────────────────────────────────────
Python        | 8     | 2 days ago | Advanced     | ★★★★★ (5/5)
JavaScript    | 6     | 1 week ago | Advanced     | ★★★★☆ (4/5)
TypeScript    | 4     | 2 weeks    | Intermediate | ★★★☆☆ (3/5)
Go            | 1     | 6 months   | Beginner     | ★★☆☆☆ (2/5)
Java          | 0     | Never      | None         | ☆☆☆☆☆ (0/5)

FRONTEND FRAMEWORKS
─────────────────────────────────────────────────────────────────
React         | 5     | 1 week ago | Advanced     | ★★★★☆ (4/5)
Next.js       | 2     | 3 weeks    | Intermediate | ★★★☆☆ (3/5)
Vue           | 1     | 8 months   | Beginner     | ★★☆☆☆ (2/5)
Angular       | 0     | Never      | None         | ☆☆☆☆☆ (0/5)

[Continue for all technology categories...]
```

**Step 6: Strategic Analysis**
Provide analysis in these sections:

**YOUR STRENGTHS (4-5 stars):**
List technologies where you have strong evidence. These should be prominently featured in your resume and applications.

**DEVELOPING SKILLS (2-3 stars):**
Technologies you have some experience with. Mention these if relevant to the job, but be prepared to discuss scope of experience.

**SKILL GAPS (0-1 stars):**
Common job requirements where you lack portfolio evidence. Options:
- Build example projects to fill gaps
- Avoid claiming expertise in these areas
- Target jobs that don't require these skills

**PORTFOLIO RECOMMENDATIONS:**
- Which jobs to target based on your strongest technologies
- Highest-value skills to build examples for
- Technologies to deprioritize in job search

**Step 7: Save Matrix**
Write the matrix to: `portfolio_matrix_[date].txt` in your project root.

Also create a JSON version for programmatic access: `portfolio_matrix_[date].json`

**Note:** Portfolio matrices are saved as timestamped files (not in database) since they're point-in-time snapshots for analysis.

**Step 8: Action Items**
Provide concrete next steps:
- Top 3 technologies to emphasize in applications
- Top 2 skills worth building examples for (high-demand, currently weak)
- Job search focus areas based on portfolio strengths