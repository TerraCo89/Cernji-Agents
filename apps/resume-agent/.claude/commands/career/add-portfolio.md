---
description: Add code examples to your job-agnostic portfolio library
allowed-tools: mcp__resume-agent__data_add_portfolio_example, mcp__resume-agent__data_list_portfolio_examples, Read, Bash(gh:*), Task, AskUserQuestion
argument-hint: [title] or leave empty for interactive mode
---

# Add Portfolio Example to Library

Add code examples to your centralized portfolio library. Examples are stored independently from job applications and can be referenced across multiple applications.

## Arguments
- `$ARGUMENTS` - Optional: "Example Title" or leave empty for interactive mode

## Process

### Step 1: Get Example Title

**If arguments provided:**
Use `$ARGUMENTS` as the title.

**If no arguments:**
Ask user:
```
What should this portfolio example be called?
Examples:
- "RAG Pipeline - Customer Matching"
- "Qdrant MCP Server - Agent Memory"
- "Multi-Stage Email Processing System"

Title:
```

### Step 2: Gather Example Details

Use AskUserQuestion to gather information:

**Question 1: "Where was this built?"**
Options:
- D&D Worldwide Logistics
- Aryza
- Domain
- Personal Project
- Other (specify)

**Question 2: "What project is this from?"**
Examples: "DDWL Platform", "Migration Tools", "Personal Portfolio"

**Question 3: "How do you want to provide the content?"**
Options:
1. Paste code/text directly
2. Read from specific files
3. Analyze GitHub repository
4. Combine multiple sources

### Step 3: Collect Content

#### Method 1: Paste Text Directly
Prompt:
```
Paste your code examples, explanations, or documentation below.
Include:
- Code snippets with file paths
- Brief explanation of what it demonstrates
- Any relevant metrics or outcomes

Content:
```

#### Method 2: Read from Files
Prompt:
```
Provide file paths (comma-separated or one per line).
Example:
  D:\source\ResumeAgent\repos\DDWL-Platform\backend\app\services\customer_matching_service.py
  D:\source\ResumeAgent\repos\DDWL-Platform\backend\mcp_servers\email_server_openai.py

File paths:
```

For each file:
1. Use Read tool to get content
2. Extract relevant sections if file is large
3. Format as:
   ```
   ===== FILE: {filename} =====
   Location: {full_path}

   {content or relevant excerpts}
   ```

#### Method 3: Analyze GitHub Repository
Use Task tool with repo-analyzer:
```
Task(
  subagent_type="repo-analyzer",
  description="Extract portfolio examples from GitHub repo",
  prompt="Analyze repository {repo_url} and extract:
  - Main technologies and frameworks used
  - Key features and capabilities
  - Relevant code examples for: {technologies_to_highlight}
  - Architecture patterns demonstrated

  Format as portfolio example showing technical depth."
)
```

#### Method 4: Combine Multiple Sources
Execute multiple methods above and concatenate results with section headers.

### Step 4: Extract Metadata

From the collected content, identify:

**Technologies:**
- Scan content for technology names
- Ask user to confirm/add technologies:
  ```
  Detected technologies: RAG, Redis, Supabase, FastAPI, Python

  Add or remove any? (comma-separated)
  ```

**File Paths:**
- Extract file references from content
- Format as: `{filename}:{line_number}` or `{directory}/{filename}`

**Source Repository:**
- If GitHub URL was provided, store it
- Otherwise ask: "GitHub repository URL (optional):"

**Description:**
- Auto-generate from first paragraph or ask:
  ```
  Brief description of what this demonstrates (1-2 sentences):
  ```

### Step 5: Save to Database

Use the MCP tool to save:
```
mcp__resume-agent__data_add_portfolio_example(
  title=title,
  content=full_content,
  company=company,
  project=project,
  description=description,
  technologies=technologies_list,
  file_paths=file_paths_list,
  source_repo=repo_url
)
```

### Step 6: Confirmation

Display summary:
```
✓ Portfolio example added to library

Title: {title}
Company: {company}
Project: {project}
Technologies: {technologies}
File Paths: {file_paths}
Source Repo: {repo_url}
Content Length: {content_length} characters

ID: {example_id}

This example is now stored in your portfolio library and can be:
- Searched with: /career:search-portfolio "{keyword}"
- Listed with: /career:list-portfolio
- Referenced when applying to jobs
```

## Example Usage

### Interactive Mode
```
User: /career:add-portfolio