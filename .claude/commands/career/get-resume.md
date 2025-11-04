---
description: Fetch your tailored resume for a specific job application from the database
allowed-tools: mcp__sqlite-resume__query, mcp__sqlite-resume__read_records, mcp__sqlite-resume__get_table_schema
argument-hint: [job-id-or-company] [--format=full|summary] [--include-skills]
---

# /career:get-resume

Retrieves your tailored resume from the database for a specific job application. Supports flexible lookup by job ID, company name, or job URL.

## Purpose

Fetch and display a tailored resume that you've created for a specific job application, including:
- Job application details (company, title, location, salary)
- Complete resume content
- Keywords integrated into the resume
- Changes made from your master resume
- Optional: Technical skills breakdown

## Syntax

```bash
/career:get-resume [job-id-or-company] [--format=full|summary] [--include-skills]
```

## Arguments

- `job-id-or-company` (optional): Identifier for the job application
  - Job ID (e.g., `5`)
  - Company name (e.g., `Cookpad`, `"D&D Worldwide"`)
  - Partial company match (e.g., `cookpad`)
  - If omitted, shows the most recent tailored resume

- `--format=full|summary` (optional, default: `full`)
  - `full`: Shows complete resume content
  - `summary`: Shows job details, keywords, and changes only (no full resume text)

- `--include-skills` (optional): Extract and display technical skills from resume in organized categories

## Process

### Step 1: Parse Arguments

Extract the following from `$ARGUMENTS`:
- Job identifier (ID, company name, or URL fragment)
- Format preference (`--format=full` or `--format=summary`)
- Skills flag (`--include-skills`)

If no job identifier is provided, default to the most recent tailored resume.

### Step 2: Query the Database

Use the MCP SQLite tools to fetch the tailored resume:

**Query pattern:**
```sql
SELECT
    tr.id,
    tr.job_id,
    tr.content,
    tr.keywords_used_json,
    tr.changes_from_master_json,
    tr.created_at,
    tr.updated_at,
    ja.company,
    ja.job_title,
    ja.location,
    ja.salary_range,
    ja.url
FROM tailored_resumes tr
JOIN job_applications ja ON tr.job_id = ja.id
WHERE [condition based on identifier]
ORDER BY tr.created_at DESC
LIMIT 1
```

**Conditions based on identifier type:**
- Job ID: `tr.job_id = ?`
- Company name (exact): `ja.company = ?`
- Company name (partial): `ja.company LIKE '%' || ? || '%'`
- No identifier: No WHERE clause, just get latest

### Step 3: Format and Display Results

Based on the `--format` argument:

#### Format: Full (Default)

Display:
1. **Job Application Header**
   ```
   # Tailored Resume: [Company] - [Job Title]

   **Company:** [company]
   **Position:** [job_title]
   **Location:** [location]
   **Salary Range:** [salary_range]
   **Created:** [created_at]
   **Job URL:** [url]
   ```

2. **Keywords Integrated**
   ```
   ## Keywords Used
   [Parse and display keywords_used_json as bullet list or inline]
   ```

3. **Changes from Master Resume**
   ```
   ## Changes Made
   [Parse and display changes_from_master_json as bullet list]
   ```

4. **Complete Resume**
   ```
   ## Resume Content

   [Full resume content from the 'content' field]
   ```

#### Format: Summary

Display only sections 1-3 above (omit full resume content).

### Step 4: Optional - Extract Skills

If `--include-skills` flag is present:

Parse the resume content and extract technical skills into categories:
- **AI/ML Engineering:** (e.g., Multi-agent Systems, RAG, LLM Integration)
- **Languages & Frameworks:** (e.g., Python, FastAPI, LangChain)
- **Databases:** (e.g., PostgreSQL, Qdrant, SQLite-vec)
- **Cloud & Infrastructure:** (e.g., AWS, Docker, CI/CD)
- **Other Skills:** (any remaining technical skills)

Display as:
```
## Technical Skills Summary

**AI/ML Engineering:** Multi-agent Systems, RAG, LLM Integration, Prompt Engineering
**Languages:** Python, FastAPI, Pydantic
**Databases:** PostgreSQL, Qdrant, SQLite-vec
...
```

### Step 5: Handle Errors

- **No resume found:** "No tailored resume found for '[identifier]'. Available companies: [list companies from job_applications]"
- **Multiple matches:** Show list of matches and ask user to be more specific
- **Database error:** "Error querying database: [error message]"
- **Invalid format:** "Invalid format option. Use --format=full or --format=summary"

## Examples

### Example 1: Get latest resume (no arguments)
```bash
User: /career:get-resume
Result: Displays the most recent tailored resume in full format
```

### Example 2: Get resume by company name
```bash
User: /career:get-resume Cookpad
Result: Displays tailored resume for Cookpad job application
```

### Example 3: Get resume summary with skills
```bash
User: /career:get-resume Cookpad --format=summary --include-skills
Result: Shows job details, keywords, changes, and technical skills breakdown
```

### Example 4: Get resume by job ID
```bash
User: /career:get-resume 5 --format=full
Result: Displays complete tailored resume for job_id=5
```

### Example 5: Partial company match
```bash
User: /career:get-resume "D&D"
Result: Displays resume for D&D Worldwide Logistics
```

## Error Handling

### No Matching Resume
```
No tailored resume found for 'XYZ Company'.

Available tailored resumes:
1. Cookpad - Senior Applied AI Software Engineer
2. Aryza - AI Automation Engineer
3. D&D Worldwide - Senior AI Engineer

Try: /career:get-resume <company-name>
```

### Multiple Matches
```
Found multiple resumes matching 'AI':
1. Cookpad - Senior Applied AI Software Engineer (Oct 23, 2025)
2. Aryza - AI Automation Engineer (Sep 15, 2025)

Please be more specific: /career:get-resume Cookpad
```

### Invalid Format Option
```
Invalid format option: 'compact'

Valid options:
- --format=full (default)
- --format=summary

Try: /career:get-resume Cookpad --format=summary
```

## Related Commands

- `/career:tailor-resume` - Create a new tailored resume
- `/career:list-history` - View your employment history
- `/career:apply` - Complete job application workflow

## Implementation Notes

- Use `mcp__sqlite-resume__query` for flexible SQL queries with JOINs
- Parse JSON fields (`keywords_used_json`, `changes_from_master_json`) before display
- Handle company names with special characters (quotes, ampersands)
- Cache table schemas if multiple queries are needed
- Consider case-insensitive matching for company names
