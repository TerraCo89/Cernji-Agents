---
description: Fetch and parse a job posting, automatically saving to database OR search database for cached job analysis
allowed-tools: mcp__playwright__browser_navigate, mcp__playwright__browser_snapshot, mcp__playwright__browser_close, mcp__sqlite-resume__query, mcp__sqlite-resume__create_record, Bash, Task, Skill
argument-hint: [job-url OR --company "Name" --title "Title"]
---

# Fetch and Cache Job Posting

Arguments: $ARGUMENTS

## Purpose
This command supports two modes:
1. **URL Mode**: Fetches a job posting from a URL, extracts structured data, and **automatically saves to database**
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
Query the database for cached job analysis using SQL:
```sql
SELECT
  ja.*,
  GROUP_CONCAT(DISTINCT CASE WHEN jq.qualification_type = 'required' THEN jq.description END) as required_quals,
  GROUP_CONCAT(DISTINCT CASE WHEN jq.qualification_type = 'preferred' THEN jq.description END) as preferred_quals,
  GROUP_CONCAT(DISTINCT jr.description) as responsibilities,
  GROUP_CONCAT(DISTINCT jk.keyword) as keywords
FROM job_applications ja
LEFT JOIN job_qualifications jq ON ja.id = jq.job_id
LEFT JOIN job_responsibilities jr ON ja.id = jr.job_id
LEFT JOIN job_keywords jk ON ja.id = jk.job_id
WHERE ja.company = ? AND ja.job_title = ?
GROUP BY ja.id
```

Use `mcp__sqlite-resume__query` to execute this.

### Step 3B: Handle Search Result

**If found:**
Output the cached job analysis:
```
✓ Job analysis found in database (ID: {id})

Company: {company}
Role: {job_title}
Location: {location}
Salary: {salary_range} (if available)

Required qualifications: {count}
Preferred qualifications: {count}
Responsibilities: {count}
ATS keywords: {count}

Source: {url}
Fetched: {fetched_at}
```

**If not found:**
1. Query all cached jobs: `SELECT company, job_title, fetched_at FROM job_applications ORDER BY created_at DESC LIMIT 10`
2. Output:
```
✗ Job analysis not found for: {company} - {job_title}

Recent cached jobs in database:
1. {company1} - {role1} (fetched {date})
2. {company2} - {role2} (fetched {date})
...

To fetch a new job posting, run:
/career:fetch-job [job-url]
```

---

## URL MODE (URL provided)

### Step 1A: Check if Already Cached
First check if we already have this job in the database:
```sql
SELECT id, company, job_title FROM job_applications WHERE url = ?
```

If found, inform user and skip to Step 5A (return cached data).

### Step 2A: Fetch the Job Posting
Use Playwright to navigate to the URL and capture the page content:
1. Use `mcp__playwright__browser_navigate` to load the job posting URL
2. Use `mcp__playwright__browser_snapshot` to capture the accessible page content
3. Use `mcp__playwright__browser_close` to clean up
4. Extract the main job description text from the snapshot

### Step 3A: Parse Job Posting
Extract structured information from the page content:

**Required Fields:**
- company (string): Company name
- job_title (string): Job title
- location (string): Location or "Remote"
- candidate_profile (string): 2-3 sentence ideal candidate description
- raw_description (string): Full job posting text
- url (string): Original URL
- fetched_at (string): Current ISO timestamp
- required_qualifications (array): At least 1 item
- responsibilities (array): At least 1 item
- keywords (array): 10-15 ATS keywords

**Optional Fields:**
- salary_range (string/null): Salary if listed
- preferred_qualifications (array): Nice-to-have skills

Parse the snapshot content to extract these fields. You can do this inline or use the job-analyzer skill if needed.

### Step 4A: Save to Database Automatically
**CRITICAL**: This step MUST execute automatically - never wait for user to ask.

Save across 4 tables using Python script via Bash tool:

