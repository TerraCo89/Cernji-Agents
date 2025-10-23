---
description: Fetch and parse a job posting, caching the structured data locally OR search the database for cached job analysis
allowed-tools: mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_close, mcp__resume-agent__data_read_job_analysis, mcp__resume-agent__data_write_job_analysis, mcp__resume-agent__data_list_applications, Task, Skill
argument-hint: [job-url OR --company "Name" --title "Title"]
---

# Fetch and Cache Job Posting

Arguments: $ARGUMENTS

## Purpose
This command supports two modes:
1. **URL Mode**: Fetches a job posting from a URL, extracts structured data, and caches it to the database
2. **Database Search Mode**: Searches the database for cached job analysis using company name and job title

Both operations are atomic and idempotent - running multiple times is safe.

## Process

### Step 0: Determine Mode
First, examine $ARGUMENTS to determine which mode to use:

1. **Check if URL mode**: If $ARGUMENTS starts with `http://` or `https://`, use URL Mode (go to Step 1A)
2. **Check if Database Search mode**: If $ARGUMENTS contains `--company` or `--title`, use Database Search Mode (go to Step 1B)
3. **If unclear**: Ask user to provide either a URL or `--company` and `--title` flags

---

## DATABASE SEARCH MODE (--company and --title provided)

### Step 1B: Parse Company and Title Flags
Parse the flags from $ARGUMENTS:
1. Extract value after `--company` (handle both quoted and unquoted strings)
2. Extract value after `--title` (handle both quoted and unquoted strings)
3. If either flag is missing, return error asking for both flags

Example parsing:
- Input: `--company "Cookpad" --title "Conversational AI Engineer"`
- Result: company="Cookpad", job_title="Conversational AI Engineer"

### Step 2B: Search Database
Query the database for cached job analysis:
```
result = mcp__resume-agent__data_read_job_analysis(company, job_title)
```

### Step 3B: Handle Search Result

**If found (status="success"):**
Output the cached job analysis:
```
✓ Job analysis found in database

Company: {company}
Role: {job_title}
Location: {location}
Salary: {salary_range} (if available)

Required skills: {count}
Preferred skills: {count}
Key responsibilities: {count}
ATS keywords: {count}

Source: {url}
Fetched at: {fetched_at}
```

**If not found (status="error"):**
1. Call `mcp__resume-agent__data_list_applications()` to get all cached jobs
2. Output:
```
✗ Job analysis not found for: {company} - {job_title}

Available cached jobs in database:
1. {company1} - {role1}
2. {company2} - {role2}
...

To fetch a new job posting, run:
/career:fetch-job [job-url]
```

---

## URL MODE (URL provided)

### Step 1A: Check if Already Cached
1. Extract company and job title from the URL (or ask user if not clear from URL)
2. Check if job analysis already exists:
```
result = mcp__resume-agent__data_read_job_analysis(company, job_title)
```
3. If it exists (status="success"), skip to Step 5A and return the cached data

### Step 2A: Fetch the Job Posting
Use Playwright to navigate to the URL and capture the page content:
1. Use mcp__playwright__browser_navigate to load the job posting URL
2. Use mcp__playwright__browser_snapshot to capture the accessible page content
3. Use mcp__playwright__browser_close to clean up
4. Extract the main job description text from the snapshot

### Step 3A: Parse with Job Analyzer Agent
1. Invoke the job-analyzer skill using Skill(job-analyzer) to extract structured information
2. Provide the full job posting text to the skill
3. Request the skill return data in this JSON format:
```json
{
  "url": "original URL",
  "fetched_at": "ISO timestamp (current time)",
  "company": "Company Name",
  "job_title": "Job Title",
  "location": "Location/Remote",
  "salary_range": "Salary if available",
  "required_qualifications": ["req1", "req2"],
  "preferred_qualifications": ["pref1", "pref2"],
  "responsibilities": ["resp1", "resp2"],
  "keywords": ["keyword1", "keyword2"],
  "candidate_profile": "2-3 sentence description of ideal candidate",
  "raw_description": "full job posting text"
}
```

### Step 4A: Save to Database
Save the parsed job data using the MCP tool:
```
result = mcp__resume-agent__data_write_job_analysis(
  company=job_data["company"],
  job_title=job_data["job_title"],
  job_data=job_data
)
```

The MCP tool will:
- Validate the data against the JobAnalysis schema
- Save to the database (SQLite or file-based)
- Return success status

### Step 5A: Return Summary
Output:
```
✓ Job posting cached successfully

Company: {company}
Role: {job_title}
Location: {location}
Salary: {salary_range} (if available)

Required skills: {count}
Preferred skills: {count}
Key responsibilities: {count}
ATS keywords: {count}

Data saved and validated. Ready for use by other commands.
```

## Error Handling

### URL Mode Errors:
- If fetch fails: return clear error message with URL
- If parsing fails: return error with details (job-analyzer should return JSON)
- If validation fails: MCP tool will return validation errors
- If save fails: MCP tool will return error details

### Database Search Mode Errors:
- If flags are missing: ask user to provide both `--company` and `--title`
- If job not found: show list of all cached jobs in database
- If database read fails: return error with details

## Usage Examples

### Fetch from URL (original behavior):
```bash
/career:fetch-job https://japan-dev.com/jobs/cookpad/conversational-ai-engineer
```

### Search database by company and title:
```bash
/career:fetch-job --company "Cookpad" --title "Conversational AI Engineer"
```

### Search with unquoted arguments (if no spaces):
```bash
/career:fetch-job --company Cookpad --title Engineer
```

## Important Notes

- This command uses **MCP data tools** for database operations
- Supports both SQLite and file-based storage backends (configured in .env)
- The MCP tools handle validation using Pydantic schemas
- All data is type-safe and validated before being saved
- Database search is instant - no web fetching required
- If job not found in DB, command shows all available cached jobs
- You don't need to know about file paths or directory structures
