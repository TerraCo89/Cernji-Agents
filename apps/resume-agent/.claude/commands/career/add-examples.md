---
description: Add portfolio code examples to a job application (updates database)
allowed-tools: mcp__resume-agent__data_list_applications, mcp__resume-agent__data_write_portfolio_examples, mcp__resume-agent__data_read_job_analysis, Read, Bash(gh:*), Task, AskUserQuestion
argument-hint: [company] [job-title] or leave empty to select interactively
---

# Add Portfolio Examples to Job Application

⚠️ **DEPRECATION NOTICE**

This command adds examples to **specific job applications** only.

For building a **reusable portfolio library** (recommended), use:
- `/career:add-portfolio` - Add examples to centralized library
- `/career:list-portfolio` - View all portfolio examples
- `/career:search-portfolio` - Search for specific examples

The portfolio library allows you to build examples over time and reference them across multiple applications.

---

Add and store portfolio code examples for a specific job application in the database.

## Arguments
- `$ARGUMENTS` - Optional: "Company JobTitle" or leave empty for interactive selection

## Process

### Step 1: Identify Target Job Application

**If arguments provided:**
Parse company and job title from `$ARGUMENTS`.

**If no arguments:**
1. List recent job applications using:
   ```
   mcp__resume-agent__data_list_applications(limit=10)
   ```
2. Display applications with numbers:
   ```
   1. Cookpad - Conversational AI Engineer
   2. LegalOn - Senior AI Engineer
   ...
   ```
3. Ask user to select by number or type company/title

### Step 2: Verify Job Application Exists

Load the job analysis to confirm it exists and get context:
```
job_analysis = mcp__resume-agent__data_read_job_analysis(company, job_title)
```

Display job requirements summary:
- Required skills (first 5)
- Preferred skills (first 5)
- Key technologies mentioned

This helps user choose relevant examples.

### Step 3: Choose Input Method

Ask user how they want to provide examples using AskUserQuestion:

**Options:**
1. **Paste text directly** - User will paste code/examples
2. **Read from files** - Provide file paths to read
3. **Parse GitHub repo** - Provide GitHub repo URL to analyze
4. **Combine multiple sources** - Mix of above

### Step 4: Collect Examples Based on Method

#### Method 1: Paste Text Directly
1. Prompt: "Paste your code examples below (can be code, project descriptions, links to work):"
2. Accept multi-line input
3. Store as-is

#### Method 2: Read from Files
1. Prompt: "Provide file paths (comma-separated or one per line):"
2. Read each file using Read tool
3. Concatenate with file headers:
   ```
   ===== FILE: path/to/file.py =====
   [file contents]
   ```

#### Method 3: Parse GitHub Repo
1. Prompt: "Provide GitHub repository URL:"
2. Extract repo info (owner/name)
3. Use Task tool with subagent_type="repo-analyzer" to analyze repo:
   ```
   Task(
     subagent_type="repo-analyzer",
     description="Analyze GitHub repo for portfolio examples",
     prompt="Analyze GitHub repository {repo_url} and extract:
     - Main technologies used
     - Key features/capabilities demonstrated
     - Relevant code examples for these job requirements: {job_requirements}
     - Project complexity and scale

     Format as structured portfolio examples showing what skills are demonstrated."
   )
   ```

#### Method 4: Combine Multiple Sources
1. Repeat steps for each source type selected
2. Concatenate all examples with clear section headers

### Step 5: Structure the Examples

Parse and structure the collected content:

**Format:**
```
PORTFOLIO EXAMPLES FOR [Company] - [Job Title]
Added: [Current Date/Time]

JOB REQUIREMENTS MATCHED:
- [Requirement 1]
- [Requirement 2]
...

EXAMPLES PROVIDED:
[Structured examples from user input]

SOURCE INFORMATION:
- [List of files/repos/sources used]
```

### Step 6: Save to Database

Save the structured examples using MCP tool:
```
mcp__resume-agent__data_write_portfolio_examples(
  company=company,
  job_title=job_title,
  content=structured_examples
)
```

### Step 7: Confirmation

Display summary:
```
✓ Portfolio examples saved successfully

Company: [Company]
Job Title: [Job Title]
Examples Added: [count or summary]
Sources: [file paths, repo URLs, or "direct input"]

These examples are now stored in the database and associated with this job application.
```

## Example Usage

### Interactive Mode
```
User: /career:add-examples