```python
import json
import sqlite3
from datetime import datetime

# Prepare the job data dictionary with all parsed fields
job_data = {
    'url': '{url}',
    'company': '{company}',
    'job_title': '{job_title}',
    'location': '{location}',
    'salary_range': '{salary_range or None}',
    'candidate_profile': '{candidate_profile}',
    'raw_description': '{raw_description}',
    'fetched_at': '{fetched_at}',
    'required_qualifications': [list of strings],
    'preferred_qualifications': [list of strings],
    'responsibilities': [list of strings],
    'keywords': [list of strings]
}

# Connect to database
conn = sqlite3.connect('data/resume_agent.db')
cursor = conn.cursor()

try:
    # 1. Insert main job application record
    cursor.execute('''
        INSERT INTO job_applications
        (user_id, url, company, job_title, location, salary_range,
         candidate_profile, raw_description, fetched_at, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'default',
        job_data['url'],
        job_data['company'],
        job_data['job_title'],
        job_data['location'],
        job_data['salary_range'],
        job_data['candidate_profile'],
        job_data['raw_description'],
        job_data['fetched_at'],
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))

    job_id = cursor.lastrowid

    # 2. Insert required qualifications
    for qual in job_data['required_qualifications']:
        cursor.execute(
            'INSERT INTO job_qualifications (job_id, qualification_type, description) VALUES (?, ?, ?)',
            (job_id, 'required', qual)
        )

    # 3. Insert preferred qualifications
    for qual in job_data.get('preferred_qualifications', []):
        cursor.execute(
            'INSERT INTO job_qualifications (job_id, qualification_type, description) VALUES (?, ?, ?)',
            (job_id, 'preferred', qual)
        )

    # 4. Insert responsibilities
    for resp in job_data['responsibilities']:
        cursor.execute(
            'INSERT INTO job_responsibilities (job_id, description) VALUES (?, ?)',
            (job_id, resp)
        )

    # 5. Insert keywords
    for keyword in job_data['keywords']:
        cursor.execute(
            'INSERT INTO job_keywords (job_id, keyword) VALUES (?, ?)',
            (job_id, keyword)
        )

    conn.commit()

    # Success output (parse this to get job_id)
    print(f'SUCCESS|job_id={job_id}|tables=4|records={1 + len(job_data["required_qualifications"]) + len(job_data.get("preferred_qualifications", [])) + len(job_data["responsibilities"]) + len(job_data["keywords"])}')

except Exception as e:
    conn.rollback()
    print(f'ERROR|{str(e)}')
    raise
finally:
    conn.close()
```

**Implementation Notes:**
- Execute this Python code using the Bash tool
- Parse the output to extract job_id (look for "SUCCESS|job_id=X")
- If output contains "ERROR", report failure to user
- The transaction is atomic - all or nothing

### Step 5A: Return Summary
After successful database save, output:
```
✓ Job posting saved to database successfully

Database ID: {job_id}
Company: {company}
Role: {job_title}
Location: {location}
Salary: {salary_range} (if available)

Database records created:
- job_applications: 1 record
- job_qualifications: {required + preferred} records
- job_responsibilities: {count} records
- job_keywords: {count} records
Total: {total_records} records

The job analysis is now available for:
- /career:tailor-resume
- /career:cover-letter
- /career:analyze-job
```

## Error Handling

### URL Mode Errors:
- **Fetch fails**: Return clear error message with URL, suggest checking URL accessibility
- **Parsing fails**: Return partial data if possible, ask user for manual input of missing fields
- **Database save fails**: Show SQL error, suggest checking database permissions/disk space
- **Duplicate URL**: Inform user job already cached, show existing record

### Database Search Mode Errors:
- **Flags missing**: Ask user to provide both `--company` and `--title` flags
- **Job not found**: Show list of all cached jobs, suggest running with URL to fetch new job
- **Database error**: Show SQL error, suggest checking database file exists

## Usage Examples

### Fetch from URL (automatically saves to database):
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

- **Database First**: This command always saves to SQLite database automatically
- **No Manual Intervention**: User should never need to ask "save to database"
- **Atomic Operations**: All database insertions happen in one transaction
- **Idempotent**: Running the same URL twice checks for duplicates first
- **Multi-Table**: Data is normalized across 4 tables for efficient querying
- **Backward Compatible**: JSON files are no longer created (database is source of truth)
